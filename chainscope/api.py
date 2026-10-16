"""Klien API CoinGecko untuk ChainScope ID (tanpa dependensi Streamlit)."""

import pandas as pd
import requests

from . import config


class ChainScopeAPIError(Exception):
    """Error saat berkomunikasi dengan CoinGecko."""


def fetch_market_data(vs_currency: str, limit: int) -> pd.DataFrame:
    """Ambil data pasar top-N koin berdasarkan kapitalisasi pasar."""
    url = f"{config.API_BASE}/coins/markets"
    params = {
        "vs_currency": vs_currency.lower(),
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "price_change_percentage": "24h",
    }
    try:
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi CoinGecko: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError(f"Respons bukan JSON yang valid: {exc}") from exc

    if not isinstance(data, list) or not data:
        raise ChainScopeAPIError("Respons API kosong atau tidak sesuai format.")
    return pd.DataFrame(data)


def fetch_price_history(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    """Ambil riwayat harga untuk satu koin."""
    url = f"{config.API_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency.lower(), "days": days}
    try:
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi CoinGecko: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError(f"Respons bukan JSON yang valid: {exc}") from exc

    prices = payload.get("prices") if isinstance(payload, dict) else None
    if not prices:
        raise ChainScopeAPIError(f"Data riwayat harga untuk {coin_id} kosong.")

    df = pd.DataFrame(prices, columns=["timestamp_ms", "price"])
    df["waktu"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    return df[["waktu", "price"]]