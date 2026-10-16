"""Pencarian koin untuk ChainScope ID."""

import pandas as pd


def filter_coins(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Filter DataFrame koin berdasarkan kata kunci.

    Pencarian case-insensitive pada kolom `name` dan `symbol`.
    - Query kosong / whitespace → kembalikan DataFrame asli.
    - Query dengan beberapa kata → semua kata harus cocok (AND).
    - Jika kolom `name`/`symbol` tidak ada, kembalikan DataFrame asli.
    """
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()

    if query is None:
        return df

    q = str(query).strip().lower()
    if not q:
        return df

    if "name" not in df.columns and "symbol" not in df.columns:
        return df

    tokens = [t for t in q.split() if t]
    if not tokens:
        return df

    name_col = df["name"].astype(str).str.lower() if "name" in df.columns else None
    symbol_col = (
        df["symbol"].astype(str).str.lower() if "symbol" in df.columns else None
    )

    mask = pd.Series([True] * len(df), index=df.index)
    for token in tokens:
        token_mask = pd.Series([False] * len(df), index=df.index)
        if name_col is not None:
            token_mask = token_mask | name_col.str.contains(token, regex=False)
        if symbol_col is not None:
            token_mask = token_mask | symbol_col.str.contains(token, regex=False)
        mask = mask & token_mask

    return df[mask]