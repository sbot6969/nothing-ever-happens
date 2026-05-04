"""Paper-only market-making order lifecycle simulator.

No network, wallets, live orders, cancellations, or transfers. This models the
states a maker bot must handle before any production quote logic is considered.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class QuoteStatus(str, Enum):
    PLACED = "placed"
    REPLACED = "replaced"
    CANCELLED = "cancelled"
    STALE = "stale"
    WOULD_FILL = "would_fill"
    MISSED_FILL = "missed_fill"


@dataclass(frozen=True)
class QuoteIntent:
    token_id: str
    side: str
    price: float
    size: float
    created_ts: int
    ttl_sec: int = 60
    queue_ahead_size: float = 0.0


@dataclass(frozen=True)
class MarketTick:
    timestamp: int
    best_bid: float
    best_ask: float
    last_trade_price: float | None = None
    last_trade_size: float = 0.0


@dataclass(frozen=True)
class QuoteEvent:
    timestamp: int
    status: QuoteStatus
    reason: str
    remaining_size: float
    filled_size: float = 0.0


def _crosses_quote(quote: QuoteIntent, tick: MarketTick) -> bool:
    side = quote.side.upper()
    if side == "BUY":
        return tick.best_ask <= quote.price
    if side == "SELL":
        return tick.best_bid >= quote.price
    return False


def _trade_reaches_quote(quote: QuoteIntent, tick: MarketTick) -> bool:
    if tick.last_trade_price is None:
        return False
    side = quote.side.upper()
    if side == "BUY":
        return tick.last_trade_price <= quote.price
    if side == "SELL":
        return tick.last_trade_price >= quote.price
    return False


def simulate_quote_lifecycle(quote: QuoteIntent, ticks: Iterable[MarketTick], *, replace_if_price_moves_bps: float = 100.0) -> list[QuoteEvent]:
    events = [QuoteEvent(quote.created_ts, QuoteStatus.PLACED, "quote_placed", quote.size)]
    remaining = quote.size
    reference_mid: float | None = None
    for tick in sorted(ticks, key=lambda row: row.timestamp):
        if tick.timestamp < quote.created_ts:
            continue
        mid = (tick.best_bid + tick.best_ask) / 2 if tick.best_bid > 0 and tick.best_ask > 0 else 0.0
        if reference_mid is None and mid > 0:
            reference_mid = mid
        if tick.timestamp - quote.created_ts > quote.ttl_sec:
            events.append(QuoteEvent(tick.timestamp, QuoteStatus.STALE, "ttl_expired", remaining))
            events.append(QuoteEvent(tick.timestamp, QuoteStatus.CANCELLED, "cancel_stale_quote", remaining))
            return events
        if reference_mid and mid:
            move_bps = abs(mid - reference_mid) / reference_mid * 10_000
            if move_bps >= replace_if_price_moves_bps:
                events.append(QuoteEvent(tick.timestamp, QuoteStatus.REPLACED, "mid_price_moved", remaining))
                return events
        if _crosses_quote(quote, tick):
            fill = min(remaining, max(0.0, tick.last_trade_size - quote.queue_ahead_size) if tick.last_trade_size else remaining)
            if fill > 0:
                remaining = max(0.0, remaining - fill)
                events.append(QuoteEvent(tick.timestamp, QuoteStatus.WOULD_FILL, "touch_or_cross_after_queue", remaining, fill))
                if remaining <= 1e-9:
                    return events
            else:
                events.append(QuoteEvent(tick.timestamp, QuoteStatus.MISSED_FILL, "queue_ahead_not_cleared", remaining))
        elif _trade_reaches_quote(quote, tick):
            events.append(QuoteEvent(tick.timestamp, QuoteStatus.MISSED_FILL, "trade_reached_price_but_not_best_quote", remaining))
    events.append(QuoteEvent(max([quote.created_ts, *[t.timestamp for t in ticks]], default=quote.created_ts), QuoteStatus.CANCELLED, "simulation_end_cancel", remaining))
    return events


def liquidity_reward_proxy(notional_quoted_usd: float, uptime_fraction: float, spread_bps: float, *, max_reward_bps: float = 5.0) -> float:
    """Tiny maker-incentive proxy for stress testing, not a real reward claim."""
    if notional_quoted_usd <= 0 or uptime_fraction <= 0:
        return 0.0
    quality = max(0.0, 1.0 - max(0.0, spread_bps) / 500.0)
    reward_bps = max_reward_bps * min(1.0, uptime_fraction) * quality
    return round(notional_quoted_usd * reward_bps / 10_000.0, 6)
