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