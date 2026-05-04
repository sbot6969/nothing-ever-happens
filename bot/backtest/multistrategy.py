"""Safe multi-strategy backtest comparison skeletons.

These primitives are deterministic and paper-only. They provide a common result
shape for comparing the four requested strategy families without adding any
runtime order submission, wallet, or live trading paths.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable

from bot.backtest.whale_copy import Resolution, WhaleBacktestConfig, run_backtest

STRATEGY_FAMILIES = (
    "nothing_happens",
    "whale_copy",
    "market_making",
    "normal_distribution_amm",
)


@dataclass(frozen=True)
class StrategyBacktestResult:
    strategy: str
    trades_seen: int
    copied_or_actions: int
    total_notional_usd: float
    total_pnl_usd: float
    roi_pct: float
    max_drawdown_usd: float
    notes: str


def _safe_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed >= 0 else 0.0


def _resolved_edge(row: dict[str, Any], resolutions: dict[str, Resolution]) -> float:
    price = _safe_float(row.get("price"))
    if not 0 < price < 1:
        return 0.0
    resolution = resolutions.get(str(row.get("asset") or ""))
    if resolution is None:
        return 0.0
    return float(resolution.payout) - price


def _nothing_happens(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    return StrategyBacktestResult(
        strategy="nothing_happens",
        trades_seen=len(trades),
        copied_or_actions=0,
        total_notional_usd=0.0,
        total_pnl_usd=0.0,
        roi_pct=0.0,
        max_drawdown_usd=0.0,
        notes="Baseline safety strategy: observes markets and takes no positions.",
    )


def _whale_copy(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    result = run_backtest(trades, resolutions, WhaleBacktestConfig())
    return StrategyBacktestResult(
        strategy="whale_copy",
        trades_seen=result.trades_seen,
        copied_or_actions=len(result.copied),
        total_notional_usd=result.total_copy_notional_usd,
        total_pnl_usd=result.total_pnl_usd,
        roi_pct=result.roi_pct,
        max_drawdown_usd=result.max_drawdown_usd,
        notes="Copies qualified whale BUY signals using paper sizing and conservative execution costs.",
    )


def _market_making(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    # Skeleton proxy: quote only reasonably centered binary markets where a
    # spread capture model would be testable with order-book snapshots later.
    actions = [row for row in trades if 0.25 <= _safe_float(row.get("price")) <= 0.75]
    notional = round(sum(min(5.0, _safe_float(row.get("size")) * _safe_float(row.get("price")) * 0.01) for row in actions), 6)
    pnl = round(sum(min(5.0, _safe_float(row.get("size")) * _safe_float(row.get("price")) * 0.01) * _resolved_edge(row, resolutions) for row in actions), 6)
    roi = round((pnl / notional * 100.0), 6) if notional else 0.0
    return StrategyBacktestResult(
        strategy="market_making",
        trades_seen=len(trades),
        copied_or_actions=len(actions),
        total_notional_usd=notional,
        total_pnl_usd=pnl,
        roi_pct=roi,
        max_drawdown_usd=round(abs(min(0.0, pnl)), 6),
        notes="Paper skeleton for inventory/spread-aware quoting; needs historical order books before production claims.",
    )


def _normal_distribution_amm(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    # Skeleton proxy: allocate small paper notional around mid-probability events,
    # tapering toward tails like a distribution-based allocator.
    actions: list[tuple[dict[str, Any], float]] = []
    for row in trades:
        price = _safe_float(row.get("price"))
        if not 0 < price < 1:
            continue
        weight = max(0.0, 1.0 - abs(price - 0.5) / 0.5)
        if weight <= 0:
            continue
        actions.append((row, round(3.0 * weight, 6)))
    notional = round(sum(size for _, size in actions), 6)
    pnl = round(sum(size * _resolved_edge(row, resolutions) for row, size in actions), 6)
    roi = round((pnl / notional * 100.0), 6) if notional else 0.0
    return StrategyBacktestResult(
        strategy="normal_distribution_amm",
        trades_seen=len(trades),
        copied_or_actions=len(actions),
        total_notional_usd=notional,
        total_pnl_usd=pnl,
        roi_pct=roi,
        max_drawdown_usd=round(abs(min(0.0, pnl)), 6),
        notes="Paper allocation skeleton using probability-centered sizing; requires calibrated distributions before live use.",
    )


RUNNERS: dict[str, Callable[[list[dict[str, Any]], dict[str, Resolution]], StrategyBacktestResult]] = {
    "nothing_happens": _nothing_happens,
    "whale_copy": _whale_copy,
    "market_making": _market_making,
    "normal_distribution_amm": _normal_distribution_amm,
}


def compare_strategies(
    trade_rows: Iterable[dict[str, Any]],
    resolutions: dict[str, Resolution],
    strategies: Iterable[str] = STRATEGY_FAMILIES,
) -> list[StrategyBacktestResult]:
    trades = list(trade_rows)
    results: list[StrategyBacktestResult] = []
    for strategy in strategies:
        if strategy not in RUNNERS:
            raise ValueError(f"unknown strategy family: {strategy}")
        results.append(RUNNERS[strategy](trades, resolutions))
    return results


def comparison_to_dict(results: Iterable[StrategyBacktestResult]) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]
