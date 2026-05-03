from __future__ import annotations

from pathlib import Path

from bot.backtest import data_downloader


def test_market_resolution_skips_unresolved_and_maps_token_payouts() -> None:
    market = {"clobTokenIds": '["yes", "no"]', "outcomePrices": '["1", "0"]'}

    assert data_downloader._market_resolution(market) == {"yes": {"payout": 1.0}, "no": {"payout": 0.0}}
    assert data_downloader._market_resolution({"clobTokenIds": '["yes", "no"]', "outcomePrices": '["0.5", "0.5"]'}) == {}


def test_build_snapshot_enriches_trades_and_dedupes(monkeypatch) -> None:
    markets = [
        {
            "conditionId": "cond-1",
            "slug": "market",
            "question": "Question?",
            "category": "Politics",
            "volumeNum": "1000",
            "liquidityNum": "500",
            "clobTokenIds": '["asset-win", "asset-lose"]',
            "outcomePrices": '["1", "0"]',
        }
    ]
    trades = [
        {
            "conditionId": "cond-1",
            "proxyWallet": "0x1111111111111111111111111111111111111111",
            "side": "BUY",
            "asset": "asset-win",
            "size": 100,
            "price": 0.5,
            "timestamp": 1,
            "transactionHash": "0xaaa",
        },
        {
            "conditionId": "cond-1",
            "proxyWallet": "0x1111111111111111111111111111111111111111",
            "side": "BUY",
            "asset": "asset-win",
            "size": 100,
            "price": 0.5,
            "timestamp": 1,
            "transactionHash": "0xaaa",
        },
    ]
    monkeypatch.setattr(data_downloader, "fetch_closed_markets", lambda limit: markets)
    monkeypatch.setattr(data_downloader, "fetch_market_trades", lambda condition_id, limit: trades)

    snapshot = data_downloader.build_snapshot(market_limit=1, trades_per_market=2, sleep_sec=0)

    assert len(snapshot["markets"]) == 1
    assert len(snapshot["trades"]) == 1
    assert snapshot["trades"][0]["history_count"] == 1
    assert snapshot["trades"][0]["market_category"] == "Politics"
    assert snapshot["resolutions"]["asset-win"] == {"payout": 1.0}


def test_write_snapshot_manifest(tmp_path: Path) -> None:
    manifest = data_downloader.write_snapshot(
        {"markets": [{"slug": "x"}], "trades": [{"tx": "y"}], "resolutions": {"asset": {"payout": 1}}},
        tmp_path,
        market_limit=1,
        trades_per_market=2,
    )

    assert manifest.markets_saved == 1
    assert (tmp_path / "trades.json").exists()


def test_downloader_cli_bounds_reject_unbounded_downloads(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError, match="market_limit"):
        data_downloader.main(["--out-dir", str(tmp_path), "--market-limit", "999999"])
    with pytest.raises(ValueError, match="trades_per_market"):
        data_downloader.main(["--out-dir", str(tmp_path), "--trades-per-market", "999999"])
    with pytest.raises(ValueError, match="sleep_sec"):
        data_downloader.main(["--out-dir", str(tmp_path), "--sleep-sec", "99"])
