"""Multi-exchange analytics and cross-exchange arbitrage intelligence module."""

from datetime import datetime, timezone
import requests
import pandas as pd

from chainscope import api


SUPPORTED_EXCHANGES = [
    {"id": "indodax", "name": "Indodax", "country": "Indonesia", "license": "Bappebti"},
    {"id": "binance", "name": "Binance", "country": "Global", "license": "Global"},
    {"id": "bybit", "name": "Bybit", "country": "Global", "license": "Global"},
    {"id": "okx", "name": "OKX", "country": "Global", "license": "Global"},
    {"id": "coinbase", "name": "Coinbase", "country": "United States", "license": "SEC / NYDFS"},
    {"id": "kraken", "name": "Kraken", "country": "United States", "license": "FinCEN"},
]


def fetch_cross_exchange_tickers(coin_id: str = "bitcoin", vs_currency: str = "usd", timeout: int = 6) -> pd.DataFrame:
    """Fetch multi-exchange tickers for a coin using CoinGecko public multi-exchange aggregator.
    
    Includes Indodax direct ticker integration for local price discovery.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/tickers?include_exchange_logo=true&depth=true"
    headers = {"User-Agent": "Mozilla/5.0 ChainScope/2.0"}
    
    records = []
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            tickers = data.get("tickers", [])
            for t in tickers:
                market = t.get("market", {})
                market_name = market.get("name", "Unknown")
                target = t.get("target", "").upper()
                last_price = t.get("last", 0.0)
                converted_last = t.get("converted_last", {})
                price_usd = converted_last.get("usd") or (last_price if target in {"USD", "USDT", "USDC"} else None)
                volume_usd = (t.get("converted_volume", {}) or {}).get("usd", 0.0)
                spread_pct = t.get("bid_ask_spread_percentage", 0.0)
                trust_score = t.get("trust_score", "green")
                
                if price_usd and price_usd > 0:
                    records.append({
                        "Exchange": market_name,
                        "Pair": f"{t.get('base', '').upper()}/{target}",
                        "Price_USD": float(price_usd),
                        "Volume_24h_USD": float(volume_usd or 0.0),
                        "Spread_Pct": float(spread_pct or 0.0),
                        "Trust": str(trust_score).capitalize() if trust_score else "N/A",
                        "Timestamp": t.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                    })
    except Exception:
        pass

    # If aggregator request was empty or offline, generate multi-exchange overview from Indodax and reference
    if not records:
        try:
            # Query Indodax direct
            indodax_df = api.fetch_indodax_all_tickers()
            base_sym = "BTC" if coin_id == "bitcoin" else "ETH" if coin_id == "ethereum" else "SOL"
            match = indodax_df[indodax_df["Symbol"] == base_sym]
            if not match.empty:
                idx_price_idr = float(match.iloc[0]["Price"])
                rate_idr = api.fetch_usd_currency_rate("idr") or 16000.0
                idx_price_usd = idx_price_idr / rate_idr
                records.append({
                    "Exchange": "Indodax",
                    "Pair": f"{base_sym}/IDR",
                    "Price_USD": idx_price_usd,
                    "Volume_24h_USD": float(match.iloc[0].get("Volume", 0.0)) / rate_idr,
                    "Spread_Pct": 0.15,
                    "Trust": "Green",
                    "Timestamp": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            pass

    if not records:
        return pd.DataFrame(columns=["Exchange", "Pair", "Price_USD", "Volume_24h_USD", "Spread_Pct", "Trust"])

    df = pd.DataFrame(records)
    # Deduplicate by exchange, picking largest volume
    df = df.sort_values("Volume_24h_USD", ascending=False).drop_duplicates(subset=["Exchange"])
    return df


def calculate_arbitrage_opportunities(df_tickers: pd.DataFrame) -> dict:
    """Analyze price discrepancies and calculate potential cross-exchange arbitrage spreads."""
    if df_tickers.empty or len(df_tickers) < 2 or "Price_USD" not in df_tickers.columns:
        return {
            "has_arbitrage": False,
            "min_price": None,
            "max_price": None,
            "spread_usd": 0.0,
            "spread_pct": 0.0,
            "lowest_exchange": None,
            "highest_exchange": None,
            "potential_profit_note": "Memerlukan minimal 2 bursa untuk membandingkan spread.",
        }

    valid = df_tickers.dropna(subset=["Price_USD"])
    valid = valid[valid["Price_USD"] > 0]
    if len(valid) < 2:
        return {"has_arbitrage": False, "spread_pct": 0.0}

    min_row = valid.loc[valid["Price_USD"].idxmin()]
    max_row = valid.loc[valid["Price_USD"].idxmax()]
    
    min_price = float(min_row["Price_USD"])
    max_price = float(max_row["Price_USD"])
    spread_usd = max_price - min_price
    spread_pct = (spread_usd / min_price * 100.0) if min_price > 0 else 0.0
    
    return {
        "has_arbitrage": spread_pct >= 0.5,
        "min_price": min_price,
        "max_price": max_price,
        "spread_usd": spread_usd,
        "spread_pct": round(spread_pct, 2),
        "lowest_exchange": str(min_row["Exchange"]),
        "highest_exchange": str(max_row["Exchange"]),
        "potential_profit_note": (
            f"Beli di {min_row['Exchange']} (${min_price:,.2f}), jual di {max_row['Exchange']} (${max_price:,.2f}). "
            f"Gross spread: {spread_pct:.2f}%. Perhatikan biaya transfer blockchain dan fee trading."
        ),
    }
