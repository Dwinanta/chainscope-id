"""Tes untuk data demo."""

from chainscope import config, demo
# (ganti 'chainsope' menjadi 'chainscope')


def test_demo_returns_requested_number_of_rows():
    df = demo.get_demo_market_data(limit=5, currency="USD")
    assert len(df) == 5


def test_demo_returns_50_rows():
    df = demo.get_demo_market_data(limit=50, currency="USD")
    assert len(df) == 50


def test_demo_idr_scales_prices_by_rate():
    usd = demo.get_demo_market_data(limit=3, currency="USD")
    idr = demo.get_demo_market_data(limit=3, currency="IDR")
    for u, i in zip(usd["current_price"], idr["current_price"]):
        assert abs(i - u * config.DEMO_USD_TO_IDR) < 1


def test_demo_history_has_7_days_of_hourly_points():
    hist = demo.get_demo_price_history(current_price=100.0)
    assert len(hist) == 7 * 24
    assert list(hist.columns) == ["waktu", "price"]