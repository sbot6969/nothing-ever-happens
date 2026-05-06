#!/usr/bin/env python3
"""Build a two-year top-100 Polymarket public snapshot and run all bot backtests.

Paper/offline only. Uses public Gamma/Data APIs and cached artifacts; never reads
wallet secrets and never submits orders.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import urlencode

from bot.backtest.data_downloader import (
    GAMMA_MARKETS,
    DATA_TRADES,
    PUBLIC_BACKTEST_PROVENANCE,
    DownloadManifest,
    _as_float,
    _fetch_json,
    _market_resolution,
)
from bot.backtest.multistrategy_report import generate_report


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fetch_top_closed_candidates(limit: int) -> list[dict[str, Any]]:
    qs = urlencode({"limit": limit, "closed": "true", "order": "volumeNum", "ascending": "false"})
    data = _fetch_json(f"{GAMMA_MARKETS}?{qs}", timeout=45, attempts=4, backoff_sec=2)
    if not isinstance(data, list):
        raise ValueError("Gamma markets response was not a JSON array")
    return [row for row in data if isinstance(row, dict)]


def _fetch_market_trades_paginated(condition_id: str, *, per_page: int, max_trades: int, sleep_sec: float) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    offset = 0
    seen: set[tuple[str, str, str]] = set()
    while len(trades) < max_trades:
        limit = min(per_page, max_trades - len(trades))
        qs = urlencode({"limit": limit, "offset": offset, "market": condition_id})
        data = _fetch_json(f"{DATA_TRADES}?{qs}", timeout=45, attempts=4, backoff_sec=2)
        if not isinstance(data, list) or not data:
            break
        added = 0
        for row in data:
            if not isinstance(row, dict) or str(row.get("conditionId") or "") != condition_id:
                continue
            key = (str(row.get("transactionHash") or "no-tx"), str(row.get("asset") or ""), str(row.get("timestamp") or ""))
            if key in seen:
                continue
            seen.add(key)
            trades.append(row)
            added += 1
        if len(data) < limit or added == 0:
            break
        offset += len(data)
        if sleep_sec:
            time.sleep(sleep_sec)
    return trades


def build_two_year_top100_snapshot(
    *,
    target_markets: int,
    candidate_limit: int,
    max_trades_per_market: int,
    page_size: int,
    sleep_sec: float,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=365 * 2)
    candidates = _fetch_top_closed_candidates(candidate_limit)
    markets: list[dict[str, Any]] = []
    resolutions: dict[str, dict[str, float]] = {}
    raw_trades: list[tuple[dict[str, Any], dict[str, Any]]] = []
    skipped: list[dict[str, Any]] = []

    for market in candidates:
        if len(markets) >= target_markets:
            break
        condition_id = str(market.get("conditionId") or "")
        closed_dt = _parse_dt(market.get("closedTime") or market.get("endDate"))
        market_resolutions = _market_resolution(market)
        if not condition_id:
            skipped.append({"slug": market.get("slug"), "reason": "missing_condition_id"})
            continue
        if closed_dt is None or closed_dt < start or closed_dt > now:
            skipped.append({"slug": market.get("slug"), "reason": "outside_two_year_window", "closed": str(market.get("closedTime") or market.get("endDate") or "")})
            continue
        if not market_resolutions:
            skipped.append({"slug": market.get("slug"), "reason": "unresolved_or_non_binary"})
            continue
        trades = _fetch_market_trades_paginated(
            condition_id,
            per_page=page_size,
            max_trades=max_trades_per_market,
            sleep_sec=sleep_sec,
        )
        if sleep_sec:
            time.sleep(sleep_sec)
        if not trades:
            skipped.append({"slug": market.get("slug"), "reason": "no_public_trades"})
            continue
        meta = {
            "conditionId": condition_id,
            "slug": str(market.get("slug") or ""),
            "question": str(market.get("question") or market.get("title") or ""),
            "category": str(market.get("category") or ""),
            "volumeNum": _as_float(market.get("volumeNum") or market.get("volume")),
            "liquidityNum": _as_float(market.get("liquidityNum") or market.get("liquidity")),
            "closedTime": str(market.get("closedTime") or market.get("endDate") or ""),
            "rank_by_volume_in_candidate_set": len(markets) + 1,
            "trades_downloaded": len(trades),
        }
        markets.append(meta)
        resolutions.update(market_resolutions)
        for trade in trades:
            raw_trades.append((meta, trade))

    # Global chronological order makes history_count closer to a real two-year
    # wallet-seen counter instead of per-market ordering.
    wallet_seen_count: dict[str, int] = {}
    enriched_trades: list[dict[str, Any]] = []
    for meta, row in sorted(raw_trades, key=lambda pair: int(float(pair[1].get("timestamp") or 0))):
        wallet = str(row.get("proxyWallet") or row.get("user") or "").lower()
        wallet_seen_count[wallet] = wallet_seen_count.get(wallet, 0) + 1
        enriched = dict(row)
        enriched["history_count"] = wallet_seen_count[wallet]
        enriched["market_category"] = meta["category"]
        enriched["market_volume_usd"] = meta["volumeNum"]
        enriched["market_size_usd"] = meta["volumeNum"]
        enriched["market_size_source"] = PUBLIC_BACKTEST_PROVENANCE.market_size_source + " top-100-by-volume two-year snapshot"
        if meta["liquidityNum"] > 0:
            enriched["liquidity_usd"] = meta["liquidityNum"]
            enriched["liquidity_source"] = PUBLIC_BACKTEST_PROVENANCE.liquidity_source
        enriched_trades.append(enriched)

    return {
        "markets": markets,
        "trades": enriched_trades,
        "resolutions": resolutions,
        "skipped_markets": skipped,
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "candidate_limit": candidate_limit,
        "target_markets": target_markets,
        "max_trades_per_market": max_trades_per_market,
    }


def write_snapshot(snapshot: dict[str, Any], out_dir: Path) -> DownloadManifest:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("markets", "trades", "resolutions", "skipped_markets"):
        (out_dir / f"{name}.json").write_text(json.dumps(snapshot[name], indent=2, sort_keys=True) + "\n")
    manifest = DownloadManifest(
        created_at=datetime.now(timezone.utc).isoformat(),
        market_limit=int(snapshot["target_markets"]),
        trades_per_market=int(snapshot["max_trades_per_market"]),
        markets_saved=len(snapshot["markets"]),
        trades_saved=len(snapshot["trades"]),
        resolution_assets=len(snapshot["resolutions"]),
        notes=[
            "Public Gamma/Data API paper-only snapshot; no secrets, wallets, or live trading paths used.",
            f"Two-year window: {snapshot['window_start']} to {snapshot['window_end']}.",
            f"Selected top markets by Gamma volumeNum from {snapshot['candidate_limit']} closed-market candidates; target top markets saved: {snapshot['target_markets']}.",
            f"Trades are paginated from Data API with max {snapshot['max_trades_per_market']} rows per market, then globally sorted by timestamp.",
            "history_count is first-visible within this downloaded two-year snapshot, not proof of wallet lifetime outside the snapshot.",
            "Market-making and AMM results remain trade-snapshot proxy backtests without historical L2 order book queue/depth.",
        ],
    )
    (out_dir / "manifest.json").write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts/whale_copy/top100_two_year"))
    parser.add_argument("--target-markets", type=int, default=100)
    parser.add_argument("--candidate-limit", type=int, default=500)
    parser.add_argument("--max-trades-per-market", type=int, default=2000)
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--sleep-sec", type=float, default=0.05)
    parser.add_argument("--out-md", type=Path, default=Path("docs/polymarket_multi_bot/BACKTEST_RESULTS_TOP100_2Y.md"))
    parser.add_argument("--out-json", type=Path, default=Path("artifacts/whale_copy/top100_two_year/multistrategy_report.json"))
    args = parser.parse_args()
    if not 1 <= args.target_markets <= 200:
        raise ValueError("target-markets must be between 1 and 200")
    if args.candidate_limit < args.target_markets or args.candidate_limit > 1000:
        raise ValueError("candidate-limit must be >= target-markets and <= 1000")
    if not 1 <= args.max_trades_per_market <= 10000:
        raise ValueError("max-trades-per-market must be between 1 and 10000")
    if not 1 <= args.page_size <= 1000:
        raise ValueError("page-size must be between 1 and 1000")
    if not 0 <= args.sleep_sec <= 10:
        raise ValueError("sleep-sec must be between 0 and 10")

    snapshot = build_two_year_top100_snapshot(
        target_markets=args.target_markets,
        candidate_limit=args.candidate_limit,
        max_trades_per_market=args.max_trades_per_market,
        page_size=args.page_size,
        sleep_sec=args.sleep_sec,
    )
    manifest = write_snapshot(snapshot, args.out_dir)
    results = generate_report(args.out_dir, args.out_md, args.out_json)
    print(json.dumps({"manifest": asdict(manifest), "results": [asdict(r) for r in results]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
