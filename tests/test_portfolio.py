"""Tes untuk modul portfolio."""

from unittest.mock import patch

import pandas as pd
import pytest

from chainscope import portfolio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_file(tmp_path):
    return tmp_path / "portfolio.json"


def _mk_market_df():
    return pd.DataFrame([
        {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc",
         "current_price": 83_000.0, "market_cap": 1_650_000_000_000,
         "total_volume": 30_000_000_000, "price_change_percentage_24h": 0.5},
        {"id": "ethereum", "name": "Ethereum", "symbol": "eth",
         "current_price": 2_500.0, "market_cap": 300_000_000_000,
         "total_volume": 15_000_000_000, "price_change_percentage_24h": 0.1},
    ])


# ---------------------------------------------------------------------------
# Persistensi
# ---------------------------------------------------------------------------

def test_load_holdings_empty_when_file_missing(fake_file):
    with patch.object(portfolio, "PORTFOLIO_FILE", fake_file):
        assert portfolio.load_holdings() == []


def test_save_and_load_roundtrip(fake_file):
    with patch.object(portfolio, "PORTFOLIO_FILE", fake_file):
        portfolio.save_holdings([
            {"coin_id": "bitcoin", "amount": 0.5, "buy_price_usd": 80_000.0},
            {"coin_id": "ethereum", "amount": 2.0, "buy_price_usd": 2_400.0},
        ])
        loaded = portfolio.load_holdings()
        assert len(loaded) == 2
        assert loaded[0]["coin_id"] == "bitcoin"
        assert loaded[0]["amount"] == 0.5


def test_add_or_update_holding(fake_file):
    with patch.object(portfolio, "PORTFOLIO_FILE", fake_file):
        portfolio.add_or_update_holding("bitcoin", 0.5, 80_000.0)
        portfolio.add_or_update_holding("bitcoin", 0.8, 75_000.0)
        loaded = portfolio.load_holdings()
        assert len(loaded) == 1
        assert loaded[0]["amount"] == 0.8
        assert loaded[0]["buy_price_usd"] == 75_000.0


def test_remove_holding(fake_file):
    with patch.object(portfolio, "PORTFOLIO_FILE", fake_file):
        portfolio.save_holdings([
            {"coin_id": "bitcoin", "amount": 0.5, "buy_price_usd": 80_000.0},
            {"coin_id": "ethereum", "amount": 2.0, "buy_price_usd": 2_400.0},
        ])
        portfolio.remove_holding("bitcoin")
        loaded = portfolio.load_holdings()
        assert len(loaded) == 1
        assert loaded[0]["coin_id"] == "ethereum"


def test_clear_holdings(fake_file):
    with patch.object(portfolio, "PORTFOLIO_FILE", fake_file):
        portfolio.save_holdings([
            {"coin_id": "bitcoin", "amount": 0.5, "buy_price_usd": 80_000.0},
        ])
        portfolio.clear_holdings()
        assert portfolio.load_holdings() == []


# ---------------------------------------------------------------------------
# Perhitungan
# ---------------------------------------------------------------------------

def test_compute_portfolio_usd():
    holdings = [
        {"coin_id": "bitcoin", "amount": 1.0, "buy_price_usd": 80_000.0},
    ]
    df = portfolio.compute_portfolio(
        holdings, _mk_market_df(), usd_idr_rate=16_000.0, currency="USD"
    )
    row = df.iloc[0]
    assert bool(row["found"]) is True
    assert row["invested"] == 80_000.0
    assert row["current_value"] == 83_000.0
    assert row["pnl"] == 3_000.0
    assert row["pnl_pct"] == pytest.approx(3.75)


def test_compute_portfolio_idr():
    holdings = [
        {"coin_id": "bitcoin", "amount": 1.0, "buy_price_usd": 80_000.0},
    ]
    # market_df dalam IDR
    market = pd.DataFrame([
        {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc",
         "current_price": 83_000.0 * 16_000.0},
    ])
    df = portfolio.compute_portfolio(
        holdings, market, usd_idr_rate=16_000.0, currency="IDR"
    )
    row = df.iloc[0]
    assert row["buy_price"] == 80_000.0 * 16_000.0
    assert row["invested"] == 80_000.0 * 16_000.0
    assert row["current_value"] == 83_000.0 * 16_000.0


def test_compute_portfolio_missing_coin():
    holdings = [
        {"coin_id": "solana", "amount": 10.0, "buy_price_usd": 100.0},
    ]
    df = portfolio.compute_portfolio(
        holdings, _mk_market_df(), usd_idr_rate=16_000.0, currency="USD"
    )
    row = df.iloc[0]
    assert bool(row["found"]) is False
    assert row["current_value"] is None
    assert row["pnl"] is None