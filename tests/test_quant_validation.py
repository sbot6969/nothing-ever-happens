from __future__ import annotations

from dataclasses import dataclass

import pytest

from bot.backtest.quant_validation import (
    adverse_cost_roi_pct,
    assess_backtest_evidence,
    copied_wins_from_hit_rate,
    wilson_hit_rate_interval,
)


@dataclass(frozen=True)
class Result:
    copied: int
    total_copy_notional_usd: float
    total_pnl_usd: float
    roi_pct: float
    hit_rate_pct: float
    max_drawdown_usd: float


def test_tiny_extreme_roi_is_flagged_as_overfit_or_underpowered() -> None:
    result = Result(copied=5, total_copy_notional_usd=39.92, total_pnl_usd=94.17, roi_pct=235.91, hit_rate_pct=100.0, max_drawdown_usd=0.0)

    assessment = assess_backtest_evidence(result)

    assert assessment.label == "overfit_or_underpowered"
    assert any("sample too small" in reason for reason in assessment.reasons)
    assert any("headline ROI is extreme" in reason for reason in assessment.reasons)


def test_large_positive_sample_is_only_candidate_edge_not_live_claim() -> None:
    result = Result(copied=313, total_copy_notional_usd=7_825.0, total_pnl_usd=169.07, roi_pct=2.16, hit_rate_pct=99.36, max_drawdown_usd=25.02)

    assessment = assess_backtest_evidence(result)

    assert assessment.label == "candidate_edge_needs_oos"
    assert "requires walk-forward/OOS validation" in assessment.reasons[0]


def test_drawdown_can_make_positive_roi_fragile() -> None:
    result = Result(copied=150, total_copy_notional_usd=5_000.0, total_pnl_usd=100.0, roi_pct=2.0, hit_rate_pct=55.0, max_drawdown_usd=250.0)

    assessment = assess_backtest_evidence(result)

    assert assessment.label == "fragile_positive"
    assert assessment.drawdown_to_pnl == pytest.approx(2.5)


def test_negative_roi_is_not_edge() -> None:
    result = Result(copied=200, total_copy_notional_usd=5_000.0, total_pnl_usd=-10.0, roi_pct=-0.2, hit_rate_pct=49.0, max_drawdown_usd=200.0)

    assessment = assess_backtest_evidence(result)

    assert assessment.label == "negative_or_no_edge"
    assert "non-positive net PnL/ROI" in assessment.reasons


def test_wilson_interval_keeps_perfect_tiny_sample_uncertain() -> None:
    interval = wilson_hit_rate_interval(wins=5, total=5)

    assert interval.lower_pct < 60.0
    assert interval.upper_pct == pytest.approx(100.0)


def test_hit_rate_count_and_adverse_cost_sensitivity() -> None:
    assert copied_wins_from_hit_rate(5, 100.0) == 5
    assert copied_wins_from_hit_rate(313, 99.361022) == 311
    assert adverse_cost_roi_pct(2.160593, 75) == pytest.approx(1.410593)
