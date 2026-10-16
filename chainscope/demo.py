"""Data contoh untuk Mode Demo ChainScope ID."""

import pandas as pd

from . import config

# Data dasar dalam USD (angka fiktif).
# Jika limit > 10, sisa baris dibuat secara sintetis.
_DEMO_BASE = [
    ("bitcoin",      "btc",  "Bitcoin",   83000.0, 1_650_000_000_000, 30_000_000_000,  0.50),
    ("ethereum",     "eth",  "Ethereum",   2500.0,   300_000_000_000, 15_000_000_000,  0.10),
    ("tether",       "usdt", "Tether",        1.0,   120_000_000_000, 50_000_000_000,  0.01),
    ("ripple",       "xrp",  "XRP",           2.2,   120_000_000_000,  5_000_000_000, -1.20),
    ("binancecoin",  "bnb",  "BNB",         600.0,    90_000_000_000,  1_500_000_000,  0.80),
    ("solana",       "sol",  "Solana",      150.0,    70_000_000_000,  3_000_000_000,  2.50),
    ("usd-coin",     "usdc", "USDC",          1.0,    40_000_000_000,  8_000_000_000,  0.00),
    ("dogecoin",     "doge", "Dogecoin",      0.15,   22_000_000_000,  1_200_000_000, -3.10),
    ("cardano",      "ada",  "Cardano",       0.50,   18_000_000_000,    500_000_000,  1.50),
    ("tron",         "trx",  "TRON",          0.25,   22_000_000_000,    800_000_000, -0.40),
]


def get_demo_market_data(limit: int, currency: str) -> pd.DataFrame:
    """Data demo dalam mata uang terpilih (USD dasar * kurs)."""
    rate = config.DEMO_USD_TO_IDR if currency.upper() == "IDR" else 1.0
    rows = []
    for i in range(limit):
        if i < len(_DEMO_BASE):
            cid, sym, name, price, mcap, vol, chg = _DEMO_BASE[i]
        else:
            cid = f"demo-coin-{i + 1}"
            sym = f"d{i + 1:02d}"
            name = f"Demo Coin {i + 1}"
            price = max(0.0001, 10.0 / (i + 1))
            mcap = max(1_000_000, 1_000_000_000 // (i + 1))
            vol = max(100_000, 100_000_000 // (i + 1))
            chg = ((i % 7) - 3) * 0.5
        rows.append({
            "id": cid,
            "symbol": sym,
            "name": name,
            "current_price": price * rate,
            "market_cap": mcap * rate,
            "total_volume": vol * rate,
            "price_change_percentage_24h": chg,
        })
    return pd.DataFrame(rows)


def get_demo_price_history(current_price: float) -> pd.DataFrame:
    """Riwayat harga contoh, konsisten dengan harga saat ini."""
    now = pd.Timestamp.now("UTC").tz_localize(None)
    timestamps = pd.date_range(end=now, periods=7 * 24, freq="h")
    base = current_price if current_price and current_price > 0 else 100.0
    amp = base * 0.02
    prices = [base + amp * ((i % 12) - 6) / 6 for i in range(len(timestamps))]
    return pd.DataFrame({"waktu": timestamps, "price": prices})