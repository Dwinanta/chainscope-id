"""Forex market intelligence module covering major pairs, currency strength, and volatility."""

from datetime import datetime, timezone
import requests
import pandas as pd


FOREX_PAIRS = [
    {"pair": "USD/IDR", "symbol": "USDIDR=X", "name": "US Dollar / Indonesian Rupiah", "base": "USD", "quote": "IDR"},
    {"pair": "EUR/USD", "symbol": "EURUSD=X", "name": "Euro / US Dollar", "base": "EUR", "quote": "USD"},
    {"pair": "GBP/USD", "symbol": "GBPUSD=X", "name": "British Pound / US Dollar", "base": "GBP", "quote": "USD"},
    {"pair": "USD/JPY", "symbol": "USDJPY=X", "name": "US Dollar / Japanese Yen", "base": "USD", "quote": "JPY"},
    {"pair": "USD/CHF", "symbol": "USDCHF=X", "name": "US Dollar / Swiss Franc", "base": "USD", "quote": "CHF"},
    {"pair": "AUD/USD", "symbol": "AUDUSD=X", "name": "Australian Dollar / US Dollar", "base": "AUD", "quote": "USD"},
    {"pair": "USD/CAD", "symbol": "USDCAD=X", "name": "US Dollar / Canadian Dollar", "base": "USD", "quote": "CAD"},
    {"pair": "EUR/GBP", "symbol": "EURGBP=X", "name": "Euro / British Pound", "base": "EUR", "quote": "GBP"},
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChainScope/2.0"}


def get_forex_pairs() -> list[dict[str, str]]:
    """Return the list of tracked major and regional forex pairs."""
    return FOREX_PAIRS


def fetch_forex_quote(symbol: str = "USDIDR=X", timeout: int = 6) -> dict:
    """Fetch current exchange rate from Yahoo Finance chart endpoint."""
    cleaned = symbol.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{cleaned}?range=1d&interval=1d"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=timeout)
        if res.status_code != 200:
            return _fallback_forex_quote(cleaned)
        
        data = res.json()
        results = data.get("chart", {}).get("result")
        if not results:
            return _fallback_forex_quote(cleaned)
            
        meta = results[0].get("meta", {})
        rate = meta.get("regularMarketPrice") or meta.get("chartPreviousClose", 0.0)
        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose", rate)
        
        change = rate - prev_close if rate and prev_close else 0.0
        change_pct = (change / prev_close * 100.0) if prev_close else 0.0
        
        pair_info = next((p for p in FOREX_PAIRS if p["symbol"] == cleaned), None)
        pair_name = pair_info["pair"] if pair_info else cleaned
        
        return {
            "pair": pair_name,
            "symbol": cleaned,
            "rate": float(rate),
            "previous_close": float(prev_close),
            "change": float(change),
            "change_pct": float(change_pct),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "LIVE",
        }
    except Exception:
        return _fallback_forex_quote(cleaned)


def fetch_forex_history(symbol: str = "USDIDR=X", period: str = "1mo", interval: str = "1d", timeout: int = 8) -> pd.DataFrame:
    """Fetch historical exchange rate series for charting."""
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
        }).dropna(subset=["close"])
        
        df["price"] = df["close"]
        return df
    except Exception:
        return pd.DataFrame()


def calculate_currency_strength(quotes: list[dict] | None = None) -> pd.DataFrame:
    """Calculate relative currency strength index (0-100) across major currencies.
    
    Uses pairwise 24h performance changes across cross rates.
    """
    if quotes is None:
        quotes = [fetch_forex_quote(p["symbol"]) for p in FOREX_PAIRS]
        
    scores = {"USD": 50.0, "EUR": 50.0, "GBP": 50.0, "JPY": 50.0, "CHF": 50.0, "AUD": 50.0, "CAD": 50.0, "IDR": 50.0}
    weights = {"USD": 0, "EUR": 0, "GBP": 0, "JPY": 0, "CHF": 0, "AUD": 0, "CAD": 0, "IDR": 0}
    
    for q in quotes:
        pair_str = q.get("pair", "")
        if "/" in pair_str:
            base, quote = pair_str.split("/", 1)
            pct = q.get("change_pct", 0.0)
            if base in scores and quote in scores:
                # If base rose against quote, base gets strength points, quote loses
                scores[base] += pct * 2.0
                scores[quote] -= pct * 2.0
                weights[base] += 1
                weights[quote] += 1
                
    result = []
    for curr, raw_score in scores.items():
        bounded = max(5.0, min(95.0, raw_score))
        status = "Strong" if bounded > 60 else "Weak" if bounded < 40 else "Neutral"
        result.append({
            "currency": curr,
            "strength_score": round(bounded, 1),
            "status": status,
        })
        
    df = pd.DataFrame(result).sort_values("strength_score", ascending=False)
    return df


def _fallback_forex_quote(symbol: str) -> dict:
    pair_info = next((p for p in FOREX_PAIRS if p["symbol"] == symbol), None)
    pair_name = pair_info["pair"] if pair_info else symbol
    return {
        "pair": pair_name,
        "symbol": symbol,
        "rate": 0.0,
        "previous_close": 0.0,
        "change": 0.0,
        "change_pct": 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "UNAVAILABLE",
    }
