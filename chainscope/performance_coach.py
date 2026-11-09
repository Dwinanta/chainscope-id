"""Journal-based performance and strategy portfolio analytics."""

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
import math
import re

import pandas as pd


_OUTCOME_COLUMNS = [
    "trade_time",
    "strategy_tag",
    "coin_id",
    "symbol",
    "realized_pnl_usd",
    "closed_amount",
    "session",
]
_POSITION_COLUMNS = [
    "coin_id",
    "symbol",
    "strategy_tag",
    "amount",
    "avg_buy_price_usd",
    "allocated_capital_usd",
    "current_price_usd",
    "market_value_usd",
    "unrealized_pnl_usd",
]


def _session_for_hour(hour: int) -> str:
    if hour < 7:
        return "Asia (UTC)"
    if hour < 13:
        return "Europe (UTC)"
    if hour < 21:
        return "US (UTC)"
    return "Off-hours (UTC)"


def _group_outcomes(
    outcomes: pd.DataFrame,
    positions: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    keys = set(outcomes[group_column].dropna()) if not outcomes.empty else set()
    if not positions.empty:
        keys.update(positions[group_column].dropna())

    rows = []
    for key in sorted(keys):
        closed = (
            outcomes[outcomes[group_column] == key]
            if not outcomes.empty
            else pd.DataFrame(columns=_OUTCOME_COLUMNS)
        )
        open_positions = (
            positions[positions[group_column] == key]
            if not positions.empty
            else pd.DataFrame(columns=_POSITION_COLUMNS)
        )
        wins = int((closed["realized_pnl_usd"] > 0).sum())
        values = pd.to_numeric(
            open_positions["market_value_usd"], errors="coerce"
        )
        prices_complete = values.notna().all()
        current_value = float(values.sum()) if prices_complete else None
        unrealized = pd.to_numeric(
            open_positions["unrealized_pnl_usd"], errors="coerce"
        )
        rows.append({
            group_column: key,
            "closed_trades": len(closed),
            "wins": wins,
            "win_rate_pct": wins / len(closed) * 100 if len(closed) else None,
            "realized_pnl_usd": float(closed["realized_pnl_usd"].sum()),
            "allocated_capital_usd": float(
                open_positions["allocated_capital_usd"].sum()
            ),
            "current_value_usd": current_value,
            "unrealized_pnl_usd": (
                float(unrealized.sum()) if unrealized.notna().all() else None
            ),
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        total_value = result["current_value_usd"].sum(min_count=1)
        complete_values = result["current_value_usd"].notna().all()
        result["allocation_pct"] = (
            result["current_value_usd"] / total_value * 100
            if complete_values and pd.notna(total_value) and total_value > 0
            else None
        )
        result = result.sort_values(
            "realized_pnl_usd", ascending=False, kind="stable"
        ).reset_index(drop=True)
    return result


def analyze_trades(
    trades: Iterable[Mapping],
    current_prices_usd: Mapping[str, float] | None = None,
) -> dict:
    """Analyze user journal records with FIFO matching per asset and strategy.

    A sell is matched only against buys of the same asset and strategy. Unmatched
    sells are reported rather than silently treated as short positions.
    """
    prices = current_prices_usd or {}
    records = []
    symbols_by_id = {}
    invalid_count = 0
    date_only_count = 0
    precise_time_pattern = re.compile(r"(?:T| )\d{2}:\d{2}")

    for index, trade in enumerate(trades):
        try:
            side = str(trade.get("side", "")).strip().lower()
            amount = float(trade.get("amount"))
            price = float(trade.get("price_usd"))
            coin_id = str(trade.get("coin_id", "")).strip().lower()
            timestamp_text = str(trade.get("trade_time", "")).strip()
            timestamp = pd.to_datetime(timestamp_text, utc=True, errors="coerce")
            if (
                side not in {"buy", "sell"}
                or not coin_id
                or not math.isfinite(amount)
                or not math.isfinite(price)
                or amount <= 0
                or price <= 0
                or pd.isna(timestamp)
            ):
                invalid_count += 1
                continue
        except (AttributeError, TypeError, ValueError, OverflowError):
            invalid_count += 1
            continue

        has_time = bool(precise_time_pattern.search(timestamp_text))
        has_timezone = (
            timestamp_text.upper().endswith("Z")
            or bool(re.search(r"[+-]\d{2}:?\d{2}$", timestamp_text))
        )
        date_only_count += not has_time
        strategy = str(trade.get("strategy_tag") or "").strip() or "Unassigned"
        symbol = str(trade.get("symbol") or coin_id).strip().upper()
        records.append({
            "index": index,
            "trade_time": timestamp,
            "has_time": has_time,
            "has_timezone": has_timezone,
            "side": side,
            "amount": amount,
            "price_usd": price,
            "coin_id": coin_id,
            "symbol": symbol,
            "strategy_tag": strategy,
        })
        symbols_by_id[coin_id] = symbol

    records.sort(key=lambda row: (row["trade_time"], row["index"]))
    timestamp_groups = defaultdict(list)
    for row in records:
        timestamp_groups[
            (row["coin_id"], row["strategy_tag"], row["trade_time"])
        ].append(row)
    ambiguous_rows = [
        row
        for rows in timestamp_groups.values()
        if len(rows) > 1
        for row in rows
    ]
    ambiguous_indices = {row["index"] for row in ambiguous_rows}
    records = [row for row in records if row["index"] not in ambiguous_indices]
    ordered_size_analysis_available = (
        bool(records)
        and all(row["has_time"] for row in records)
        and len({row["trade_time"] for row in records}) == len(records)
    )
    lots_by_key = defaultdict(deque)
    realized_rows = []
    post_loss_size_checks = []
    last_buy_notional = None
    pending_loss_baseline = None
    unmatched_sells_amount = 0.0

    for trade in records:
        key = (trade["coin_id"], trade["strategy_tag"])
        if trade["side"] == "buy":
            notional = trade["amount"] * trade["price_usd"]
            if ordered_size_analysis_available and pending_loss_baseline is not None:
                post_loss_size_checks.append({
                    "increased": notional > pending_loss_baseline,
                    "previous_buy_notional_usd": pending_loss_baseline,
                    "next_buy_notional_usd": notional,
                })
                pending_loss_baseline = None
            if ordered_size_analysis_available:
                last_buy_notional = notional
            lots_by_key[key].append({
                "amount": trade["amount"],
                "price_usd": trade["price_usd"],
            })
            continue

        remaining = trade["amount"]
        realized_pnl = 0.0
        matched_amount = 0.0
        lots = lots_by_key[key]
        while remaining > 1e-12 and lots:
            lot = lots[0]
            closed_amount = min(remaining, lot["amount"])
            realized_pnl += (
                trade["price_usd"] - lot["price_usd"]
            ) * closed_amount
            matched_amount += closed_amount
            remaining -= closed_amount
            lot["amount"] -= closed_amount
            if lot["amount"] <= 1e-12:
                lots.popleft()

        unmatched_sells_amount += remaining
        if matched_amount > 0:
            session = (
                _session_for_hour(trade["trade_time"].hour)
                if trade["has_time"] and trade["has_timezone"]
                else None
            )
            realized_rows.append({
                "trade_time": trade["trade_time"],
                "strategy_tag": trade["strategy_tag"],
                "coin_id": trade["coin_id"],
                "symbol": trade["symbol"],
                "realized_pnl_usd": realized_pnl,
                "closed_amount": matched_amount,
                "session": session,
            })
            if realized_pnl < 0 and ordered_size_analysis_available:
                pending_loss_baseline = last_buy_notional

    outcome_df = pd.DataFrame(realized_rows, columns=_OUTCOME_COLUMNS)
    position_rows = []
    for (coin_id, strategy), lots in lots_by_key.items():
        amount = sum(lot["amount"] for lot in lots)
        capital = sum(lot["amount"] * lot["price_usd"] for lot in lots)
        if amount <= 1e-12:
            continue
        current_price = prices.get(coin_id)
        try:
            current_price = float(current_price)
        except (TypeError, ValueError):
            current_price = None
        if current_price is not None and (
            not math.isfinite(current_price) or current_price < 0
        ):
            current_price = None
        market_value = amount * current_price if current_price is not None else None
        position_rows.append({
            "coin_id": coin_id,
            "symbol": symbols_by_id.get(coin_id, coin_id.upper()),
            "strategy_tag": strategy,
            "amount": amount,
            "avg_buy_price_usd": capital / amount,
            "allocated_capital_usd": capital,
            "current_price_usd": current_price,
            "market_value_usd": market_value,
            "unrealized_pnl_usd": (
                market_value - capital if market_value is not None else None
            ),
        })
    position_df = pd.DataFrame(position_rows, columns=_POSITION_COLUMNS)

    closed_pnls = (
        outcome_df["realized_pnl_usd"].tolist() if not outcome_df.empty else []
    )
    wins = [value for value in closed_pnls if value > 0]
    losses = [value for value in closed_pnls if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    equity_curve = 0.0
    peak = 0.0
    max_drawdown = 0.0
    time_bucket_pnls = (
        outcome_df.groupby("trade_time")["realized_pnl_usd"]
        .sum()
        .sort_index()
        .tolist()
        if not outcome_df.empty
        else []
    )
    for pnl in time_bucket_pnls:
        equity_curve += pnl
        peak = max(peak, equity_curve)
        max_drawdown = max(max_drawdown, peak - equity_curve)

    current_streak = 0
    current_streak_type = None
    best_win_streak = 0
    best_loss_streak = 0
    streak_analysis_available = (
        not outcome_df.empty and outcome_df["trade_time"].is_unique
    )
    if streak_analysis_available:
        for pnl in closed_pnls:
            result = "win" if pnl > 0 else "loss" if pnl < 0 else None
            if result is None:
                current_streak = 0
                current_streak_type = None
            elif result == current_streak_type:
                current_streak += 1
            else:
                current_streak = 1
                current_streak_type = result
            if result == "win":
                best_win_streak = max(best_win_streak, current_streak)
            elif result == "loss":
                best_loss_streak = max(best_loss_streak, current_streak)

    strategy_stats = _group_outcomes(
        outcome_df, position_df, "strategy_tag"
    )
    asset_stats = _group_outcomes(outcome_df, position_df, "coin_id")
    market_data_complete = bool(
        not position_df.empty
        and position_df["market_value_usd"].notna().all()
    )
    total_market_value = (
        float(position_df["market_value_usd"].sum())
        if market_data_complete
        else None
    )
    total_allocated_capital = (
        float(position_df["allocated_capital_usd"].sum())
        if not position_df.empty
        else 0.0
    )
    total_unrealized = (
        float(position_df["unrealized_pnl_usd"].sum())
        if market_data_complete
        else None
    )
    sessions = pd.DataFrame()
    precise_outcomes = (
        outcome_df[outcome_df["session"].notna()]
        if not outcome_df.empty
        else outcome_df
    )
    if not precise_outcomes.empty:
        sessions = (
            precise_outcomes.groupby("session", as_index=False)
            .agg(
                closed_trades=("realized_pnl_usd", "size"),
                realized_pnl_usd=("realized_pnl_usd", "sum"),
                wins=("realized_pnl_usd", lambda values: int((values > 0).sum())),
            )
        )
        sessions["win_rate_pct"] = (
            sessions["wins"] / sessions["closed_trades"] * 100
        )

    frequency_per_week = None
    if len(records) > 1:
        span_days = (
            records[-1]["trade_time"] - records[0]["trade_time"]
        ).total_seconds() / 86400
        if span_days > 0:
            frequency_per_week = len(records) / span_days * 7

    trend = None
    if len(time_bucket_pnls) >= 4:
        midpoint = len(time_bucket_pnls) // 2
        earlier = sum(time_bucket_pnls[:midpoint])
        recent = sum(time_bucket_pnls[midpoint:])
        trend = {
            "earlier_realized_pnl_usd": earlier,
            "recent_realized_pnl_usd": recent,
            "direction": (
                "improving" if recent > earlier
                else "deteriorating" if recent < earlier
                else "unchanged"
            ),
        }

    insights = []
    closed_strategy_stats = (
        strategy_stats[strategy_stats["closed_trades"] > 0]
        if not strategy_stats.empty
        else strategy_stats
    )
    if not closed_strategy_stats.empty:
        best = closed_strategy_stats.iloc[0]
        insights.append(
            f"Strategi dengan realized P/L tertinggi: {best['strategy_tag']} "
            f"(${best['realized_pnl_usd']:,.2f}; {int(best['closed_trades'])} "
            "penutupan tercatat)."
        )
    loss_assets = (
        asset_stats[asset_stats["realized_pnl_usd"] < 0]
        if not asset_stats.empty
        else asset_stats
    )
    if not loss_assets.empty:
        worst = loss_assets.sort_values("realized_pnl_usd").iloc[0]
        insights.append(
            f"Aset dengan realized loss terbesar: {worst['coin_id']} "
            f"(${worst['realized_pnl_usd']:,.2f})."
        )
    if not sessions.empty:
        best_session = sessions.sort_values("realized_pnl_usd").iloc[-1]
        insights.append(
            f"Bucket UTC dengan realized P/L tertinggi: {best_session['session']} "
            f"(${best_session['realized_pnl_usd']:,.2f})."
        )
    if post_loss_size_checks:
        increases = sum(check["increased"] for check in post_loss_size_checks)
        insights.append(
            f"Notional pembelian berikutnya lebih besar setelah {increases} dari "
            f"{len(post_loss_size_checks)} kerugian tercatat; ini hanya proxy "
            "ukuran transaksi, bukan ukuran risiko."
        )
    if trend:
        insights.append(
            "Realized P/L pada paruh data yang lebih baru "
            f"{trend['direction']} dibanding paruh sebelumnya; ini perbandingan "
            "historis sederhana, bukan prediksi."
        )

    return {
        "total_trades": len(records),
        "invalid_trades": invalid_count,
        "date_only_trades": date_only_count,
        "ambiguous_trades": len(ambiguous_rows),
        "closed_trades": len(closed_pnls),
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(closed_pnls) - len(wins) - len(losses),
        "win_rate_pct": len(wins) / len(closed_pnls) * 100 if closed_pnls else None,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else None,
        "gross_profit_usd": gross_profit,
        "gross_loss_usd": gross_loss,
        "average_win_usd": sum(wins) / len(wins) if wins else None,
        "average_loss_usd": sum(losses) / len(losses) if losses else None,
        "average_win_loss_ratio": (
            sum(wins) / len(wins) / abs(sum(losses) / len(losses))
            if wins and losses
            else None
        ),
        "max_drawdown_usd": max_drawdown,
        "best_win_streak": best_win_streak,
        "best_loss_streak": best_loss_streak,
        "streak_analysis_available": streak_analysis_available,
        "trades_per_week": frequency_per_week,
        "unmatched_sells_amount": unmatched_sells_amount,
        "allocated_capital_usd": total_allocated_capital,
        "current_value_usd": total_market_value,
        "unrealized_pnl_usd": total_unrealized,
        "market_data_complete": market_data_complete,
        "strategy_stats": strategy_stats,
        "asset_stats": asset_stats,
        "positions": position_df,
        "outcomes": outcome_df,
        "sessions": sessions,
        "post_loss_size_checks": post_loss_size_checks,
        "post_loss_size_analysis_available": ordered_size_analysis_available,
        "trend": trend,
        "insights": insights,
        "risk_assessment_available": False,
        "timeframe_analysis_available": False,
        "session_analysis_available": not sessions.empty,
    }
