import pytest
import streamlit as st
import pandas as pd

from chainscope import (
    views_market, views_finance, views_web3,
    stocks, forex, fundamentals, exchanges, backtesting,
    personal_finance, reconciliation, education,
    web3_networks, web3_wallet, dex_analytics, dex_swap, token_safety,
)


@pytest.fixture(autouse=True)
def mock_external_network_calls(monkeypatch):
    """Mock external APIs so integration tests run instantaneously without network latency."""
    monkeypatch.setattr(stocks, "fetch_stock_quote", lambda sym: {
        "symbol": sym, "price": 10000.0, "previous_close": 9800.0, "change": 200.0,
        "change_pct": 2.04, "currency": "IDR", "exchange": "IDX", "status": "LIVE"
    })
    monkeypatch.setattr(stocks, "fetch_stock_history", lambda sym, period="1mo": pd.DataFrame({
        "timestamp": pd.date_range("2026-10-01", periods=10),
        "open": [100.0]*10, "high": [105.0]*10, "low": [95.0]*10, "close": [102.0]*10, "price": [102.0]*10
    }))
    monkeypatch.setattr(forex, "fetch_forex_quote", lambda sym: {
        "pair": "USD/IDR", "symbol": sym, "rate": 16000.0, "previous_close": 15950.0,
        "change": 50.0, "change_pct": 0.31, "status": "LIVE"
    })
    monkeypatch.setattr(forex, "fetch_forex_history", lambda sym, period="1mo": pd.DataFrame({
        "timestamp": pd.date_range("2026-10-01", periods=10),
        "open": [16000.0]*10, "high": [16100.0]*10, "low": [15900.0]*10, "close": [16050.0]*10, "price": [16050.0]*10
    }))
    monkeypatch.setattr(exchanges, "fetch_cross_exchange_tickers", lambda cid: pd.DataFrame([
        {"Exchange": "Binance", "Pair": "BTC/USDT", "Price_USD": 60000.0, "Volume_24h_USD": 1e6, "Spread_Pct": 0.1, "Trust": "Green"},
        {"Exchange": "Indodax", "Pair": "BTC/IDR", "Price_USD": 60800.0, "Volume_24h_USD": 5e5, "Spread_Pct": 0.2, "Trust": "Green"},
    ]))
    monkeypatch.setattr(dex_analytics, "fetch_trending_dex_pools", lambda net: pd.DataFrame([
        {"Pool": "PEPE / WETH", "Price_USD": 0.00001, "Liquidity_USD": 1e7, "Volume_24h_USD": 2e6, "Change_24h_Pct": 5.0, "Buys_24h": 500, "Sells_24h": 400, "Address": "0x123", "Network": "ETH"}
    ]))


def test_views_market_renders_without_crashing(monkeypatch):
    """Verify all market view components execute safely."""
    monkeypatch.setattr(st, "markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "caption", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "success", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "error", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "plotly_chart", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "dataframe", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "metric", lambda *args, **kwargs: None)

    views_market.render_fundamental_analysis_page(dark_mode=False)
    views_market.render_stock_market_page(currency="USD", dark_mode=True)
    views_market.render_forex_market_page(dark_mode=False)
    views_market.render_multi_exchange_page(dark_mode=True)


def test_views_finance_renders_without_crashing(monkeypatch):
    """Verify all personal finance view components execute safely."""
    monkeypatch.setattr(st, "markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "caption", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "success", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "plotly_chart", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "dataframe", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "progress", lambda *args, **kwargs: None)

    views_finance.render_financial_overview_page("test-user-id", dark_mode=False)
    views_finance.render_income_expense_page("test-user-id", dark_mode=True)
    views_finance.render_budget_management_page("test-user-id", dark_mode=False)
    views_finance.render_savings_goals_page("test-user-id", dark_mode=True)
    views_finance.render_assets_liabilities_page("test-user-id", dark_mode=False)
    views_finance.render_portfolio_reconciliation_page("test-user-id", dark_mode=True)
    views_finance.render_financial_education_page(dark_mode=False)


def test_views_web3_renders_without_crashing(monkeypatch):
    """Verify all web3 view components execute safely."""
    monkeypatch.setattr(st, "markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "caption", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "warning", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "success", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "dataframe", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(st, "code", lambda *args, **kwargs: None)

    views_web3.render_web3_dashboard_page("test-user-id", dark_mode=False)
    views_web3.render_dex_analytics_page(dark_mode=True)
    views_web3.render_dex_swap_page("test-user-id", dark_mode=False)
    views_web3.render_token_safety_page(dark_mode=True)
