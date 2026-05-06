"""Best-effort Telegram finance notifications.

The trading hot path must never depend on Telegram delivery. This module is
therefore intentionally asynchronous-at-the-edge: callers enqueue compact events
and a daemon worker sends them either through a dedicated Telegram bot token
(`FINANCE_TG_BOT_TOKEN` + `FINANCE_TG_CHAT_ID`) or, as a fallback, through
OpenClaw messaging.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

_QUEUE: queue.Queue[dict[str, Any] | None] = queue.Queue(maxsize=256)
_WORKER: threading.Thread | None = None
_LOCK = threading.Lock()
_LAST_ERROR_SENT_AT = 0.0

_ACTIONS_DEFAULT = {
    "buy",
    "sell",
    "redeem",
    "settlement",
    "settled",
    "error",
    "feed_crashed",
    "feed_dead",
    "shutdown_complete",
    "whale_signal",
    "whale_copy_paper_trade",
    "whale_copy_live_trade",
}


def _enabled() -> bool:
    raw = os.getenv("FINANCE_TG_ENABLED", "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _target() -> str:
    return os.getenv("FINANCE_TG_TARGET", "").strip()


def _bot_token() -> str:
    return os.getenv("FINANCE_TG_BOT_TOKEN", os.getenv("TG_BOT_TOKEN", "")).strip()


def _chat_id() -> str:
    return os.getenv("FINANCE_TG_CHAT_ID", os.getenv("TG_CHAT_ID", "")).strip()


def _thread_id() -> str:
    return os.getenv("FINANCE_TG_THREAD_ID", os.getenv("TG_THREAD_ID", "")).strip()


def _has_destination() -> bool:
    return bool((_bot_token() and _chat_id()) or _target())


def _channel() -> str:
    return os.getenv("FINANCE_TG_CHANNEL", "telegram").strip() or "telegram"


def _account() -> str:
    return os.getenv("FINANCE_TG_ACCOUNT", "").strip()


def _bot_name() -> str:
    return os.getenv("BOT_VARIANT", os.getenv("BOT_INSTANCE", "polymarket-bot")).strip() or "polymarket-bot"


def _actions() -> set[str]:
    raw = os.getenv("FINANCE_TG_ACTIONS", "").strip()
    if not raw:
        return set(_ACTIONS_DEFAULT)
    return {part.strip() for part in raw.split(",") if part.strip()}


def _fmt_usd(value: Any) -> str:
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "--"


def _compact(value: Any, limit: int = 96) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _format_message(record: dict[str, Any]) -> str:
    bot = _bot_name()
    action = str(record.get("action") or record.get("event") or "event")
    slug = _compact(record.get("market_slug") or record.get("slug") or "")
    side = str(record.get("side") or "")
    amount = _fmt_usd(record.get("amount") or record.get("spent_usd") or record.get("notional"))
    price = record.get("reference_price") or record.get("price") or record.get("fill_price")
    status = record.get("order_status") or record.get("status") or ""
    error = record.get("error") or ""
    pnl = record.get("pnl_usd")

    icon = "ℹ️"
    if action in {"buy", "whale_copy_live_trade"}:
        icon = "🟢"
    elif action in {"sell", "redeem", "settlement", "settled"}:
        icon = "🔵"
    elif action in {"error", "feed_crashed", "feed_dead"} or error:
        icon = "🔴"
    elif action.startswith("whale_"):
        icon = "🐋"

    lines = [f"{icon} {bot}: {action}"]
    if slug:
        lines.append(f"market: {slug}")
    if side:
        lines.append(f"side: {side}")
    if amount != "--":
        lines.append(f"amount: {amount}")
    if price:
        try:
            lines.append(f"price: {float(price):.4f}")
        except Exception:
            lines.append(f"price: {price}")
    if pnl is not None:
        lines.append(f"PnL: {_fmt_usd(pnl)}")
    if status:
        lines.append(f"status: {_compact(status)}")
    if error:
        lines.append(f"error: {_compact(error, 160)}")
    if record.get("wallet"):
        lines.append(f"wallet: {_compact(record.get('wallet'), 48)}")
    if record.get("confidence") is not None:
        lines.append(f"confidence: {record.get('confidence')}")
    return "\n".join(lines)


def _send_message(text: str) -> None:
    token = _bot_token()
    chat_id = _chat_id()
    if token and chat_id:
        payload = {"chat_id": chat_id, "text": text}
        thread_id = _thread_id()
        if thread_id:
            payload["message_thread_id"] = thread_id
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - configured Telegram Bot API endpoint
            resp.read()
        return

    target = _target()
    if not target:
        return
    cmd = ["openclaw", "message", "send", "--channel", _channel(), "--target", target, "--message", text]
    account = _account()
    if account:
        cmd.extend(["--account", account])
    subprocess.run(cmd, timeout=15, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _worker() -> None:
    while True:
        item = _QUEUE.get()
        try:
            if item is None:
                return
            _send_message(_format_message(item))
        except Exception as exc:
            logger.debug("finance_notifier_send_failed: %s", exc)
        finally:
            _QUEUE.task_done()


def _ensure_worker() -> None:
    global _WORKER
    if _WORKER is not None and _WORKER.is_alive():
        return
    with _LOCK:
        if _WORKER is not None and _WORKER.is_alive():
            return
        _WORKER = threading.Thread(target=_worker, name="finance-notifier", daemon=True)
        _WORKER.start()


def notify_event(record: dict[str, Any]) -> None:
    """Queue a finance notification if enabled/configured and action is wanted."""
    if not _enabled() or not _has_destination():
        return
    action = str(record.get("action") or record.get("event") or "")
    if action not in _actions():
        return

    # Avoid spamming identical hot-loop errors.
    global _LAST_ERROR_SENT_AT
    if action == "error":
        now = time.time()
        min_gap = float(os.getenv("FINANCE_TG_ERROR_MIN_GAP_SEC", "30"))
        if now - _LAST_ERROR_SENT_AT < min_gap:
            return
        _LAST_ERROR_SENT_AT = now

    _ensure_worker()
    try:
        _QUEUE.put_nowait(dict(record))
    except queue.Full:
        logger.debug("finance_notifier_queue_full")
