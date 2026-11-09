"""Evidence-bounded crypto research snapshots and report prompts."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence

import pandas as pd

from . import indicators


def _finite_number(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def build_asset_snapshot(
    market_row: Mapping,
    history: pd.DataFrame,
    currency: str,
) -> dict:
    """Return provider data and derived technical measures without filling gaps."""
    market_fields = {
        "current_price": "current_price",
        "market_cap": "market_cap",
        "total_volume": "total_volume",
        "circulating_supply": "circulating_supply",
        "total_supply": "total_supply",
        "max_supply": "max_supply",
        "fully_diluted_valuation": "fully_diluted_valuation",
        "market_cap_rank": "market_cap_rank",
        "price_change_percentage_24h": "price_change_24h_pct",
        "ath": "all_time_high",
        "ath_change_percentage": "change_from_all_time_high_pct",
    }
    verified = {
        "source": "CoinGecko",
        "asset_id": str(market_row.get("id", "")),
        "name": str(market_row.get("name", "")),
        "symbol": str(market_row.get("symbol_upper", market_row.get("symbol", ""))).upper(),
        "currency": currency.upper(),
    }
    provider_updated_at = market_row.get("last_updated")
    if isinstance(provider_updated_at, str) and provider_updated_at.strip():
        verified["provider_updated_at"] = provider_updated_at.strip()
    for source, output in market_fields.items():
        number = _finite_number(market_row.get(source))
        if number is not None:
            verified[output] = number

    technical: dict[str, float | int | str] = {}
    if history is not None and not history.empty and "price" in history:
        prices = pd.to_numeric(history["price"], errors="coerce")
        prices = prices.replace([float("inf"), float("-inf")], pd.NA).dropna()
        prices = prices[prices > 0]
        if not prices.empty:
            technical["history_points"] = int(len(prices))
            technical["history_currency"] = currency.upper()
            technical["first_observation_price"] = float(prices.iloc[0])
            technical["last_observation_price"] = float(prices.iloc[-1])
            if "waktu" in history:
                timestamps = pd.to_datetime(
                    history["waktu"], utc=True, errors="coerce"
                ).dropna()
                if not timestamps.empty:
                    technical["history_start_utc"] = timestamps.min().isoformat()
                    technical["history_end_utc"] = timestamps.max().isoformat()
            technical["period_change_pct"] = float(
                (prices.iloc[-1] / prices.iloc[0] - 1) * 100
            )
            returns = prices.pct_change().replace([float("inf"), float("-inf")], pd.NA).dropna()
            if len(returns) >= 2:
                technical["observation_return_volatility_pct"] = float(
                    returns.std(ddof=1) * 100
                )
            if len(prices) >= 14:
                rsi_value = _finite_number(indicators.rsi(prices).iloc[-1])
                if rsi_value is not None:
                    technical["rsi"] = rsi_value
            for period in (20, 50):
                if len(prices) >= period:
                    technical[f"sma_{period}"] = float(
                        indicators.sma(prices, period).iloc[-1]
                    )

    return {
        "verified_market_data": verified,
        "derived_historical_indicators": technical,
        "fundamental_data_status": (
            "Financial statements are unavailable. Market capitalization, "
            "volume, valuation, and supply fields are provider market/token "
            "metrics, not a full fundamental analysis."
        ),
    }


def build_report_context(
    snapshots: Sequence[Mapping],
    news: Sequence[Mapping] = (),
    market_conditions: Mapping | None = None,
) -> dict:
    """Create a public-data-only context with explicit evidence categories."""
    return {
        "evidence_note": (
            "Market values are provider observations; indicators are derived "
            "from the supplied historical prices. News entries are headlines "
            "from the configured feed. Missing facts are unknown."
        ),
        "assets": list(snapshots),
        "market_conditions": (
            dict(market_conditions) if market_conditions is not None else None
        ),
        "news_headlines": [
            {
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
            }
            for item in news
        ],
    }


def build_prompt(context: Mapping, question: str) -> str:
    """Prompt the existing model to interpret only supplied public evidence."""
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Pertanyaan riset tidak boleh kosong.")
    if len(cleaned_question) > 1000:
        raise ValueError("Pertanyaan riset maksimal 1.000 karakter.")
    serialized = json.dumps(context, ensure_ascii=False, allow_nan=False)
    return (
        "You are a cautious financial research assistant. Use only the supplied "
        "public data and headlines. Clearly separate verified provider data, "
        "derived historical indicators, and AI interpretation. Do not invent "
        "prices, news, fundamentals, events, or missing values. If evidence is "
        "insufficient, say so. Explain relevant risks, avoid personalized "
        "financial advice, and state that historical observations do not "
        "predict future performance.\n"
        f"Evidence context: {serialized}\n"
        f"Research question (JSON string): "
        f"{json.dumps(cleaned_question, ensure_ascii=False)}"
    )


def build_report_text(context: Mapping, ai_interpretation: str | None = None) -> str:
    """Render a concise, exportable report with source categories intact."""
    lines = [
        "# ChainScope ID research report",
        "",
        "## Evidence and limitations",
        str(context.get("evidence_note", "")),
        "This report is research support, not investment advice.",
    ]
    for asset in context.get("assets", []):
        data = asset.get("verified_market_data", {})
        indicators_data = asset.get("derived_historical_indicators", {})
        lines.extend([
            "",
            f"## {data.get('name') or data.get('asset_id', 'Asset')} "
            f"({data.get('symbol', '')})",
            "",
            "### Verified provider observations",
            f"- Asset ID: {data.get('asset_id', 'Not available')}",
            f"- Provider last updated: "
            f"{data.get('provider_updated_at', 'Not supplied')}",
            f"- Latest displayed price: "
            f"{data.get('current_price', 'Not available')} "
            f"{data.get('currency', '')}",
            f"- 24-hour price change: "
            f"{data.get('price_change_24h_pct', 'Not available')}%",
            f"- Market capitalization: "
            f"{data.get('market_cap', 'Not available')}",
            f"- 24-hour volume: {data.get('total_volume', 'Not available')}",
            f"- Circulating supply: "
            f"{data.get('circulating_supply', 'Not available')}",
            f"- Total / maximum supply: "
            f"{data.get('total_supply', 'Not available')} / "
            f"{data.get('max_supply', 'Not available')}",
            f"- Fully diluted valuation: "
            f"{data.get('fully_diluted_valuation', 'Not available')}",
            "",
            "### Derived historical indicators",
        ])
        if indicators_data:
            lines.extend(
                f"- {key}: {value}"
                for key, value in indicators_data.items()
            )
        else:
            lines.append("- Not available from the selected history.")
        lines.append(
            f"- Fundamentals: {asset.get('fundamental_data_status', 'Not available.')}"
        )

    lines.extend(["", "## News headlines (not independently summarized)"])
    headlines = context.get("news_headlines", [])
    if headlines:
        lines.extend(
            f"- {item.get('title', '')} — {item.get('source', '')} "
            f"({item.get('url', '')})"
            for item in headlines
        )
    else:
        lines.append("- No headlines were available from the connected feed.")

    conditions = context.get("market_conditions")
    lines.extend(["", "## Broader market indicator"])
    if conditions:
        lines.extend([
            f"- Source: {conditions.get('source', 'Not supplied')}",
            f"- Fear & Greed value: {conditions.get('value', 'Not available')}",
            f"- Classification: "
            f"{conditions.get('classification', 'Not available')}",
        ])
    else:
        lines.append("- Fear & Greed index was not available.")

    lines.extend(["", "## AI-generated interpretation"])
    lines.append(
        ai_interpretation.strip()
        if ai_interpretation and ai_interpretation.strip()
        else "Not generated; this report contains provider observations and "
        "derived indicators only."
    )
    return "\n".join(lines)
