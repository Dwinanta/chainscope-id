"""Scheduled public-price alert checker with explicit delivery failures."""

import math
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests

REQUEST_TIMEOUT = 15
ALERT_PAGE_SIZE = 1000
COIN_BATCH_SIZE = 250


def get_supabase_headers(api_key: str) -> dict[str, str]:
    if not api_key or not api_key.strip():
        raise ValueError("SUPABASE_KEY is required.")
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _json_response(response: Any) -> Any:
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        raise ValueError("An external service returned invalid JSON.") from exc


def _fetch_active_alerts(
    session: requests.Session,
    base_url: str,
    headers: dict[str, str],
) -> list[dict]:
    alerts = []
    offset = 0
    while True:
        page_headers = {
            **headers,
            "Range-Unit": "items",
            "Range": f"{offset}-{offset + ALERT_PAGE_SIZE - 1}",
        }
        data = _json_response(session.get(
            f"{base_url}/rest/v1/alerts",
            params={
                "is_active": "eq.true",
                "select": (
                    "id,user_id,coin_id,symbol,condition,target_price,"
                    "currency,note"
                ),
                "order": "id.asc",
            },
            headers=page_headers,
            timeout=REQUEST_TIMEOUT,
        ))
        if not isinstance(data, list):
            raise ValueError("Supabase returned an invalid active-alert response.")
        alerts.extend(row for row in data if isinstance(row, dict))
        if len(data) < ALERT_PAGE_SIZE:
            return alerts
        offset += ALERT_PAGE_SIZE


def _fetch_prices(
    session: requests.Session,
    alerts: list[dict],
    api_key: str,
) -> dict[str, dict]:
    coin_ids = sorted({
        str(alert.get("coin_id", "")).strip()
        for alert in alerts
        if alert.get("coin_id")
    })
    currencies = sorted({
        str(alert.get("currency", "")).strip().lower()
        for alert in alerts
        if alert.get("currency")
    })
    if not coin_ids or not currencies:
        return {}

    headers = {"x-cg-demo-api-key": api_key} if api_key else {}
    prices = {}
    for start in range(0, len(coin_ids), COIN_BATCH_SIZE):
        batch = coin_ids[start : start + COIN_BATCH_SIZE]
        payload = _json_response(session.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ",".join(batch),
                "vs_currencies": ",".join(currencies),
            },
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        ))
        if not isinstance(payload, dict):
            raise ValueError("CoinGecko returned an invalid price response.")
        prices.update(payload)
    return prices


def _valid_alert(alert: dict) -> tuple[float, str] | None:
    if alert.get("condition") not in {"above", "below"}:
        return None
    currency = str(alert.get("currency", "")).strip().lower()
    if len(currency) != 3 or not currency.isalpha():
        return None
    try:
        target = float(alert.get("target_price"))
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(target) or target <= 0:
        return None
    if not all(alert.get(field) for field in ("id", "user_id", "coin_id")):
        return None
    return target, currency


def _get_telegram_chat_id(
    session: requests.Session,
    base_url: str,
    headers: dict[str, str],
    user_id: str,
    cache: dict[str, str | None],
) -> str | None:
    if user_id not in cache:
        profiles = _json_response(session.get(
            f"{base_url}/rest/v1/profiles",
            params={"id": f"eq.{user_id}", "select": "telegram_chat_id"},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        ))
        if not isinstance(profiles, list):
            raise ValueError("Supabase returned an invalid profile response.")
        chat_id = (
            profiles[0].get("telegram_chat_id")
            if profiles and isinstance(profiles[0], dict)
            else None
        )
        cache[user_id] = str(chat_id).strip() if chat_id else None
    return cache[user_id]


def _send_telegram(
    session: requests.Session,
    token: str,
    chat_id: str,
    alert: dict,
    target: float,
    currency: str,
    current_price: float,
) -> bool:
    note = str(alert.get("note") or "").strip()
    message = (
        "Price alert triggered\n"
        f"{str(alert.get('symbol') or alert['coin_id']).upper()}: "
        f"{current_price:,.8g} {currency.upper()}\n"
        f"Condition: {alert['condition']} {target:,.8g} {currency.upper()}"
    )
    if note:
        message += f"\nNote: {note[:500]}"

    response = session.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=REQUEST_TIMEOUT,
    )
    payload = _json_response(response)
    return isinstance(payload, dict) and payload.get("ok") is True


def _deactivate_alert(
    session: requests.Session,
    base_url: str,
    headers: dict[str, str],
    alert_id: str,
) -> None:
    response = session.patch(
        f"{base_url}/rest/v1/alerts",
        params={"id": f"eq.{alert_id}", "is_active": "eq.true"},
        headers=headers,
        json={
            "is_active": False,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()


def run_alert_checks(
    env: dict[str, str] | None = None,
    session: requests.Session | None = None,
) -> bool:
    """Run one alert sweep; leave failed notifications active for a later retry."""
    env = os.environ if env is None else env
    session = requests.Session() if session is None else session
    base_url = env.get("SUPABASE_URL", "").rstrip("/")
    api_key = env.get("SUPABASE_KEY", "")
    telegram_token = env.get("TELEGRAM_BOT_TOKEN", "")
    coingecko_key = env.get("COINGECKO_API_KEY", "")
    if not base_url or not api_key or not telegram_token:
        print("Required alert-check environment variables are missing.")
        return False

    headers = get_supabase_headers(api_key)
    try:
        alerts = _fetch_active_alerts(session, base_url, headers)
        if not alerts:
            print("No active alerts.")
            return True
        prices = _fetch_prices(session, alerts, coingecko_key)
    except (requests.RequestException, ValueError):
        print("Alert check failed while fetching active alerts or market prices.")
        return False

    profile_cache: dict[str, str | None] = {}
    successful = True
    for alert in alerts:
        normalized = _valid_alert(alert)
        if normalized is None:
            print(f"Skipping invalid alert record {alert.get('id', 'unknown')}.")
            continue
        target, currency = normalized
        coin_prices = prices.get(str(alert["coin_id"]), {})
        current_price = (
            coin_prices.get(currency) if isinstance(coin_prices, dict) else None
        )
        try:
            current_price = float(current_price)
        except (TypeError, ValueError, OverflowError):
            continue
        if not math.isfinite(current_price) or current_price <= 0:
            continue
        hit = (
            current_price >= target
            if alert["condition"] == "above"
            else current_price <= target
        )
        if not hit:
            continue

        try:
            chat_id = _get_telegram_chat_id(
                session, base_url, headers, str(alert["user_id"]), profile_cache
            )
            if chat_id and not _send_telegram(
                session,
                telegram_token,
                chat_id,
                alert,
                target,
                currency,
                current_price,
            ):
                print(f"Telegram did not confirm delivery for alert {alert['id']}.")
                successful = False
                continue
            _deactivate_alert(session, base_url, headers, str(alert["id"]))
            if chat_id:
                print(f"Alert {alert['id']} delivered and marked triggered.")
            else:
                print(
                    f"Alert {alert['id']} triggered but no Telegram chat is "
                    "configured; marked triggered."
                )
        except (requests.RequestException, ValueError):
            print(f"Delivery or status update failed for alert {alert['id']}.")
            successful = False
    return successful


def main() -> int:
    return 0 if run_alert_checks() else 1


if __name__ == "__main__":
    sys.exit(main())
