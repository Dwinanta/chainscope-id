import pandas as pd
from chainscope import dex_analytics


def test_fetch_trending_dex_pools_returns_dataframe():
    df = dex_analytics.fetch_trending_dex_pools("eth")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Pool" in df.columns
    assert "Liquidity_USD" in df.columns
    assert "Volume_24h_USD" in df.columns


def test_search_dex_tokens_empty_string():
    res = dex_analytics.search_dex_tokens("")
    assert res == []
