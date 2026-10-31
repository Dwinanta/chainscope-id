"""Klien API untuk ChainScope ID (CoinGecko & Indodax)."""

import time
import pandas as pd
import requests
from . import config

class ChainScopeAPIError(Exception):
    """Error saat berkomunikasi dengan API."""

# ==============================================================================
# 1. COINGECKO API (Untuk Data Pasar & Riwayat Harga)
# ==============================================================================

def fetch_market_data(vs_currency: str, limit: int) -> pd.DataFrame:
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


def fetch_price_history(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
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


# ==============================================================================
# 2. INDODAX API (Untuk Chart Candlestick)
# ==============================================================================

def fetch_indodax_klines(symbol: str, interval: str = "60", limit: int = 200) -> pd.DataFrame:
    """
    Mengambil data candlestick dari Indodax (endpoint history_v2).
    Symbol contoh: 'btcidr', 'ethidr'.
    Interval (tf): '1', '5', '15', '60', '240', 'D', 'W'.
    """
    url = "https://indodax.com/tradingview/history_v2"
    
    to_time = int(time.time())
    
    if interval == "D": minutes = 1440
    elif interval == "W": minutes = 10080
    else: minutes = int(interval)
    
    from_time = to_time - (limit * minutes * 60)
    
    params = {
        "symbol": symbol.lower().replace("_", ""), # Indodax v2 pakai 'btcidr'
        "tf": interval,
        "from": from_time,
        "to": to_time
    }
    
    try:
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi Indodax: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError("Respons Indodax tidak valid (bukan JSON).") from exc

    if not isinstance(data, list) or not data:
        raise ChainScopeAPIError(f"Data Klines untuk {symbol} kosong.")

    df = pd.DataFrame(data)
    
    # Mapping nama kolom (bisa huruf besar/kecil tergantung respons)
    rename_map = {
        "Time": "time", "time": "time",
        "Open": "open", "open": "open",
        "High": "high", "high": "high",
        "Low": "low", "low": "low",
        "Close": "close", "close": "close",
        "Volume": "volume", "volume": "volume"
    }
    df = df.rename(columns=rename_map)
    
    required_cols = ["time", "open", "high", "low", "close", "volume"]
    for col in required_cols:
        if col not in df.columns:
            raise ChainScopeAPIError(f"Kolom '{col}' tidak ditemukan dalam respons Indodax.")
    
    df["time"] = pd.to_datetime(df["time"], unit="s")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
        
    return df[["time", "open", "high", "low", "close", "volume"]]