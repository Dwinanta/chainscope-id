import pandas as pd
from chainscope import exchanges


def test_calculate_arbitrage_opportunities_detects_spread():
    sample_df = pd.DataFrame([
        {"Exchange": "Binance", "Price_USD": 60000.0, "Volume_24h_USD": 1000000.0},
        {"Exchange": "Indodax", "Price_USD": 61200.0, "Volume_24h_USD": 500000.0},
    ])
    arb = exchanges.calculate_arbitrage_opportunities(sample_df)
    assert arb["has_arbitrage"] is True
    assert arb["min_price"] == 60000.0
    assert arb["max_price"] == 61200.0
    assert arb["spread_pct"] == 2.0
    assert arb["lowest_exchange"] == "Binance"
    assert arb["highest_exchange"] == "Indodax"


def test_calculate_arbitrage_handles_empty_or_single_exchange():
    arb = exchanges.calculate_arbitrage_opportunities(pd.DataFrame())
    assert arb["has_arbitrage"] is False
    assert arb["spread_pct"] == 0.0
