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


def test_search_matches_stable_coin_id():
    result = search.filter_coins(_mk_df(), "ethereum")

    assert result["id"].tolist() == ["ethereum"]


def test_coin_selector_limits_results_and_prioritizes_selected_and_popular():
    catalog = pd.DataFrame([
        {
            "id": f"token-{index:03d}",
            "name": f"Token {index:03d}",
            "symbol": f"t{index:03d}",
            "label": f"Token {index:03d} (T{index:03d})",
        }
        for index in range(100)
    ] + [{
        "id": "bitcoin",
        "name": "Bitcoin",
        "symbol": "btc",
        "label": "Bitcoin (BTC)",
    }])

    options = search.coin_selector_options(catalog, "")

    assert len(options) == 50
    assert options[0] == "bitcoin"


def test_coin_selector_prioritizes_exact_match_and_preserves_selection():
    catalog = pd.DataFrame([
        {"id": "ethereum", "name": "Ethereum", "symbol": "eth", "label": "Ethereum (ETH)"},
        {"id": "ethereum-classic", "name": "Ethereum Classic", "symbol": "etc", "label": "Ethereum Classic (ETC)"},
        {"id": "my-eth-token", "name": "My ETH Token", "symbol": "met", "label": "My ETH Token (MET)"},
    ])

    options = search.coin_selector_options(
        catalog, "eth", selected_ids=["ethereum-classic"]
    )

    assert options == ["ethereum-classic", "ethereum", "my-eth-token"]


def test_coin_selector_preserves_existing_choices_even_over_result_limit():
    catalog = pd.DataFrame([
        {"id": f"coin-{index}", "name": f"Coin {index}", "symbol": f"c{index}"}
        for index in range(60)
    ])

    options = search.coin_selector_options(
        catalog,
        "coin",
        selected_ids=[f"coin-{index}" for index in range(52)],
        limit=50,
    )

    assert len(options) == 52
    assert options[:52] == [f"coin-{index}" for index in range(52)]


def test_coin_selector_does_not_make_unmatched_assets_selectable():
    catalog = pd.DataFrame([
        {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc"},
        {"id": "ethereum", "name": "Ethereum", "symbol": "eth"},
    ])

    assert search.coin_selector_options(catalog, "missing") == []