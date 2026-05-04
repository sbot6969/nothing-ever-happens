from __future__ import annotations

import json
from pathlib import Path

from bot.backtest.validation_report import generate_validation, stress_grid
from bot.backtest.multistrategy import compare_strategies
from bot.backtest.whale_copy import Resolution


def _snapshot(tmp_path: Path) -> Path:
    p = tmp_path / "snapshot"
    p.mkdir()
    trades = []
    for i in range(9):
        trades.append({
            "proxyWallet": f"0x{i+1:040x}",
            "side": "BUY",
            "asset": "asset-win" if i % 2 == 0 else "asset-lose",
            "size": 1000 + i,
            "price": 0.5,
            "timestamp": i + 1,
            "transactionHash": f"0x{i}",
            "history_count": 1,
            "market_size_usd": 20_000,
            "market_size_source": "test-source",
            "market_category": "politics" if i < 5 else "crypto",
            "liquidity_usd": 5_000 if i < 6 else 20_000,
        })
    (p / "trades.json").write_text(json.dumps(trades), encoding="utf-8")
    (p / "resolutions.json").write_text(json.dumps({"asset-win": {"payout": 1}, "asset-lose": {"payout": 0}}), encoding="utf-8")
    return p


def test_generate_validation_writes_walkforward_cohorts_and_stress(tmp_path: Path) -> None:
    out_md = tmp_path / "validation.md"
    out_json = tmp_path / "validation.json"
    payload = generate_validation(_snapshot(tmp_path), out_md, out_json)

    text = out_md.read_text(encoding="utf-8")
    assert "oos_late" in text
    assert "category:politics" in text
    assert "Latency / cost stress grid" in text
    assert payload["stress_grid"]
    assert json.loads(out_json.read_text(encoding="utf-8"))["slices"]


def test_stress_grid_subtracts_extra_cost_bps() -> None:
    results = compare_strategies([{"asset": "asset-win", "price": 0.5, "size": 10, "side": "BUY", "timestamp": 1, "proxyWallet": "0x1111111111111111111111111111111111111111", "history_count": 1, "market_size_usd": 20_000}], {"asset-win": Resolution("asset-win", 1)})
    rows = stress_grid(results, [100])

    assert all(row["stressed_roi_pct"] == row["base_roi_pct"] - 1 for row in rows)
