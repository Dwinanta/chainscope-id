"""Klien API untuk ChainScope ID (CoinGecko & Indodax)."""

import logging
import math
import time
import unicodedata
import pandas as pd
import requests
from . import config

logger = logging.getLogger(__name__)


class ChainScopeAPIError(Exception):
    """Error saat berkomunikasi dengan API."""


def _clean_metadata_text(
    value: object,
    *,
    reject_controls: bool = False,
) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = unicodedata.normalize("NFC", value.lstrip("\ufeff"))
    if reject_controls and any(
        unicodedata.category(character) in {"Cc", "Cs"}
        for character in normalized
    ):
        return None
    cleaned = "".join(
        " " if unicodedata.category(character) in {"Cc", "Cs"} else character
        for character in normalized
    )
    cleaned = " ".join(cleaned.split())
    return cleaned or None


def prepare_coin_catalog(coins: pd.DataFrame) -> pd.DataFrame:
    """Validate CoinGecko identity fields and derive consistent display labels.

    Coin IDs remain the stable selection key. Numeric names and unusual symbols
    are retained when the source provides valid, non-empty metadata.
    """
    result = coins.copy()
    for column in ("id", "symbol", "name"):
        if column not in result.columns:
            result[column] = pd.Series(dtype="object")

    rows = []
    seen_ids = set()
    invalid_count = 0
    duplicate_count = 0
    for row in result.to_dict("records"):
        coin_id = _clean_metadata_text(row.get("id"), reject_controls=True)
        symbol = _clean_metadata_text(row.get("symbol"))
        name = _clean_metadata_text(row.get("name"))
        if not coin_id or not symbol or not name:
            invalid_count += 1
            continue

        identity = coin_id.casefold()
        if identity in seen_ids:
            duplicate_count += 1
            continue
        seen_ids.add(identity)
        row.update({
            "id": coin_id,
            "symbol": symbol.lower(),
            "name": name,
        })
        rows.append(row)

    prepared = pd.DataFrame(rows, columns=result.columns)
    if prepared.empty:
        prepared = result.iloc[:0].copy()
    prepared["symbol_upper"] = prepared["symbol"].astype(str).str.upper()
    prepared["label"] = (
        prepared["name"].astype(str)
        + " ("
        + prepared["symbol_upper"]
        + ")"
    )
    if invalid_count or duplicate_count:
        logger.warning(
            "CoinGecko catalog normalization removed %d invalid rows and "
            "%d duplicate IDs.",
            invalid_count,
            duplicate_count,
        )
    return prepared


def resolve_coin_identifier(value: object, catalog: pd.DataFrame) -> str | None:
    """Resolve an exact CoinGecko ID, symbol, or name without fuzzy matches."""
    query = _clean_metadata_text(value)
    if not query or not {"id", "symbol", "name"}.issubset(catalog.columns):
        return None

    normalized_query = query.casefold()
    ids = catalog["id"].astype(str)
    exact_ids = catalog.loc[ids.str.casefold() == normalized_query, "id"]
    if len(exact_ids) == 1:
        return str(exact_ids.iloc[0])

    symbols = catalog["symbol"].astype(str)
    exact_symbols = catalog.loc[
        symbols.str.casefold() == normalized_query, "id"
    ].drop_duplicates()
    if len(exact_symbols) == 1:
        return str(exact_symbols.iloc[0])
    if len(exact_symbols) > 1:
        return None

    names = catalog["name"].astype(str)
    exact_names = catalog.loc[
        names.str.casefold() == normalized_query, "id"
    ].drop_duplicates()
    return str(exact_names.iloc[0]) if len(exact_names) == 1 else None


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
    market_data = prepare_coin_catalog(pd.DataFrame(data))
    if market_data.empty:
        raise ChainScopeAPIError("Respons API tidak berisi metadata aset yang valid.")
    return market_data


def fetch_market_data_for_ids(
    vs_currency: str,
    coin_ids: list[str] | tuple[str, ...],
) -> pd.DataFrame:
    """Fetch current market rows only for the requested coin IDs."""
    ids = list(dict.fromkeys(coin_id for coin_id in coin_ids if coin_id))
    if not ids:
        return pd.DataFrame(columns=["id", "symbol", "name", "current_price", "image"])

    url = f"{config.API_BASE}/coins/markets"
    frames = []
    try:
        for start in range(0, len(ids), 250):
            response = requests.get(
                url,
                params={
                    "vs_currency": vs_currency.lower(),
                    "ids": ",".join(ids[start : start + 250]),
                },
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ChainScopeAPIError("Respons data pasar tidak sesuai format.")
            if data:
                frames.append(pd.DataFrame(data))
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi CoinGecko: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError(f"Respons bukan JSON yang valid: {exc}") from exc

    if not frames:
        return pd.DataFrame(columns=["id", "symbol", "name", "current_price", "image"])
    market_data = prepare_coin_catalog(pd.concat(frames, ignore_index=True))
    for column in ("id", "symbol", "name", "current_price", "image"):
        if column not in market_data:
            market_data[column] = None
    return market_data


def fetch_usd_currency_rate(currency: str) -> float:
    """Return units of the selected currency per USD using one targeted request."""
    target_currency = currency.lower()
    if target_currency == "usd":
        return 1.0

    try:
        response = requests.get(
            f"{config.API_BASE}/simple/price",
            params={"ids": "bitcoin", "vs_currencies": f"usd,{target_currency}"},
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        raise ChainScopeAPIError(f"Gagal menghubungi CoinGecko: {exc}") from exc
    except ValueError as exc:
        raise ChainScopeAPIError("Respons kurs mata uang bukan JSON yang valid.") from exc

    bitcoin_prices = payload.get("bitcoin") if isinstance(payload, dict) else None
    if not isinstance(bitcoin_prices, dict):
        raise ChainScopeAPIError("CoinGecko tidak mengembalikan data kurs Bitcoin.")

    usd_price = bitcoin_prices.get("usd")
    target_price = bitcoin_prices.get(target_currency)
    if (
        not isinstance(usd_price, (int, float))
        or isinstance(usd_price, bool)
        or not isinstance(target_price, (int, float))
        or isinstance(target_price, bool)
        or not math.isfinite(usd_price)
        or not math.isfinite(target_price)
        or usd_price <= 0
        or target_price <= 0
    ):
        raise ChainScopeAPIError("Data kurs mata uang dari CoinGecko tidak valid.")
    return float(target_price / usd_price)


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

    coin_rows = [coin for coin in data if isinstance(coin, dict)]
    if len(coin_rows) != len(data):
        logger.warning(
            "CoinGecko catalog skipped %d non-object rows.",
            len(data) - len(coin_rows),
        )
    coins = prepare_coin_catalog(pd.DataFrame(coin_rows))

    if coins.empty:
        raise ChainScopeAPIError("CoinGecko tidak mengembalikan daftar koin yang valid.")
    return coins[["id", "symbol", "name"]].to_dict("records")


def merge_market_and_coin_list(
    market_data: pd.DataFrame,
    all_coins: pd.DataFrame,
) -> pd.DataFrame:
    """Gabungkan data pasar dengan katalog lengkap, sambil menjaga urutan pasar."""
    required = {"id", "symbol", "name"}
    if not required.issubset(market_data.columns) or not required.issubset(all_coins.columns):
        raise ValueError("Data pasar dan katalog wajib memiliki kolom id, symbol, dan name.")

    market = prepare_coin_catalog(market_data)
    catalog = prepare_coin_catalog(all_coins)
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
    return prepare_coin_catalog(merged)


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