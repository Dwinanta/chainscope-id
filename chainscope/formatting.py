"""Fungsi format angka untuk tampilan ChainScope ID."""

import pandas as pd

from chainscope.config import CURRENCY_OPTIONS


def format_money(value, currency: str) -> str:
    """Format singkat angka (mis. Rp1,65 T / $83.38 K / Rp12.345)."""
    if value is None or pd.isna(value):
        return "-"
    v = float(value)
    cur = currency.upper()

    if cur == "IDR":
        abs_v = abs(v)
        if abs_v >= 1_000_000_000_000:
            return f"Rp{v / 1_000_000_000_000:.2f} T".replace(".", ",")
        if abs_v >= 1_000_000_000:
            return f"Rp{v / 1_000_000_000:.2f} M".replace(".", ",")
        if abs_v >= 1_000_000:
            return f"Rp{v / 1_000_000:.2f} jt".replace(".", ",")
        if abs_v >= 1:
            return f"Rp{v:,.0f}".replace(",", ".")
        return f"Rp{v:.6f}".replace(".", ",")

    prefix = CURRENCY_OPTIONS.get(cur, {}).get("prefix", f"{cur} ")
    abs_v = abs(v)
    if abs_v >= 1_000_000_000_000:
        return f"{prefix}{v / 1_000_000_000_000:.2f} T"
    if abs_v >= 1_000_000_000:
        return f"{prefix}{v / 1_000_000_000:.2f} B"
    if abs_v >= 1_000_000:
        return f"{prefix}{v / 1_000_000:.2f} M"
    if abs_v >= 1:
        return f"{prefix}{v:,.2f}"
    if abs_v >= 0.01:
        return f"{prefix}{v:.4f}"
    return f"{prefix}{v:.8f}"


def format_percent(value) -> str:
    """Format persentase dengan tanda +/-."""
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):+.2f}%"