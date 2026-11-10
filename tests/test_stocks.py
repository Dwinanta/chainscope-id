import pandas as pd
from chainscope import stocks


def test_get_stock_universe_contains_idx_and_us_stocks():
    universe = stocks.get_stock_universe()
    assert len(universe) >= 10
    symbols = [s["symbol"] for s in universe]
    assert "BBCA.JK" in symbols
    assert "BBRI.JK" in symbols
    assert "AAPL" in symbols
    assert "NVDA" in symbols


def test_fetch_stock_quote_returns_structured_data(monkeypatch):
    quote = stocks.fetch_stock_quote("BBCA.JK")
    assert "symbol" in quote
    assert "price" in quote
    assert "currency" in quote
    assert quote["currency"] == "IDR"
    assert "status" in quote


def test_fallback_stock_quote_returns_safe_zero_values():
    fallback = stocks._fallback_stock_quote("UNKNOWN.JK")
    assert fallback["price"] == 0.0
    assert fallback["status"] == "UNAVAILABLE"
    assert fallback["currency"] == "IDR"


def test_fetch_stock_history_returns_dataframe_or_empty():
    df = stocks.fetch_stock_history("AAPL", period="5d")
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "close" in df.columns
        assert "price" in df.columns
