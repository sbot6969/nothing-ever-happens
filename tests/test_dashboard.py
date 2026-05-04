"""Smoke tests for dashboard server."""

import asyncio

import aiohttp
import pytest

from bot.dashboard import DashboardServer
from bot.nothing_happens_control import NothingHappensControlState
from bot.portfolio_state import PortfolioState, PositionSnapshot


def _make_portfolio_state() -> PortfolioState:
    portfolio_state = PortfolioState()
    portfolio_state.update(
        updated_at_us=1,
        monitored_markets=12,
        eligible_markets=10,
        in_range_markets=3,
        positions=[],
        cash_balance=42.0,
        last_market_refresh_ts=1.0,
        last_position_sync_ts=1.0,
        last_price_cycle_ts=1.0,
        last_error="",
    )
    return portfolio_state


def test_dashboard_creates():
    server = DashboardServer(port=0)
    assert server.port == 0
    assert server._clients == set()


def test_dashboard_force_portfolio_snapshot_replays_latest_state():
    portfolio_state = _make_portfolio_state()
    server = DashboardServer(port=0, portfolio_state=portfolio_state)

    first = server._make_portfolio_message(force=True)
    second = server._make_portfolio_message(force=True)

    assert first is not None
    assert second is not None
    assert first["cash_balance"] == 42.0
    assert first["in_range_markets"] == 3
    assert second["cash_balance"] == 42.0
    assert second["in_range_markets"] == 3


def test_dashboard_portfolio_message_clearly_reports_paper_runtime(monkeypatch):
    monkeypatch.setenv("BOT_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN", "true")
    portfolio_state = _make_portfolio_state()
    server = DashboardServer(port=0, portfolio_state=portfolio_state)

    message = server._make_portfolio_message(force=True)

    assert message["runtime"] == {
        "variant": "nothing_happens",
        "mode": "paper",
        "bot_mode": "paper",
        "live_send_enabled": False,
        "live_trading_enabled": False,
        "dry_run": True,
        "label": "PAPER / DRY-RUN",
    }


def test_dashboard_portfolio_message_clearly_reports_live_runtime(monkeypatch):
    monkeypatch.setenv("BOT_MODE", "live")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("BOT_VARIANT", "nothing_happens")
    portfolio_state = _make_portfolio_state()
    server = DashboardServer(port=0, portfolio_state=portfolio_state)

    message = server._make_portfolio_message(force=True)

    assert message["runtime"] == {
        "variant": "nothing_happens",
        "mode": "live",
        "bot_mode": "live",
        "live_send_enabled": True,
        "live_trading_enabled": True,
        "dry_run": False,
        "label": "LIVE SEND ENABLED",
    }


def test_dashboard_portfolio_message_includes_four_bot_platform(monkeypatch):
    monkeypatch.setenv("BOT_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("WHALE_COPY_PAPER_SIGNALS", "7")
    monkeypatch.setenv("WHALE_BACKTEST_BEST_ROI_PCT", "12.5")
    monkeypatch.setenv("WHALE_BACKTEST_BEST_PNL_USD", "34.56")
    monkeypatch.setenv("MARKET_MAKER_PAPER_QUOTES", "11")
    monkeypatch.setenv("NORMAL_AMM_PAPER_ALLOCATIONS", "3")
    portfolio_state = _make_portfolio_state()
    server = DashboardServer(port=0, portfolio_state=portfolio_state)

    message = server._make_portfolio_message(force=True)

    platform = message["platform"]
    assert platform["type"] == "polymarket_multi_bot_platform"
    assert platform["bot_count"] == 4
    assert platform["agent_count"] == 6
    assert platform["live_enabled_count"] == 0
    bot_names = {bot["name"] for bot in platform["bots"]}
    assert bot_names == {
        "Nothing Ever Happens",
        "Whale / ALT Copy",
        "Market-making",
        "Normal-distribution AMM Allocation",
    }
    whale = next(bot for bot in platform["bots"] if bot["id"] == "whale_alt_copy")
    assert whale["mode_label"] == "PAPER / DRY-RUN"
    assert whale["paper_signal_count"] == 7
    assert whale["pnl_usd"] == 34.56
    assert whale["roi_pct"] == 12.5
    assert all("wallet" not in bot for bot in platform["bots"])
    agent_names = {agent["name"] for agent in platform["agents"]}
    assert "Deep Research Agent" in agent_names
    assert "Quant / Math Agent" in agent_names
    assert all("key" not in agent for agent in platform["agents"])


def test_dashboard_platform_model_sanitizes_error(monkeypatch):
    monkeypatch.setenv("MARKET_MAKER_LAST_ERROR", "x" * 250)
    server = DashboardServer(port=0, portfolio_state=_make_portfolio_state())

    message = server._make_portfolio_message(force=True)

    market_maker = next(bot for bot in message["platform"]["bots"] if bot["id"] == "market_making")
    assert market_maker["health"] == "degraded"
    assert len(market_maker["last_error"]) == 180


def test_dashboard_does_not_report_live_counts_when_live_gate_is_off(monkeypatch):
    monkeypatch.setenv("BOT_MODE", "paper")
    monkeypatch.setenv("WHALE_COPY_LIVE_SIGNALS", "4")
    server = DashboardServer(port=0, portfolio_state=_make_portfolio_state())

    message = server._make_portfolio_message(force=True)

    whale = next(bot for bot in message["platform"]["bots"] if bot["id"] == "whale_alt_copy")
    assert whale["live_send_enabled"] is False
    assert whale["live_signal_count"] == 0
    assert whale["metrics"]["configured_live_signal_count"] == 4


def test_dashboard_portfolio_message_includes_finalization_info():
    portfolio_state = PortfolioState()
    portfolio_state.update(
        updated_at_us=1,
        monitored_markets=1,
        eligible_markets=1,
        in_range_markets=1,
        positions=[
            PositionSnapshot(
                slug="ended-market",
                title="Ended market",
                outcome="No",
                asset="token",
                condition_id="condition",
                size=10.0,
                avg_price=0.5,
                initial_value=5.0,
                current_price=0.0,
                current_value=0.0,
                pnl_usd=-5.0,
                pnl_pct=-100.0,
                end_date="2026-05-03T19:00:00Z",
                eta_seconds=0.0,
                source="test",
            )
        ],
        cash_balance=1.0,
        last_market_refresh_ts=1.0,
        last_position_sync_ts=1.0,
        last_price_cycle_ts=1.0,
    )
    server = DashboardServer(port=0, portfolio_state=portfolio_state)

    message = server._make_portfolio_message(force=True)

    assert message["finalization"]["ended_positions"] == 1
    assert message["positions"][0]["finalization_status"] == "awaiting_resolution"
    assert message["positions"][0]["finalization_priority"] == 0

@pytest.mark.asyncio
async def test_dashboard_http_serves_html():
    server = DashboardServer(port=0)
    app = aiohttp.web.Application()
    app.router.add_get("/", server._index)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    port = site._server.sockets[0].getsockname()[1]
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://127.0.0.1:{port}/") as resp:
            assert resp.status == 200
            text = await resp.text()
            assert "Dashboard" in text
            assert "Open Positions" in text
            assert "In Range" in text
            assert "Finalization" in text
            assert "PAPER / DRY-RUN" in text
            assert "Unified Polymarket Platform" in text
            assert "Whale / ALT Copy" in text
            assert "Market-making" in text
            assert "Normal-distribution AMM Allocation" in text

    await runner.cleanup()


@pytest.mark.asyncio
async def test_dashboard_http_serves_background_image():
    server = DashboardServer(port=0)
    app = aiohttp.web.Application()
    app.router.add_get("/nothingeverhappens.svg", server._background_image)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    port = site._server.sockets[0].getsockname()[1]
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://127.0.0.1:{port}/nothingeverhappens.svg") as resp:
            assert resp.status == 200
            assert resp.headers["Content-Type"].startswith("image/svg+xml")
            text = await resp.text()
            assert "<svg" in text

    await runner.cleanup()


@pytest.mark.asyncio
async def test_dashboard_websocket_sends_initial_portfolio():
    server = DashboardServer(port=0, portfolio_state=_make_portfolio_state())
    app = aiohttp.web.Application()
    app.router.add_get("/ws", server._ws_handler)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    port = site._server.sockets[0].getsockname()[1]
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"http://127.0.0.1:{port}/ws") as ws:
            message = await asyncio.wait_for(ws.receive_json(), timeout=2)
            assert message["type"] == "portfolio"
            assert message["cash_balance"] == 42.0
            assert message["in_range_markets"] == 3
            await ws.close()

    await runner.cleanup()


@pytest.mark.asyncio
async def test_dashboard_websocket_rejects_nothing_happens_target_updates():
    control_state = NothingHappensControlState()
    control_state.update_status(
        current_open_positions=0,
        pending_entry_count=0,
        remaining_capacity=None,
        opened_this_run=0,
    )
    server = DashboardServer(
        port=0,
        portfolio_state=_make_portfolio_state(),
        nothing_happens_control=control_state,
    )
    app = aiohttp.web.Application()
    app.router.add_get("/ws", server._ws_handler)

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    port = site._server.sockets[0].getsockname()[1]
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"http://127.0.0.1:{port}/ws") as ws:
            initial = await asyncio.wait_for(ws.receive_json(), timeout=2)
            assert initial["type"] == "portfolio"
            assert initial["controls_enabled"] is True
            await ws.send_json({"type": "set_position_target", "target_open_positions": 17})
            ack = await asyncio.wait_for(ws.receive_json(), timeout=2)
            assert ack == {
                "type": "control_ack",
                "ok": False,
                "error": "controls_disabled",
            }
            await ws.close()

    assert control_state.snapshot().target_open_positions is None
    await runner.cleanup()
