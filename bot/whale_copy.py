"""Standalone first-time-whale copy-trading monitor.

Safety: defaults to paper/dry-run. It monitors Polymarket Data API trades,
identifies unusually large BUY trades from wallets with no earlier visible
Polymarket trade history, records the signal, and exposes a rich dashboard.
Live mirroring is intentionally gated behind WHALE_COPY_LIVE_ENABLED=true and
is not wired to a funded wallet until the operator explicitly configures it.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, asdict
import json
import logging
import os
import signal
import time
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

from bot.logging_config import configure_logging
from bot.trade_ledger import record_order

logger = logging.getLogger(__name__)
DATA_API = "https://data-api.polymarket.com/trades"
USER_AGENT = "Mozilla/5.0 (compatible; neh-whale-copy/1.0)"


@dataclass
class WhaleSignal:
    ts: int
    detected_at: float
    wallet: str
    pseudonym: str
    side: str
    slug: str
    title: str
    outcome: str
    asset: str
    size: float
    price: float
    notional: float
    tx: str
    history_count: int
    confidence: float
    action: str
    reason: str


class WhaleCopyState:
    def __init__(self, maxlen: int = 500) -> None:
        self._lock = asyncio.Lock()
        self.signals: deque[WhaleSignal] = deque(maxlen=maxlen)
        self.seen_txs: set[str] = set()
        self.wallet_history_cache: dict[str, int] = {}
        self.last_poll_ts = 0.0
        self.last_error = ""
        self.poll_count = 0
        self.signal_count = 0
        self.paper_trade_count = 0
        self.live_trade_count = 0

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            recent_signals = list(self.signals)[-200:]
            signal_rows = []
            first_visible_count = 0
            for sig in recent_signals:
                row = asdict(sig)
                row["masked_wallet"] = _mask_wallet(sig.wallet)
                row.pop("wallet", None)
                signal_rows.append(row)
                if int(sig.history_count or 0) <= 1:
                    first_visible_count += 1
            runtime_mode = "live" if live_enabled() else "paper"
            return {
                "type": "whale_state",
                "updated_at": time.time(),
                "runtime": {
                    "mode": runtime_mode,
                    "label": "LIVE COPY ENABLED" if runtime_mode == "live" else "PAPER / DRY-RUN",
                    "live_enabled": runtime_mode == "live",
                },
                "last_poll_ts": self.last_poll_ts,
                "last_error": self.last_error,
                "notification_health": {
                    "status": "degraded" if self.last_error else "ok",
                    "detail": self.last_error or "ledger/notifier best-effort",
                },
                "poll_count": self.poll_count,
                "signal_count": self.signal_count,
                "paper_trade_count": self.paper_trade_count,
                "live_trade_count": self.live_trade_count,
                "unique_wallets_checked": len(self.wallet_history_cache),
                "wallet_history": {
                    "unique_wallets_checked": len(self.wallet_history_cache),
                    "first_visible_signal_count": first_visible_count,
                    "history_cache_size": len(self.wallet_history_cache),
                },
                "signal_quality": _signal_quality(recent_signals),
                "backtest_metrics": backtest_metrics(),
                "live_enabled": live_enabled(),
                "min_notional_usd": min_notional_usd(),
                "copy_fraction": copy_fraction(),
                "max_copy_notional_usd": max_copy_notional_usd(),
                "signals": signal_rows[::-1],
            }

    async def set_error(self, error: str) -> None:
        async with self._lock:
            self.last_error = error

    async def mark_poll(self) -> None:
        async with self._lock:
            self.last_poll_ts = time.time()
            self.poll_count += 1
            self.last_error = ""

    async def add_signal(self, signal: WhaleSignal) -> None:
        async with self._lock:
            self.signals.append(signal)
            self.signal_count += 1
            if signal.action == "paper":
                self.paper_trade_count += 1
            elif signal.action == "live":
                self.live_trade_count += 1


def min_notional_usd() -> float:
    return float(os.getenv("WHALE_MIN_NOTIONAL_USD", "250"))


def copy_fraction() -> float:
    return float(os.getenv("WHALE_COPY_FRACTION", "0.10"))


def max_copy_notional_usd() -> float:
    return float(os.getenv("WHALE_MAX_COPY_NOTIONAL_USD", "25"))


def poll_interval_sec() -> float:
    return float(os.getenv("WHALE_POLL_INTERVAL_SEC", "20"))


def live_enabled() -> bool:
    return os.getenv("WHALE_COPY_LIVE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _mask_wallet(wallet: str) -> str:
    wallet = str(wallet or "")
    if len(wallet) <= 12:
        return wallet or "--"
    return f"{wallet[:6]}…{wallet[-4:]}"


def _optional_float_env(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    return float(raw)


def _optional_int_env(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    return int(raw)


def backtest_metrics() -> dict[str, Any]:
    """Operator-supplied latest backtest summary for dashboard display.

    The whale-copy runtime is intentionally not doing live accounting here; these
    fields let generated backtest reports surface in the dashboard without
    touching transaction code.
    """
    return {
        "iterations_completed": _optional_int_env("WHALE_BACKTEST_ITERATIONS") or 0,
        "best_roi_pct": _optional_float_env("WHALE_BACKTEST_BEST_ROI_PCT"),
        "best_pnl_usd": _optional_float_env("WHALE_BACKTEST_BEST_PNL_USD"),
        "best_strategy": os.getenv("WHALE_BACKTEST_BEST_STRATEGY", ""),
        "report_path": os.getenv("WHALE_BACKTEST_REPORT", ""),
    }


def _signal_quality(signals: list[WhaleSignal]) -> dict[str, Any]:
    if not signals:
        return {"avg_confidence": 0.0, "latest_confidence": 0.0, "high_confidence_count": 0}
    confidences = [float(sig.confidence or 0.0) for sig in signals]
    return {
        "avg_confidence": round(sum(confidences) / len(confidences), 3),
        "latest_confidence": round(confidences[-1], 3),
        "high_confidence_count": sum(1 for value in confidences if value >= 0.75),
    }


def _trade_key(trade: dict[str, Any]) -> str:
    return str(trade.get("transactionHash") or trade.get("name") or json.dumps(trade, sort_keys=True)[:240])


def _notional(trade: dict[str, Any]) -> float:
    return float(trade.get("size") or 0.0) * float(trade.get("price") or 0.0)


async def _fetch_json(session: aiohttp.ClientSession, url: str) -> list[dict[str, Any]]:
    async with session.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=15) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data if isinstance(data, list) else []


async def _wallet_history_count(session: aiohttp.ClientSession, state: WhaleCopyState, wallet: str) -> int:
    if wallet in state.wallet_history_cache:
        return state.wallet_history_cache[wallet]
    url = f"{DATA_API}?limit=3&user={wallet}"
    rows = await _fetch_json(session, url)
    count = len(rows)
    state.wallet_history_cache[wallet] = count
    return count


def _confidence(trade: dict[str, Any], history_count: int) -> float:
    notional = _notional(trade)
    base = min(0.7, notional / max(min_notional_usd() * 4.0, 1.0))
    novelty = 0.3 if history_count <= 1 else 0.0
    buy_bonus = 0.1 if str(trade.get("side") or "").upper() == "BUY" else 0.0
    return round(min(0.99, base + novelty + buy_bonus), 3)


async def _handle_signal(trade: dict[str, Any], history_count: int, state: WhaleCopyState) -> None:
    notional = _notional(trade)
    copy_notional = min(max_copy_notional_usd(), max(0.0, notional * copy_fraction()))
    is_live = live_enabled()
    signal = WhaleSignal(
        ts=int(trade.get("timestamp") or 0),
        detected_at=time.time(),
        wallet=str(trade.get("proxyWallet") or ""),
        pseudonym=str(trade.get("pseudonym") or ""),
        side=str(trade.get("side") or ""),
        slug=str(trade.get("slug") or trade.get("eventSlug") or ""),
        title=str(trade.get("title") or ""),
        outcome=str(trade.get("outcome") or ""),
        asset=str(trade.get("asset") or ""),
        size=float(trade.get("size") or 0.0),
        price=float(trade.get("price") or 0.0),
        notional=round(notional, 4),
        tx=str(trade.get("transactionHash") or ""),
        history_count=history_count,
        confidence=_confidence(trade, history_count),
        action="live" if is_live else "paper",
        reason="first_visible_trade_large_buy" if history_count <= 1 else "large_trade",
    )
    await state.add_signal(signal)
    action = "whale_copy_live_trade" if is_live else "whale_copy_paper_trade"
    record_order(
        action="whale_signal",
        market_slug=signal.slug,
        side=signal.side,
        token_id=signal.asset,
        amount=signal.notional,
        reference_price=signal.price,
        wallet=signal.wallet,
        pseudonym=signal.pseudonym,
        confidence=signal.confidence,
        history_count=history_count,
        tx=signal.tx,
        title=signal.title,
        outcome=signal.outcome,
        planned_copy_notional=copy_notional,
    )
    record_order(
        action=action,
        market_slug=signal.slug,
        side=signal.side,
        token_id=signal.asset,
        amount=copy_notional,
        reference_price=signal.price,
        wallet=signal.wallet,
        confidence=signal.confidence,
        status="live_disabled" if not is_live else "live_not_implemented_without_wallet_confirmation",
    )
    logger.info(
        "whale_signal slug=%s wallet=%s notional=%.2f price=%.4f history=%d action=%s",
        signal.slug,
        signal.wallet,
        signal.notional,
        signal.price,
        history_count,
        signal.action,
    )


async def poll_whales(state: WhaleCopyState, shutdown: asyncio.Event) -> None:
    async with aiohttp.ClientSession() as session:
        while not shutdown.is_set():
            try:
                rows = await _fetch_json(session, f"{DATA_API}?limit=100")
                await state.mark_poll()
                for trade in sorted(rows, key=lambda row: int(row.get("timestamp") or 0)):
                    key = _trade_key(trade)
                    if key in state.seen_txs:
                        continue
                    state.seen_txs.add(key)
                    if str(trade.get("side") or "").upper() != "BUY":
                        continue
                    notional = _notional(trade)
                    if notional < min_notional_usd():
                        continue
                    wallet = str(trade.get("proxyWallet") or "")
                    if not wallet:
                        continue
                    history_count = await _wallet_history_count(session, state, wallet)
                    if history_count > 1 and os.getenv("WHALE_REQUIRE_FIRST_TRADE", "true").lower() in {"1", "true", "yes", "on"}:
                        continue
                    await _handle_signal(trade, history_count, state)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("whale_poll_failed: %s", exc)
                await state.set_error(str(exc))
                record_order(action="error", market_slug="", side="", token_id="", amount=0, error=f"whale_poll_failed: {exc}")
            await asyncio.sleep(poll_interval_sec())


HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Whale Copy Dashboard</title>
<style>body{margin:0;background:#0d1117;color:#e6edf3;font-family:system-ui,-apple-system,sans-serif}.shell{max-width:1440px;margin:auto;padding:24px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.card,.panel{background:#161b22;border:1px solid #30363d;border-radius:16px;padding:14px}.label{color:#8b949e;text-transform:uppercase;font-size:12px;letter-spacing:.08em}.value{font-size:24px;font-weight:800;margin-top:6px}.meta{color:#8b949e;font-size:13px;margin-top:6px}.panel{margin-top:16px}table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #30363d;padding:10px;text-align:left;vertical-align:top;font-size:14px}th{color:#8b949e;text-transform:uppercase;font-size:12px}.mono{font-family:ui-monospace,monospace}.good{color:#3fb950}.bad{color:#f85149}.warn{color:#d29922}a{color:#58a6ff}.pill{display:inline-block;border:1px solid #30363d;border-radius:999px;padding:3px 8px;background:#21262d}.title{display:flex;justify-content:space-between;gap:12px;align-items:center}.subgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}@media(max-width:900px){.grid,.subgrid{grid-template-columns:1fr}}</style></head><body><div class="shell"><div class="title"><h1>🐋 Whale Copy Bot</h1><div id="socket" class="pill bad">socket disconnected</div></div><div class="grid"><div class="card"><div class="label">Mode</div><div id="mode" class="value">--</div><div id="mode-meta" class="meta">live gate off by default</div></div><div class="card"><div class="label">Signals</div><div id="signals" class="value">--</div><div class="meta">first-time large BUYs</div></div><div class="card"><div class="label">Paper</div><div id="paper" class="value">--</div><div class="meta">simulated copies</div></div><div class="card"><div class="label">Live</div><div id="live" class="value">--</div><div class="meta">real copies</div></div><div class="card"><div class="label">Wallet History</div><div id="wallets" class="value">--</div><div id="wallet-meta" class="meta">history checked</div></div><div class="card"><div class="label">Signal Quality</div><div id="quality" class="value">--</div><div id="quality-meta" class="meta">avg / high confidence</div></div><div class="card"><div class="label">Notification Health</div><div id="notify" class="value">--</div><div id="notify-meta" class="meta">ledger/notifier best-effort</div></div><div class="card"><div class="label">Copy Rule</div><div id="copy" class="value">--</div><div id="copy-meta" class="meta">fraction / cap</div></div></div><div class="subgrid"><div class="card"><div class="label">Min Whale</div><div id="min" class="value">--</div><div class="meta">notional threshold</div></div><div class="card"><div class="label">Backtest Best</div><div id="backtest" class="value">--</div><div id="backtest-meta" class="meta">waiting for reports</div></div><div class="card"><div class="label">Last Error</div><div id="err" class="value bad">none</div><div id="poll" class="meta">poll --</div></div></div><div class="panel"><h2>Recent Whale Signals</h2><table><thead><tr><th>Market</th><th>Whale</th><th>Trade</th><th>Copy</th><th>Confidence</th><th>Reason</th><th>Tx</th></tr></thead><tbody id="rows"><tr><td colspan="7" class="meta">waiting for signals</td></tr></tbody></table></div></div><script>
const $=id=>document.getElementById(id);function usd(x){return '$'+Number(x||0).toFixed(2)}function pct(x){return x==null?'--':Number(x).toFixed(2)+'%'}function ago(ts){if(!ts)return'--';let d=Math.max(0,Date.now()/1000-ts);if(d<60)return Math.floor(d)+'s ago';if(d<3600)return Math.floor(d/60)+'m ago';return Math.floor(d/3600)+'h ago'}function esc(v){return String(v??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}function render(s){let rt=s.runtime||{};$('mode').textContent=rt.label||(s.live_enabled?'LIVE COPY ENABLED':'PAPER / DRY-RUN');$('mode').className='value '+(s.live_enabled?'bad':'warn');$('mode-meta').textContent=s.live_enabled?'live copy gate is ON':'no live funds/orders from this dashboard';$('signals').textContent=s.signal_count;$('paper').textContent=s.paper_trade_count;$('live').textContent=s.live_trade_count;let wh=s.wallet_history||{};$('wallets').textContent=wh.unique_wallets_checked??s.unique_wallets_checked;$('wallet-meta').textContent='first-visible signals '+(wh.first_visible_signal_count??0)+' | cache '+(wh.history_cache_size??0);let q=s.signal_quality||{};$('quality').textContent=Number(q.avg_confidence||0).toFixed(3);$('quality-meta').textContent='latest '+Number(q.latest_confidence||0).toFixed(3)+' | high '+(q.high_confidence_count||0);let nh=s.notification_health||{};$('notify').textContent=nh.status||'ok';$('notify').className='value '+((nh.status==='ok')?'good':'warn');$('notify-meta').textContent=nh.detail||'ledger/notifier best-effort';$('min').textContent=usd(s.min_notional_usd);$('copy').textContent=Math.round(s.copy_fraction*100)+'% / '+usd(s.max_copy_notional_usd);$('copy-meta').textContent='paper unless WHALE_COPY_LIVE_ENABLED=true';let bt=s.backtest_metrics||{};$('backtest').textContent=bt.best_roi_pct==null?'--':pct(bt.best_roi_pct);$('backtest-meta').textContent='iter '+(bt.iterations_completed||0)+' | PnL '+(bt.best_pnl_usd==null?'--':usd(bt.best_pnl_usd))+(bt.best_strategy?' | '+bt.best_strategy:'');$('err').textContent=s.last_error||'none';$('poll').textContent='poll '+ago(s.last_poll_ts);let rows=$('rows');rows.innerHTML='';if(!s.signals.length){rows.innerHTML='<tr><td colspan="7" class="meta">no signals yet</td></tr>';return}for(const sig of s.signals){let tr=document.createElement('tr');let url='https://polymarket.com/event/'+encodeURIComponent(sig.slug||'');let tx=sig.tx?'<a target="_blank" rel="noreferrer" href="https://polygonscan.com/tx/'+encodeURIComponent(sig.tx)+'">tx</a>':'--';tr.innerHTML='<td><a target="_blank" rel="noreferrer" href="'+url+'">'+esc(sig.title||sig.slug)+'</a><div class="meta mono">'+esc(sig.slug)+'</div></td><td><div class="mono">'+esc(sig.masked_wallet||'--')+'</div><div class="meta">'+esc(sig.pseudonym||'')+' | history '+esc(sig.history_count)+'</div></td><td>'+esc(sig.side)+' '+esc(sig.outcome)+'<div class="meta">'+usd(sig.notional)+' @ '+Number(sig.price).toFixed(4)+'</div></td><td><span class="pill">'+esc(sig.action)+'</span></td><td>'+esc(sig.confidence)+'</td><td>'+esc(sig.reason)+'</td><td>'+tx+'<div class="meta">'+ago(sig.detected_at)+'</div></td>';rows.appendChild(tr)}}function connect(){let ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws');ws.onopen=()=>{$('socket').textContent='socket connected';$('socket').className='pill good'};ws.onclose=()=>{$('socket').textContent='socket disconnected';$('socket').className='pill bad';setTimeout(connect,2000)};ws.onmessage=e=>render(JSON.parse(e.data))}connect();</script></body></html>'''

async def run_dashboard(state: WhaleCopyState, shutdown: asyncio.Event) -> None:
    clients: set[web.WebSocketResponse] = set()

    async def index(_request):
        return web.Response(text=HTML, content_type="text/html")

    async def ws_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        clients.add(ws)
        await ws.send_str(json.dumps(await state.snapshot()))
        try:
            async for _ in ws:
                pass
        finally:
            clients.discard(ws)
        return ws

    async def broadcaster():
        while not shutdown.is_set():
            msg = json.dumps(await state.snapshot())
            dead = []
            for ws in clients:
                try:
                    await ws.send_str(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                clients.discard(ws)
            await asyncio.sleep(2)

    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/ws", ws_handler)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    port = int(os.getenv("DASHBOARD_PORT", os.getenv("PORT", "8766")))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("whale_dashboard_started", extra={"port": port})
    task = asyncio.create_task(broadcaster())
    try:
        await shutdown.wait()
    finally:
        task.cancel()
        await runner.cleanup()


async def async_main() -> None:
    load_dotenv()
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))
    os.environ.setdefault("BOT_VARIANT", "whale-copy")
    state = WhaleCopyState()
    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown.set)
    logger.info("whale_copy_starting", extra={"live_enabled": live_enabled(), "min_notional_usd": min_notional_usd()})
    record_order(action="whale_copy_starting", market_slug="", side="", token_id="", amount=0, status="paper" if not live_enabled() else "live")
    tasks = [
        asyncio.create_task(poll_whales(state, shutdown), name="whale_poll"),
        asyncio.create_task(run_dashboard(state, shutdown), name="whale_dashboard"),
    ]
    try:
        await shutdown.wait()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
