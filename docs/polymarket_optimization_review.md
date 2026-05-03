# Polymarket bot optimization review

## Research signals used

- Polymarket CLOB docs recommend SDK clients for signing/auth, and emphasize order-book, prices, spreads, tick sizes, min order sizes, and live order querying.
- `py-clob-client` examples and docs center execution around current book/rules, not stale Gamma prices.
- Practical bot patterns from CLOB/market-making bots: avoid thin books, avoid wide spreads, cap slippage/price impact, rank opportunities, size by expected edge and liquidity, keep hard risk caps and retry/backoff.

## Main issues found

1. Entries were accepted mostly by top ask and `max_entry_price`; thin top-of-book and wide spread could still pass.
2. Pending queue was FIFO-ish, so a mediocre market could execute before a clearly better one.
3. Position size was static/fixed/cash-percent only; it did not distinguish a deep, tight, high-quality entry from a marginal one.
4. Config had no explicit market volume/liquidity gates, making stale/illiquid markets easier to enter.

## Implemented

- Added configurable market quality filters:
  - `min_market_volume`
  - `min_market_liquidity`
  - `max_bid_ask_spread`
  - `min_best_ask_depth_usd`
- Added entry quality scoring from:
  - discount to `max_entry_price`
  - bid/ask spread
  - safe depth under price cap
  - best ask depth
  - Gamma volume/liquidity
- Pending entries now dispatch highest-score due opportunity first instead of arbitrary insertion order.
- Added optional dynamic sizing:
  - `dynamic_position_sizing_enabled`
  - `edge_size_multiplier`
  - `max_trade_amount`
- Kept everything backward-compatible and disabled by default unless config/env enables it.

## Suggested conservative config to try first

```json
{
  "min_market_volume": 250,
  "min_market_liquidity": 100,
  "max_bid_ask_spread": 0.05,
  "min_best_ask_depth_usd": 5,
  "dynamic_position_sizing_enabled": true,
  "edge_size_multiplier": 0.5,
  "max_trade_amount": 8
}
```

Tune upward if fills are too noisy; tune downward if too few trades appear.

## Verification

- `./venv/bin/python -m pytest tests/test_config.py tests/test_nothing_happens.py -q` → `46 passed`
