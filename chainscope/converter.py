"""Logika konversi antar-aset untuk ChainScope ID."""

from typing import Optional

import pandas as pd

from . import config


def build_price_map(
    market_df: pd.DataFrame,
    currency: str,
    usd_currency_rate: float,
) -> dict[str, float]:
    """Bangun peta harga dalam mata uang yang dipilih.

    USD dan mata uang terpilih dapat dikonversi; harga koin mengikuti
    mata uang terpilih dan berasal dari market_df.
    """
    cur = currency.upper()
    if cur not in config.CURRENCY_OPTIONS:
        raise ValueError(f"Mata uang tidak dikenal: {currency}")
    if usd_currency_rate <= 0:
        raise ValueError("Kurs USD terhadap mata uang terpilih harus positif.")

    prices: dict[str, float] = {cur: 1.0, "USD": usd_currency_rate}

    if "id" in market_df.columns and "current_price" in market_df.columns:
        for _, row in market_df.iterrows():
            cid = str(row["id"])
            try:
                prices[cid] = float(row["current_price"])
            except (TypeError, ValueError):
                continue

    return prices


def convert(
    amount: float,
    from_asset: str,
    to_asset: str,
    price_map: dict[str, float],
) -> Optional[float]:
    """Konversi `amount` dari `from_asset` ke `to_asset`.

    Return None jika input tidak valid atau harga tidak tersedia.
    """
    if amount is None or amount < 0:
        return None
    if from_asset == to_asset:
        return amount
    p_from = price_map.get(from_asset)
    p_to = price_map.get(to_asset)
    if p_from is None or p_to is None or p_to <= 0 or p_from < 0:
        return None
    return amount * p_from / p_to