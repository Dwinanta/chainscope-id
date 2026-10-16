"""Tes untuk modul indikator teknikal."""

import pandas as pd
import pytest

from chainscope import indicators


def _series(values):
    return pd.Series(values, dtype="float64")


def test_sma_basic():
    s = _series([1, 2, 3, 4, 5])
    result = indicators.sma(s, window=3)
    # min_periods=1 → rata-rata tersedia sejak data pertama
    assert result.iloc[0] == 1.0
    assert result.iloc[1] == 1.5
    assert result.iloc[2] == 2.0
    assert result.iloc[3] == 3.0
    assert result.iloc[4] == 4.0


def test_ema_responds_to_change():
    s = _series([10, 10, 10, 20, 20])
    result = indicators.ema(s, window=3)
    assert result.iloc[0] == 10.0
    # EMA naik setelah harga naik
    assert result.iloc[3] > 10.0
    assert result.iloc[4] > result.iloc[3]


def test_rsi_all_gains_is_100():
    s = _series(list(range(1, 30)))  # naik terus
    result = indicators.rsi(s, window=14)
    # Baris terakhir seharusnya 100 (tidak ada loss)
    assert result.iloc[-1] == pytest.approx(100.0)


def test_rsi_all_losses_is_0():
    s = _series(list(range(30, 1, -1)))  # turun terus
    result = indicators.rsi(s, window=14)
    assert result.iloc[-1] == pytest.approx(0.0, abs=0.01)


def test_rsi_short_series():
    s = _series([1.0])
    result = indicators.rsi(s, window=14)
    assert result.iloc[0] == 50.0


def test_bollinger_bands_shape_and_order():
    s = _series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    mid, upper, lower = indicators.bollinger_bands(s, window=5, num_std=2)
    assert len(mid) == len(s)
    # upper selalu >= mid >= lower
    for m, u, l in zip(mid, upper, lower):
        assert u >= m >= l
    # Mid pada titik terakhir = rata-rata 5 data terakhir (6..10) = 8
    assert mid.iloc[-1] == pytest.approx(8.0)