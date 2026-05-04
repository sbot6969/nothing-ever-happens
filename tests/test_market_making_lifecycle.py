from bot.backtest.market_making_lifecycle import MarketTick, QuoteIntent, QuoteStatus, liquidity_reward_proxy, simulate_quote_lifecycle


def test_quote_lifecycle_models_queue_miss_then_fill() -> None:
    quote = QuoteIntent("asset", "BUY", price=0.49, size=10, created_ts=100, queue_ahead_size=5)
    events = simulate_quote_lifecycle(quote, [MarketTick(101, 0.48, 0.49, 0.49, 3), MarketTick(102, 0.48, 0.49, 0.49, 20)])

    assert [event.status for event in events] == [QuoteStatus.PLACED, QuoteStatus.MISSED_FILL, QuoteStatus.WOULD_FILL]
    assert events[-1].remaining_size == 0


def test_quote_lifecycle_cancels_stale_quote() -> None:
    events = simulate_quote_lifecycle(QuoteIntent("asset", "SELL", 0.55, 1, 0, ttl_sec=5), [MarketTick(10, 0.50, 0.52)])

    assert events[-2].status == QuoteStatus.STALE
    assert events[-1].status == QuoteStatus.CANCELLED


def test_liquidity_reward_proxy_is_bounded() -> None:
    assert liquidity_reward_proxy(10_000, 1.0, 0) == 5.0
    assert liquidity_reward_proxy(10_000, 1.0, 500) == 0.0
