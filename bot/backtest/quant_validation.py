"""Paper-only quant validation helpers for backtest evidence.

The functions here deliberately avoid live trading, wallet access, network calls,
or secret handling. They provide deterministic labels for research/backtest reports
so headline ROI cannot be mistaken for statistically robust edge.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, Protocol


class BacktestLike(Protocol):
    copied: int
    total_copy_notional_usd: float
    total_pnl_usd: float
    roi_pct: float
    hit_rate_pct: float
    max_drawdown_usd: float


@dataclass(frozen=True)
class EvidenceAssessment:
    label: str
    reasons: tuple[str, ...]
    copied: int
    roi_pct: float
    pnl_usd: float
    drawdown_to_pnl: float | None


@dataclass(frozen=True)
class HitRateInterval:
    lower_pct: float
    upper_pct: float


def wilson_hit_rate_interval(wins: int, total: int, z: float = 1.96) -> HitRateInterval:
    """Return a 95%-style Wilson interval for a binomial hit-rate.

    Wilson is preferred over a naive normal interval for small samples; for
    example 5/5 wins still has a wide lower bound instead of implying certainty.
    """
    if total <= 0:
        return HitRateInterval(0.0, 100.0)
    wins = max(0, min(int(wins), int(total)))
    n = float(total)
    phat = wins / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / denom
    margin = z * sqrt((phat * (1.0 - phat) + z * z / (4.0 * n)) / n) / denom
    return HitRateInterval(round(max(0.0, center - margin) * 100.0, 6), round(min(1.0, center + margin) * 100.0, 6))


def copied_wins_from_hit_rate(copied: int, hit_rate_pct: float) -> int:
    """Convert rounded hit-rate percent back into an approximate win count."""
    if copied <= 0:
        return 0
    return max(0, min(copied, round(copied * hit_rate_pct / 100.0)))


def assess_backtest_evidence(
    result: BacktestLike,
    *,
    min_copied_for_claim: int = 100,
    min_notional_for_claim_usd: float = 1_000.0,
    max_drawdown_to_pnl: float = 1.0,
) -> EvidenceAssessment:
    """Classify whether a backtest result supports a strategy-edge claim.

    Labels:
    - ``overfit_or_underpowered``: too few fills/notional or obvious in-sample tuning risk.
    - ``fragile_positive``: positive but sensitive to costs/drawdown/sampling.
    - ``negative_or_no_edge``: no positive expected value in the run.
    - ``candidate_edge_needs_oos``: enough paper evidence to justify larger out-of-sample testing,
      not enough for live trading.
    """
    copied = int(getattr(result, "copied"))
    notional = float(getattr(result, "total_copy_notional_usd"))
    pnl = float(getattr(result, "total_pnl_usd"))
    roi = float(getattr(result, "roi_pct"))
    max_dd = float(getattr(result, "max_drawdown_usd"))
    reasons: list[str] = []

    if copied < min_copied_for_claim:
        reasons.append(f"sample too small: {copied} copied actions < {min_copied_for_claim}")
    if notional < min_notional_for_claim_usd:
        reasons.append(f"notional too small: ${notional:.2f} < ${min_notional_for_claim_usd:.2f}")
    if roi <= 0 or pnl <= 0:
        reasons.append("non-positive net PnL/ROI")
    drawdown_to_pnl = (max_dd / pnl) if pnl > 0 else None
    if drawdown_to_pnl is not None and drawdown_to_pnl > max_drawdown_to_pnl:
        reasons.append(f"drawdown is large relative to PnL: {drawdown_to_pnl:.2f}x")

    # Very high ROI from tiny sample is a classic data-mining smell, even with a
    # perfect observed hit-rate. Keep it explicit so reports cannot cherry-pick it.
    if copied < 30 and roi > 50:
        reasons.append("headline ROI is extreme on a tiny filtered sample")

    if roi <= 0 or pnl <= 0:
        label = "negative_or_no_edge"
    elif copied < min_copied_for_claim or notional < min_notional_for_claim_usd or (copied < 30 and roi > 50):
        label = "overfit_or_underpowered"
    elif drawdown_to_pnl is not None and drawdown_to_pnl > max_drawdown_to_pnl:
        label = "fragile_positive"
    else:
        label = "candidate_edge_needs_oos"

    if not reasons and label == "candidate_edge_needs_oos":
        reasons.append("positive in-sample evidence with adequate fill/notional count; still requires walk-forward/OOS validation")

    return EvidenceAssessment(
        label=label,
        reasons=tuple(reasons),
        copied=copied,
        roi_pct=roi,
        pnl_usd=pnl,
        drawdown_to_pnl=round(drawdown_to_pnl, 6) if drawdown_to_pnl is not None else None,
    )


def adverse_cost_roi_pct(base_roi_pct: float, extra_cost_bps: float) -> float:
    """Approximate ROI after additional execution/fee/latency cost in bps."""
    return round(float(base_roi_pct) - float(extra_cost_bps) / 100.0, 6)


def summarize_assessments(results: Iterable[BacktestLike]) -> list[EvidenceAssessment]:
    return [assess_backtest_evidence(result) for result in results]
