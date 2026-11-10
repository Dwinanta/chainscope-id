"""Stock market intelligence module supporting Indonesian (IDX) and global equities."""

from datetime import datetime, timezone
import requests
import pandas as pd


# Default curated stock universe
POPULAR_STOCKS = [
    # Indonesian Equities (IDX)
    {"symbol": "BBCA.JK", "name": "Bank Central Asia Tbk", "sector": "Financials", "country": "ID"},
    {"symbol": "BBRI.JK", "name": "Bank Rakyat Indonesia Tbk", "sector": "Financials", "country": "ID"},
    {"symbol": "BMRI.JK", "name": "Bank Mandiri Tbk", "sector": "Financials", "country": "ID"},
    {"symbol": "BBNI.JK", "name": "Bank Negara Indonesia Tbk", "sector": "Financials", "country": "ID"},
    {"symbol": "TLKM.JK", "name": "Telkom Indonesia Tbk", "sector": "Telecommunications", "country": "ID"},
    {"symbol": "ASII.JK", "name": "Astra International Tbk", "sector": "Consumer / Industrial", "country": "ID"},
    {"symbol": "UNVR.JK", "name": "Unilever Indonesia Tbk", "sector": "Consumer Goods", "country": "ID"},
    {"symbol": "ICBP.JK", "name": "Indofood CBP Sukses Makmur Tbk", "sector": "Consumer Goods", "country": "ID"},
    {"symbol": "GOTO.JK", "name": "GoTo Gojek Tokopedia Tbk", "sector": "Technology", "country": "ID"},
    {"symbol": "AMMN.JK", "name": "Amman Mineral Internasional Tbk", "sector": "Basic Materials", "country": "ID"},
    # Global Equities (US)
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "country": "US"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "country": "US"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "country": "US"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary", "country": "US"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "country": "US"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "country": "US"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary", "country": "US"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials", "country": "US"},
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChainScope/2.0"}


def get_stock_universe() -> list[dict[str, str]]:
    """Return the curated list of available stock symbols and sectors."""
    return POPULAR_STOCKS


def fetch_stock_quote(symbol: str, timeout: int = 6) -> dict:
    """Fetch current market quote for a stock symbol from Yahoo Finance public v8 chart endpoint."""
    cleaned = symbol.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{cleaned}?range=1d&interval=1d"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=timeout)
        if res.status_code != 200:
            return _fallback_stock_quote(cleaned)
        
        data = res.json()
        results = data.get("chart", {}).get("result")
        if not results:
            return _fallback_stock_quote(cleaned)
            
        meta = results[0].get("meta", {})
        price = meta.get("regularMarketPrice") or meta.get("chartPreviousClose", 0.0)
        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose", price)
        
        change = price - prev_close if price and prev_close else 0.0
        change_pct = (change / prev_close * 100.0) if prev_close else 0.0
        currency = meta.get("currency", "USD")
        
        return {
            "symbol": cleaned,
            "price": float(price),
            "previous_close": float(prev_close),
            "change": float(change),
            "change_pct": float(change_pct),
            "currency": currency,
            "exchange": meta.get("exchangeName", "N/A"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "LIVE",
        }
    except Exception:
        return _fallback_stock_quote(cleaned)


def fetch_stock_history(symbol: str, period: str = "1mo", interval: str = "1d", timeout: int = 8) -> pd.DataFrame:
    """Fetch historical OHLCV data for charting and indicators."""
    cleaned = symbol.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{cleaned}?range={period}&interval={interval}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=timeout)
        if res.status_code != 200:
            return pd.DataFrame()
            
        data = res.json()
        result = data.get("chart", {}).get("result")
        if not result:
            return pd.DataFrame()
            
        timestamps = result[0].get("timestamp", [])
        quote = result[0].get("indicators", {}).get("quote", [{}])[0]
        
        df = pd.DataFrame({
            "timestamp": [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in timestamps],
            "open": quote.get("open", []),
            "high": quote.get("high", []),
            "low": quote.get("low", []),
            "close": quote.get("close", []),
            "volume": quote.get("volume", []),
        }).dropna(subset=["close"])
        
        df["price"] = df["close"]
        return df
    except Exception:
        return pd.DataFrame()


def _fallback_stock_quote(symbol: str) -> dict:
    """Graceful metadata fallback if network is unreachable."""
    matching = next((s for s in POPULAR_STOCKS if s["symbol"] == symbol), None)
    name = matching["name"] if matching else symbol
    currency = "IDR" if symbol.endswith(".JK") else "USD"
    return {
        "symbol": symbol,
        "name": name,
        "price": 0.0,
        "previous_close": 0.0,
        "change": 0.0,
        "change_pct": 0.0,
        "currency": currency,
        "exchange": "IDX" if symbol.endswith(".JK") else "US",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "UNAVAILABLE",
    }
