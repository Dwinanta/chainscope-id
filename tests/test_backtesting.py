import pandas as pd
import pytest
from chainscope import backtesting


def test_run_backtest_sma_cross():
    prices = [100.0 + i * (1.0 if i % 2 == 0 else -0.5) for i in range(50)]
    df = pd.DataFrame({"price": prices})
    
    result = backtesting.run_backtest(df, strategy="sma_cross", initial_capital=10000.0, sma_fast=5, sma_slow=15)
    assert "final_equity" in result
    assert "total_return_pct" in result
    assert "benchmark_return_pct" in result
    assert "max_drawdown_pct" in result
    assert "sharpe_ratio" in result
    assert "equity_curve" in result


def test_run_backtest_rejects_insufficient_data():
    df = pd.DataFrame({"price": [100.0, 101.0]})
    with pytest.raises(ValueError, match="Dibutuhkan minimal"):
        backtesting.run_backtest(df, strategy="sma_cross", sma_slow=30)
