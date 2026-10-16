"""Tes untuk modul laporan PDF."""

import pandas as pd

from chainscope import report


def _mk_market_df():
    return pd.DataFrame([
        {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc",
         "current_price": 83000.0, "market_cap": 1_650_000_000_000,
         "total_volume": 30_000_000_000, "price_change_percentage_24h": 0.5},
        {"id": "ethereum", "name": "Ethereum", "symbol": "eth",
         "current_price": 2500.0, "market_cap": 300_000_000_000,
         "total_volume": 15_000_000_000, "price_change_percentage_24h": 0.1},
        {"id": "tether", "name": "Tether", "symbol": "usdt",
         "current_price": 1.0, "market_cap": 120_000_000_000,
         "total_volume": 50_000_000_000, "price_change_percentage_24h": 0.0},
    ])


def test_build_report_returns_pdf_bytes():
    df = _mk_market_df()
    pdf_bytes = report.build_weekly_report(df, "IDR", "LIVE")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


def test_build_report_usd():
    df = _mk_market_df()
    pdf_bytes = report.build_weekly_report(df, "USD", "DEMO")
    assert pdf_bytes.startswith(b"%PDF")


def test_build_report_empty_df():
    df = pd.DataFrame(
        columns=["id", "name", "symbol", "current_price",
                 "market_cap", "total_volume", "price_change_percentage_24h"]
    )
    pdf_bytes = report.build_weekly_report(df, "IDR", "LIVE")
    assert pdf_bytes.startswith(b"%PDF")


def test_safe_replaces_unicode():
    assert report._safe("Rp1 \u2014 two") == "Rp1 - two"
    assert report._safe("\u2248") == "~"


def test_money_format():
    assert "Rp1.50 T" in report._money(1_500_000_000_000, "IDR")
    assert "$1.50 B" in report._money(1_500_000_000, "USD")
    assert report._money(None, "IDR") == "-"


def test_percent_format():
    assert report._percent(1.5) == "+1.50%"
    assert report._percent(-2.345) == "-2.35%"
    assert report._percent(None) == "-"


def test_report_top_n_capped_by_dataframe_size():
    df = _mk_market_df()
    # top_n=20 tapi hanya ada 3 baris -> harus tetap jalan tanpa error
    pdf_bytes = report.build_weekly_report(df, "IDR", "LIVE", top_n=20)
    assert pdf_bytes.startswith(b"%PDF")