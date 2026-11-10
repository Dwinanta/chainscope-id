"""Technical analysis indicators for ChainScope ID.

All functions operate on pandas Series or DataFrames and return Series with matching indexes.
"""

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=window, min_periods=1).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder smoothing).

    Value 0–100. >70 overbought, <30 oversold.
    Short series (< 2 points) returns 50 (neutral).
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

    # If avg_loss = 0, RSI = 100
    result = result.where(avg_loss != 0, 100.0)
    # First row NaN -> fill with 50.0
    return result.fillna(50.0)


def bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (middle, upper, lower) from Bollinger Bands."""
    mid = series.rolling(window=window, min_periods=1).mean()
    std = series.rolling(window=window, min_periods=1).std().fillna(0.0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower


def macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Moving Average Convergence Divergence.
    
    Returns (macd_line, signal_line, histogram).
    """
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def atr(
    high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
) -> pd.Series:
    """Average True Range for volatility estimation."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window, min_periods=1).mean()


def mfi(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, window: int = 14
) -> pd.Series:
    """Money Flow Index (volume-weighted momentum)."""
    typical_price = (high + low + close) / 3.0
    raw_money_flow = typical_price * volume
    price_diff = typical_price.diff()
    
    pos_flow = raw_money_flow.where(price_diff > 0, 0.0)
    neg_flow = raw_money_flow.where(price_diff < 0, 0.0)
    
    pos_mf = pos_flow.rolling(window=window, min_periods=1).sum()
    neg_mf = neg_flow.rolling(window=window, min_periods=1).sum()
    
    mfr = pos_mf / neg_mf.replace(0, np.nan)
    res = 100 - (100 / (1 + mfr))
    return res.fillna(50.0)


def calculate_support_resistance(series: pd.Series, window: int = 20) -> tuple[float, float]:
    """Calculate key recent support and resistance price levels."""
    if series.empty:
        return 0.0, 0.0
    recent = series.tail(window)
    support = float(recent.min())
    resistance = float(recent.max())
    return support, resistance


def detect_order_blocks(df: pd.DataFrame, lookback: int = 30) -> list[dict]:
    """Detect institutional order blocks based on strong displacement moves."""
    if df.empty or len(df) < 5 or not {"open", "high", "low", "close"}.issubset(df.columns):
        return []
        
    recent = df.tail(lookback).reset_index(drop=True)
    blocks = []
    
    for i in range(1, len(recent) - 1):
        prev_candle = recent.iloc[i - 1]
        curr_candle = recent.iloc[i]
        next_candle = recent.iloc[i + 1]
        
        # Bullish Order Block: Bearish candle followed by strong bullish displacement
        if prev_candle["close"] < prev_candle["open"] and next_candle["close"] > prev_candle["high"]:
            blocks.append({
                "type": "Bullish Order Block",
                "high": float(prev_candle["open"]),
                "low": float(prev_candle["low"]),
                "timestamp": str(prev_candle.get("timestamp", i - 1)),
            })
        # Bearish Order Block: Bullish candle followed by strong bearish displacement
        elif prev_candle["close"] > prev_candle["open"] and next_candle["close"] < prev_candle["low"]:
            blocks.append({
                "type": "Bearish Order Block",
                "high": float(prev_candle["high"]),
                "low": float(prev_candle["open"]),
                "timestamp": str(prev_candle.get("timestamp", i - 1)),
            })
            
    return blocks[-5:]  # return the latest 5 blocks
