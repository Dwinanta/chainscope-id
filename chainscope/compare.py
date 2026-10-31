"""Utilitas untuk membandingkan beberapa koin."""

import pandas as pd


def build_comparison_df(history_by_coin: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Gabungkan beberapa DataFrame riwayat harga menjadi satu DataFrame.

    Input : {coin_id: DataFrame dengan kolom 'waktu' dan 'price'}
    Output: DataFrame dengan kolom 'waktu' + satu kolom per coin_id.
    """
    if not history_by_coin:
        return pd.DataFrame()

    dfs = []
    for coin_id, df in history_by_coin.items():
        if df is None or df.empty:
            continue
        if "waktu" not in df.columns or "price" not in df.columns:
            continue
        sub = df[["waktu", "price"]].rename(columns={"price": coin_id})
        dfs.append(sub)

    if not dfs:
        return pd.DataFrame()

    result = dfs[0]
    for other in dfs[1:]:
        result = result.merge(other, on="waktu", how="outer")

    return result.sort_values("waktu").reset_index(drop=True)


def normalize_to_100(df: pd.DataFrame, exclude_cols=("waktu",)) -> pd.DataFrame:
    """Normalisasi setiap kolom harga agar nilai awalnya 100.

    Berguna untuk membandingkan koin dengan harga sangat berbeda
    (mis. BTC ~$80k vs DOGE ~$0.15) dalam skala yang sebanding.
    """
    if df is None or df.empty:
        return df

    out = df.copy()
    for col in out.columns:
        if col in exclude_cols:
            continue
        series = out[col]
        first_valid = series.dropna()
        if first_valid.empty:
            continue
        base = float(first_valid.iloc[0])
        if base == 0:
            continue
        out[col] = series / base * 100.0
    return out


def build_relative_ratio(
    history_a: pd.DataFrame,
    history_b: pd.DataFrame,
    moving_average_period: int = 20,
) -> pd.DataFrame:
    """Hitung rasio harga A/B beserta moving average dari riwayat harga."""
    if moving_average_period <= 0:
        raise ValueError("Periode moving average harus lebih besar dari nol.")

    required = {"waktu", "price"}
    for history in (history_a, history_b):
        if history is None or history.empty:
            return pd.DataFrame(columns=["waktu", "ratio", "ma20"])
        if not required.issubset(history.columns):
            return pd.DataFrame(columns=["waktu", "ratio", "ma20"])

    prices_a = history_a[["waktu", "price"]].rename(columns={"price": "price_a"})
    prices_b = history_b[["waktu", "price"]].rename(columns={"price": "price_b"})
    merged = prices_a.merge(prices_b, on="waktu", how="inner").sort_values("waktu")
    merged["price_a"] = pd.to_numeric(merged["price_a"], errors="coerce")
    merged["price_b"] = pd.to_numeric(merged["price_b"], errors="coerce")
    merged = merged.dropna(subset=["price_a", "price_b"])
    merged = merged[(merged["price_a"] > 0) & (merged["price_b"] > 0)]
    if merged.empty:
        return pd.DataFrame(columns=["waktu", "ratio", "ma20"])

    merged["ratio"] = merged["price_a"] / merged["price_b"]
    merged["ma20"] = merged["ratio"].rolling(
        window=moving_average_period,
        min_periods=moving_average_period,
    ).mean()
    return merged[["waktu", "ratio", "ma20"]].reset_index(drop=True)