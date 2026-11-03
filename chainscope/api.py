"""Klien API untuk ChainScope ID (CoinGecko & Indodax)."""

import logging
import time
import pandas as pd
import requests
from . import config

logger = logging.getLogger(__name__)


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


def fetch_fear_greed_index() -> dict[str, str]:
    """Fetch the latest Alternative.me Fear & Greed index entry."""
    try:
        response = requests.get(
            "https://api.alternative.me/fng/",
            params={"limit": 1},
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi Alternative.me: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError("Respons Fear & Greed bukan JSON yang valid.") from exc

    entries = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
        raise ChainScopeAPIError("Alternative.me tidak mengembalikan data Fear & Greed.")

    value = entries[0].get("value")
    classification = entries[0].get("value_classification")
    if (
        not isinstance(value, str)
        or not value.isdigit()
        or not isinstance(classification, str)
        or not classification.strip()
    ):
        raise ChainScopeAPIError("Data Fear & Greed tidak sesuai format.")
    return {"value": value, "classification": classification.strip()}


def fetch_crypto_news(limit: int = 5) -> list[dict[str, str]]:
    """Fetch the latest news from the free cryptocurrency.cv endpoint."""
    if limit <= 0:
        raise ValueError("Jumlah berita harus lebih besar dari nol.")

    try:
        response = requests.get(
            "https://cryptocurrency.cv/api/news",
            params={"limit": limit},
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException:
        raise ChainScopeAPIError("Gagal menghubungi layanan berita crypto.") from None
    except ValueError as exc:
        raise ChainScopeAPIError("Respons berita crypto bukan JSON yang valid.") from exc

    if isinstance(payload, list):
        results = payload
    elif isinstance(payload, dict):
        results = next(
            (
                payload.get(key)
                for key in ("news", "articles", "results", "data")
                if isinstance(payload.get(key), list)
            ),
            None,
        )
    else:
        results = None
    if results is None:
        raise ChainScopeAPIError("Respons berita crypto tidak sesuai format.")

    news = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        url = item.get("url") or item.get("link")
        source_data = item.get("source") or item.get("provider") or item.get("publisher")
        if isinstance(source_data, dict):
            source = (
                source_data.get("name")
                or source_data.get("title")
                or source_data.get("domain")
            )
        else:
            source = source_data or item.get("source_name") or item.get("site")
        if not isinstance(title, str) or not title.strip():
            continue
        if not isinstance(url, str) or not url.strip():
            continue
        if not url.startswith(("https://", "http://")):
            continue
        if not isinstance(source, str) or not source.strip():
            source = url.split("/")[2]
        news.append({
            "title": title.strip(),
            "source": source.strip(),
            "url": url.strip(),
        })
        if len(news) == limit:
            break
    return news


def fetch_all_coins() -> list[dict[str, str]]:
    """Mengambil daftar lengkap koin CoinGecko (id, symbol, dan name)."""
    url = f"{config.API_BASE}/coins/list"
    try:
        response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi CoinGecko: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError(f"Respons daftar koin bukan JSON yang valid: {exc}") from exc

    if not isinstance(data, list):
        raise ChainScopeAPIError("Respons daftar koin CoinGecko tidak sesuai format.")

    coins = []
    for coin in data:
        if not isinstance(coin, dict):
            continue
        coin_id, symbol, name = coin.get("id"), coin.get("symbol"), coin.get("name")
        if all(isinstance(value, str) and value.strip() for value in (coin_id, symbol, name)):
            coins.append({
                "id": coin_id.strip(),
                "symbol": symbol.strip().lower(),
                "name": name.strip(),
            })

    if not coins:
        raise ChainScopeAPIError("CoinGecko tidak mengembalikan daftar koin yang valid.")
    return coins


def merge_market_and_coin_list(
    market_data: pd.DataFrame,
    all_coins: pd.DataFrame,
) -> pd.DataFrame:
    """Gabungkan data pasar dengan katalog lengkap, sambil menjaga urutan pasar."""
    required = {"id", "symbol", "name"}
    if not required.issubset(market_data.columns) or not required.issubset(all_coins.columns):
        raise ValueError("Data pasar dan katalog wajib memiliki kolom id, symbol, dan name.")

    market = market_data.copy()
    catalog = all_coins.copy()
    market["id"] = market["id"].astype(str)
    catalog["id"] = catalog["id"].astype(str)
    market = market.drop_duplicates("id", keep="first")
    market["_market_rank"] = range(len(market))

    coins = pd.concat(
        [market[["id", "symbol", "name"]], catalog[["id", "symbol", "name"]]],
        ignore_index=True,
    ).drop_duplicates("id", keep="first")
    market_columns = [
        column for column in market.columns if column not in {"symbol", "name"}
    ]
    merged = coins.merge(
        market[market_columns],
        on="id",
        how="left",
        sort=False,
    )
    merged = merged.sort_values(
        "_market_rank", na_position="last", kind="stable"
    ).drop(columns="_market_rank")
    if "current_price" in merged:
        merged["current_price"] = merged["current_price"].fillna(0)
    if "image" in merged:
        merged["image"] = merged["image"].fillna("")
    return merged


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

def fetch_exchange_prices() -> dict:
    """Mengambil harga BTC dan ETH dari Indodax dan Upbit Indonesia."""
    result = {
        "Indodax": {"BTC": None, "ETH": None},
        "Upbit Indonesia": {"BTC": None, "ETH": None},
    }

    try:
        response = requests.get(
            "https://indodax.com/api/summaries",
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("tickers"), dict):
            raise ValueError("Respons Indodax tidak sesuai format.")
        tickers = data["tickers"]
        for symbol in ("BTC", "ETH"):
            ticker = tickers.get(f"{symbol.lower()}_idr")
            if ticker and ticker.get("last") is not None:
                result["Indodax"][symbol] = float(ticker["last"])
    except (requests.exceptions.RequestException, ValueError, TypeError) as exc:
        logger.warning("Gagal mengambil harga dari Indodax: %s", exc)

    try:
        response = requests.get(
            "https://id-api.upbit.com/v1/ticker",
            params={"markets": "IDR-BTC,IDR-ETH"},
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        tickers = response.json()
        if not isinstance(tickers, list):
            raise ValueError("Respons Upbit tidak sesuai format.")
        for ticker in tickers:
            if not isinstance(ticker, dict):
                raise ValueError("Ticker Upbit tidak sesuai format.")
            market = ticker.get("market")
            if market in ("IDR-BTC", "IDR-ETH"):
                result["Upbit Indonesia"][market[4:]] = float(ticker["trade_price"])
    except (requests.exceptions.RequestException, ValueError, TypeError, KeyError) as exc:
        logger.warning("Gagal mengambil harga dari Upbit Indonesia: %s", exc)

    if all(price is None for exchange in result.values() for price in exchange.values()):
        raise ChainScopeAPIError("Harga BTC/ETH tidak tersedia dari Indodax maupun Upbit.")

    return result


def fetch_indodax_all_tickers() -> pd.DataFrame:
    """Mengambil semua harga koin yang ada di Indodax (IDR)."""
    try:
        response = requests.get(
            "https://indodax.com/api/summaries",
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi Indodax: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError("Respons Indodax bukan JSON yang valid.") from exc

    tickers = data.get("tickers") if isinstance(data, dict) else None
    if not isinstance(tickers, dict) or not tickers:
        raise ChainScopeAPIError("Respons Indodax tidak berisi data ticker.")

    rows = []
    for pair, info in tickers.items():
        if pair.endswith("_idr") and isinstance(info, dict):
            try:
                rows.append({
                    "Symbol": pair[:-4].upper(),
                    "Name": pair[:-4].upper(),
                    "Price": float(info["last"]),
                    "High": float(info["high"]),
                    "Low": float(info["low"]),
                    "Volume": float(info["vol_idr"]),
                })
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Ticker Indodax %s dilewati: %s", pair, exc)

    if not rows:
        raise ChainScopeAPIError("Indodax tidak mengembalikan ticker IDR yang valid.")

    return pd.DataFrame(
        rows,
        columns=["Symbol", "Name", "Price", "High", "Low", "Volume"],
    ).sort_values("Volume", ascending=False, ignore_index=True)