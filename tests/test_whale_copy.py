from __future__ import annotations

import asyncio
import os

from bot import whale_copy


def test_trade_key_prefers_transaction_hash():
    assert whale_copy._trade_key({"transactionHash": "0xabc", "name": "fallback"}) == "0xabc"


def test_notional_uses_size_times_price():
    assert whale_copy._notional({"size": "10", "price": "0.42"}) == 4.2


def test_live_enabled_defaults_false(monkeypatch):
    monkeypatch.delenv("WHALE_COPY_LIVE_ENABLED", raising=False)
    assert whale_copy.live_enabled() is False


def test_live_enabled_accepts_true(monkeypatch):
    monkeypatch.setenv("WHALE_COPY_LIVE_ENABLED", "true")
    assert whale_copy.live_enabled() is True


def test_confidence_bounds(monkeypatch):
    monkeypatch.setenv("WHALE_MIN_NOTIONAL_USD", "100")
    c = whale_copy._confidence({"side": "BUY", "size": "1000", "price": "1"}, history_count=1)
    assert 0 < c <= 0.99


def test_snapshot_reports_paper_defaults(monkeypatch):
    monkeypatch.delenv("WHALE_COPY_LIVE_ENABLED", raising=False)
    state = whale_copy.WhaleCopyState()

    snap = asyncio.run(state.snapshot())
    assert snap["live_enabled"] is False
    assert snap["runtime"]["label"] == "PAPER / DRY-RUN"
    assert snap["notification_health"]["status"] == "ok"
    assert snap["signal_quality"]["avg_confidence"] == 0.0
    assert snap["backtest_metrics"]["iterations_completed"] == 0
    assert snap["signals"] == []


def test_snapshot_masks_wallets_and_reports_quality(monkeypatch):
    monkeypatch.delenv("WHALE_COPY_LIVE_ENABLED", raising=False)
    state = whale_copy.WhaleCopyState()
    signal = whale_copy.WhaleSignal(
        ts=1,
        detected_at=2.0,
        wallet="0x1234567890abcdef",
        pseudonym="whale",
        side="BUY",
        slug="sample-market",
        title="Sample market",
        outcome="Yes",
        asset="asset-token",
        size=100.0,
        price=0.5,
        notional=50.0,
        tx="0xtx",
        history_count=1,
        confidence=0.8,
        action="paper",
        reason="first_visible_trade_large_buy",
    )

    asyncio.run(state.add_signal(signal))
    snap = asyncio.run(state.snapshot())

    assert snap["paper_trade_count"] == 1
    assert snap["signal_quality"]["avg_confidence"] == 0.8
    assert snap["signal_quality"]["high_confidence_count"] == 1
    assert snap["wallet_history"]["first_visible_signal_count"] == 1
    assert snap["signals"][0]["masked_wallet"] == "0x1234…cdef"
    assert "wallet" not in snap["signals"][0]


def test_backtest_metrics_from_env(monkeypatch):
    monkeypatch.setenv("WHALE_BACKTEST_ITERATIONS", "5")
    monkeypatch.setenv("WHALE_BACKTEST_BEST_ROI_PCT", "123.4")
    monkeypatch.setenv("WHALE_BACKTEST_BEST_PNL_USD", "56.78")
    monkeypatch.setenv("WHALE_BACKTEST_BEST_STRATEGY", "iteration-4")

    metrics = whale_copy.backtest_metrics()

    assert metrics["iterations_completed"] == 5
    assert metrics["best_roi_pct"] == 123.4
    assert metrics["best_pnl_usd"] == 56.78
    assert metrics["best_strategy"] == "iteration-4"


def test_whale_dashboard_html_has_required_reporting_blocks():
    assert "Wallet History" in whale_copy.HTML
    assert "Signal Quality" in whale_copy.HTML
    assert "Notification Health" in whale_copy.HTML
    assert "Backtest Best" in whale_copy.HTML
    assert "PAPER / DRY-RUN" in whale_copy.HTML
