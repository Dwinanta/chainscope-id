"""Tes untuk modul compare."""

import pandas as pd
import pytest

from chainscope import compare


def _mk_history(values):
    times = pd.date_range("2026-01-01", periods=len(values), freq="h")
    return pd.DataFrame({"waktu": times, "price": values})


def test_build_comparison_df_basic():
    hist = {
        "bitcoin": _mk_history([100, 110, 120]),
        "ethereum": _mk_history([10, 11, 12]),
    }
    result = compare.build_comparison_df(hist)
    assert "waktu" in result.columns
    assert "bitcoin" in result.columns
    assert "ethereum" in result.columns
    assert len(result) == 3


def test_build_comparison_df_empty_input():
    assert compare.build_comparison_df({}).empty
    assert compare.build_comparison_df({"x": pd.DataFrame()}).empty


def test_build_comparison_df_skips_bad_frames():
    hist = {
        "bitcoin": _mk_history([100, 110]),
        "broken": pd.DataFrame({"foo": [1, 2]}),
    }
    result = compare.build_comparison_df(hist)
    assert "bitcoin" in result.columns
    assert "broken" not in result.columns


def test_normalize_to_100():
    df = pd.DataFrame({
        "waktu": pd.date_range("2026-01-01", periods=3, freq="h"),
        "bitcoin": [100.0, 110.0, 120.0],
        "ethereum": [50.0, 50.0, 25.0],
    })
    result = compare.normalize_to_100(df)
    # bitcoin mulai dari 100, naik jadi 110, 120
    assert result["bitcoin"].iloc[0] == 100.0
    assert abs(result["bitcoin"].iloc[1] - 110.0) < 1e-9
    assert abs(result["bitcoin"].iloc[2] - 120.0) < 1e-9
    # ethereum mulai dari 100, flat, lalu turun ke 50
    assert result["ethereum"].iloc[0] == 100.0
    assert abs(result["ethereum"].iloc[1] - 100.0) < 1e-9
    assert abs(result["ethereum"].iloc[2] - 50.0) < 1e-9


def test_normalize_handles_empty():
    assert compare.normalize_to_100(pd.DataFrame()).empty


def test_build_relative_ratio_calculates_ratio_and_ma20():
    history_a = _mk_history(list(range(10, 40)))
    history_b = _mk_history([2.0] * 30)

    result = compare.build_relative_ratio(history_a, history_b)

    assert list(result.columns) == ["waktu", "ratio", "ma20"]
    assert len(result) == 30
    assert result["ratio"].iloc[0] == 5.0
    assert pd.isna(result["ma20"].iloc[18])
    assert result["ma20"].iloc[19] == sum(range(10, 30)) / 40
    assert result["ma20"].iloc[-1] == sum(range(20, 40)) / 40


def test_build_relative_ratio_ignores_invalid_prices_and_joins_matching_times():
    times = pd.date_range("2026-01-01", periods=4, freq="D")
    history_a = pd.DataFrame({
        "waktu": times,
        "price": [10.0, 20.0, 0.0, 40.0],
    })
    history_b = pd.DataFrame({
        "waktu": [times[0], times[1], times[3]],
        "price": [2.0, 4.0, 0.0],
    })

    result = compare.build_relative_ratio(history_a, history_b)

    assert result["waktu"].tolist() == [times[0], times[1]]
    assert result["ratio"].tolist() == [5.0, 5.0]


def test_build_relative_ratio_returns_empty_for_invalid_input():
    assert compare.build_relative_ratio(pd.DataFrame(), pd.DataFrame()).empty
    with pytest.raises(ValueError, match="moving average"):
        compare.build_relative_ratio(_mk_history([1]), _mk_history([1]), 0)