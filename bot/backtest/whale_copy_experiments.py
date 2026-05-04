"""Run whale-copy strategy improvement iterations on cached snapshots."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Callable

from bot.backtest.whale_copy import Resolution, WhaleBacktestConfig, result_to_dict, run_backtest


@dataclass(frozen=True)
class IterationReport:
    iteration: int
    name: str
    copied: int
    rejected: int
    total_copy_notional_usd: float
    total_pnl_usd: float
    roi_pct: float
    hit_rate_pct: float
    max_drawdown_usd: float
    notes: str


@dataclass(frozen=True)
class ExperimentReport:
    best_iteration: int | None
    best_name: str
    best_roi_pct: float
    best_pnl_usd: float
    iterations: list[IterationReport]
    feasibility_notes: list[str]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_resolutions(path: Path) -> dict[str, Resolution]:
    raw = load_json(path)
    return {str(asset): Resolution(asset=str(asset), payout=float(value["payout"] if isinstance(value, dict) else value)) for asset, value in raw.items()}


def _category(trade: dict[str, Any]) -> str:
    return str(trade.get("market_category") or trade.get("category") or "").strip().lower()


def _title(trade: dict[str, Any]) -> str:
    return (str(trade.get("title") or "") + " " + str(trade.get("slug") or trade.get("eventSlug") or "")).lower()


def _filter(trades: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
    return [trade for trade in trades if predicate(trade)]


def _best_category(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> tuple[str, float]:
    categories = sorted({_category(t) for t in trades if _category(t)})
    best = ("", float("-inf"))
    for category in categories:
        sample = _filter(trades, lambda t, c=category: _category(t) == c)
        if len(sample) < 5:
            continue
        result = run_backtest(
            sample,
            resolutions,
            WhaleBacktestConfig(min_whale_notional_usd=100, copy_fraction=0.08, max_copy_notional_usd=20, max_history_count=3),
        )
        if result.copied and result.roi_pct > best[1]:
            best = (category, result.roi_pct)
    return best


def _wallet_scores(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> dict[str, float]:
    # Conservative hindsight-derived quality proxy for offline research only.
    scores: dict[str, list[float]] = {}
    for trade in trades:
        wallet = str(trade.get("proxyWallet") or trade.get("user") or "").lower()
        asset = str(trade.get("asset") or "")
        payout = resolutions.get(asset)
        if not wallet or payout is None or str(trade.get("side") or "").upper() != "BUY":
            continue
        try:
            price = float(trade.get("price") or 0.0)
        except (TypeError, ValueError):
            continue
        if not 0 < price < 1:
            continue
        roi = (float(payout.payout) / price) - 1.0
        scores.setdefault(wallet, []).append(roi)
    return {wallet: sum(values) / len(values) for wallet, values in scores.items() if len(values) >= 1}


def run_iterations(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> ExperimentReport:
    reports: list[IterationReport] = []
    raw_scores = _wallet_scores(trades, resolutions)
    category, _category_roi = _best_category(trades, resolutions)

    strategies: list[tuple[str, list[dict[str, Any]], WhaleBacktestConfig, str]] = [
        (
            "iteration_0_baseline_first_visible_large_buy",
            trades,
            WhaleBacktestConfig(min_whale_notional_usd=250, copy_fraction=0.10, max_copy_notional_usd=25, max_history_count=1),
            "Copy first-visible large BUY signals with fixed cap.",
        ),
        (
            "iteration_1_liquidity_spread_aware",
            _filter(trades, lambda t: float(t.get("liquidity_usd") or t.get("market_volume_usd") or 0) >= 1000 and float(t.get("price") or 0) <= 0.80),
            WhaleBacktestConfig(min_whale_notional_usd=250, copy_fraction=0.08, max_copy_notional_usd=20, max_history_count=2, spread_bps=35, slippage_bps=50, max_liquidity_fraction=0.05),
            "Require better market liquidity and avoid high entry prices.",
        ),
        (
            "iteration_2_wallet_quality_scored",
            _filter(trades, lambda t: raw_scores.get(str(t.get("proxyWallet") or t.get("user") or "").lower(), -99) > 0),
            WhaleBacktestConfig(min_whale_notional_usd=150, copy_fraction=0.08, max_copy_notional_usd=20, max_history_count=5, spread_bps=35, slippage_bps=50),
            "Keep wallets with positive realized edge inside the cached sample. Research-only; avoid overfitting.",
        ),
        (
            "iteration_3_market_type_specialization",
            _filter(trades, lambda t: _category(t) == category) if category else trades,
            WhaleBacktestConfig(min_whale_notional_usd=100, copy_fraction=0.08, max_copy_notional_usd=20, max_history_count=3, spread_bps=35, slippage_bps=60),
            f"Specialize to best cached category: {category or 'none'}.",
        ),
        (
            "iteration_4_portfolio_risk_optimized",
            _filter(trades, lambda t: float(t.get("price") or 0) <= 0.70 and "updown-5m" not in _title(t)),
            WhaleBacktestConfig(min_whale_notional_usd=150, copy_fraction=0.05, max_copy_notional_usd=12, max_history_count=3, spread_bps=40, slippage_bps=75, max_liquidity_fraction=0.03, gas_cost_usd=0.02),
            "Smaller Kelly-like sizing, avoid expensive entries and 5m latency-heavy markets.",
        ),
        (
            "iteration_5_calibration_arbitrage_addons",
            _filter(
                trades,
                lambda t: float(t.get("price") or 0) <= 0.50
                and "updown-5m" not in _title(t)
                and raw_scores.get(str(t.get("proxyWallet") or t.get("user") or "").lower(), -99) >= 0.50,
            ),
            WhaleBacktestConfig(
                min_whale_notional_usd=100,
                copy_fraction=0.04,
                max_copy_notional_usd=10,
                max_history_count=10,
                spread_bps=45,
                slippage_bps=90,
                max_liquidity_fraction=0.03,
                gas_cost_usd=0.02,
            ),
            "Calibration overlay: lower-price non-5m markets with stronger positive wallet sample score; true CEX/YES-NO arb needs order-book history. High overfit risk.",
        ),
    ]

    for idx, (name, strategy_trades, cfg, notes) in enumerate(strategies):
        result = run_backtest(strategy_trades, resolutions, cfg)
        reports.append(
            IterationReport(
                iteration=idx,
                name=name,
                copied=len(result.copied),
                rejected=len(result.rejected),
                total_copy_notional_usd=result.total_copy_notional_usd,
                total_pnl_usd=result.total_pnl_usd,
                roi_pct=result.roi_pct,
                hit_rate_pct=result.hit_rate_pct,
                max_drawdown_usd=result.max_drawdown_usd,
                notes=notes,
            )
        )

    eligible = [r for r in reports if r.copied > 0]
    best = max(eligible, key=lambda r: (r.roi_pct, r.total_pnl_usd), default=None)
    return ExperimentReport(
        best_iteration=best.iteration if best else None,
        best_name=best.name if best else "",
        best_roi_pct=best.roi_pct if best else 0.0,
        best_pnl_usd=best.total_pnl_usd if best else 0.0,
        iterations=reports,
        feasibility_notes=[
            "Iteration 5 is a filtered calibration proxy, not proof of executable arbitrage: historical order-book snapshots and CEX candle alignment are required.",
            "Wallet-quality scoring uses the cached sample and can overfit; use walk-forward validation before live deployment.",
            "If best ROI is below 100%, keep whale-copy in paper mode and iterate. If above 100% on a small sample, still paper-test because sample bias may be severe.",
        ],
    )


def write_markdown(report: ExperimentReport, out: Path) -> None:
    lines = [
        "# Whale-Copy Backtest Iteration Report",
        "",
        f"Best iteration: `{report.best_iteration}` — `{report.best_name}`",
        f"Best ROI: `{report.best_roi_pct:.2f}%`; best PnL: `${report.best_pnl_usd:.2f}`",
        "",
        "| Iteration | Strategy | Copied | Notional | PnL | ROI | Hit rate | Max DD | Notes |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report.iterations:
        lines.append(
            f"| {row.iteration} | {row.name} | {row.copied} | ${row.total_copy_notional_usd:.2f} | ${row.total_pnl_usd:.2f} | {row.roi_pct:.2f}% | {row.hit_rate_pct:.1f}% | ${row.max_drawdown_usd:.2f} | {row.notes} |"
        )
    lines.extend(["", "## Feasibility notes", ""])
    lines.extend(f"- {note}" for note in report.feasibility_notes)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class WalkForwardIterationRow:
    iteration: int
    name: str
    train_copied: int
    train_roi_pct: float
    validation_copied: int
    validation_roi_pct: float
    oos_copied: int
    oos_roi_pct: float
    selected_on_train: bool
    verdict: str


def _split_thirds(trades: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(trades, key=lambda row: int(float(row.get("timestamp") or 0)))
    n = len(ordered)
    if n == 0:
        return [], [], []
    a = max(1, n // 3)
    b = max(a + 1, 2 * n // 3) if n >= 3 else n
    return ordered[:a], ordered[a:b], ordered[b:]


def _iteration_specs(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]):
    raw_scores = _wallet_scores(trades, resolutions)
    category, _category_roi = _best_category(trades, resolutions)
    return [
        ("iteration_0_baseline_first_visible_large_buy", lambda rows: rows, WhaleBacktestConfig(min_whale_notional_usd=250, copy_fraction=0.10, max_copy_notional_usd=25, max_history_count=1)),
        ("iteration_1_liquidity_spread_aware", lambda rows: _filter(rows, lambda t: float(t.get("liquidity_usd") or t.get("market_volume_usd") or 0) >= 1000 and float(t.get("price") or 0) <= 0.80), WhaleBacktestConfig(min_whale_notional_usd=250, copy_fraction=0.08, max_copy_notional_usd=20, max_history_count=2, spread_bps=35, slippage_bps=50, max_liquidity_fraction=0.05)),
        ("iteration_2_wallet_quality_scored", lambda rows: _filter(rows, lambda t: raw_scores.get(str(t.get("proxyWallet") or t.get("user") or "").lower(), -99) > 0), WhaleBacktestConfig(min_whale_notional_usd=150, copy_fraction=0.08, max_copy_notional_usd=20, max_history_count=5, spread_bps=35, slippage_bps=50)),
        ("iteration_3_market_type_specialization", lambda rows: _filter(rows, lambda t: _category(t) == category) if category else rows, WhaleBacktestConfig(min_whale_notional_usd=100, copy_fraction=0.08, max_copy_notional_usd=20, max_history_count=3, spread_bps=35, slippage_bps=60)),
        ("iteration_4_portfolio_risk_optimized", lambda rows: _filter(rows, lambda t: float(t.get("price") or 0) <= 0.70 and "updown-5m" not in _title(t)), WhaleBacktestConfig(min_whale_notional_usd=150, copy_fraction=0.05, max_copy_notional_usd=12, max_history_count=3, spread_bps=40, slippage_bps=75, max_liquidity_fraction=0.03, gas_cost_usd=0.02)),
        ("iteration_5_calibration_arbitrage_addons", lambda rows: _filter(rows, lambda t: float(t.get("price") or 0) <= 0.50 and "updown-5m" not in _title(t) and raw_scores.get(str(t.get("proxyWallet") or t.get("user") or "").lower(), -99) >= 0.50), WhaleBacktestConfig(min_whale_notional_usd=100, copy_fraction=0.04, max_copy_notional_usd=10, max_history_count=10, spread_bps=45, slippage_bps=90, max_liquidity_fraction=0.03, gas_cost_usd=0.02)),
    ]


def run_walk_forward_iterations(trades: list[dict[str, Any]], resolutions: dict[str, Resolution]) -> list[WalkForwardIterationRow]:
    train, validation, oos = _split_thirds(trades)
    specs = _iteration_specs(train, resolutions)
    train_results = []
    for idx, (name, filter_fn, cfg) in enumerate(specs):
        result = run_backtest(filter_fn(train), resolutions, cfg)
        train_results.append((idx, name, filter_fn, cfg, result))
    eligible = [row for row in train_results if len(row[4].copied) >= 5]
    best_idx = max(eligible, key=lambda row: (row[4].roi_pct, row[4].total_pnl_usd), default=train_results[0])[0] if train_results else -1
    rows: list[WalkForwardIterationRow] = []
    for idx, name, filter_fn, cfg, train_result in train_results:
        validation_result = run_backtest(filter_fn(validation), resolutions, cfg)
        oos_result = run_backtest(filter_fn(oos), resolutions, cfg)
        selected = idx == best_idx
        verdict = "reject_underpowered"
        if selected and len(oos_result.copied) >= 20 and oos_result.roi_pct > 0 and validation_result.roi_pct > 0:
            verdict = "candidate_needs_l2_replay"
        elif selected:
            verdict = "selected_on_train_but_rejected_oos_or_sample"
        rows.append(WalkForwardIterationRow(idx, name, len(train_result.copied), train_result.roi_pct, len(validation_result.copied), validation_result.roi_pct, len(oos_result.copied), oos_result.roi_pct, selected, verdict))
    return rows


def write_walk_forward_markdown(rows: list[WalkForwardIterationRow], out: Path) -> None:
    lines = [
        "# Whale-Copy Walk-Forward Iteration Validation",
        "",
        "Paper/offline only. Iterations are selected using the train slice and then checked on validation and OOS slices.",
        "",
        "| Iteration | Strategy | Train copied | Train ROI | Validation copied | Validation ROI | OOS copied | OOS ROI | Selected | Verdict |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row.iteration} | `{row.name}` | {row.train_copied} | {row.train_roi_pct:.2f}% | {row.validation_copied} | {row.validation_roi_pct:.2f}% | {row.oos_copied} | {row.oos_roi_pct:.2f}% | {str(row.selected_on_train).lower()} | `{row.verdict}` |")
    lines.extend(["", "## Rule", "", "A whale-copy iteration remains paper-only unless train selection survives validation and OOS with enough copied actions and then passes L2/order-lifecycle replay plus live security review."])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run whale-copy strategy iteration backtests")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, default=Path("artifacts/whale_copy/iteration_report.json"))
    parser.add_argument("--out-md", type=Path, default=Path("docs/whale_copy_research/BACKTEST_ITERATIONS.md"))
    parser.add_argument("--out-walkforward-md", type=Path, default=None)
    parser.add_argument("--out-walkforward-json", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    trades = load_json(args.snapshot_dir / "trades.json")
    resolutions = load_resolutions(args.snapshot_dir / "resolutions.json")
    if not isinstance(trades, list):
        raise ValueError("trades.json must be a JSON array")
    report = run_iterations(trades, resolutions)
    payload = asdict(report)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.out_md)
    if args.out_walkforward_md or args.out_walkforward_json:
        wf_rows = run_walk_forward_iterations(trades, resolutions)
        wf_payload = [asdict(row) for row in wf_rows]
        if args.out_walkforward_json:
            args.out_walkforward_json.parent.mkdir(parents=True, exist_ok=True)
            args.out_walkforward_json.write_text(json.dumps(wf_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.out_walkforward_md:
            write_walk_forward_markdown(wf_rows, args.out_walkforward_md)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
