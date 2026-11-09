import pytest

from chainscope.performance_coach import analyze_trades


def _trade(side, amount, price, day, strategy="Swing", coin="bitcoin"):
    return {
        "coin_id": coin,
        "symbol": coin.upper(),
        "side": side,
        "amount": amount,
        "price_usd": price,
        "trade_time": day,
        "strategy_tag": strategy,
    }


def test_fifo_realized_and_unrealized_are_split_by_strategy():
    trades = [
        _trade("buy", 2, 100, "2026-01-01", "Swing"),
        _trade("buy", 1, 200, "2026-01-02", "Scalp"),
        _trade("sell", 1, 150, "2026-01-03", "Swing"),
    ]

    report = analyze_trades(trades, {"bitcoin": 180})

    assert report["closed_trades"] == 1
    assert report["outcomes"].iloc[0]["realized_pnl_usd"] == pytest.approx(50)
    positions = report["positions"].set_index("strategy_tag")
    assert positions.loc["Swing", "amount"] == pytest.approx(1)
    assert positions.loc["Swing", "unrealized_pnl_usd"] == pytest.approx(80)
    assert positions.loc["Scalp", "amount"] == pytest.approx(1)
    assert positions.loc["Scalp", "unrealized_pnl_usd"] == pytest.approx(-20)
    assert set(report["strategy_stats"]["strategy_tag"]) == {"Swing", "Scalp"}


def test_metrics_profit_factor_streaks_and_drawdown_use_closed_trade_results():
    trades = [
        _trade("buy", 1, 100, "2026-01-01"),
        _trade("sell", 1, 120, "2026-01-02"),
        _trade("buy", 1, 100, "2026-01-03"),
        _trade("sell", 1, 90, "2026-01-04"),
        _trade("buy", 1, 100, "2026-01-05"),
        _trade("sell", 1, 80, "2026-01-06"),
    ]

    report = analyze_trades(trades)

    assert report["win_rate_pct"] == pytest.approx(100 / 3)
    assert report["profit_factor"] == pytest.approx(20 / 30)
    assert report["average_win_usd"] == pytest.approx(20)
    assert report["average_loss_usd"] == pytest.approx(-15)
    assert report["average_win_loss_ratio"] == pytest.approx(4 / 3)
    assert report["best_win_streak"] == 1
    assert report["best_loss_streak"] == 2
    assert report["max_drawdown_usd"] == pytest.approx(30)


def test_unmatched_sells_and_missing_risk_fields_are_explicit():
    report = analyze_trades([_trade("sell", 2, 100, "2026-01-01")])

    assert report["closed_trades"] == 0
    assert report["unmatched_sells_amount"] == pytest.approx(2)
    assert report["risk_assessment_available"] is False
    assert report["timeframe_analysis_available"] is False
    assert report["positions"].empty


def test_invalid_rows_are_counted_and_timed_trades_can_be_grouped_by_utc_session():
    trades = [
        _trade("buy", 1, 100, "2026-01-01T08:00:00Z"),
        _trade("sell", 1, 110, "2026-01-01T10:00:00Z"),
        _trade("buy", 0, 100, "2026-01-02"),
    ]

    report = analyze_trades(trades)

    assert report["invalid_trades"] == 1
    assert report["date_only_trades"] == 0
    assert report["session_analysis_available"] is True
    assert report["sessions"].iloc[0]["session"] == "Europe (UTC)"
    assert report["sessions"].iloc[0]["realized_pnl_usd"] == pytest.approx(10)


def test_ambiguous_same_timestamp_records_are_excluded_from_fifo_metrics():
    report = analyze_trades([
        _trade("buy", 1, 100, "2026-01-01"),
        _trade("sell", 1, 120, "2026-01-01"),
    ])

    assert report["ambiguous_trades"] == 2
    assert report["closed_trades"] == 0
    assert report["positions"].empty


def test_position_size_after_a_loss_is_reported_as_notional_proxy():
    report = analyze_trades([
        _trade("buy", 0.1, 100, "2026-01-01T08:00:00Z"),
        _trade("sell", 0.1, 90, "2026-01-02T08:00:00Z"),
        _trade("buy", 0.2, 100, "2026-01-03T08:00:00Z"),
    ])

    assert report["post_loss_size_checks"] == [{
        "increased": True,
        "previous_buy_notional_usd": 10,
        "next_buy_notional_usd": 20,
    }]
    assert "proxy ukuran transaksi" in report["insights"][0] or any(
        "proxy ukuran transaksi" in insight for insight in report["insights"]
    )


def test_missing_market_prices_do_not_produce_zero_unrealized_returns():
    report = analyze_trades([
        _trade("buy", 1, 100, "2026-01-01"),
    ])

    assert report["market_data_complete"] is False
    assert report["current_value_usd"] is None
    assert report["positions"].iloc[0]["unrealized_pnl_usd"] is None
    assert report["strategy_stats"].iloc[0]["allocation_pct"] is None


def test_naive_intraday_timestamps_are_not_assumed_to_be_utc_sessions():
    report = analyze_trades([
        _trade("buy", 1, 100, "2026-01-01 08:00:00"),
        _trade("sell", 1, 110, "2026-01-02 08:00:00"),
    ])

    assert report["session_analysis_available"] is False
    assert report["sessions"].empty


def test_no_trades_returns_empty_metrics_without_inventing_results():
    report = analyze_trades([])

    assert report["total_trades"] == 0
    assert report["win_rate_pct"] is None
    assert report["profit_factor"] is None
    assert report["insights"] == []
