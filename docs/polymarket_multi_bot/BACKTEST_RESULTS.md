# Multi-Bot Backtest Results

Generated: `2026-05-04T16:28:18.659463+00:00`

## Safety / interpretation

- Paper/offline report only; no live orders, wallet creation, transfers, position closes, or live-trading toggles were performed.
- Market-making and normal/AMM rows are conservative skeleton/proxy simulations until historical order-book/queue data exists.
- `candidate_edge_needs_oos` means larger out-of-sample validation is justified; it is **not** live-trading approval.
- `overfit_or_underpowered` is expected for small or heavily filtered samples and must not be marketed as real edge.

## Snapshot

- Snapshot dir: `artifacts/whale_copy/closed_recent_150`
- Created at: `2026-05-04T15:56:33.272064+00:00`
- Market limit: `150`; markets saved: `150`
- Trades per market cap: `300`; trades saved: `20979`
- Resolution assets: `300`
- Note: Public Gamma closed markets + Data API trades only; no private data or live trading.
- Note: history_count is first-visible within this downloaded snapshot, not proof of wallet's entire Polymarket lifetime.
- Note: Closed markets with non-0/1 outcome prices are skipped as unresolved/ambiguous.

## Comparable metrics

| Strategy | Actions | Notional | PnL | ROI | Hit rate | 95% hit-rate interval | Max DD | Turnover | Max exposure | Skipped | Evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `nothing_happens` | 8556 | $10,107.18 | $-414.24 | -4.10% | 15.09% | 14.3–15.9% | $414.24 | $10,107.18 | $5.00 | 12423 | `negative_or_no_edge` |
| `whale_copy` | 5 | $125.00 | $0.03 | 0.02% | 100.00% | 56.6–100.0% | $0.00 | $125.00 | $25.00 | 20974 | `overfit_or_underpowered` |
| `market_making` | 3544 | $1,844.95 | $55.34 | 3.00% | 47.07% | 45.4–48.7% | $0.00 | $3,689.90 | $5.00 | 17435 | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 20979 | $13,037.63 | $-121.75 | -0.93% | 63.04% | 62.4–63.7% | $121.75 | $13,037.63 | $3.00 | 0 | `negative_or_no_edge` |

## Skipped / rejected signal reasons

### `nothing_happens`

- Top reasons: outside_max_entry_price: 12194; below_min_market_size_proxy: 229
- Evidence reasons: non-positive net PnL/ROI
- Notes: Executable paper adapter for existing entry gates using public trade snapshots as an order-book-free proxy; needs L2 replay before production claims.
- Provenance: {"market_size_source": "missing (20979)"}

### `whale_copy`

- Top reasons: below_min_notional: 14100; non_buy_trade: 6861; prior_wallet_history: 13
- Evidence reasons: sample too small: 5 copied actions < 100; notional too small: $125.00 < $1000.00
- Notes: Copies qualified whale BUY signals using paper sizing and conservative execution costs.
- Provenance: {"market_size_source": "missing (20979)"}

### `market_making`

- Top reasons: outside_centered_price_band: 17435
- Evidence reasons: positive in-sample evidence with adequate fill/notional count; still requires walk-forward/OOS validation
- Notes: Paper skeleton for inventory/spread-aware quoting; needs historical order books before production claims.
- Provenance: {"market_size_source": "missing (20979)"}

### `normal_distribution_amm`

- Top reasons: —
- Evidence reasons: non-positive net PnL/ROI
- Notes: Paper allocation skeleton using probability-centered sizing; requires calibrated distributions before live use.
- Provenance: {"market_size_source": "missing (20979)"}

## Next backtest work

- Add historical order-book snapshots to replace market-making and AMM proxy fills with queue/depth-aware simulations.
- Split results by category, close-time bucket, liquidity bucket, and whale-wallet cohort.
- Run walk-forward/OOS validation instead of scoring wallets on the same cached sample used for reporting.
- Replace trade-snapshot proxies with historical L2/order lifecycle data before production claims.
- Keep all live-financial actions blocked until separate typed confirmation and another security review.
