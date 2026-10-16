"""Tes untuk modul pencarian koin."""

import pandas as pd

from chainscope import search


def _mk_df():
    return pd.DataFrame([
        {"id": "bitcoin",  "name": "Bitcoin",  "symbol": "btc",  "current_price": 83000.0},
        {"id": "ethereum", "name": "Ethereum", "symbol": "eth",  "current_price": 2500.0},
        {"id": "tether",   "name": "Tether",   "symbol": "usdt", "current_price": 1.0},
    ])


def test_empty_query_returns_all_rows():
    df = _mk_df()
    assert len(search.filter_coins(df, "")) == 3
    assert len(search.filter_coins(df, "   ")) == 3
    assert len(search.filter_coins(df, None)) == 3


def test_search_by_name_case_insensitive():
    df = _mk_df()
    result = search.filter_coins(df, "BITCOIN")
    assert len(result) == 1
    assert result.iloc[0]["id"] == "bitcoin"


def test_search_by_symbol():
    df = _mk_df()
    result = search.filter_coins(df, "eth")
    # 'eth' cocok dengan 'Ethereum' (nama) dan 'Tether' (nama)
    assert len(result) == 2
    assert set(result["id"]) == {"ethereum", "tether"}


def test_search_partial_match():
    df = _mk_df()
    # 'eth' juga cocok dengan 'Tether'
    result = search.filter_coins(df, "eth")
    assert set(result["id"]) == {"ethereum", "tether"}

    # 'er' cocok dengan Ethereum dan Tether
    result2 = search.filter_coins(df, "er")
    assert set(result2["id"]) == {"ethereum", "tether"}

    # 'usd' cocok dengan USDT (simbol Tether)
    result3 = search.filter_coins(df, "usd")
    assert set(result3["id"]) == {"tether"}


def test_search_no_match_returns_empty():
    df = _mk_df()
    result = search.filter_coins(df, "xyz-nonexistent")
    assert len(result) == 0


def test_search_multiple_tokens_and_logic():
    df = _mk_df()
    # 'bit' + 'btc' → harus keduanya cocok untuk Bitcoin
    result = search.filter_coins(df, "bit btc")
    assert len(result) == 1
    assert result.iloc[0]["id"] == "bitcoin"

    # 'eth' + 'bit' → tidak ada yang cocok keduanya
    result2 = search.filter_coins(df, "eth bit")
    assert len(result2) == 0


def test_filter_empty_dataframe():
    df = pd.DataFrame(columns=["id", "name", "symbol"])
    result = search.filter_coins(df, "bitcoin")
    assert len(result) == 0