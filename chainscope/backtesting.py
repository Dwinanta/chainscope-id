"""Hedge fund backtesting lab for historical strategy simulation, risk-adjusted returns, and benchmark comparison."""

import math
import numpy as np
import pandas as pd


def run_backtest(
    history_df: pd.DataFrame,
    strategy: str = "sma_cross",
    initial_capital: float = 10000.0,
    fee_pct: float = 0.1,  # 0.1% fee per trade
    sma_fast: int = 10,
    sma_slow: int = 30,
    rsi_period: int = 14,
    rsi_oversold: float = 30.0,
    rsi_overbought: float = 70.0,
) -> dict:
    """Run an event-driven backtest simulation avoiding lookahead bias.
    
    Generates signals strictly on bar close and executes at next open/close.
    """
    if history_df.empty or "price" not in history_df.columns:
        raise ValueError("Data riwayat harga tidak boleh kosong.")
    if len(history_df) < max(sma_slow, 35):
        raise ValueError(f"Dibutuhkan minimal {max(sma_slow, 35)} data poin untuk menjalankan simulasi.")

    df = history_df.copy().reset_index(drop=True)
    prices = df["price"].astype(float)
    
    # 1. Generate Signals
    signals = pd.Series(0, index=df.index)  # 1 = Long, 0 = Cash
    
    if strategy == "sma_cross":
        fast_ma = prices.rolling(window=sma_fast).mean()
        slow_ma = prices.rolling(window=sma_slow).mean()
        # Long when fast MA > slow MA
        signals = (fast_ma > slow_ma).astype(int)
    elif strategy == "rsi_mean_reversion":
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=rsi_period).mean()
        avg_loss = loss.rolling(window=rsi_period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        pos = 0
        sig_list = []
        for val in rsi:
            if val < rsi_oversold:
                pos = 1  # Buy oversold
            elif val > rsi_overbought:
                pos = 0  # Exit overbought
            sig_list.append(pos)
        signals = pd.Series(sig_list, index=df.index)
    elif strategy == "momentum_breakout":
        highest = prices.rolling(window=20).max()
        lowest = prices.rolling(window=20).min()
        pos = 0
        sig_list = []
        for i, p in enumerate(prices):
            if i > 20 and p >= highest.iloc[i-1]:
                pos = 1
            elif i > 20 and p <= lowest.iloc[i-1]:
                pos = 0
            sig_list.append(pos)
        signals = pd.Series(sig_list, index=df.index)
    else:  # Buy and Hold
        signals = pd.Series(1, index=df.index)

    # Shift signals by 1 to prevent lookahead bias (trade on next bar)
    trade_signals = signals.shift(1).fillna(0)

    # 2. Portfolio Simulation
    cash = initial_capital
    holdings = 0.0
    equity_curve = []
    trades = []
    entry_price = 0.0
    
    fee_mult = fee_pct / 100.0

    for i in range(len(df)):
        price = prices.iloc[i]
        target_sig = trade_signals.iloc[i]
        
        # Check for trade execution
        if target_sig == 1 and holdings == 0.0:
            # Buy
            cost_basis = cash * (1.0 - fee_mult)
            holdings = cost_basis / price
            cash = 0.0
            entry_price = price
            trades.append({"type": "BUY", "bar": i, "price": price})
        elif target_sig == 0 and holdings > 0.0:
            # Sell
            proceeds = holdings * price * (1.0 - fee_mult)
            cash = proceeds
            pnl = (price - entry_price) / entry_price * 100.0 if entry_price > 0 else 0.0
            holdings = 0.0
            trades.append({"type": "SELL", "bar": i, "price": price, "pnl_pct": pnl})
            
        total_equity = cash + (holdings * price)
        equity_curve.append(total_equity)

    df["strategy_equity"] = equity_curve
    # Benchmark: Buy & Hold
    first_price = prices.iloc[0]
    df["benchmark_equity"] = (prices / first_price) * initial_capital

    # 3. Performance Metrics
    final_equity = equity_curve[-1]
    total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100.0
    
    benchmark_final = df["benchmark_equity"].iloc[-1]
    benchmark_return_pct = ((benchmark_final - initial_capital) / initial_capital) * 100.0

    # Drawdown calculation
    equity_series = pd.Series(equity_curve)
    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_drawdown_pct = abs(float(drawdown.min())) * 100.0

    bench_series = df["benchmark_equity"]
    bench_max = bench_series.cummax()
    bench_dd = (bench_series - bench_max) / bench_max
    bench_max_dd_pct = abs(float(bench_dd.min())) * 100.0

    # Sharpe & Sortino (assuming daily bars)
    daily_returns = equity_series.pct_change().dropna()
    std_dev = daily_returns.std()
    downside_std = daily_returns[daily_returns < 0].std()
    
    mean_ret = daily_returns.mean()
    sharpe_ratio = float((mean_ret / std_dev) * math.sqrt(252)) if std_dev and std_dev > 0 else 0.0
    sortino_ratio = float((mean_ret / downside_std) * math.sqrt(252)) if downside_std and downside_std > 0 else 0.0

    # Trade stats
    completed_trades = [t for t in trades if t["type"] == "SELL"]
    winning_trades = [t for t in completed_trades if t.get("pnl_pct", 0) > 0]
    win_rate_pct = (len(winning_trades) / len(completed_trades) * 100.0) if completed_trades else 0.0

    gross_profit = sum(t.get("pnl_pct", 0) for t in winning_trades)
    gross_loss = abs(sum(t.get("pnl_pct", 0) for t in completed_trades if t.get("pnl_pct", 0) < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 1.0)

    return {
        "strategy": strategy,
        "initial_capital": initial_capital,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round(total_return_pct, 2),
        "benchmark_return_pct": round(benchmark_return_pct, 2),
        "alpha_pct": round(total_return_pct - benchmark_return_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "benchmark_max_drawdown_pct": round(bench_max_dd_pct, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sortino_ratio": round(sortino_ratio, 2),
        "total_trades": len(completed_trades),
        "win_rate_pct": round(win_rate_pct, 1),
        "profit_factor": round(profit_factor, 2),
        "equity_curve": df[["price", "strategy_equity", "benchmark_equity"]],
        "drawdown_curve": drawdown * 100.0,
    }
