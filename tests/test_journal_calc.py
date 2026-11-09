import pytest

from chainscope import journal_calc


def test_portfolio_positions_are_grouped_and_sold_by_stable_coin_id():
    trades = [
        {
            "coin_id": "asset-one",
            "symbol": "SAME",
            "side": "buy",
            "amount": 2,
            "price_usd": 100,
            "trade_time": "2026-01-01",
            "strategy_tag": "Swing",
        },
        {
            "coin_id": "asset-two",
            "symbol": "SAME",
            "side": "buy",
            "amount": 3,
            "price_usd": 200,
            "trade_time": "2026-01-01",
            "strategy_tag": "Swing",
        },
        {
            "coin_id": "asset-one",
            "symbol": "SAME",
            "side": "sell",
            "amount": 1,
            "price_usd": 150,
            "trade_time": "2026-01-02",
            "strategy_tag": "Swing",
        },
    ]

    positions = journal_calc.calculate_portfolio_from_trades(trades).set_index("coin_id")

    assert set(positions.index) == {"asset-one", "asset-two"}
    assert positions.loc["asset-one", "amount"] == pytest.approx(1)
    assert positions.loc["asset-one", "total_invested_usd"] == pytest.approx(100)
    assert positions.loc["asset-two", "amount"] == pytest.approx(3)
    assert positions.loc["asset-two", "total_invested_usd"] == pytest.approx(600)


def test_sells_close_fifo_lots_only_within_their_strategy():
    trades = [
        {
            "coin_id": "bitcoin",
            "symbol": "BTC",
            "side": "buy",
            "amount": 1,
            "price_usd": 100,
            "trade_time": "2026-01-01T10:00:00Z",
            "strategy_tag": "Swing",
        },
        {
            "coin_id": "bitcoin",
            "symbol": "BTC",
            "side": "buy",
            "amount": 2,
            "price_usd": 200,
            "trade_time": "2026-01-02T10:00:00Z",
            "strategy_tag": "Position",
        },
        {
            "coin_id": "bitcoin",
            "symbol": "BTC",
            "side": "sell",
            "amount": 1.5,
            "price_usd": 250,
            "trade_time": "2026-01-03T10:00:00Z",
            "strategy_tag": "Position",
        },
        {
            "coin_id": "bitcoin",
            "symbol": "BTC",
            "side": "sell",
            "amount": 10,
            "price_usd": 300,
            "trade_time": "2026-01-04T10:00:00Z",
            "strategy_tag": "Swing",
        },
    ]

    positions = journal_calc.calculate_portfolio_from_trades(trades).set_index(
        "strategy_tag"
    )

    assert "Swing" not in positions.index
    assert positions.loc["Position", "amount"] == pytest.approx(0.5)
    assert positions.loc["Position", "total_invested_usd"] == pytest.approx(100)
