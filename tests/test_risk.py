import pandas as pd
import pytest

from chainscope import risk


def test_exposure_summary_computes_asset_and_strategy_percentages():
    positions = pd.DataFrame([
        {
            "coin_id": "bitcoin",
            "strategy_tag": "Swing",
            "market_value_usd": 75.0,
        },
        {
            "coin_id": "bitcoin",
            "strategy_tag": "Long-term",
            "market_value_usd": 25.0,
        },
    ])

    exposure = risk.summarize_exposure(positions)

    assert exposure["total_market_value_usd"] == 100
    assert exposure["by_asset"].iloc[0]["allocation_pct"] == 100
    assert exposure["by_strategy"]["allocation_pct"].tolist() == [75, 25]


def test_exposure_summary_withholds_percentages_for_unpriced_positions():
    exposure = risk.summarize_exposure(pd.DataFrame([{
        "coin_id": "bitcoin",
        "strategy_tag": "Swing",
        "market_value_usd": None,
    }]))

    assert not exposure["complete"]
    assert exposure["total_market_value_usd"] is None
    assert exposure["by_asset"].empty


def test_position_sizing_and_reward_to_risk_for_long_and_short():
    long = risk.calculate_position_size(10000, 1, 100, 95, 110, "long")
    short = risk.calculate_position_size(10000, 2, 100, 105, 90, "short")

    assert long["risk_amount"] == 100
    assert long["quantity"] == 20
    assert long["notional"] == 2000
    assert long["notional_to_equity_pct"] == 20
    assert long["reward_to_risk"] == 2
    assert short["direction"] == "short"
    assert short["reward_to_risk"] == 2


@pytest.mark.parametrize(
    "values",
    [
        (0, 1, 100, 90, None, "long"),
        (1000, 101, 100, 90, None, "long"),
        (1000, 1, 100, 100, None, "long"),
        (1000, 1, 100, 90, 95, "long"),
        (1000, 1, 100, 90, None, "short"),
    ],
)
def test_position_sizing_rejects_invalid_scenarios(values):
    with pytest.raises(ValueError):
        risk.calculate_position_size(*values)


def test_price_history_reports_daily_volatility_and_drawdown():
    history = pd.DataFrame({
        "waktu": pd.date_range("2026-01-01", periods=6, freq="D"),
        "price": [100, 110, 90, 100, 80, 90],
    })

    metrics = risk.analyze_price_history(history)

    assert metrics["observations"] == 6
    assert metrics["daily_volatility_pct"] == pytest.approx(
        pd.Series([0.1, -2 / 11, 1 / 9, -0.2, 0.125]).std(ddof=1) * 100
    )
    assert metrics["max_drawdown_pct"] == pytest.approx(-30 / 110 * 100)
    assert metrics["annualized_sharpe_zero_risk_free"] is not None


def test_return_correlation_uses_aligned_daily_returns():
    dates = pd.date_range("2026-01-01", periods=8, freq="D")
    histories = {
        "a": pd.DataFrame({"waktu": dates, "price": [100, 102, 101, 105, 106, 104, 108, 110]}),
        "b": pd.DataFrame({"waktu": dates, "price": [50, 51, 50.5, 52.5, 53, 52, 54, 55]}),
    }

    correlation = risk.calculate_return_correlation(histories)

    assert correlation.loc["a", "b"] == pytest.approx(1.0)
    assert risk.calculate_return_correlation({"a": histories["a"]}).empty
