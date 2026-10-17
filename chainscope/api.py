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
        "sparkline": "true",
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


def fetch_price_history(
    coin_id: str, vs_currency: str, days: int = 7
) -> pd.DataFrame:
    """Ambil riwayat harga + volume untuk satu koin.

    Return DataFrame dengan kolom: waktu, price, volume.
    """
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

    if not isinstance(payload, dict):
        raise ChainScopeAPIError("Respons API tidak sesuai format.")

    prices = payload.get("prices")
    if not prices:
        raise ChainScopeAPIError(f"Data riwayat harga untuk {coin_id} kosong.")

    df = pd.DataFrame(prices, columns=["timestamp_ms", "price"])
    df["waktu"] = pd.to_datetime(df["timestamp_ms"], unit="ms")

    volumes = payload.get("total_volumes") or []
    if volumes:
        vol_df = pd.DataFrame(volumes, columns=["timestamp_ms", "volume"])
        vol_df["waktu"] = pd.to_datetime(vol_df["timestamp_ms"], unit="ms")
        df = df.merge(vol_df[["waktu", "volume"]], on="waktu", how="left")
    else:
        df["volume"] = None

    return df[["waktu", "price", "volume"]]

def fetch_ohlc(
    coin_id: str, vs_currency: str, days: int = 7
) -> pd.DataFrame:
    """Ambil data OHLC (Open, High, Low, Close) untuk candlestick.

    Endpoint CoinGecko `/coins/{id}/ohlc` hanya mendukung beberapa
    nilai `days`: 1, 7, 14, 30, 90, 180, 365.
    """
    url = f"{config.API_BASE}/coins/{coin_id}/ohlc"
    params = {"vs_currency": vs_currency.lower(), "days": days}
    try:
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi CoinGecko: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError(f"Respons bukan JSON yang valid: {exc}") from exc

    if not isinstance(data, list) or not data:
        raise ChainScopeAPIError(f"Data OHLC untuk {coin_id} kosong.")

    df = pd.DataFrame(data, columns=["timestamp_ms", "open", "high", "low", "close"])
    df["waktu"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    return df[["waktu", "open", "high", "low", "close"]]