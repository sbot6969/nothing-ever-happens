from __future__ import annotations

from bot.backtest.whale_copy import Resolution
from bot.backtest.whale_copy_experiments import run_iterations


def test_run_iterations_reports_all_strategies() -> None:
    trades = [
        {
            "proxyWallet": "0x1111111111111111111111111111111111111111",
            "side": "BUY",
            "asset": "asset-win",
            "size": 1000,
            "price": 0.4,
            "timestamp": 1,
            "transactionHash": "0x1",
            "history_count": 1,
            "liquidity_usd": 5000,
            "market_category": "Politics",
            "title": "Will X happen?",
        },
        {
            "proxyWallet": "0x2222222222222222222222222222222222222222",
            "side": "BUY",
            "asset": "asset-lose",
            "size": 1000,
            "price": 0.3,
            "timestamp": 2,
            "transactionHash": "0x2",
            "history_count": 1,
            "liquidity_usd": 5000,
            "market_category": "Sports",
            "title": "Will Y happen?",
        },
    ]
    report = run_iterations(trades, {"asset-win": Resolution("asset-win", 1), "asset-lose": Resolution("asset-lose", 0)})

    assert len(report.iterations) == 6
    assert report.best_iteration is not None
    assert report.best_roi_pct > 0
