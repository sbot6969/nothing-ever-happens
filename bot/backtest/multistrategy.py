"""Safe multi-strategy backtest comparison skeletons.

These primitives are deterministic and paper-only. They provide a common result
shape for comparing the four requested strategy families without adding any
runtime order submission, wallet, or live trading paths.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable

from bot.backtest.whale_copy import Resolution, WhaleBacktestConfig, run_backtest
from bot.backtest.quant_validation import assess_backtest_evidence, copied_wins_from_hit_rate, wilson_hit_rate_interval

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
    hit_rate_pct: float = 0.0
    turnover_usd: float = 0.0
    max_exposure_usd: float = 0.0
    rejected_or_skipped: int = 0
    skipped_reasons: dict[str, int] | None = None
    evidence_label: str = "not_assessed"
    evidence_reasons: tuple[str, ...] = ()
    hit_rate_interval_pct: tuple[float, float] = (0.0, 100.0)


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


def _assess_result(result: StrategyBacktestResult) -> StrategyBacktestResult:
    class _Adapter:
        copied = result.copied_or_actions
        total_copy_notional_usd = result.total_notional_usd
        total_pnl_usd = result.total_pnl_usd
        roi_pct = result.roi_pct
        hit_rate_pct = result.hit_rate_pct
        max_drawdown_usd = result.max_drawdown_usd

    assessment = assess_backtest_evidence(_Adapter())
    wins = copied_wins_from_hit_rate(result.copied_or_actions, result.hit_rate_pct)
    interval = wilson_hit_rate_interval(wins, result.copied_or_actions)
    return StrategyBacktestResult(
        **{**asdict(result), "evidence_label": assessment.label, "evidence_reasons": assessment.reasons, "hit_rate_interval_pct": (interval.lower_pct, interval.upper_pct)}
    )


def _skip_counts(reasons: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for reason in reasons:
        counts[str(reason)] = counts.get(str(reason), 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _nothing_happens(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    return _assess_result(StrategyBacktestResult(
        strategy="nothing_happens",
        trades_seen=len(trades),
        copied_or_actions=0,
        total_notional_usd=0.0,
        total_pnl_usd=0.0,
        roi_pct=0.0,
        max_drawdown_usd=0.0,
        notes="Baseline safety strategy: observes markets and takes no positions until wrapped into StrategySignal.",
        rejected_or_skipped=len(trades),
        skipped_reasons={"baseline_not_wrapped_yet": len(trades)},
    ))


def _whale_copy(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    result = run_backtest(trades, resolutions, WhaleBacktestConfig())
    copied_count = len(result.copied)
    return _assess_result(StrategyBacktestResult(
        strategy="whale_copy",
        trades_seen=result.trades_seen,
        copied_or_actions=copied_count,
        total_notional_usd=result.total_copy_notional_usd,
        total_pnl_usd=result.total_pnl_usd,
        roi_pct=result.roi_pct,
        max_drawdown_usd=result.max_drawdown_usd,
        notes="Copies qualified whale BUY signals using paper sizing and conservative execution costs.",
        hit_rate_pct=result.hit_rate_pct,
        turnover_usd=result.total_copy_notional_usd,
        max_exposure_usd=max((copy.copy_notional_usd for copy in result.copied), default=0.0),
        rejected_or_skipped=len(result.rejected),
        skipped_reasons=_skip_counts(row.reason for row in result.rejected),
    ))


def _market_making(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    # Skeleton proxy: quote only reasonably centered binary markets where a
    # spread capture model would be testable with order-book snapshots later.
    actions = [row for row in trades if 0.25 <= _safe_float(row.get("price")) <= 0.75]
    notionals = [min(5.0, _safe_float(row.get("size")) * _safe_float(row.get("price")) * 0.01) for row in actions]
    pnls = [size * _resolved_edge(row, resolutions) for row, size in zip(actions, notionals)]
    notional = round(sum(notionals), 6)
    pnl = round(sum(pnls), 6)
    roi = round((pnl / notional * 100.0), 6) if notional else 0.0
    return _assess_result(StrategyBacktestResult(
        strategy="market_making",
        trades_seen=len(trades),
        copied_or_actions=len(actions),
        total_notional_usd=notional,
        total_pnl_usd=pnl,
        roi_pct=roi,
        max_drawdown_usd=round(abs(min(0.0, pnl)), 6),
        notes="Paper skeleton for inventory/spread-aware quoting; needs historical order books before production claims.",
        hit_rate_pct=round(sum(1 for value in pnls if value > 0) / len(pnls) * 100.0, 6) if pnls else 0.0,
        turnover_usd=notional * 2.0,
        max_exposure_usd=max(notionals, default=0.0),
        rejected_or_skipped=len(trades) - len(actions),
        skipped_reasons=_skip_counts("outside_centered_price_band" for row in trades if row not in actions),
    ))


def _normal_distribution_amm(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> StrategyBacktestResult:
    # Skeleton proxy: allocate small paper notional around mid-probability events,
    # tapering toward tails like a distribution-based allocator.
    actions: list[tuple[dict[str, Any], float]] = []
    skipped: list[str] = []
    for row in trades:
        price = _safe_float(row.get("price"))
        if not 0 < price < 1:
            skipped.append("invalid_price")
            continue
        weight = max(0.0, 1.0 - abs(price - 0.5) / 0.5)
        if weight <= 0:
            skipped.append("tail_price_zero_weight")
            continue
        actions.append((row, round(3.0 * weight, 6)))
    pnls = [size * _resolved_edge(row, resolutions) for row, size in actions]
    notional = round(sum(size for _, size in actions), 6)
    pnl = round(sum(pnls), 6)
    roi = round((pnl / notional * 100.0), 6) if notional else 0.0
    return _assess_result(StrategyBacktestResult(
        strategy="normal_distribution_amm",
        trades_seen=len(trades),
        copied_or_actions=len(actions),
        total_notional_usd=notional,
        total_pnl_usd=pnl,
        roi_pct=roi,
        max_drawdown_usd=round(abs(min(0.0, pnl)), 6),
        notes="Paper allocation skeleton using probability-centered sizing; requires calibrated distributions before live use.",
        hit_rate_pct=round(sum(1 for value in pnls if value > 0) / len(pnls) * 100.0, 6) if pnls else 0.0,
        turnover_usd=notional,
        max_exposure_usd=max((size for _, size in actions), default=0.0),
        rejected_or_skipped=len(skipped),
        skipped_reasons=_skip_counts(skipped),
    ))


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
