"""Risk calculations based on journal positions and public price history."""

from __future__ import annotations

import math
from collections.abc import Mapping

import pandas as pd


def _positive_number(value: object, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be a positive finite number.") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be a positive finite number.")
    return number


def summarize_exposure(positions: pd.DataFrame) -> dict:
    """Summarize priced FIFO positions; refuse percentages for incomplete prices."""
    required = {"coin_id", "strategy_tag", "market_value_usd"}
    if positions.empty:
        return {
            "total_market_value_usd": 0.0,
            "complete": True,
            "by_asset": pd.DataFrame(),
            "by_strategy": pd.DataFrame(),
        }
    if not required.issubset(positions.columns):
        raise ValueError("Position data is missing required exposure fields.")

    values = pd.to_numeric(positions["market_value_usd"], errors="coerce")
    complete = bool(values.notna().all() and (values >= 0).all())
    if not complete:
        return {
            "total_market_value_usd": None,
            "complete": False,
            "by_asset": pd.DataFrame(),
            "by_strategy": pd.DataFrame(),
        }

    priced = positions.copy()
    priced["market_value_usd"] = values.astype(float)
    total = float(values.sum())

    def breakdown(group: str) -> pd.DataFrame:
        result = (
            priced.groupby(group, dropna=False)["market_value_usd"]
            .sum()
            .reset_index()
            .sort_values("market_value_usd", ascending=False)
        )
        result["allocation_pct"] = (
            result["market_value_usd"] / total * 100 if total > 0 else 0.0
        )
        return result.reset_index(drop=True)

    return {
        "total_market_value_usd": total,
        "complete": True,
        "by_asset": breakdown("coin_id"),
        "by_strategy": breakdown("strategy_tag"),
    }


def calculate_position_size(
    account_equity: float,
    risk_percent: float,
    entry_price: float,
    stop_price: float,
    target_price: float | None = None,
    direction: str | None = None,
) -> dict[str, float | str | None]:
    """Calculate an illustrative position size from a declared stop distance."""
    equity = _positive_number(account_equity, "Account equity")
    entry = _positive_number(entry_price, "Entry price")
    stop = _positive_number(stop_price, "Stop price")
    try:
        risk_pct = float(risk_percent)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Risk percent must be between 0 and 100.") from exc
    if not math.isfinite(risk_pct) or not 0 < risk_pct <= 100:
        raise ValueError("Risk percent must be between 0 and 100.")
    if stop == entry:
        raise ValueError("Stop price must differ from entry price.")

    inferred_direction = "long" if stop < entry else "short"
    if direction is not None and not isinstance(direction, str):
        raise ValueError("Direction must be long or short.")
    direction = inferred_direction if direction is None else direction.lower()
    if direction not in {"long", "short"}:
        raise ValueError("Direction must be long or short.")
    if direction != inferred_direction:
        raise ValueError("Stop price is on the wrong side of entry for this direction.")
    risk_amount = equity * risk_pct / 100
    quantity = risk_amount / abs(entry - stop)
    notional = quantity * entry
    target = None
    reward_to_risk = None
    if target_price is not None:
        target = _positive_number(target_price, "Target price")
        if (direction == "long" and target <= entry) or (
            direction == "short" and target >= entry
        ):
            raise ValueError("Target price must be beyond entry in the trade direction.")
        reward_to_risk = abs(target - entry) / abs(entry - stop)

    return {
        "direction": direction,
        "risk_amount": risk_amount,
        "stop_distance": abs(entry - stop),
        "quantity": quantity,
        "notional": notional,
        "notional_to_equity_pct": notional / equity * 100,
        "target_price": target,
        "reward_to_risk": reward_to_risk,
    }


def analyze_price_history(history: pd.DataFrame) -> dict[str, float | int | None]:
    """Calculate daily historical volatility and peak-to-trough drawdown."""
    if history is None or history.empty or not {"waktu", "price"}.issubset(history):
        return {
            "observations": 0,
            "daily_volatility_pct": None,
            "annualized_volatility_pct": None,
            "max_drawdown_pct": None,
            "annualized_sharpe_zero_risk_free": None,
        }
    data = history[["waktu", "price"]].copy()
    data["waktu"] = pd.to_datetime(data["waktu"], utc=True, errors="coerce")
    data["price"] = pd.to_numeric(data["price"], errors="coerce")
    data = data.dropna().loc[lambda frame: frame["price"] > 0]
    if data.empty:
        return {
            "observations": 0,
            "daily_volatility_pct": None,
            "annualized_volatility_pct": None,
            "max_drawdown_pct": None,
            "annualized_sharpe_zero_risk_free": None,
        }
    daily = (
        data.drop_duplicates("waktu")
        .set_index("waktu")["price"]
        .resample("1D")
        .last()
        .dropna()
    )
    returns = daily.pct_change().dropna()
    daily_vol = float(returns.std(ddof=1) * 100) if len(returns) >= 2 else None
    return_std = float(returns.std(ddof=1)) if len(returns) >= 2 else None
    sharpe = (
        float(returns.mean() / return_std * math.sqrt(365))
        if return_std and math.isfinite(return_std) and return_std > 0
        else None
    )
    running_peak = daily.cummax()
    drawdown = (daily / running_peak - 1) * 100
    return {
        "observations": int(len(daily)),
        "daily_volatility_pct": daily_vol,
        "annualized_volatility_pct": (
            daily_vol * math.sqrt(365) if daily_vol is not None else None
        ),
        "max_drawdown_pct": float(drawdown.min()) if len(daily) >= 2 else None,
        "annualized_sharpe_zero_risk_free": sharpe,
    }


def calculate_return_correlation(
    histories: Mapping[str, pd.DataFrame],
    minimum_observations: int = 5,
) -> pd.DataFrame:
    """Correlate aligned daily close-to-close returns with pairwise data sufficiency."""
    if minimum_observations < 2:
        raise ValueError("At least two aligned return observations are required.")
    closes = {}
    for asset_id, history in histories.items():
        if history is None or history.empty or not {"waktu", "price"}.issubset(history):
            continue
        data = history[["waktu", "price"]].copy()
        data["waktu"] = pd.to_datetime(data["waktu"], utc=True, errors="coerce")
        data["price"] = pd.to_numeric(data["price"], errors="coerce")
        data = data.dropna().loc[lambda frame: frame["price"] > 0]
        if not data.empty:
            closes[str(asset_id)] = (
                data.drop_duplicates("waktu")
                .set_index("waktu")["price"]
                .resample("1D")
                .last()
            )
    if len(closes) < 2:
        return pd.DataFrame()
    returns = pd.DataFrame(closes).pct_change().replace(
        [float("inf"), float("-inf")], pd.NA
    )
    corr = returns.corr(min_periods=minimum_observations)
    counts = returns.notna().astype(int).T.dot(returns.notna().astype(int))
    result = corr.where(counts >= minimum_observations)
    return result
