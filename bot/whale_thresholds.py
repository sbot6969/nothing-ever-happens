"""Pure whale-candidate threshold helpers.

Safety: this module only classifies cached/observed public trade rows. It never
submits orders, touches wallets, or reads secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ABSOLUTE_WHALE_NOTIONAL_USD = 10_000.0
RELATIVE_WHALE_FRACTION = 0.30
RELATIVE_MARKET_SIZE_GUARD_USD = 10_000.0


@dataclass(frozen=True)
class WhaleClassification:
    is_whale: bool
    reason: str
    notional_usd: float
    market_size_usd: float | None = None
    relative_market_fraction: float | None = None


def to_non_negative_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def trade_notional_usd(trade: dict[str, Any]) -> float:
    explicit = to_non_negative_float(
        trade.get("notional")
        or trade.get("notional_usd")
        or trade.get("notionalUsd")
        or trade.get("amount_usd")
        or trade.get("amountUsd")
    )
    if explicit is not None:
        return explicit
    size = to_non_negative_float(trade.get("size")) or 0.0
    price = to_non_negative_float(trade.get("price")) or 0.0
    return size * price


def market_size_usd(trade: dict[str, Any]) -> float | None:
    for key in (
        "market_size_usd",
        "marketSizeUsd",
        "market_size",
        "marketSize",
        "market_volume_usd",
        "marketVolumeUsd",
        "liquidity_usd",
        "liquidityUsd",
    ):
        parsed = to_non_negative_float(trade.get(key))
        if parsed is not None:
            return parsed
    return None


def classify_whale_trade(
    trade: dict[str, Any],
    *,
    absolute_notional_usd: float = ABSOLUTE_WHALE_NOTIONAL_USD,
    relative_fraction: float = RELATIVE_WHALE_FRACTION,
    relative_market_size_guard_usd: float = RELATIVE_MARKET_SIZE_GUARD_USD,
) -> WhaleClassification:
    """Classify a trade using the required whale rules.

    A trade is a whale candidate if either:
    - trade notional >= $10,000, OR
    - trade notional >= 30% of market size, with market size >= $10,000.
    """
    notional = trade_notional_usd(trade)
    market_size = market_size_usd(trade)
    relative = (notional / market_size) if market_size and market_size > 0 else None

    if notional >= absolute_notional_usd:
        return WhaleClassification(
            is_whale=True,
            reason="absolute_notional_threshold",
            notional_usd=notional,
            market_size_usd=market_size,
            relative_market_fraction=relative,
        )

    if (
        market_size is not None
        and market_size >= relative_market_size_guard_usd
        and relative is not None
        and relative >= relative_fraction
    ):
        return WhaleClassification(
            is_whale=True,
            reason="relative_market_size_threshold",
            notional_usd=notional,
            market_size_usd=market_size,
            relative_market_fraction=relative,
        )

    return WhaleClassification(
        is_whale=False,
        reason="below_whale_threshold",
        notional_usd=notional,
        market_size_usd=market_size,
        relative_market_fraction=relative,
    )
