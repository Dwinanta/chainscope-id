import pandas as pd
from chainscope import forex


def test_get_forex_pairs_includes_usdidr_and_majors():
    pairs = forex.get_forex_pairs()
    symbols = [p["symbol"] for p in pairs]
    assert "USDIDR=X" in symbols
    assert "EURUSD=X" in symbols


def test_fetch_forex_quote_structure():
    quote = forex.fetch_forex_quote("USDIDR=X")
    assert "pair" in quote
    assert "rate" in quote
    assert "change_pct" in quote
    assert "status" in quote


def test_calculate_currency_strength_bounded_scores():
    sample_quotes = [
        {"pair": "USD/IDR", "change_pct": 0.5},
        {"pair": "EUR/USD", "change_pct": -0.3},
        {"pair": "GBP/USD", "change_pct": 0.2},
    ]
    df = forex.calculate_currency_strength(sample_quotes)
    assert not df.empty
    assert "currency" in df.columns
    assert "strength_score" in df.columns
    for score in df["strength_score"]:
        assert 0.0 <= score <= 100.0
