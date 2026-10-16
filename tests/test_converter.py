"""Tes untuk modul converter."""

import pandas as pd
import pytest

from chainscope import converter


def _mk_market_df():
    return pd.DataFrame([
        {"id": "bitcoin",  "current_price": 83_000.0},
        {"id": "ethereum", "current_price": 2_500.0},
    ])


def test_price_map_usd_currency():
    df = _mk_market_df()
    prices = converter.build_price_map(df, "USD", usd_idr_rate=16_000.0)
    assert prices["USD"] == 1.0
    assert prices["IDR"] == pytest.approx(1.0 / 16_000.0)
    assert prices["bitcoin"] == 83_000.0
    assert prices["ethereum"] == 2_500.0


def test_price_map_idr_currency():
    df = _mk_market_df()
    prices = converter.build_price_map(df, "IDR", usd_idr_rate=16_000.0)
    assert prices["IDR"] == 1.0
    assert prices["USD"] == 16_000.0


def test_convert_btc_to_eth():
    df = _mk_market_df()
    prices = converter.build_price_map(df, "USD", usd_idr_rate=16_000.0)
    # 1 BTC = 83,000 USD ; 1 ETH = 2,500 USD  ->  33.2 ETH
    assert converter.convert(1.0, "bitcoin", "ethereum", prices) == pytest.approx(33.2)


def test_convert_returns_none_for_unknown_asset():
    df = _mk_market_df()
    prices = converter.build_price_map(df, "USD", usd_idr_rate=16_000.0)
    assert converter.convert(1.0, "bitcoin", "unknown", prices) is None


def test_convert_same_asset_returns_amount():
    prices = {"USD": 1.0}
    assert converter.convert(42.0, "USD", "USD", prices) == 42.0


def test_convert_negative_amount_returns_none():
    prices = {"USD": 1.0, "IDR": 0.0000625}
    assert converter.convert(-1.0, "USD", "IDR", prices) is None


def test_build_price_map_invalid_currency():
    df = _mk_market_df()
    with pytest.raises(ValueError):
        converter.build_price_map(df, "EUR", usd_idr_rate=16_000.0)