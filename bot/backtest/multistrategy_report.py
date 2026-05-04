"""Generate paper-only multi-strategy backtest reports.

The report writer consumes cached public snapshots only. It never reads secrets,
creates wallets, submits orders, closes positions, or touches live funds.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from bot.backtest.multistrategy import STRATEGY_FAMILIES, StrategyBacktestResult, compare_strategies, comparison_to_dict
from bot.backtest.whale_copy import Resolution


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_resolutions(path: Path) -> dict[str, Resolution]:
    raw = load_json(path)
    if not isinstance(raw, dict):
        raise ValueError("resolutions.json must be a JSON object")
    out: dict[str, Resolution] = {}
    for asset, value in raw.items():
        payout = value.get("payout") if isinstance(value, dict) else value
        out[str(asset)] = Resolution(asset=str(asset), payout=float(payout))
    return out


def _manifest_lines(snapshot_dir: Path) -> list[str]:
    manifest = snapshot_dir / "manifest.json"
    if not manifest.exists():
        return ["- Manifest: not found; cached snapshot provenance incomplete."]
    data = load_json(manifest)
    notes = data.get("notes") if isinstance(data, dict) else []
    lines = [
        f"- Snapshot dir: `{snapshot_dir}`",
        f"- Created at: `{data.get('created_at', 'unknown')}`",
        f"- Market limit: `{data.get('market_limit', 'unknown')}`; markets saved: `{data.get('markets_saved', 'unknown')}`",
        f"- Trades per market cap: `{data.get('trades_per_market', 'unknown')}`; trades saved: `{data.get('trades_saved', 'unknown')}`",
        f"- Resolution assets: `{data.get('resolution_assets', 'unknown')}`",
    ]
    lines.extend(f"- Note: {note}" for note in notes)
    return lines


def _fmt_money(value: float) -> str:
    return f"${value:,.2f}"


def _fmt_pct(value: float) -> str:
    return f"{value:,.2f}%"


def _top_reasons(result: StrategyBacktestResult, *, limit: int = 5) -> str:
    if not result.skipped_reasons:
        return "—"
    pairs = sorted(result.skipped_reasons.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return "; ".join(f"{reason}: {count}" for reason, count in pairs)


def write_markdown(results: list[StrategyBacktestResult], snapshot_dir: Path, out_path: Path) -> None:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Multi-Bot Backtest Results",
        "",
        f"Generated: `{now}`",
        "",
        "## Safety / interpretation",
        "",
        "- Paper/offline report only; no live orders, wallet creation, transfers, position closes, or live-trading toggles were performed.",
        "- Market-making and normal/AMM rows are conservative skeleton/proxy simulations until historical order-book/queue data exists.",
        "- `candidate_edge_needs_oos` means larger out-of-sample validation is justified; it is **not** live-trading approval.",
        "- `overfit_or_underpowered` is expected for small or heavily filtered samples and must not be marketed as real edge.",
        "",
        "## Snapshot",
        "",
        *_manifest_lines(snapshot_dir),
        "",
        "## Comparable metrics",
        "",
        "| Strategy | Actions | Notional | PnL | ROI | Hit rate | 95% hit-rate interval | Max DD | Turnover | Max exposure | Skipped | Evidence |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in results:
        interval = f"{row.hit_rate_interval_pct[0]:.1f}–{row.hit_rate_interval_pct[1]:.1f}%"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.strategy}`",
                    str(row.copied_or_actions),
                    _fmt_money(row.total_notional_usd),
                    _fmt_money(row.total_pnl_usd),
                    _fmt_pct(row.roi_pct),
                    _fmt_pct(row.hit_rate_pct),
                    interval,
                    _fmt_money(row.max_drawdown_usd),
                    _fmt_money(row.turnover_usd),
                    _fmt_money(row.max_exposure_usd),
                    str(row.rejected_or_skipped),
                    f"`{row.evidence_label}`",
                ]
            )
            + " |"
        )

    lines.extend(["", "## Skipped / rejected signal reasons", ""])
    for row in results:
        lines.extend([
            f"### `{row.strategy}`",
            "",
            f"- Top reasons: {_top_reasons(row)}",
            f"- Evidence reasons: {'; '.join(row.evidence_reasons) if row.evidence_reasons else 'none'}",
            f"- Notes: {row.notes}",
            "",
        ])

    lines.extend(
        [
            "## Next backtest work",
            "",
            "- Add historical order-book snapshots to replace market-making and AMM proxy fills with queue/depth-aware simulations.",
            "- Split results by category, close-time bucket, liquidity bucket, and whale-wallet cohort.",
            "- Run walk-forward/OOS validation instead of scoring wallets on the same cached sample used for reporting.",
            "- Add Nothing Ever Happens strategy adapter so it emits standard `StrategySignal` and skipped reasons.",
            "- Keep all live-financial actions blocked until separate typed confirmation and another security review.",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_report(snapshot_dir: Path, out_md: Path, out_json: Path | None = None) -> list[StrategyBacktestResult]:
    trades = load_json(snapshot_dir / "trades.json")
    if not isinstance(trades, list):
        raise ValueError("trades.json must be a JSON array")
    results = compare_strategies(trades, load_resolutions(snapshot_dir / "resolutions.json"), STRATEGY_FAMILIES)
    write_markdown(results, snapshot_dir, out_md)
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps({"results": comparison_to_dict(results)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate paper-only multi-bot backtest report from cached public snapshot")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, default=Path("docs/polymarket_multi_bot/BACKTEST_RESULTS.md"))
    parser.add_argument("--out-json", type=Path, default=Path("artifacts/whale_copy/multistrategy_report.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    results = generate_report(args.snapshot_dir, args.out_md, args.out_json)
    print(json.dumps({"results": [asdict(result) for result in results]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
