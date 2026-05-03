"""Deterministic whale-copy backtest simulator.

This module is intentionally offline-only: it accepts cached JSON inputs and
never submits orders, creates wallets, closes positions, or touches live funds.
It models explicit spread/slippage/liquidity/gas costs so PnL claims are
reproducible from fixtures or artifact snapshots.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class WhaleBacktestConfig:
    min_whale_notional_usd: float = 250.0
    copy_fraction: float = 0.10
    max_copy_notional_usd: float = 25.0
    max_history_count: int = 1
    spread_bps: float = 50.0
    slippage_bps: float = 75.0
    max_liquidity_fraction: float = 0.10
    gas_cost_usd: float = 0.02
    explicit_fee_bps: float = 0.0
    ignore_before_ts: int | None = None
    max_signal_age_sec: int | None = None


@dataclass(frozen=True)
class BacktestConfig:
    """Compatibility config for the first whale-copy backtest tests.

    New code should prefer ``WhaleBacktestConfig``; this keeps the original
    lightweight API stable for existing tests and notebooks.
    """

    min_notional_usd: float = 250.0
    copy_fraction: float = 0.10
    max_copy_notional_usd: float = 25.0
    max_history_count: int = 1
    slippage_bps: float = 75.0


@dataclass(frozen=True)
class LegacyFill:
    slug: str
    wallet: str
    outcome: str
    entry_price: float
    copy_notional: float
    shares: float
    payout: float
    pnl: float


@dataclass(frozen=True)
class WhaleTrade:
    wallet: str
    side: str
    asset: str
    timestamp: int
    size: float
    price: float
    title: str = ""
    slug: str = ""
    outcome: str = ""
    tx: str = ""
    history_count: int = 1
    liquidity_usd: float | None = None

    @property
    def notional(self) -> float:
        return self.size * self.price


@dataclass(frozen=True)
class Resolution:
    asset: str
    payout: float


@dataclass(frozen=True)
class SimulatedCopy:
    trade_key: str
    wallet: str
    asset: str
    slug: str
    timestamp: int
    whale_notional_usd: float
    copy_notional_usd: float
    execution_price: float
    shares: float
    payout_per_share: float
    exit_value_usd: float
    fees_usd: float
    gas_usd: float
    pnl_usd: float
    roi_pct: float
    reason: str


@dataclass(frozen=True)
class RejectedSignal:
    trade_key: str
    reason: str


@dataclass(frozen=True)
class BacktestResult:
    trades_seen: int
    unique_trades_seen: int
    copied: list[SimulatedCopy]
    rejected: list[RejectedSignal]
    total_copy_notional_usd: float
    total_pnl_usd: float
    roi_pct: float
    hit_rate_pct: float
    max_drawdown_usd: float


class TradeValidationError(ValueError):
    """Raised when a cached Polymarket trade row is malformed."""


def adjusted_entry_price(price: float, side: str, slippage_bps: float) -> float:
    """Return conservative copied-entry price for legacy simulations."""
    side = str(side).upper()
    multiplier = 1.0 + (slippage_bps / 10_000.0) if side == "BUY" else 1.0 - (slippage_bps / 10_000.0)
    return max(0.001, min(0.999, float(price) * multiplier))


def select_signals(
    trades: Iterable[dict[str, Any]],
    wallet_history: dict[str, int],
    cfg: BacktestConfig | None = None,
) -> list[dict[str, Any]]:
    """Select first-visible large BUY whale signals from cached trade rows."""
    cfg = cfg or BacktestConfig()
    signals: list[dict[str, Any]] = []
    seen: set[str] = set()
    for trade in sorted(trades, key=lambda row: int(row.get("timestamp") or 0)):
        key = str(trade.get("transactionHash") or "") + ":" + str(trade.get("asset") or "") + ":" + str(trade.get("timestamp") or "")
        if key in seen:
            continue
        seen.add(key)
        if str(trade.get("side") or "").upper() != "BUY":
            continue
        wallet = str(trade.get("proxyWallet") or trade.get("user") or "").lower().strip()
        history_count = int(wallet_history.get(wallet, trade.get("history_count", trade.get("historyCount", 99))))
        if history_count > cfg.max_history_count:
            continue
        notional = float(trade.get("size") or 0.0) * float(trade.get("price") or 0.0)
        if notional < cfg.min_notional_usd:
            continue
        signals.append(trade)
    return signals


def simulate(
    trades: Iterable[dict[str, Any]],
    resolved_outcomes_by_slug: dict[str, str],
    wallet_history: dict[str, int],
    cfg: BacktestConfig | None = None,
) -> tuple[list[LegacyFill], dict[str, float]]:
    """Small legacy simulator used by existing tests.

    This is intentionally deterministic and offline. It applies slippage to the
    copied BUY entry and resolves to 1/0 based on cached outcome labels.
    """
    cfg = cfg or BacktestConfig()
    fills: list[LegacyFill] = []
    total_notional = 0.0
    total_pnl = 0.0
    for trade in select_signals(trades, wallet_history, cfg):
        price = float(trade.get("price") or 0.0)
        entry = adjusted_entry_price(price, str(trade.get("side") or "BUY"), cfg.slippage_bps)
        whale_notional = float(trade.get("size") or 0.0) * price
        copy_notional = min(cfg.max_copy_notional_usd, whale_notional * cfg.copy_fraction)
        shares = copy_notional / entry if entry > 0 else 0.0
        slug = str(trade.get("slug") or trade.get("eventSlug") or "")
        outcome = str(trade.get("outcome") or "")
        payout = 1.0 if resolved_outcomes_by_slug.get(slug) == outcome else 0.0
        pnl = shares * payout - copy_notional
        fills.append(
            LegacyFill(
                slug=slug,
                wallet=str(trade.get("proxyWallet") or trade.get("user") or ""),
                outcome=outcome,
                entry_price=entry,
                copy_notional=copy_notional,
                shares=shares,
                payout=payout,
                pnl=pnl,
            )
        )
        total_notional += copy_notional
        total_pnl += pnl
    roi = (total_pnl / total_notional) if total_notional else 0.0
    return fills, {"pnl": total_pnl, "notional": total_notional, "roi": roi}


def _as_float(value: Any, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise TradeValidationError(f"invalid {field}: {value!r}") from exc
    if parsed < 0:
        raise TradeValidationError(f"{field} must be non-negative")
    return parsed


def _as_int(value: Any, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TradeValidationError(f"invalid {field}: {value!r}") from exc
    if parsed < 0:
        raise TradeValidationError(f"{field} must be non-negative")
    return parsed


def parse_trade_row(row: dict[str, Any]) -> WhaleTrade:
    """Parse and validate a Polymarket Data API trade row.

    Expected source fields mirror ``https://data-api.polymarket.com/trades``:
    ``proxyWallet``, ``side``, ``asset``, ``size``, ``price``, ``timestamp``,
    plus optional ``transactionHash``, ``slug``/``eventSlug`` and metadata.
    """
    if not isinstance(row, dict):
        raise TradeValidationError("trade row must be a dict")

    wallet = str(row.get("proxyWallet") or row.get("user") or "").lower().strip()
    if not (wallet.startswith("0x") and len(wallet) == 42):
        raise TradeValidationError("missing or invalid wallet field")

    side = str(row.get("side") or "").upper().strip()
    if side not in {"BUY", "SELL"}:
        raise TradeValidationError("side must be BUY or SELL")

    asset = str(row.get("asset") or "").strip()
    if not asset:
        raise TradeValidationError("missing asset")

    size = _as_float(row.get("size"), "size")
    price = _as_float(row.get("price"), "price")
    if price <= 0 or price >= 1:
        raise TradeValidationError("price must be between 0 and 1")

    timestamp = _as_int(row.get("timestamp"), "timestamp")
    history_count = _as_int(row.get("history_count", row.get("historyCount", 1)), "history_count")
    liquidity_raw = row.get("liquidity_usd", row.get("liquidityUsd"))
    liquidity_usd = None if liquidity_raw is None else _as_float(liquidity_raw, "liquidity_usd")

    return WhaleTrade(
        wallet=wallet,
        side=side,
        asset=asset,
        timestamp=timestamp,
        size=size,
        price=price,
        title=str(row.get("title") or ""),
        slug=str(row.get("eventSlug") or row.get("slug") or ""),
        outcome=str(row.get("outcome") or ""),
        tx=str(row.get("transactionHash") or ""),
        history_count=history_count,
        liquidity_usd=liquidity_usd,
    )


def trade_dedupe_key(trade: WhaleTrade) -> str:
    """Stable dedupe key: transaction hash + asset + timestamp when possible."""
    tx = trade.tx or "no-tx"
    return f"{tx}:{trade.asset}:{trade.timestamp}"


def is_first_visible_whale(trade: WhaleTrade, config: WhaleBacktestConfig) -> bool:
    return trade.history_count <= config.max_history_count


def _rejection_reason(trade: WhaleTrade, config: WhaleBacktestConfig, now_ts: int | None) -> str | None:
    if trade.side != "BUY":
        return "non_buy_trade"
    if trade.notional < config.min_whale_notional_usd:
        return "below_min_notional"
    if not is_first_visible_whale(trade, config):
        return "prior_wallet_history"
    if config.ignore_before_ts is not None and trade.timestamp <= config.ignore_before_ts:
        return "startup_bootstrap_trade"
    if now_ts is not None and config.max_signal_age_sec is not None:
        if now_ts - trade.timestamp > config.max_signal_age_sec:
            return "stale_signal"
    return None


def _execution_price(observed_price: float, config: WhaleBacktestConfig) -> float:
    cost = (config.spread_bps + config.slippage_bps) / 10_000.0
    return min(0.999, observed_price * (1.0 + cost))


def _copy_notional(trade: WhaleTrade, config: WhaleBacktestConfig) -> float:
    desired = min(config.max_copy_notional_usd, trade.notional * config.copy_fraction)
    if trade.liquidity_usd is not None:
        desired = min(desired, trade.liquidity_usd * config.max_liquidity_fraction)
    return max(0.0, desired)


def run_backtest(
    trade_rows: Iterable[dict[str, Any]],
    resolutions: dict[str, Resolution],
    config: WhaleBacktestConfig | None = None,
    *,
    now_ts: int | None = None,
) -> BacktestResult:
    """Run a deterministic event-driven whale-copy simulation."""
    config = config or WhaleBacktestConfig()
    parsed: list[WhaleTrade] = []
    rejected: list[RejectedSignal] = []
    seen: set[str] = set()

    for row in trade_rows:
        try:
            trade = parse_trade_row(row)
        except TradeValidationError as exc:
            rejected.append(RejectedSignal(trade_key="invalid", reason=str(exc)))
            continue
        parsed.append(trade)

    copied: list[SimulatedCopy] = []
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0

    for trade in sorted(parsed, key=lambda t: t.timestamp):
        key = trade_dedupe_key(trade)
        if key in seen:
            rejected.append(RejectedSignal(trade_key=key, reason="duplicate_trade"))
            continue
        seen.add(key)

        reason = _rejection_reason(trade, config, now_ts)
        if reason:
            rejected.append(RejectedSignal(trade_key=key, reason=reason))
            continue

        resolution = resolutions.get(trade.asset)
        if resolution is None:
            rejected.append(RejectedSignal(trade_key=key, reason="missing_resolution"))
            continue

        copy_notional = _copy_notional(trade, config)
        if copy_notional <= 0:
            rejected.append(RejectedSignal(trade_key=key, reason="liquidity_cap_zero"))
            continue

        execution_price = _execution_price(trade.price, config)
        shares = copy_notional / execution_price
        explicit_fees = copy_notional * (config.explicit_fee_bps / 10_000.0)
        exit_value = shares * max(0.0, min(1.0, resolution.payout))
        pnl = exit_value - copy_notional - explicit_fees - config.gas_cost_usd
        roi = (pnl / copy_notional * 100.0) if copy_notional else 0.0

        copied.append(
            SimulatedCopy(
                trade_key=key,
                wallet=trade.wallet,
                asset=trade.asset,
                slug=trade.slug,
                timestamp=trade.timestamp,
                whale_notional_usd=round(trade.notional, 6),
                copy_notional_usd=round(copy_notional, 6),
                execution_price=round(execution_price, 6),
                shares=round(shares, 6),
                payout_per_share=resolution.payout,
                exit_value_usd=round(exit_value, 6),
                fees_usd=round(explicit_fees, 6),
                gas_usd=round(config.gas_cost_usd, 6),
                pnl_usd=round(pnl, 6),
                roi_pct=round(roi, 6),
                reason="first_visible_large_buy",
            )
        )
        equity += pnl
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity - peak)

    total_notional = sum(copy.copy_notional_usd for copy in copied)
    total_pnl = sum(copy.pnl_usd for copy in copied)
    hit_rate = (sum(1 for copy in copied if copy.pnl_usd > 0) / len(copied) * 100.0) if copied else 0.0
    roi_pct = (total_pnl / total_notional * 100.0) if total_notional else 0.0
    return BacktestResult(
        trades_seen=len(parsed),
        unique_trades_seen=len(seen),
        copied=copied,
        rejected=rejected,
        total_copy_notional_usd=round(total_notional, 6),
        total_pnl_usd=round(total_pnl, 6),
        roi_pct=round(roi_pct, 6),
        hit_rate_pct=round(hit_rate, 6),
        max_drawdown_usd=round(abs(max_drawdown), 6),
    )


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_resolutions(path: Path) -> dict[str, Resolution]:
    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise ValueError("resolution file must be a JSON object keyed by asset")
    resolutions: dict[str, Resolution] = {}
    for asset, value in raw.items():
        if isinstance(value, dict):
            payout = _as_float(value.get("payout"), f"resolution[{asset}].payout")
        else:
            payout = _as_float(value, f"resolution[{asset}]")
        resolutions[str(asset)] = Resolution(asset=str(asset), payout=max(0.0, min(1.0, payout)))
    return resolutions


def result_to_dict(result: BacktestResult) -> dict[str, Any]:
    return asdict(result)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run offline whale-copy backtest")
    parser.add_argument("--trades", required=True, type=Path, help="Cached Data API trades JSON array")
    parser.add_argument("--resolutions", required=True, type=Path, help="Asset payout JSON object")
    parser.add_argument("--out", type=Path, help="Optional output JSON report path")
    parser.add_argument("--min-notional", type=float, default=250.0)
    parser.add_argument("--copy-fraction", type=float, default=0.10)
    parser.add_argument("--max-copy", type=float, default=25.0)
    parser.add_argument("--spread-bps", type=float, default=50.0)
    parser.add_argument("--slippage-bps", type=float, default=75.0)
    parser.add_argument("--gas-cost", type=float, default=0.02)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    trades = _load_json(args.trades)
    if not isinstance(trades, list):
        raise ValueError("trades file must be a JSON array")
    config = WhaleBacktestConfig(
        min_whale_notional_usd=args.min_notional,
        copy_fraction=args.copy_fraction,
        max_copy_notional_usd=args.max_copy,
        spread_bps=args.spread_bps,
        slippage_bps=args.slippage_bps,
        gas_cost_usd=args.gas_cost,
    )
    result = run_backtest(trades, _load_resolutions(args.resolutions), config)
    payload = result_to_dict(result)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
