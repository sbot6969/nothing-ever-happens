from __future__ import annotations

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
    import asyncio

    snap = asyncio.run(state.snapshot())
    assert snap["live_enabled"] is False
    assert snap["signals"] == []
