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
def test_fetch_price_history_returns_dataframe(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "prices": [
            [1700000000000, 83000.0],
            [1700003600000, 83100.0],
        ]
    }
    mock_get.return_value = mock_resp

    df = api.fetch_price_history("bitcoin", "usd", days=7)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["waktu", "price"]
    assert len(df) == 2


@patch("chainscope.api.requests.get")
def test_fetch_price_history_raises_on_missing_prices(mock_get):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp

    with pytest.raises(api.ChainScopeAPIError):
        api.fetch_price_history("bitcoin", "usd")