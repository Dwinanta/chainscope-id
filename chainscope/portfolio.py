"""Portofolio tracker untuk ChainScope ID.

Holding disimpan di file JSON lokal (portfolio.json).
Harga beli (buy_price_usd) disimpan dalam USD agar tidak terpengaruh
mata uang tampilan yang dipilih pengguna.
"""

import json
from pathlib import Path

import pandas as pd

PORTFOLIO_FILE = Path(__file__).resolve().parent.parent / "portfolio.json"


# ---------------------------------------------------------------------------
# Baca / tulis
# ---------------------------------------------------------------------------

def load_holdings() -> list[dict]:
    """Baca daftar holding dari disk. Kembalikan list of dict."""
    if not PORTFOLIO_FILE.exists():
        return []
    try:
        data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    cleaned = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "coin_id" not in item:
            continue
        try:
            cleaned.append({
                "coin_id": str(item["coin_id"]),
                "amount": float(item.get("amount", 0)),
                "buy_price_usd": float(item.get("buy_price_usd", 0)),
            })
        except (TypeError, ValueError):
            continue
    return cleaned


def save_holdings(holdings: list[dict]) -> None:
    """Simpan list holding ke disk (format konsisten)."""
    cleaned = []
    for h in holdings:
        if not isinstance(h, dict) or "coin_id" not in h:
            continue
        try:
            cleaned.append({
                "coin_id": str(h["coin_id"]),
                "amount": float(h.get("amount", 0)),
                "buy_price_usd": float(h.get("buy_price_usd", 0)),
            })
        except (TypeError, ValueError):
            continue
    PORTFOLIO_FILE.write_text(
        json.dumps(cleaned, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Operasi tingkat tinggi
# ---------------------------------------------------------------------------

def add_or_update_holding(
    coin_id: str,
    amount: float,
    buy_price_usd: float,
) -> list[dict]:
    """Tambah holding baru, atau perbarui jika coin_id sudah ada."""
    holdings = load_holdings()
    existing = next(
        (h for h in holdings if h["coin_id"] == coin_id), None
    )
    if existing:
        existing["amount"] = float(amount)
        existing["buy_price_usd"] = float(buy_price_usd)
    else:
        holdings.append({
            "coin_id": coin_id,
            "amount": float(amount),
            "buy_price_usd": float(buy_price_usd),
        })
    save_holdings(holdings)
    return load_holdings()


def remove_holding(coin_id: str) -> list[dict]:
    """Hapus satu coin dari portofolio."""
    holdings = [h for h in load_holdings() if h["coin_id"] != coin_id]
    save_holdings(holdings)
    return holdings


def clear_holdings() -> None:
    """Kosongkan seluruh portofolio."""
    save_holdings([])


# ---------------------------------------------------------------------------
# Perhitungan
# ---------------------------------------------------------------------------

def compute_portfolio(
    holdings: list[dict],
    market_df: pd.DataFrame,
    usd_idr_rate: float,
    currency: str,
) -> pd.DataFrame:
    """Hitung metrik portofolio untuk ditampilkan.

    Parameter
    ---------
    holdings : list dict dengan 'coin_id', 'amount', 'buy_price_usd'
    market_df : DataFrame harga saat ini (kolom 'current_price' dalam
                mata uang `currency`)
    usd_idr_rate : kurs untuk konversi harga beli USD -> display currency
    currency : 'USD' atau 'IDR'

    Return
    ------
    DataFrame dengan kolom: coin_id, name, symbol, amount, current_price,
    buy_price, invested, current_value, pnl, pnl_pct, found
    """
    if not holdings:
        return pd.DataFrame(columns=[
            "coin_id", "name", "symbol", "amount", "current_price",
            "buy_price", "invested", "current_value", "pnl", "pnl_pct",
            "found",
        ])

    if currency.upper() not in ("USD", "IDR"):
        raise ValueError(f"Mata uang tidak dikenal: {currency}")

    cur = currency.upper()
    rows = []

    for h in holdings:
        cid = str(h["coin_id"])
        amt = float(h.get("amount", 0))
        buy_usd = float(h.get("buy_price_usd", 0))

        # Konversi harga beli dari USD ke display currency
        buy_display = buy_usd * usd_idr_rate if cur == "IDR" else buy_usd

        match = (
            market_df[market_df["id"] == cid]
            if "id" in market_df.columns
            else pd.DataFrame()
        )

        if match.empty:
            rows.append({
                "coin_id": cid,
                "name": cid,
                "symbol": cid.upper(),
                "amount": amt,
                "current_price": None,
                "buy_price": buy_display,
                "invested": amt * buy_display,
                "current_value": None,
                "pnl": None,
                "pnl_pct": None,
                "found": False,
            })
            continue

        row = match.iloc[0]
        try:
            cur_price = float(row["current_price"])
        except (TypeError, ValueError):
            cur_price = None

        invested = amt * buy_display
        current_value = amt * cur_price if cur_price is not None else None
        pnl = (
            current_value - invested
            if current_value is not None
            else None
        )
        pnl_pct = (
            (pnl / invested * 100.0)
            if invested > 0 and pnl is not None
            else None
        )

        rows.append({
            "coin_id": cid,
            "name": row.get("name", cid),
            "symbol": str(row.get("symbol", cid)).upper(),
            "amount": amt,
            "current_price": cur_price,
            "buy_price": buy_display,
            "invested": invested,
            "current_value": current_value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "found": True,
        })

    return pd.DataFrame(rows)