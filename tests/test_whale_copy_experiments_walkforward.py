from bot.backtest.whale_copy import Resolution
from bot.backtest.whale_copy_experiments import run_walk_forward_iterations


def test_walk_forward_iterations_select_train_and_report_oos() -> None:
    trades = []
    for i in range(30):
        trades.append({
            "proxyWallet": f"0x{i+1:040x}",
            "side": "BUY",
            "asset": "asset-win" if i % 3 else "asset-lose",
            "size": 1000,
            "price": 0.5,
            "timestamp": i,
            "history_count": 1,
            "market_size_usd": 20_000,
        })
    rows = run_walk_forward_iterations(trades, {"asset-win": Resolution("asset-win", 1), "asset-lose": Resolution("asset-lose", 0)})

    assert len(rows) == 6
    assert sum(1 for row in rows if row.selected_on_train) == 1
    assert all(row.verdict for row in rows)
