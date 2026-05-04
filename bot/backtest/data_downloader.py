"""Offline historical data downloader for whale-copy backtests.

Downloads public Polymarket Gamma/Data API snapshots only. It never reads
wallet secrets and never submits orders. Artifacts are intended for ignored
local directories such as ``artifacts/whale_copy``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0 (compatible; neh-whale-copy-backtest/1.0)"
GAMMA_MARKETS = "https://gamma-api.polymarket.com/markets"
DATA_TRADES = "https://data-api.polymarket.com/trades"


@dataclass(frozen=True)
class DownloadManifest:
    created_at: str
    market_limit: int
    trades_per_market: int
    markets_saved: int
    trades_saved: int
    resolution_assets: int
    notes: list[str]


@dataclass(frozen=True)
class BacktestProvenance:
    """Primary-source fields used to enrich an offline public snapshot."""

    market_size_source: str
    market_size_field: str
    liquidity_source: str
    liquidity_field: str
    trades_source: str
    resolution_source: str


PUBLIC_BACKTEST_PROVENANCE = BacktestProvenance(
    market_size_source="Polymarket Gamma API closed-market volumeNum",
    market_size_field="market_volume_usd",
    liquidity_source="Polymarket Gamma API closed-market liquidityNum when positive",
    liquidity_field="liquidity_usd",
    trades_source="Polymarket Data API /trades market=<conditionId>",
    resolution_source="Polymarket Gamma API closed-market outcomePrices/clobTokenIds settled at 0/1",
)


def _fetch_json(url: str, *, timeout: float = 30.0, attempts: int = 3, backoff_sec: float = 1.0) -> Any:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            with urlopen(req, timeout=timeout) as resp:  # nosec B310 - fixed public HTTPS endpoints
                return json.load(resp)
        except HTTPError as exc:
            last_error = exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
            delay = float(retry_after) if retry_after and retry_after.isdigit() else backoff_sec * (2**attempt)
            time.sleep(min(delay, 30.0))
        except (TimeoutError, URLError) as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise
            time.sleep(min(backoff_sec * (2**attempt), 30.0))
    if last_error:
        raise last_error
    raise RuntimeError("fetch failed without an exception")


def _loads_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _market_resolution(market: dict[str, Any]) -> dict[str, dict[str, float]]:
    token_ids = [str(x) for x in _loads_json_list(market.get("clobTokenIds"))]
    prices = [_as_float(x) for x in _loads_json_list(market.get("outcomePrices"))]
    if len(token_ids) != len(prices) or not token_ids:
        return {}
    # Closed Polymarket binary markets generally settle at prices 0/1.
    # Skip ambiguous/unsettled rows (e.g. 50/50 or stale non-binary prices).
    if not all(price in {0.0, 1.0} for price in prices):
        return {}
    return {token: {"payout": price} for token, price in zip(token_ids, prices)}


def fetch_closed_markets(limit: int) -> list[dict[str, Any]]:
    qs = urlencode({"limit": limit, "closed": "true", "order": "endDate", "ascending": "false"})
    data = _fetch_json(f"{GAMMA_MARKETS}?{qs}")
    if not isinstance(data, list):
        raise ValueError("Gamma markets response was not a JSON array")
    return [m for m in data if isinstance(m, dict)]


def fetch_market_trades(condition_id: str, limit: int) -> list[dict[str, Any]]:
    qs = urlencode({"limit": limit, "market": condition_id})
    data = _fetch_json(f"{DATA_TRADES}?{qs}")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict) and str(row.get("conditionId") or "") == condition_id]


def build_snapshot(*, market_limit: int, trades_per_market: int, sleep_sec: float = 0.05) -> dict[str, Any]:
    raw_markets = fetch_closed_markets(market_limit)
    markets: list[dict[str, Any]] = []
    resolutions: dict[str, dict[str, float]] = {}
    trades: list[dict[str, Any]] = []
    seen_trade_keys: set[str] = set()
    wallet_seen_count: dict[str, int] = {}

    for market in raw_markets:
        condition_id = str(market.get("conditionId") or "")
        market_resolutions = _market_resolution(market)
        if not condition_id or not market_resolutions:
            continue
        meta = {
            "conditionId": condition_id,
            "slug": str(market.get("slug") or ""),
            "question": str(market.get("question") or market.get("title") or ""),
            "category": str(market.get("category") or ""),
            "volumeNum": _as_float(market.get("volumeNum") or market.get("volume")),
            "liquidityNum": _as_float(market.get("liquidityNum") or market.get("liquidity")),
            "closedTime": str(market.get("closedTime") or market.get("endDate") or ""),
        }
        market_trades = fetch_market_trades(condition_id, trades_per_market)
        if sleep_sec:
            time.sleep(sleep_sec)
        if not market_trades:
            continue
        markets.append(meta)
        resolutions.update(market_resolutions)
        for row in sorted(market_trades, key=lambda r: int(float(r.get("timestamp") or 0))):
            key = f"{row.get('transactionHash') or 'no-tx'}:{row.get('asset') or ''}:{row.get('timestamp') or ''}"
            if key in seen_trade_keys:
                continue
            seen_trade_keys.add(key)
            wallet = str(row.get("proxyWallet") or row.get("user") or "").lower()
            wallet_seen_count[wallet] = wallet_seen_count.get(wallet, 0) + 1
            enriched = dict(row)
            enriched["history_count"] = wallet_seen_count[wallet]
            enriched["market_category"] = meta["category"]
            enriched["market_volume_usd"] = meta["volumeNum"]
            enriched["market_size_usd"] = meta["volumeNum"]
            enriched["market_size_source"] = PUBLIC_BACKTEST_PROVENANCE.market_size_source
            # Closed markets often report current liquidity as 0 after settlement.
            # Do not turn that into a zero executable-size cap; keep the field absent
            # unless Gamma reports positive liquidity. Volume remains available as
            # a coarse historical activity proxy.
            if meta["liquidityNum"] > 0:
                enriched["liquidity_usd"] = meta["liquidityNum"]
                enriched["liquidity_source"] = PUBLIC_BACKTEST_PROVENANCE.liquidity_source
            trades.append(enriched)

    return {"markets": markets, "trades": trades, "resolutions": resolutions}


def write_snapshot(snapshot: dict[str, Any], out_dir: Path, *, market_limit: int, trades_per_market: int) -> DownloadManifest:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "markets.json").write_text(json.dumps(snapshot["markets"], indent=2, sort_keys=True) + "\n")
    (out_dir / "trades.json").write_text(json.dumps(snapshot["trades"], indent=2, sort_keys=True) + "\n")
    (out_dir / "resolutions.json").write_text(json.dumps(snapshot["resolutions"], indent=2, sort_keys=True) + "\n")
    manifest = DownloadManifest(
        created_at=datetime.now(timezone.utc).isoformat(),
        market_limit=market_limit,
        trades_per_market=trades_per_market,
        markets_saved=len(snapshot["markets"]),
        trades_saved=len(snapshot["trades"]),
        resolution_assets=len(snapshot["resolutions"]),
        notes=[
            "Public Gamma closed markets + Data API trades only; no private data or live trading.",
            "history_count is first-visible within this downloaded snapshot, not proof of wallet's entire Polymarket lifetime.",
            "Closed markets with non-0/1 outcome prices are skipped as unresolved/ambiguous.",
            f"market_size_usd uses {PUBLIC_BACKTEST_PROVENANCE.market_size_source}; it is a historical activity proxy, not current executable depth.",
        ],
    )
    (out_dir / "manifest.json").write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n")
    return manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download public Polymarket history for offline whale-copy backtests")
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts/whale_copy/latest"))
    parser.add_argument("--market-limit", type=int, default=50)
    parser.add_argument("--trades-per-market", type=int, default=200)
    parser.add_argument("--sleep-sec", type=float, default=0.05)
    return parser


def _bounded_int(value: int, *, name: str, min_value: int, max_value: int) -> int:
    if not min_value <= value <= max_value:
        raise ValueError(f"{name} must be between {min_value} and {max_value}")
    return value


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    market_limit = _bounded_int(args.market_limit, name="market_limit", min_value=1, max_value=500)
    trades_per_market = _bounded_int(args.trades_per_market, name="trades_per_market", min_value=1, max_value=1000)
    if not 0 <= args.sleep_sec <= 10:
        raise ValueError("sleep_sec must be between 0 and 10")
    snapshot = build_snapshot(market_limit=market_limit, trades_per_market=trades_per_market, sleep_sec=args.sleep_sec)
    manifest = write_snapshot(snapshot, args.out_dir, market_limit=market_limit, trades_per_market=trades_per_market)
    print(json.dumps(asdict(manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
