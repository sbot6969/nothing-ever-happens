from __future__ import annotations

import pytest

from bot.whale_thresholds import classify_whale_trade, market_size_usd, trade_notional_usd


def test_absolute_whale_threshold_detects_10000_notional() -> None:
    result = classify_whale_trade({"size": 20_000, "price": 0.5, "market_size_usd": 1_000_000})

    assert result.is_whale is True
    assert result.reason == "absolute_notional_threshold"
    assert result.notional_usd == 10_000


def test_relative_market_size_threshold_detects_30_percent_of_large_market() -> None:
    result = classify_whale_trade({"notional_usd": 3_000, "market_size_usd": 10_000})

    assert result.is_whale is True
    assert result.reason == "relative_market_size_threshold"
    assert result.relative_market_fraction == pytest.approx(0.30)


def test_relative_threshold_requires_market_size_guard() -> None:
    result = classify_whale_trade({"notional_usd": 2_700, "market_size_usd": 9_000})

    assert result.is_whale is False
    assert result.reason == "below_whale_threshold"
    assert result.relative_market_fraction == pytest.approx(0.30)


def test_below_both_thresholds_is_not_whale() -> None:
    result = classify_whale_trade({"notional_usd": 2_999.99, "market_size_usd": 10_000})

    assert result.is_whale is False
    assert result.reason == "below_whale_threshold"


def test_missing_market_size_can_still_use_absolute_threshold() -> None:
    result = classify_whale_trade({"notionalUsd": 10_001})

    assert result.is_whale is True
    assert result.reason == "absolute_notional_threshold"
    assert result.market_size_usd is None


def test_notional_prefers_explicit_amount_and_market_size_aliases() -> None:
    trade = {"notionalUsd": "123.45", "size": 999, "price": 0.9, "marketVolumeUsd": "50000"}

    assert trade_notional_usd(trade) == 123.45
    assert market_size_usd(trade) == 50_000
