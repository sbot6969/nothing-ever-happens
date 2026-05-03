from __future__ import annotations

import json
from pathlib import Path

import pytest

from bot.backtest.whale_copy import (
    Resolution,
    TradeValidationError,
    WhaleBacktestConfig,
    WhaleTrade,
    main,
    parse_trade_row,
    run_backtest,
    trade_dedupe_key,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "whale_copy"


def _fixture_trades() -> list[dict]:
    return json.loads((FIXTURE_DIR / "trades.json").read_text())


def test_parse_trade_row_uses_proxy_wallet_and_event_slug() -> None:
    trade = parse_trade_row(_fixture_trades()[0])

    assert trade.wallet == "0x1111111111111111111111111111111111111111"
    assert trade.side == "BUY"
    assert trade.slug == "test-market"
    assert trade.notional == pytest.approx(400.0)


def test_parse_trade_row_validates_wallet_side_and_price() -> None:
    bad = dict(_fixture_trades()[0])
    bad["proxyWallet"] = "not-a-wallet"
    with pytest.raises(TradeValidationError, match="wallet"):
        parse_trade_row(bad)

    bad = dict(_fixture_trades()[0])
    bad["side"] = "HOLD"
    with pytest.raises(TradeValidationError, match="BUY or SELL"):
        parse_trade_row(bad)

    bad = dict(_fixture_trades()[0])
    bad["price"] = "1.50"
    with pytest.raises(TradeValidationError, match="between 0 and 1"):
        parse_trade_row(bad)


def test_trade_dedupe_key_uses_transaction_asset_timestamp() -> None:
    trade = WhaleTrade(
        wallet="0x1111111111111111111111111111111111111111",
        side="BUY",
        asset="asset",
        timestamp=123,
        size=10,
        price=0.5,
        tx="0xabc",
    )

    assert trade_dedupe_key(trade) == "0xabc:asset:123"


def test_backtest_accounts_for_spread_slippage_liquidity_and_resolution() -> None:
    config = WhaleBacktestConfig(
        min_whale_notional_usd=200,
        copy_fraction=0.10,
        max_copy_notional_usd=25,
        spread_bps=50,
        slippage_bps=75,
        max_liquidity_fraction=0.10,
        gas_cost_usd=0.02,
    )
    result = run_backtest(
        _fixture_trades(),
        {
            "asset-win": Resolution(asset="asset-win", payout=1.0),
            "asset-lose": Resolution(asset="asset-lose", payout=0.0),
        },
        config,
    )

    assert result.trades_seen == 6
    assert result.unique_trades_seen == 5
    assert len(result.copied) == 2
    assert result.total_copy_notional_usd == pytest.approx(50.0)
    # First copy wins after paying worse execution price; second copy resolves to 0.
    assert result.total_pnl_usd == pytest.approx(11.688395, abs=1e-6)
    assert result.roi_pct == pytest.approx(23.37679, abs=1e-6)
    assert result.hit_rate_pct == 50.0
    assert {r.reason for r in result.rejected} >= {
        "duplicate_trade",
        "non_buy_trade",
        "below_min_notional",
        "prior_wallet_history",
    }


def test_backtest_rejects_startup_bootstrap_and_stale_signals() -> None:
    config = WhaleBacktestConfig(
        min_whale_notional_usd=200,
        ignore_before_ts=1000,
        max_signal_age_sec=60,
    )
    result = run_backtest(
        _fixture_trades()[:2],
        {
            "asset-win": Resolution(asset="asset-win", payout=1.0),
            "asset-lose": Resolution(asset="asset-lose", payout=0.0),
        },
        config,
        now_ts=2_000,
    )

    assert len(result.copied) == 0
    assert [r.reason for r in result.rejected] == ["startup_bootstrap_trade", "stale_signal"]


def test_cli_runs_offline_fixture_and_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "report.json"

    rc = main(
        [
            "--trades",
            str(FIXTURE_DIR / "trades.json"),
            "--resolutions",
            str(FIXTURE_DIR / "resolutions.json"),
            "--out",
            str(out),
            "--min-notional",
            "200",
        ]
    )

    assert rc == 0
    payload = json.loads(out.read_text())
    assert payload["trades_seen"] == 6
    assert len(payload["copied"]) == 2
    assert payload["total_copy_notional_usd"] == 50.0
