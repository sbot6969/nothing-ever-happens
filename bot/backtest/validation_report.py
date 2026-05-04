"""Walk-forward, stress, and cohort validation for paper-only snapshots."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from bot.backtest.multistrategy import STRATEGY_FAMILIES, StrategyBacktestResult, compare_strategies, comparison_to_dict
from bot.backtest.multistrategy_report import load_json, load_resolutions
from bot.backtest.quant_validation import adverse_cost_roi_pct


@dataclass(frozen=True)
class ValidationSlice:
    name: str
    rows: int
    results: list[StrategyBacktestResult]


def _safe_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed >= 0 else 0.0


def _timestamp(row: dict[str, Any]) -> int:
    return int(_safe_float(row.get("timestamp")))


def _category(row: dict[str, Any]) -> str:
    return str(row.get("market_category") or row.get("category") or "unknown") or "unknown"


def _liquidity_bucket(row: dict[str, Any]) -> str:
    liquidity = _safe_float(row.get("liquidity_usd"))
    if liquidity <= 0:
        return "liquidity_missing_or_zero"
    if liquidity < 1_000:
        return "liquidity_lt_1k"
    if liquidity < 10_000:
        return "liquidity_1k_10k"
    return "liquidity_gte_10k"


def _time_bucket(row: dict[str, Any], cutoffs: tuple[int, int]) -> str:
    ts = _timestamp(row)
    if ts <= cutoffs[0]:
        return "time_early"
    if ts <= cutoffs[1]:
        return "time_middle"
    return "time_late"


def _split_by_quantiles(trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(trades, key=_timestamp)
    n = len(ordered)
    if n == 0:
        return [], [], []
    a = max(1, n // 3)
    b = max(a + 1, 2 * n // 3) if n >= 3 else n
    return ordered[:a], ordered[a:b], ordered[b:]


def walk_forward_slices(trades: list[dict[str, Any]], resolutions) -> list[ValidationSlice]:
    early, middle, late = _split_by_quantiles(trades)
    return [
        ValidationSlice("train_early", len(early), compare_strategies(early, resolutions)),
        ValidationSlice("validation_middle", len(middle), compare_strategies(middle, resolutions)),
        ValidationSlice("oos_late", len(late), compare_strategies(late, resolutions)),
    ]


def cohort_slices(trades: list[dict[str, Any]], resolutions, *, max_per_family: int = 8) -> list[ValidationSlice]:
    if not trades:
        return []
    ts_sorted = sorted(_timestamp(row) for row in trades)
    cutoffs = (ts_sorted[len(ts_sorted) // 3], ts_sorted[(2 * len(ts_sorted)) // 3])
    families: list[tuple[str, callable]] = [
        ("category", _category),
        ("liquidity", _liquidity_bucket),
        ("time", lambda row: _time_bucket(row, cutoffs)),
    ]
    out: list[ValidationSlice] = []
    for family, fn in families:
        groups: dict[str, list[dict[str, Any]]] = {}
        for row in trades:
            groups.setdefault(str(fn(row)), []).append(row)
        for name, rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))[:max_per_family]:
            out.append(ValidationSlice(f"{family}:{name}", len(rows), compare_strategies(rows, resolutions)))
    return out


def stress_grid(results: Iterable[StrategyBacktestResult], cost_bps_values: Iterable[float] = (0, 25, 50, 100, 200)) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        for bps in cost_bps_values:
            rows.append({
                "strategy": result.strategy,
                "extra_cost_bps": float(bps),
                "base_roi_pct": result.roi_pct,
                "stressed_roi_pct": adverse_cost_roi_pct(result.roi_pct, float(bps)),
            })
    return rows


def _metrics_table(results: list[StrategyBacktestResult]) -> list[str]:
    lines = ["| Strategy | Actions | PnL | ROI | Evidence |", "|---|---:|---:|---:|---|"]
    for row in results:
        lines.append(f"| `{row.strategy}` | {row.copied_or_actions} | ${row.total_pnl_usd:,.2f} | {row.roi_pct:,.2f}% | `{row.evidence_label}` |")
    return lines


def write_validation_markdown(slices: list[ValidationSlice], stress: list[dict[str, Any]], out_md: Path) -> None:
    lines = [
        "# Multi-Bot Walk-Forward / Cohort Validation",
        "",
        "Paper/offline validation only. These tables do not authorize live trading, wallet funding, position closing, or transfers.",
        "",
        "## Walk-forward / OOS slices",
        "",
    ]
    for sl in slices:
        lines.extend([f"### `{sl.name}` ({sl.rows} rows)", "", *_metrics_table(sl.results), ""])
    lines.extend(["## Latency / cost stress grid", "", "| Strategy | Extra cost bps | Base ROI | Stressed ROI |", "|---|---:|---:|---:|"])
    for row in stress:
        lines.append(f"| `{row['strategy']}` | {row['extra_cost_bps']:.0f} | {row['base_roi_pct']:.2f}% | {row['stressed_roi_pct']:.2f}% |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Any strategy whose result only appears in one cohort is treated as underpowered/possibly overfit.",
        "- Extra cost bps approximates fees, slippage, queue loss, and latency decay; true market-making validation still needs L2/order-book replay.",
        "- Live finance remains blocked until typed confirmation plus fresh security/secret/wallet review.",
    ])
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_validation(snapshot_dir: Path, out_md: Path, out_json: Path | None = None) -> dict[str, Any]:
    trades = load_json(snapshot_dir / "trades.json")
    if not isinstance(trades, list):
        raise ValueError("trades.json must be a JSON array")
    resolutions = load_resolutions(snapshot_dir / "resolutions.json")
    wf = walk_forward_slices(trades, resolutions)
    cohorts = cohort_slices(trades, resolutions)
    all_slices = wf + cohorts
    baseline = compare_strategies(trades, resolutions, STRATEGY_FAMILIES)
    stress = stress_grid(baseline)
    write_validation_markdown(all_slices, stress, out_md)
    payload = {
        "slices": [{"name": sl.name, "rows": sl.rows, "results": comparison_to_dict(sl.results)} for sl in all_slices],
        "stress_grid": stress,
    }
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate paper-only walk-forward/cohort validation report")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, default=Path("docs/polymarket_multi_bot/VALIDATION_RESULTS.md"))
    parser.add_argument("--out-json", type=Path, default=Path("artifacts/whale_copy/validation_report.json"))
    args = parser.parse_args(argv)
    payload = generate_validation(args.snapshot_dir, args.out_md, args.out_json)
    print(json.dumps({"slice_count": len(payload["slices"]), "stress_rows": len(payload["stress_grid"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
