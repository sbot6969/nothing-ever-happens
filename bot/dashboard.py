"""Dashboard web server via aiohttp + WebSocket."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import deque
from pathlib import Path

from aiohttp import web

from bot.nothing_happens_control import NothingHappensControlState

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
BACKGROUND_IMAGE = STATIC_DIR / "nothingeverhappens.svg"
BALANCE_POLL_INTERVAL_SEC = 30.0
BALANCE_TIMEOUT_SEC = 10.0
RESOLUTION_POLL_INTERVAL_SEC = 15.0
TRADE_HISTORY_LIMIT = 1000
BALANCE_HISTORY_LIMIT = 2880


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float | None = None) -> float | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _bot_mode(prefix: str, *, default_live_enabled: bool = False) -> dict:
    mode_raw = os.getenv(f"{prefix}_MODE", os.getenv("BOT_MODE", "paper")).strip().lower() or "paper"
    live_enabled = _env_bool(f"{prefix}_LIVE_ENABLED", default_live_enabled)
    dry_run = _env_bool(f"{prefix}_DRY_RUN", True)
    live_send_enabled = mode_raw == "live" and live_enabled and not dry_run
    return {
        "mode": "live" if live_send_enabled else "paper",
        "configured_mode": mode_raw,
        "live_send_enabled": live_send_enabled,
        "dry_run": dry_run,
        "label": "LIVE SEND ENABLED" if live_send_enabled else "PAPER / DRY-RUN",
    }


def _runtime_status() -> dict:
    bot_mode = os.getenv("BOT_MODE", "paper").strip().lower() or "paper"
    live_trading_enabled = _env_bool("LIVE_TRADING_ENABLED", False)
    dry_run = _env_bool("DRY_RUN", True)
    live_send_enabled = bot_mode == "live" and live_trading_enabled and not dry_run
    return {
        "variant": os.getenv("BOT_VARIANT", "nothing_happens"),
        "mode": "live" if live_send_enabled else "paper",
        "bot_mode": bot_mode,
        "live_send_enabled": live_send_enabled,
        "live_trading_enabled": live_trading_enabled,
        "dry_run": dry_run,
        "label": "LIVE SEND ENABLED" if live_send_enabled else "PAPER / DRY-RUN",
    }


def _platform_bot_card(
    *,
    bot_id: str,
    name: str,
    family: str,
    prefix: str,
    status: str = "planned",
    health: str | None = None,
    paper_signal_count: int = 0,
    live_signal_count: int = 0,
    pnl_usd: float | None = None,
    roi_pct: float | None = None,
    backtest_label: str = "",
    last_error: str = "",
    metrics: dict | None = None,
) -> dict:
    mode = _bot_mode(prefix)
    safe_error = str(last_error or "")[:180]
    resolved_health = health or ("degraded" if safe_error else ("idle" if status == "planned" else "ok"))
    configured_live_signal_count = int(live_signal_count or 0)
    safe_metrics = dict(metrics or {})
    if configured_live_signal_count and not mode["live_send_enabled"]:
        safe_metrics.setdefault("configured_live_signal_count", configured_live_signal_count)
    return {
        "id": bot_id,
        "name": name,
        "family": family,
        "status": status,
        "mode": mode["mode"],
        "mode_label": mode["label"],
        "configured_mode": mode["configured_mode"],
        "live_send_enabled": mode["live_send_enabled"],
        "dry_run": mode["dry_run"],
        "health": resolved_health,
        "paper_signal_count": int(paper_signal_count or 0),
        "live_signal_count": configured_live_signal_count if mode["live_send_enabled"] else 0,
        "pnl_usd": round(pnl_usd, 4) if pnl_usd is not None else None,
        "roi_pct": round(roi_pct, 4) if roi_pct is not None else None,
        "backtest_label": backtest_label,
        "last_error": safe_error,
        "metrics": safe_metrics,
    }


def _platform_agent_card(*, agent_id: str, name: str, role: str, status_env: str, default_status: str, output_doc: str) -> dict:
    status = os.getenv(status_env, default_status).strip() or default_status
    return {
        "id": agent_id,
        "name": name,
        "role": role,
        "status": status[:80],
        "output_doc": output_doc,
    }


class DashboardServer:
    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8080,
        exchange=None,
        portfolio_state=None,
        nothing_happens_control: NothingHappensControlState | None = None,
    ):
        self.host = host
        self.port = port
        self._exchange = exchange
        self._portfolio_state = portfolio_state
        self._nothing_happens_control = nothing_happens_control
        self._clients: set[web.WebSocketResponse] = set()
        self._last_portfolio_version = -1
        self._last_nothing_happens_control_version = -1
        self._last_resolution_version = -1
        self._ledger_path = os.getenv("TRADE_LEDGER_PATH", "trades.jsonl")
        self._ledger_pos = 0
        self._trade_history: deque[dict] = deque(maxlen=TRADE_HISTORY_LIMIT)
        self._starting_balance: float | None = None
        self._current_balance: float | None = None
        self._last_balance_poll = 0.0
        self._balance_history: deque[tuple[float, float]] = deque(maxlen=BALANCE_HISTORY_LIMIT)
        self._resolutions: dict[str, str] = {}
        self._resolution_version = 0
        self._pending_resolution_slugs: list[str] = []
        self._last_resolution_poll = 0.0

    async def _index(self, request):
        return web.FileResponse(STATIC_DIR / "dashboard.html")

    async def _background_image(self, request):
        if not BACKGROUND_IMAGE.exists():
            raise web.HTTPNotFound(text="background image not found")
        return web.FileResponse(BACKGROUND_IMAGE)

    async def _ws_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._clients.add(ws)
        logger.info("Dashboard client connected (%d total)", len(self._clients))
        await self._send_initial(ws)
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    await self._handle_ws_message(ws, msg.data)
        finally:
            self._clients.discard(ws)
            logger.info("Dashboard client disconnected (%d remaining)", len(self._clients))
        return ws

    async def _handle_ws_message(self, ws: web.WebSocketResponse, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await self._send_to(ws, {"type": "control_ack", "ok": False, "error": "invalid_json"})
            return
        if not isinstance(payload, dict):
            await self._send_to(ws, {"type": "control_ack", "ok": False, "error": "invalid_payload"})
            return
        if payload.get("type") == "set_position_target":
            await self._send_to(ws, {"type": "control_ack", "ok": False, "error": "controls_disabled"})

    async def _send_to(self, ws: web.WebSocketResponse, data: dict) -> None:
        try:
            await ws.send_str(json.dumps(data))
        except Exception:
            self._clients.discard(ws)

    async def _broadcast(self, data: dict) -> None:
        if not self._clients:
            return
        message = json.dumps(data)
        dead: set[web.WebSocketResponse] = set()
        for ws in self._clients:
            try:
                await ws.send_str(message)
            except Exception:
                dead.add(ws)
        self._clients -= dead

    async def _send_initial(self, ws: web.WebSocketResponse) -> None:
        portfolio_message = self._make_portfolio_message(force=True)
        if portfolio_message is not None:
            await self._send_to(ws, portfolio_message)
        if self._starting_balance is not None and self._current_balance is not None:
            await self._send_to(ws, self._make_pnl_message())
        if self._balance_history:
            await self._send_to(
                ws,
                {
                    "type": "balance_history",
                    "points": [
                        {"ts": ts * 1000, "balance": round(balance, 2)}
                        for ts, balance in self._balance_history
                    ],
                },
            )
        for trade in list(self._trade_history)[-500:]:
            await self._send_to(ws, trade)
        for slug, winner in self._resolutions.items():
            await self._send_to(
                ws,
                {"type": "resolution", "market_slug": slug, "winner": winner},
            )

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("Dashboard poll error: %s", exc)
            await asyncio.sleep(0.25)

    async def _poll_once(self) -> None:
        portfolio_message = self._make_portfolio_message()
        if portfolio_message is not None:
            await self._broadcast(portfolio_message)
        await self._poll_trades()
        await self._poll_balance()
        await self._poll_resolutions()

    def _make_portfolio_message(self, *, force: bool = False) -> dict | None:
        if self._portfolio_state is None:
            return None
        version = self._portfolio_state.version()
        control_version = (
            self._nothing_happens_control.version()
            if self._nothing_happens_control is not None
            else -1
        )
        if (
            not force
            and version == self._last_portfolio_version
            and control_version == self._last_nothing_happens_control_version
            and self._resolution_version == self._last_resolution_version
        ):
            return None
        self._last_portfolio_version = version
        self._last_nothing_happens_control_version = control_version
        self._last_resolution_version = self._resolution_version
        snapshot = self._portfolio_state.snapshot()
        control_snapshot = (
            self._nothing_happens_control.snapshot()
            if self._nothing_happens_control is not None
            else None
        )
        finalization_summary = self._make_finalization_summary(snapshot.positions)
        platform = self._make_platform_summary(snapshot, finalization_summary)
        return {
            "type": "portfolio",
            "runtime": _runtime_status(),
            "platform": platform,
            "updated_at_us": snapshot.updated_at_us,
            "monitored_markets": snapshot.monitored_markets,
            "eligible_markets": snapshot.eligible_markets,
            "in_range_markets": snapshot.in_range_markets,
            "cash_balance": snapshot.cash_balance,
            "last_market_refresh_ts": snapshot.last_market_refresh_ts,
            "last_position_sync_ts": snapshot.last_position_sync_ts,
            "last_price_cycle_ts": snapshot.last_price_cycle_ts,
            "last_error": snapshot.last_error,
            "target_open_positions": (
                control_snapshot.target_open_positions if control_snapshot is not None else None
            ),
            "pending_entry_count": (
                control_snapshot.pending_entry_count if control_snapshot is not None else 0
            ),
            "remaining_position_capacity": (
                control_snapshot.remaining_capacity if control_snapshot is not None else None
            ),
            "opened_this_run": (
                control_snapshot.opened_this_run if control_snapshot is not None else 0
            ),
            "controls_enabled": control_snapshot is not None,
            "finalization": finalization_summary,
            "positions": [
                {
                    "slug": position.slug,
                    "title": position.title,
                    "outcome": position.outcome,
                    "asset": position.asset,
                    "condition_id": position.condition_id,
                    "size": round(position.size, 6),
                    "avg_price": round(position.avg_price, 6),
                    "initial_value": round(position.initial_value, 6),
                    "current_price": round(position.current_price, 6),
                    "current_value": round(position.current_value, 6),
                    "pnl_usd": round(position.pnl_usd, 6),
                    "pnl_pct": round(position.pnl_pct, 6),
                    "end_date": position.end_date,
                    "eta_seconds": round(position.eta_seconds, 3),
                    "finalization_status": self._finalization_status(position),
                    "finalization_priority": self._finalization_priority(position),
                    "resolution_winner": self._resolutions.get(position.slug),
                    "source": position.source,
                }
                for position in snapshot.positions
            ],
        }

    def _make_platform_summary(self, snapshot, finalization_summary: dict) -> dict:
        positions_value = sum(float(position.current_value or 0.0) for position in snapshot.positions)
        open_positions = len(snapshot.positions)
        nothing_error = snapshot.last_error or ""
        nothing_health = "degraded" if nothing_error else "ok"
        if finalization_summary.get("ended_positions", 0) > 0:
            nothing_health = "needs_resolution" if not nothing_error else "degraded"

        bots = [
            _platform_bot_card(
                bot_id="nothing_happens",
                name="Nothing Ever Happens",
                family="baseline_strategy",
                prefix="NOTHING_HAPPENS",
                status="running" if snapshot.updated_at_us else "waiting",
                health=nothing_health,
                paper_signal_count=int(snapshot.in_range_markets or 0),
                live_signal_count=open_positions if _runtime_status()["live_send_enabled"] else 0,
                pnl_usd=sum(float(position.pnl_usd or 0.0) for position in snapshot.positions),
                roi_pct=None,
                backtest_label=os.getenv("NOTHING_HAPPENS_BACKTEST_LABEL", "current portfolio"),
                last_error=nothing_error,
                metrics={
                    "monitored_markets": int(snapshot.monitored_markets or 0),
                    "eligible_markets": int(snapshot.eligible_markets or 0),
                    "in_range_markets": int(snapshot.in_range_markets or 0),
                    "open_positions": open_positions,
                    "cash_balance": round(float(snapshot.cash_balance or 0.0), 4),
                    "positions_value": round(positions_value, 4),
                    "finalization": finalization_summary,
                },
            ),
            _platform_bot_card(
                bot_id="whale_alt_copy",
                name="Whale / ALT Copy",
                family="copy_trading",
                prefix="WHALE_COPY",
                status=os.getenv("WHALE_COPY_STATUS", "paper_ready"),
                paper_signal_count=_env_int("WHALE_COPY_PAPER_SIGNALS", _env_int("WHALE_SIGNALS_SEEN", 0)),
                live_signal_count=_env_int("WHALE_COPY_LIVE_SIGNALS", 0),
                pnl_usd=_env_float("WHALE_BACKTEST_BEST_PNL_USD"),
                roi_pct=_env_float("WHALE_BACKTEST_BEST_ROI_PCT"),
                backtest_label=os.getenv("WHALE_BACKTEST_BEST_STRATEGY", "awaiting larger backtest"),
                last_error=os.getenv("WHALE_COPY_LAST_ERROR", ""),
                metrics={
                    "min_notional_usd": _env_float("WHALE_MIN_NOTIONAL_USD"),
                    "relative_market_size_threshold_pct": 30.0,
                    "expected_slippage_bps": _env_float("WHALE_EXPECTED_SLIPPAGE_BPS"),
                },
            ),
            _platform_bot_card(
                bot_id="market_making",
                name="Market-making",
                family="inventory_aware_quoting",
                prefix="MARKET_MAKER",
                status=os.getenv("MARKET_MAKER_STATUS", "planned_paper"),
                paper_signal_count=_env_int("MARKET_MAKER_PAPER_QUOTES", 0),
                live_signal_count=_env_int("MARKET_MAKER_LIVE_QUOTES", 0),
                pnl_usd=_env_float("MARKET_MAKER_BACKTEST_PNL_USD"),
                roi_pct=_env_float("MARKET_MAKER_BACKTEST_ROI_PCT"),
                backtest_label=os.getenv("MARKET_MAKER_BACKTEST_LABEL", "paper quote model pending"),
                last_error=os.getenv("MARKET_MAKER_LAST_ERROR", ""),
                metrics={
                    "quote_count": _env_int("MARKET_MAKER_PAPER_QUOTES", 0),
                    "inventory_cap_usd": _env_float("MARKET_MAKER_INVENTORY_CAP_USD"),
                    "spread_bps": _env_float("MARKET_MAKER_SPREAD_BPS"),
                },
            ),
            _platform_bot_card(
                bot_id="normal_amm_allocation",
                name="Normal-distribution AMM Allocation",
                family="portfolio_allocator",
                prefix="NORMAL_AMM",
                status=os.getenv("NORMAL_AMM_STATUS", "planned_paper"),
                paper_signal_count=_env_int("NORMAL_AMM_PAPER_ALLOCATIONS", 0),
                live_signal_count=_env_int("NORMAL_AMM_LIVE_ALLOCATIONS", 0),
                pnl_usd=_env_float("NORMAL_AMM_BACKTEST_PNL_USD"),
                roi_pct=_env_float("NORMAL_AMM_BACKTEST_ROI_PCT"),
                backtest_label=os.getenv("NORMAL_AMM_BACKTEST_LABEL", "allocation simulator pending"),
                last_error=os.getenv("NORMAL_AMM_LAST_ERROR", ""),
                metrics={
                    "paper_allocations": _env_int("NORMAL_AMM_PAPER_ALLOCATIONS", 0),
                    "capital_cap_usd": _env_float("NORMAL_AMM_CAPITAL_CAP_USD"),
                    "distribution_sigma": _env_float("NORMAL_AMM_SIGMA"),
                },
            ),
        ]
        agents = [
            _platform_agent_card(
                agent_id="research_agent",
                name="Deep Research Agent",
                role="source research + Markdown reports",
                status_env="RESEARCH_AGENT_STATUS",
                default_status="running",
                output_doc="docs/polymarket_multi_bot/RESEARCH_APPENDIX.md",
            ),
            _platform_agent_card(
                agent_id="quant_math_agent",
                name="Quant / Math Agent",
                role="modeling + backtest interpretation",
                status_env="QUANT_MATH_AGENT_STATUS",
                default_status="running",
                output_doc="docs/polymarket_multi_bot/QUANT_REVIEW.md",
            ),
            _platform_agent_card(
                agent_id="backend_dev",
                name="Backend Dev",
                role="strategy code + backtests",
                status_env="BACKEND_AGENT_STATUS",
                default_status="completed initial pass",
                output_doc="docs/agent_tasks/backend-dev-multibot.md",
            ),
            _platform_agent_card(
                agent_id="frontend_dev",
                name="Frontend Dev",
                role="unified dashboard",
                status_env="FRONTEND_AGENT_STATUS",
                default_status="completed initial pass",
                output_doc="docs/agent_tasks/frontend-dev-multibot.md",
            ),
            _platform_agent_card(
                agent_id="security_reviewer",
                name="Security Reviewer",
                role="live gates + secrets + safety",
                status_env="SECURITY_AGENT_STATUS",
                default_status="pending",
                output_doc="docs/polymarket_multi_bot/SECURITY_REVIEW.md",
            ),
            _platform_agent_card(
                agent_id="cross_reviewer",
                name="Cross / Adversarial Reviewer",
                role="assumption and test-gap review",
                status_env="CROSS_REVIEW_AGENT_STATUS",
                default_status="pending",
                output_doc="docs/polymarket_multi_bot/CROSS_REVIEW.md",
            ),
        ]
        return {
            "type": "polymarket_multi_bot_platform",
            "bot_count": len(bots),
            "agent_count": len(agents),
            "live_enabled_count": sum(1 for bot in bots if bot["live_send_enabled"]),
            "paper_count": sum(1 for bot in bots if not bot["live_send_enabled"]),
            "error_count": sum(1 for bot in bots if bot["last_error"]),
            "bots": bots,
            "agents": agents,
        }

    def _finalization_status(self, position) -> str:
        winner = self._resolutions.get(position.slug)
        if winner:
            if str(position.outcome).strip().lower() == str(winner).strip().lower():
                return "resolved_win"
            return "resolved_loss"
        eta = float(position.eta_seconds or 0.0)
        if eta <= 0:
            return "awaiting_resolution"
        if eta <= 24 * 3600:
            return "ending_soon"
        return "open"

    def _finalization_priority(self, position) -> int:
        status = self._finalization_status(position)
        return {
            "awaiting_resolution": 0,
            "ending_soon": 1,
            "resolved_win": 2,
            "resolved_loss": 2,
            "open": 3,
        }.get(status, 4)

    def _make_finalization_summary(self, positions) -> dict:
        ended = 0
        ending_soon = 0
        resolved = 0
        next_position = None
        for position in positions:
            eta = float(position.eta_seconds or 0.0)
            status = self._finalization_status(position)
            if status in {"resolved_win", "resolved_loss"}:
                resolved += 1
            elif eta <= 0:
                ended += 1
            elif eta <= 24 * 3600:
                ending_soon += 1
            if eta > 0 and (next_position is None or eta < float(next_position.eta_seconds or 0.0)):
                next_position = position
        return {
            "ended_positions": ended,
            "ending_soon_24h": ending_soon,
            "resolved_positions": resolved,
            "pending_resolution_count": len(self._pending_resolution_slugs),
            "next_finalization_slug": next_position.slug if next_position is not None else "",
            "next_finalization_eta_seconds": (
                round(float(next_position.eta_seconds), 3) if next_position is not None else None
            ),
        }

    async def _poll_trades(self) -> None:
        try:
            if not os.path.exists(self._ledger_path):
                return
            with open(self._ledger_path, "r") as f:
                f.seek(self._ledger_pos)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    trade_msg = {"type": "bot_trade", **record}
                    self._trade_history.append(trade_msg)
                    await self._broadcast(trade_msg)
                self._ledger_pos = f.tell()
        except Exception as exc:
            logger.debug("Trade ledger poll error: %s", exc)

    def _make_pnl_message(self) -> dict:
        pnl_usd = (self._current_balance or 0.0) - (self._starting_balance or 0.0)
        pnl_pct = (
            (pnl_usd / self._starting_balance * 100.0)
            if self._starting_balance and self._starting_balance > 0
            else 0.0
        )
        return {
            "type": "session_pnl",
            "starting_balance": round(self._starting_balance or 0.0, 2),
            "current_balance": round(self._current_balance or 0.0, 2),
            "pnl_usd": round(pnl_usd, 2),
            "pnl_pct": round(pnl_pct, 2),
        }

    async def _poll_balance(self) -> None:
        if self._exchange is None:
            return
        loop_now = asyncio.get_running_loop().time()
        if loop_now - self._last_balance_poll < BALANCE_POLL_INTERVAL_SEC:
            return
        self._last_balance_poll = loop_now
        try:
            balance = await asyncio.wait_for(
                asyncio.to_thread(self._exchange.get_collateral_balance),
                timeout=BALANCE_TIMEOUT_SEC,
            )
            if self._starting_balance is None:
                self._starting_balance = balance
                logger.info(
                    "dashboard_starting_balance",
                    extra={"balance": round(balance, 2)},
                )
            self._current_balance = balance
            ts_sec = time.time()
            self._balance_history.append((ts_sec, balance))
            await self._broadcast(self._make_pnl_message())
            await self._broadcast(
                {
                    "type": "balance_point",
                    "ts": ts_sec * 1000,
                    "balance": round(balance, 2),
                }
            )
        except Exception as exc:
            logger.debug("Dashboard balance poll failed: %s", exc)

    async def _poll_resolutions(self) -> None:
        loop_now = asyncio.get_running_loop().time()
        if loop_now - self._last_resolution_poll < RESOLUTION_POLL_INTERVAL_SEC:
            return
        self._last_resolution_poll = loop_now

        for trade in self._trade_history:
            slug = trade.get("market_slug", "")
            if slug and slug not in self._resolutions and slug not in self._pending_resolution_slugs:
                self._pending_resolution_slugs.append(slug)

        if self._portfolio_state is not None:
            for position in self._portfolio_state.snapshot().positions:
                slug = position.slug
                if (
                    slug
                    and float(position.eta_seconds or 0.0) <= 0
                    and slug not in self._resolutions
                    and slug not in self._pending_resolution_slugs
                ):
                    self._pending_resolution_slugs.append(slug)

        if not self._pending_resolution_slugs:
            return

        from bot.live_recovery import _check_gamma_resolution

        for slug in self._pending_resolution_slugs[:5]:
            try:
                winner = await _check_gamma_resolution(slug)
                if winner is None:
                    continue
                display_winner = winner.capitalize()
                self._resolutions[slug] = display_winner
                self._resolution_version += 1
                self._pending_resolution_slugs.remove(slug)
                await self._broadcast(
                    {
                        "type": "resolution",
                        "market_slug": slug,
                        "winner": display_winner,
                    }
                )
                logger.info("Resolution: %s -> %s", slug, display_winner)
            except Exception as exc:
                logger.debug("Resolution fetch failed for %s: %s", slug, exc)

    async def run(self) -> None:
        app = web.Application()
        app.router.add_get("/", self._index)
        app.router.add_get("/nothingeverhappens.svg", self._background_image)
        app.router.add_get("/ws", self._ws_handler)

        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        ssl_context = None
        scheme = "http"
        cert_file = os.getenv("DASHBOARD_SSL_CERT")
        key_file = os.getenv("DASHBOARD_SSL_KEY")
        if cert_file and key_file:
            import ssl

            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(cert_file, key_file)
            scheme = "https"
        site = web.TCPSite(runner, self.host, self.port, ssl_context=ssl_context)
        await site.start()
        logger.info("Dashboard at %s://%s:%d", scheme, self.host, self.port)

        try:
            await self._poll_loop()
        finally:
            await runner.cleanup()
