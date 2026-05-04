"""Calibrated probability-model helpers for paper AMM/allocation research."""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from typing import Iterable


@dataclass(frozen=True)
class ProbabilitySignal:
    asset: str
    p_model: float
    confidence: float
    source: str = "market_snapshot_proxy"


@dataclass(frozen=True)
class CalibrationReport:
    count: int
    brier_score: float
    log_loss: float
    accepted_count: int
    rejected_count: int


def clamp_probability(value: float) -> float:
    return max(0.001, min(0.999, float(value)))


def confidence_gate(signal: ProbabilitySignal, *, min_confidence: float = 0.55, min_edge: float = 0.03, market_price: float | None = None) -> bool:
    if signal.confidence < min_confidence:
        return False
    if market_price is None:
        return True
    return abs(clamp_probability(signal.p_model) - clamp_probability(market_price)) >= min_edge


def calibration_report(rows: Iterable[tuple[float, float]], *, min_confidence: float = 0.0) -> CalibrationReport:
    total = 0
    brier = 0.0
    ll = 0.0
    accepted = 0
    rejected = 0
    for p_raw, outcome_raw in rows:
        total += 1
        p = clamp_probability(p_raw)
        outcome = 1.0 if float(outcome_raw) >= 0.5 else 0.0
        brier += (p - outcome) ** 2
        ll += -(outcome * log(p) + (1 - outcome) * log(1 - p))
        if max(p, 1 - p) >= min_confidence:
            accepted += 1
        else:
            rejected += 1
    if total == 0:
        return CalibrationReport(0, 0.0, 0.0, 0, 0)
    return CalibrationReport(total, round(brier / total, 6), round(ll / total, 6), accepted, rejected)


def negative_risk_placeholder_safe(outcomes: Iterable[str]) -> bool:
    labels = {str(x).strip().lower() for x in outcomes}
    return bool(labels) and ("other" in labels or "none of the above" in labels or "another" in labels)
