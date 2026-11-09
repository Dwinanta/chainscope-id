"""Portfolio positions derived from the shared journal FIFO calculation."""

import pandas as pd

from .performance_coach import analyze_trades


def calculate_portfolio_from_trades(trades: list[dict]) -> pd.DataFrame:
    """Return open FIFO lots by stable asset ID and strategy.

    Sell records only close buys for the same asset and strategy, matching the
    Performance Coach and avoiding negative or cross-strategy holdings.
    """
    if not trades:
        return pd.DataFrame()

    positions = analyze_trades(trades)["positions"]
    if positions.empty:
        return pd.DataFrame(columns=[
            "symbol",
            "coin_id",
            "amount",
            "avg_buy_price_usd",
            "total_invested_usd",
            "strategy_tag",
        ])

    return positions[[
        "symbol",
        "coin_id",
        "amount",
        "avg_buy_price_usd",
        "allocated_capital_usd",
        "strategy_tag",
    ]].rename(columns={
        "allocated_capital_usd": "total_invested_usd",
    })
