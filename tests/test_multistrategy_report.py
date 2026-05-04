from __future__ import annotations

import json
from pathlib import Path

from bot.backtest.multistrategy_report import generate_report


def test_generate_report_writes_required_metrics(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    trades = [
        {
            "proxyWallet": "0x1111111111111111111111111111111111111111",
            "side": "BUY",
            "asset": "asset-win",
            "size": 20_000,
            "price": 0.5,
            "timestamp": 1,
            "transactionHash": "0x1",
            "history_count": 1,
            "market_size_usd": 100_000,
            "liquidity_usd": 10_000,
        },
        {
            "proxyWallet": "0x2222222222222222222222222222222222222222",
            "side": "BUY",
            "asset": "asset-lose",
            "size": 6_000,
            "price": 0.5,
            "timestamp": 2,
            "transactionHash": "0x2",
            "history_count": 1,
            "market_size_usd": 10_000,
            "liquidity_usd": 10_000,
        },
    ]
    (snapshot / "trades.json").write_text(json.dumps(trades), encoding="utf-8")
    (snapshot / "resolutions.json").write_text(json.dumps({"asset-win": {"payout": 1}, "asset-lose": {"payout": 0}}), encoding="utf-8")
    (snapshot / "manifest.json").write_text(json.dumps({"created_at": "test", "market_limit": 2, "markets_saved": 2, "trades_per_market": 2, "trades_saved": 2, "resolution_assets": 2, "notes": ["paper"]}), encoding="utf-8")

    out_md = tmp_path / "BACKTEST_RESULTS.md"
    out_json = tmp_path / "report.json"
    results = generate_report(snapshot, out_md, out_json)

    text = out_md.read_text(encoding="utf-8")
    assert "PnL" in text
    assert "ROI" in text
    assert "Max DD" in text
    assert "Turnover" in text
    assert "Max exposure" in text
    assert "Skipped" in text
    assert "Evidence" in text
    assert "market_size_source" in json.dumps([row.provenance for row in results])
    assert len(results) == 4
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert {row["strategy"] for row in payload["results"]} == {"nothing_happens", "whale_copy", "market_making", "normal_distribution_amm"}
