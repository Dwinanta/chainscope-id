import pandas as pd
from chainscope import fundamentals


def test_get_stock_fundamentals_idx_bluechips():
    bbca = fundamentals.get_stock_fundamentals("BBCA.JK")
    assert bbca["name"] == "Bank Central Asia Tbk"
    assert bbca["pe_ratio"] > 0
    assert bbca["dividend_yield_pct"] > 0
    assert "valuation_grade" in bbca


def test_assess_valuation_categories():
    assert fundamentals.assess_valuation(8.0, "Financials") == "Undervalued / Attractive"
    assert fundamentals.assess_valuation(20.0, "Technology") == "Attractive for Tech"
    assert fundamentals.assess_valuation(-5.0, "General") == "Negative Earnings"


def test_get_sector_comparison_table():
    df = fundamentals.get_sector_comparison_table()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "P/E" in df.columns
    assert "Sector" in df.columns
