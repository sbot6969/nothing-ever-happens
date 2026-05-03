from __future__ import annotations

from bot.backtest.whale_copy import BacktestConfig, adjusted_entry_price, select_signals, simulate


def sample_trades():
    return [
        {"timestamp": 1, "proxyWallet": "0xnew", "slug": "m1", "outcome": "YES", "side": "BUY", "size": "1000", "price": "0.40", "transactionHash": "0x1"},
        {"timestamp": 2, "proxyWallet": "0xold", "slug": "m2", "outcome": "NO", "side": "BUY", "size": "1000", "price": "0.50", "transactionHash": "0x2"},
        {"timestamp": 3, "proxyWallet": "0xsmall", "slug": "m3", "outcome": "YES", "side": "BUY", "size": "10", "price": "0.50", "transactionHash": "0x3"},
    ]


def test_adjusted_entry_price_buy_is_conservative():
    assert adjusted_entry_price(0.5, "BUY", 100) == 0.505


def test_select_signals_filters_old_and_small_wallets():
    signals = select_signals(sample_trades(), {"0xnew": 1, "0xold": 4}, cfg=BacktestConfig(min_notional_usd=100))
    assert [s["proxyWallet"] for s in signals] == ["0xnew"]


def test_simulate_resolved_win_has_positive_pnl():
    fills, metrics = simulate(sample_trades(), {"m1": "YES"}, {"0xnew": 1}, cfg=BacktestConfig(min_notional_usd=100, slippage_bps=0))
    assert len(fills) == 1
    assert fills[0].pnl > 0
    assert metrics["roi"] > 0


def test_simulate_resolved_loss_has_negative_pnl():
    fills, metrics = simulate(sample_trades(), {"m1": "NO"}, {"0xnew": 1}, cfg=BacktestConfig(min_notional_usd=100, slippage_bps=0))
    assert len(fills) == 1
    assert fills[0].pnl < 0
    assert metrics["roi"] == -1
