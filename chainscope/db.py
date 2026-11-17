"""Modul koneksi database dan query Supabase."""
import base64
from datetime import datetime, timedelta
import json
import logging
import os
import re
from urllib.parse import urlparse

import streamlit as st
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseConfigError(ValueError):
    """Error ketika konfigurasi SUPABASE_URL atau SUPABASE_KEY tidak valid."""


def _clean_secret_value(value: object) -> str:
    """Bersihkan spasi, karakter kontrol/BOM, dan tanda kutip berlebih pada secret."""
    if not isinstance(value, str):
        return ""
    cleaned = value.strip().strip("\ufeff\r\n\t ")
    while len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.strip('"\' \t\r\n\ufeff')
    return cleaned


def extract_supabase_project_ref(api_key: str) -> str | None:
    """Ekstrak klaim 'ref' (project ID) dari payload JWT Supabase tanpa mencetak key."""
    cleaned_key = _clean_secret_value(api_key)
    parts = cleaned_key.split(".")
    if len(parts) != 3:
        return None
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    try:
        decoded_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(decoded_bytes.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("iss") != "supabase":
        return None
    ref = payload.get("ref")
    if isinstance(ref, str) and re.fullmatch(r"[a-z0-9]{10,40}", ref):
        return ref
    return None


def normalize_supabase_url(raw_url: object, api_key: str = "") -> str:
    """Validasi dan normalisasi SUPABASE_URL ke format https://<hostname>."""
    cleaned = _clean_secret_value(raw_url)
    if not cleaned:
        raise SupabaseConfigError(
            "SUPABASE_URL atau SUPABASE_KEY belum di-set di secrets.toml"
        )

    # Perbaiki skema ganda seperti https://https://...
    cleaned = re.sub(
        r"^(https?://)+",
        lambda m: "https://" if "https://" in m.group(0).lower() else "http://",
        cleaned,
        flags=re.IGNORECASE,
    )

    if "://" not in cleaned and cleaned.lower().endswith(".supabase.co"):
        cleaned = f"https://{cleaned}"

    parsed = urlparse(cleaned)
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname or ""
    netloc = parsed.netloc or ""

    if (
        scheme not in {"http", "https"}
        or not hostname
        or any(ch.isspace() or ch in {'"', "'", "\\"} for ch in netloc)
        or ("." not in hostname and hostname != "localhost")
    ):
        raise SupabaseConfigError(
            f"Format SUPABASE_URL tidak valid ({hostname or cleaned!r}). "
            "Gunakan format https://<project-ref>.supabase.co"
        )

    jwt_ref = extract_supabase_project_ref(api_key)
    if jwt_ref and hostname.lower().endswith(".supabase.co"):
        expected_host = f"{jwt_ref}.supabase.co"
        if hostname.lower() != expected_host.lower():
            raise SupabaseConfigError(
                f"Hostname SUPABASE_URL ({hostname}) tidak sesuai dengan project "
                f"pada SUPABASE_KEY ({expected_host}). Periksa konfigurasi Secrets."
            )

    return f"{scheme}://{netloc}"


def _read_secret_or_env(key_name: str, section_field: str = "") -> str:
    """Baca konfigurasi dari st.secrets, section [supabase], atau environment variable."""
    raw = ""
    try:
        raw = st.secrets.get(key_name, "")
        if not raw and section_field:
            section = st.secrets.get("supabase", {})
            if isinstance(section, dict):
                raw = section.get(section_field, "") or section.get(key_name, "")
    except Exception:
        raw = ""
    if not raw:
        raw = os.environ.get(key_name, "")
    return _clean_secret_value(raw)


def get_supabase_config() -> tuple[str, str]:
    """Ambil dan validasi pasangan (url, key) Supabase."""
    raw_url = _read_secret_or_env("SUPABASE_URL", "url")
    key = _read_secret_or_env("SUPABASE_KEY", "key")
    if not raw_url or not key:
        raise SupabaseConfigError(
            "SUPABASE_URL atau SUPABASE_KEY belum di-set di secrets.toml"
        )
    url = normalize_supabase_url(raw_url, key)
    return url, key


def get_configured_supabase_host() -> str:
    """Kembalikan hostname SUPABASE_URL (aman untuk pesan diagnostik tanpa membocorkan key)."""
    raw_url = _read_secret_or_env("SUPABASE_URL", "url")
    if not raw_url:
        return "<SUPABASE_URL kosong>"
    try:
        parsed = urlparse(raw_url if "://" in raw_url else f"https://{raw_url}")
        return parsed.hostname or raw_url
    except Exception:
        return "<SUPABASE_URL tidak valid>"


@st.cache_resource
def _create_cached_supabase_client(url: str, key: str) -> Client:
    """Inisialisasi Supabase client yang di-cache berdasarkan pasangan (url, key)."""
    return create_client(url, key)


def get_supabase() -> Client:
    """Inisialisasi Supabase client (di-cache agar tidak reconnect terus)."""
    url, key = get_supabase_config()
    return _create_cached_supabase_client(url, key)


get_supabase.clear = _create_cached_supabase_client.clear


def get_user_profile(user_id: str) -> dict:
    supabase = get_supabase()
    res = (
        supabase.table("profiles")
        .select("role,subscription_tier,subscription_end,telegram_chat_id")
        .eq("id", user_id)
        .execute()
    )
    return res.data[0] if res.data else {}


def upgrade_to_premium(user_id: str):
    """Upgrade a profile to premium for 30 days."""
    subscription_end = (datetime.now() + timedelta(days=30)).date().isoformat()
    return get_supabase().table("profiles").update({
        "subscription_tier": "premium",
        "subscription_end": subscription_end,
    }).eq("id", user_id).execute()


def delete_user(user_id: str) -> bool:
    """Delete a user's app data and, when configured, their Auth account.

    Returns True when the Auth account was deleted. Without a service role
    key, only app data can be removed; the Auth account remains.
    """
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("ID pengguna wajib diisi.")
    clean_user_id = user_id.strip()

    service_role_key = _read_secret_or_env("SUPABASE_SERVICE_ROLE_KEY", "service_role_key")
    raw_supabase_url = _read_secret_or_env("SUPABASE_URL", "url")
    if service_role_key:
        if not raw_supabase_url:
            raise ValueError("SUPABASE_URL belum diatur di secrets.toml.")
        supabase_url = normalize_supabase_url(raw_supabase_url, service_role_key)
        supabase = create_client(supabase_url, service_role_key)
    else:
        supabase = get_supabase()

    for table in ("trades", "alerts", "watchlists"):
        supabase.table(table).delete().eq("user_id", clean_user_id).execute()
        if table == "trades":
            _invalidate_user_trades_cache()
    supabase.table("profiles").delete().eq("id", clean_user_id).execute()

    if not service_role_key:
        return False

    supabase.auth.admin.delete_user(clean_user_id)
    return True

def add_trade(user_id: str, coin_id: str, symbol: str, side: str, amount: float, price_usd: float, trade_time: str, source: str = "manual", strategy_tag: str = "Swing"):
    supabase = get_supabase()
    data = {
        "user_id": user_id,
        "coin_id": coin_id.lower(),
        "symbol": symbol.upper(),
        "side": side.lower(),
        "amount": amount,
        "price_usd": price_usd,
        "trade_time": trade_time,
        "source": source,
        "strategy_tag": strategy_tag
    }
    result = supabase.table("trades").insert(data).execute()
    _invalidate_user_trades_cache()
    return result

@st.cache_data(ttl=30, max_entries=128, show_spinner=False)
def get_user_trades(user_id: str, limit: int = 100):
    supabase = get_supabase()
    res = (
        supabase.table("trades")
        .select("coin_id,symbol,side,amount,price_usd,trade_time,strategy_tag")
        .eq("user_id", user_id)
        .order("trade_time", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


@st.cache_data(ttl=30, max_entries=128, show_spinner=False)
def get_user_trades_page(
    user_id: str,
    page_size: int = 100,
    offset: int = 0,
) -> tuple[list[dict], bool]:
    """Fetch one user-scoped trade page and indicate whether more rows exist."""
    if page_size <= 0 or offset < 0:
        raise ValueError("Ukuran halaman dan offset transaksi tidak valid.")

    response = (
        get_supabase()
        .table("trades")
        .select("coin_id,symbol,side,amount,price_usd,trade_time,strategy_tag")
        .eq("user_id", user_id)
        .order("trade_time", desc=True)
        .order("id", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data
    return rows[:page_size], len(rows) > page_size


@st.cache_data(ttl=30, max_entries=32, show_spinner=False)
def get_all_user_trades(user_id: str, page_size: int = 500) -> list[dict]:
    """Fetch complete user trade history in bounded pages."""
    if page_size <= 0:
        raise ValueError("Ukuran halaman transaksi harus lebih besar dari nol.")

    supabase = get_supabase()
    trades = []
    start = 0
    while True:
        response = (
            supabase.table("trades")
            .select("id,coin_id,symbol,side,amount,price_usd,trade_time,strategy_tag")
            .eq("user_id", user_id)
            .order("trade_time", desc=True)
            .order("id", desc=True)
            .range(start, start + page_size - 1)
            .execute()
        )
        page = response.data
        trades.extend(page)
        if len(page) < page_size:
            return trades
        start += page_size


def add_trades(user_id: str, trades: list[dict]) -> None:
    """Insert a batch of normalized trades with one database request."""
    if not trades:
        return

    rows = [
        {
            "user_id": user_id,
            "coin_id": str(trade["coin_id"]).lower(),
            "symbol": str(trade["symbol"]).upper(),
            "side": str(trade["side"]).lower(),
            "amount": trade["amount"],
            "price_usd": trade["price_usd"],
            "trade_time": trade["trade_time"],
            "source": trade.get("source", "csv"),
            "strategy_tag": trade.get("strategy_tag", "Swing"),
        }
        for trade in trades
    ]
    get_supabase().table("trades").insert(rows).execute()
    _invalidate_user_trades_cache()


def _invalidate_user_trades_cache() -> None:
    get_user_trades.clear()
    get_user_trades_page.clear()
    get_all_user_trades.clear()

def get_all_users_dev():
    """Hanya untuk role 'dev'."""
    supabase = get_supabase()
    res = supabase.table("profiles").select("*").execute()
    return res.data

def delete_trade(trade_id: str):
    supabase = get_supabase()
    result = supabase.table("trades").delete().eq("id", trade_id).execute()
    _invalidate_user_trades_cache()
    return result

def delete_all_user_trades(user_id: str):
    """Menghapus seluruh riwayat transaksi milik user tertentu."""
    supabase = get_supabase()
    result = supabase.table("trades").delete().eq("user_id", user_id).execute()
    _invalidate_user_trades_cache()
    return result

# ==========================================
# FUNGSI UNTUK PRICE ALERTS
# ==========================================

def add_alert(user_id: str, coin_id: str, symbol: str, condition: str, target_price: float, currency: str, note: str = ""):
    supabase = get_supabase()
    data = {
        "user_id": user_id,
        "coin_id": coin_id.lower(),
        "symbol": symbol.upper(),
        "condition": condition,
        "target_price": target_price,
        "currency": currency.upper(),
        "note": note
    }
    return supabase.table("alerts").insert(data).execute()

def count_user_alerts(user_id: str) -> int:
    """Return the number of active alerts belonging to a user."""
    response = (
        get_supabase()
        .table("alerts")
        .select("id")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    return len(response.data)

def get_user_alerts(user_id: str):
    supabase = get_supabase()
    res = (
        supabase.table("alerts")
        .select("coin_id,symbol,condition,target_price,currency,is_active,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data

def delete_alert(alert_id: str):
    supabase = get_supabase()
    return supabase.table("alerts").delete().eq("id", alert_id).execute()

def mark_alert_triggered(alert_id: str):
    supabase = get_supabase()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    return supabase.table("alerts").update({"is_active": False, "triggered_at": now}).eq("id", alert_id).execute()

def update_telegram_chat_id(user_id: str, chat_id: str | None):
    supabase = get_supabase()
    return supabase.table("profiles").update({"telegram_chat_id": chat_id}).eq("id", user_id).execute()

def get_all_active_alerts():
    """Mengambil SEMUA alert aktif dari semua user (untuk cron job)."""
    supabase = get_supabase()
    res = supabase.table("alerts").select("*").eq("is_active", True).execute()
    return res.data
# ==========================================
# FUNGSI UNTUK WATCHLIST (SUPABASE)
# ==========================================

def get_user_watchlist(user_id: str, limit: int | None = None) -> list[str]:
    if limit is not None and limit <= 0:
        raise ValueError("Batas watchlist harus lebih besar dari nol.")
    query = (
        get_supabase()
        .table("watchlists")
        .select("coin_id")
        .eq("user_id", user_id)
    )
    if limit is not None:
        query = query.order("coin_id").limit(limit)
    res = query.execute()
    return [row["coin_id"] for row in res.data]


def sync_user_watchlist(user_id: str, current_ids: list[str], desired_ids: list[str]) -> None:
    """Apply only the user's watchlist additions and removals."""
    current = set(current_ids)
    desired = set(desired_ids)
    removed = sorted(current - desired)
    added = sorted(desired - current)
    supabase = get_supabase()

    if removed:
        (
            supabase.table("watchlists")
            .delete()
            .eq("user_id", user_id)
            .in_("coin_id", removed)
            .execute()
        )
    if added:
        supabase.table("watchlists").upsert(
            [{"user_id": user_id, "coin_id": coin_id} for coin_id in added]
        ).execute()


def add_to_watchlist(user_id: str, coin_id: str):
    supabase = get_supabase()
    try:
        supabase.table("watchlists").upsert({
            "user_id": user_id, 
            "coin_id": coin_id
        }).execute()
    except Exception as e:
        print(f"Error add watchlist: {e}")

def remove_from_watchlist(user_id: str, coin_id: str):
    supabase = get_supabase()
    return supabase.table("watchlists").delete().eq("user_id", user_id).eq("coin_id", coin_id).execute()

def clear_user_watchlist(user_id: str):
    supabase = get_supabase()
    return supabase.table("watchlists").delete().eq("user_id", user_id).execute()
