"""Tes untuk klien API CoinGecko (dengan mock, tanpa internet)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from chainscope import api
# (ganti 'chainsope' menjadi 'chainscope')


@patch("chainscope.api.requests.get")
def test_fetch_market_data_returns_dataframe(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 83000,
            "market_cap": 1_650_000_000_000,
            "total_volume": 30_000_000_000,
            "price_change_percentage_24h": 0.5,
        }
    ]
    mock_get.return_value = mock_resp

    df = api.fetch_market_data("usd", 10)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["id"] == "bitcoin"


@patch("chainscope.api.requests.get")
def test_fetch_market_data_raises_on_empty_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = []
    mock_get.return_value = mock_resp

    with pytest.raises(api.ChainScopeAPIError):
        api.fetch_market_data("usd", 10)


@patch("chainscope.api.requests.get")
def test_fetch_market_data_raises_on_network_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("offline")

    with pytest.raises(api.ChainScopeAPIError):
        api.fetch_market_data("usd", 10)


@patch("chainscope.api.requests.get")
def test_fetch_all_coins_returns_coin_identity_fields(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    ]
    mock_get.return_value = mock_resp

    coins = api.fetch_all_coins()

    assert coins == [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    ]
    mock_get.assert_called_once_with(
        "https://api.coingecko.com/api/v3/coins/list",
        timeout=api.config.REQUEST_TIMEOUT,
    )


@patch("chainscope.api.requests.get")
def test_fetch_all_coins_skips_invalid_rows_and_rejects_empty_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "incomplete", "symbol": "inc"},
        None,
    ]
    mock_get.return_value = mock_resp

    assert api.fetch_all_coins() == [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}
    ]

    mock_resp.json.return_value = [{"id": "", "symbol": "x", "name": "Invalid"}]
    with pytest.raises(api.ChainScopeAPIError, match="daftar koin yang valid"):
        api.fetch_all_coins()


def test_merge_market_and_coin_list_keeps_market_rows_and_adds_unpriced_coins():
    market = pd.DataFrame([
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 100.0,
            "image": "bitcoin.png",
        },
        {
            "id": "top-market-only",
            "symbol": "top",
            "name": "Top Market Only",
            "current_price": 10.0,
            "image": "top.png",
        },
    ])
    catalog = pd.DataFrame([
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    ])

    merged = api.merge_market_and_coin_list(market, catalog)

    assert merged["id"].tolist() == ["bitcoin", "top-market-only", "ethereum"]
    assert merged["current_price"].tolist() == [100.0, 10.0, 0.0]
    assert merged.loc[merged["id"] == "ethereum", "image"].item() == ""


def test_merge_market_and_coin_list_requires_coin_identity_columns():
    with pytest.raises(ValueError, match="id, symbol, dan name"):
        api.merge_market_and_coin_list(pd.DataFrame(), pd.DataFrame())


@patch("chainscope.api.requests.get")
def test_fetch_price_history_returns_dataframe(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "prices": [
            [1700000000000, 83000.0],
            [1700003600000, 83100.0],
        ],
        "total_volumes": [
            [1700000000000, 1_000_000.0],
            [1700003600000, 1_100_000.0],
        ],
    }
    mock_get.return_value = mock_resp

    df = api.fetch_price_history("bitcoin", "usd", days=7)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["waktu", "price", "volume"]
    assert len(df) == 2
    assert df.iloc[0]["volume"] == 1_000_000.0


@patch("chainscope.api.requests.get")
def test_fetch_price_history_raises_on_missing_prices(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp

    with pytest.raises(api.ChainScopeAPIError):
        api.fetch_price_history("bitcoin", "usd")


@patch("chainscope.api.requests.get")
def test_fetch_indodax_all_tickers_returns_idr_markets(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "tickers": {
            "btc_idr": {"last": "100", "high": "110", "low": "90", "vol_idr": "500"},
            "eth_idr": {"last": "50", "high": "60", "low": "40", "vol_idr": "200"},
            "btcusdt": {"last": "1", "high": "1", "low": "1", "vol_idr": "1000"},
        }
    }
    mock_get.return_value = mock_resp

    df = api.fetch_indodax_all_tickers()

    assert list(df["Symbol"]) == ["BTC", "ETH"]
    assert list(df["Volume"]) == [500.0, 200.0]
    assert df.iloc[0]["Price"] == 100.0


@patch("chainscope.api.requests.get")
def test_fetch_indodax_all_tickers_raises_for_invalid_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"tickers": {}}
    mock_get.return_value = mock_resp

    with pytest.raises(api.ChainScopeAPIError):
        api.fetch_indodax_all_tickers()


@patch("chainscope.api.requests.get")
def test_fetch_exchange_prices_reads_indodax_and_upbit(mock_get):
    indodax_response = MagicMock()
    indodax_response.raise_for_status.return_value = None
    indodax_response.json.return_value = {
        "tickers": {
            "btc_idr": {"last": "100"},
            "eth_idr": {"last": "50"},
        }
    }
    upbit_response = MagicMock()
    upbit_response.raise_for_status.return_value = None
    upbit_response.json.return_value = [
        {"market": "IDR-BTC", "trade_price": 101},
        {"market": "IDR-ETH", "trade_price": 51},
    ]
    mock_get.side_effect = [indodax_response, upbit_response]

    result = api.fetch_exchange_prices()

    assert result == {
        "Indodax": {"BTC": 100.0, "ETH": 50.0},
        "Upbit Indonesia": {"BTC": 101.0, "ETH": 51.0},
    }