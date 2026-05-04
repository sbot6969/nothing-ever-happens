from bot.backtest.probability_model import ProbabilitySignal, calibration_report, confidence_gate, negative_risk_placeholder_safe


def test_probability_confidence_gate_requires_confidence_and_edge() -> None:
    assert confidence_gate(ProbabilitySignal("a", 0.62, 0.8), market_price=0.55)
    assert not confidence_gate(ProbabilitySignal("a", 0.56, 0.8), market_price=0.55)
    assert not confidence_gate(ProbabilitySignal("a", 0.9, 0.2), market_price=0.55)


def test_calibration_report_outputs_brier_logloss_and_counts() -> None:
    report = calibration_report([(0.8, 1), (0.2, 0), (0.6, 0)], min_confidence=0.7)

    assert report.count == 3
    assert report.accepted_count == 2
    assert report.rejected_count == 1
    assert report.brier_score > 0
    assert report.log_loss > 0


def test_negative_risk_placeholder_detection() -> None:
    assert negative_risk_placeholder_safe(["Yes", "Other"])
    assert not negative_risk_placeholder_safe(["Yes", "No"])
