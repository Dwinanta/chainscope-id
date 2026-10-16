"""Indikator teknikal untuk ChainScope ID.

Semua fungsi bekerja pada pandas Series dan mengembalikan Series
dengan index yang sama.
"""

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=window, min_periods=1).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder smoothing).

    Nilai 0–100. >70 overbought, <30 oversold.
    Series pendek (< 2 titik) akan mengembalikan 50 (netral).
    """
    if series is None or len(series) < 2:
        return pd.Series([50.0] * len(series), index=series.index)

    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    result = 100 - (100 / (1 + rs))

    # Jika avg_loss = 0 (harga naik terus), RSI = 100
    result = result.where(avg_loss != 0, 100.0)
    # Baris pertama NaN -> isi 50
    return result.fillna(50.0)


def bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (middle, upper, lower) dari Bollinger Bands."""
    mid = series.rolling(window=window, min_periods=1).mean()
    std = series.rolling(window=window, min_periods=1).std().fillna(0.0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower