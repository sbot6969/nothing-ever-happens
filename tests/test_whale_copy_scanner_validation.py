from __future__ import annotations

import pytest

from bot import whale_copy


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def raise_for_status(self):
        return None

    async def json(self):
        return self.payload


class _FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_fetch_json_uses_user_agent_and_rejects_non_list_payload() -> None:
    session = _FakeSession({"unexpected": "object"})

    rows = await whale_copy._fetch_json(session, "https://example.invalid/trades")

    assert rows == []
    url, kwargs = session.calls[0]
    assert url == "https://example.invalid/trades"
    assert kwargs["headers"]["User-Agent"] == whale_copy.USER_AGENT
    assert kwargs["headers"]["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_wallet_history_count_is_cached() -> None:
    state = whale_copy.WhaleCopyState()
    session = _FakeSession([{"trade": 1}, {"trade": 2}])

    count1 = await whale_copy._wallet_history_count(
        session,
        state,
        "0x1111111111111111111111111111111111111111",
    )
    count2 = await whale_copy._wallet_history_count(
        session,
        state,
        "0x1111111111111111111111111111111111111111",
    )

    assert count1 == 2
    assert count2 == 2
    assert len(session.calls) == 1
    assert "user=0x1111111111111111111111111111111111111111" in session.calls[0][0]


def test_trade_key_falls_back_stably_when_hash_missing() -> None:
    trade = {"name": "row-name", "timestamp": 123}

    assert whale_copy._trade_key(trade) == "row-name"


def test_notional_handles_missing_values_as_zero() -> None:
    assert whale_copy._notional({}) == 0.0


@pytest.mark.asyncio
async def test_handle_signal_defaults_to_paper_and_records_no_live_order(monkeypatch) -> None:
    state = whale_copy.WhaleCopyState()
    recorded = []
    monkeypatch.delenv("WHALE_COPY_LIVE_ENABLED", raising=False)
    monkeypatch.setenv("WHALE_COPY_FRACTION", "0.1")
    monkeypatch.setenv("WHALE_MAX_COPY_NOTIONAL_USD", "25")
    monkeypatch.setattr(whale_copy, "record_order", lambda **kwargs: recorded.append(kwargs))

    await whale_copy._handle_signal(
        {
            "timestamp": "1000",
            "proxyWallet": "0x1111111111111111111111111111111111111111",
            "side": "BUY",
            "slug": "market",
            "title": "Market title",
            "outcome": "YES",
            "asset": "asset",
            "size": "1000",
            "price": "0.50",
            "transactionHash": "0xabc",
        },
        history_count=1,
        state=state,
    )

    snapshot = await state.snapshot()
    assert snapshot["paper_trade_count"] == 1
    assert snapshot["live_trade_count"] == 0
    assert [row["action"] for row in recorded] == ["whale_signal", "whale_copy_paper_trade"]
    assert recorded[-1]["status"] == "live_disabled"


@pytest.mark.asyncio
async def test_handle_signal_live_gate_only_records_not_implemented_status(monkeypatch) -> None:
    state = whale_copy.WhaleCopyState()
    recorded = []
    monkeypatch.setenv("WHALE_COPY_LIVE_ENABLED", "true")
    monkeypatch.setattr(whale_copy, "record_order", lambda **kwargs: recorded.append(kwargs))

    await whale_copy._handle_signal(
        {
            "timestamp": "1000",
            "proxyWallet": "0x1111111111111111111111111111111111111111",
            "side": "BUY",
            "asset": "asset",
            "size": "1000",
            "price": "0.50",
        },
        history_count=1,
        state=state,
    )

    snapshot = await state.snapshot()
    assert snapshot["paper_trade_count"] == 0
    assert snapshot["live_trade_count"] == 1
    assert recorded[-1]["action"] == "whale_copy_live_trade"
    assert recorded[-1]["status"] == "live_not_implemented_without_wallet_confirmation"
