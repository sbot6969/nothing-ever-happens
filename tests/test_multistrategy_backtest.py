from __future__ import annotations

from bot.backtest.multistrategy import STRATEGY_FAMILIES, compare_strategies, comparison_to_dict
from bot.backtest.whale_copy import Resolution


def _trades() -> list[dict]:
    return [
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


def test_compare_strategies_returns_all_four_requested_families() -> None:
    results = compare_strategies(_trades(), {"asset-win": Resolution("asset-win", 1), "asset-lose": Resolution("asset-lose", 0)})

    assert [result.strategy for result in results] == list(STRATEGY_FAMILIES)
    assert results[0].strategy == "nothing_happens"
    assert results[0].copied_or_actions == 2
    assert results[0].total_notional_usd > 0
    assert "order-book-free proxy" in results[0].notes
    assert results[1].strategy == "whale_copy"
    assert results[1].copied_or_actions == 2
    assert all(result.total_notional_usd >= 0 for result in results)


def test_comparison_to_dict_is_dashboard_and_report_friendly() -> None:
    results = compare_strategies(_trades(), {"asset-win": Resolution("asset-win", 1), "asset-lose": Resolution("asset-lose", 0)})
    payload = comparison_to_dict(results)

    assert payload[0]["strategy"] == "nothing_happens"
    assert {row["strategy"] for row in payload} == set(STRATEGY_FAMILIES)
