from __future__ import annotations

from bot.backtest.data_downloader import PUBLIC_BACKTEST_PROVENANCE, build_snapshot


def test_build_snapshot_records_market_size_source(monkeypatch) -> None:
    market = {
        "conditionId": "cond-1",
        "slug": "test-market",
        "question": "Will this settle?",
        "category": "test",
        "volumeNum": "12345",
        "liquidityNum": "678",
        "clobTokenIds": '["asset-yes", "asset-no"]',
        "outcomePrices": "[1, 0]",
    }
    trade = {
        "conditionId": "cond-1",
        "transactionHash": "0x1",
        "asset": "asset-yes",
        "timestamp": 1,
        "proxyWallet": "0x1111111111111111111111111111111111111111",
        "side": "BUY",
        "size": 10,
        "price": 0.5,
    }
    monkeypatch.setattr("bot.backtest.data_downloader.fetch_closed_markets", lambda limit: [market])
    monkeypatch.setattr("bot.backtest.data_downloader.fetch_market_trades", lambda condition_id, limit: [trade])

    snapshot = build_snapshot(market_limit=1, trades_per_market=1, sleep_sec=0)

    enriched = snapshot["trades"][0]
    assert enriched["market_size_usd"] == 12345.0
    assert enriched["market_size_source"] == PUBLIC_BACKTEST_PROVENANCE.market_size_source
    assert enriched["liquidity_source"] == PUBLIC_BACKTEST_PROVENANCE.liquidity_source
