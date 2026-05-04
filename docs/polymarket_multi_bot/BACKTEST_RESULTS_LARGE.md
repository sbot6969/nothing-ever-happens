# Multi-Bot Backtest Results

Generated: `2026-05-04T16:35:51.637390+00:00`

## Safety / interpretation

- Paper/offline report only; no live orders, wallet creation, transfers, position closes, or live-trading toggles were performed.
- Market-making and normal/AMM rows are conservative skeleton/proxy simulations until historical order-book/queue data exists.
- `candidate_edge_needs_oos` means larger out-of-sample validation is justified; it is **not** live-trading approval.
- `overfit_or_underpowered` is expected for small or heavily filtered samples and must not be marketed as real edge.

## Snapshot

- Snapshot dir: `artifacts/whale_copy/closed_recent_300`
- Created at: `2026-05-04T16:34:16.874138+00:00`
- Market limit: `300`; markets saved: `300`
- Trades per market cap: `250`; trades saved: `42000`
- Resolution assets: `600`
- Note: Public Gamma closed markets + Data API trades only; no private data or live trading.
- Note: history_count is first-visible within this downloaded snapshot, not proof of wallet's entire Polymarket lifetime.
- Note: Closed markets with non-0/1 outcome prices are skipped as unresolved/ambiguous.
- Note: market_size_usd uses Polymarket Gamma API closed-market volumeNum; it is a historical activity proxy, not current executable depth.

## Comparable metrics

| Strategy | Actions | Notional | PnL | ROI | Hit rate | 95% hit-rate interval | Max DD | Turnover | Max exposure | Skipped | Evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `nothing_happens` | 15875 | $18,010.51 | $-929.30 | -5.16% | 8.69% | 8.3–9.1% | $929.30 | $18,010.51 | $5.00 | 26125 | `negative_or_no_edge` |
| `whale_copy` | 21 | $525.00 | $2.82 | 0.54% | 100.00% | 84.5–100.0% | $0.00 | $525.00 | $25.00 | 41979 | `overfit_or_underpowered` |
| `market_making` | 4360 | $2,270.63 | $53.25 | 2.35% | 45.62% | 44.1–47.1% | $0.00 | $4,541.26 | $5.00 | 37640 | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 42000 | $18,558.52 | $-254.54 | -1.37% | 64.10% | 63.6–64.6% | $254.54 | $18,558.52 | $3.00 | 0 | `negative_or_no_edge` |

## Skipped / rejected signal reasons

### `nothing_happens`

- Top reasons: outside_max_entry_price: 25800; below_min_market_size_proxy: 325
- Evidence reasons: non-positive net PnL/ROI
- Notes: Executable paper adapter for existing entry gates using public trade snapshots as an order-book-free proxy; needs L2 replay before production claims.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum (42000)"}

### `whale_copy`

- Top reasons: below_min_notional: 28165; non_buy_trade: 13741; prior_wallet_history: 73
- Evidence reasons: sample too small: 21 copied actions < 100; notional too small: $525.00 < $1000.00
- Notes: Copies qualified whale BUY signals using paper sizing and conservative execution costs.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum (42000)"}

### `market_making`

- Top reasons: outside_centered_price_band: 37640
- Evidence reasons: positive in-sample evidence with adequate fill/notional count; still requires walk-forward/OOS validation
- Notes: Paper skeleton for inventory/spread-aware quoting; needs historical order books before production claims.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum (42000)"}

### `normal_distribution_amm`

- Top reasons: —
- Evidence reasons: non-positive net PnL/ROI
- Notes: Paper allocation skeleton using probability-centered sizing; requires calibrated distributions before live use.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum (42000)"}

## Next backtest work

- Add historical order-book snapshots to replace market-making and AMM proxy fills with queue/depth-aware simulations.
- Split results by category, close-time bucket, liquidity bucket, and whale-wallet cohort.
- Run walk-forward/OOS validation instead of scoring wallets on the same cached sample used for reporting.
- Replace trade-snapshot proxies with historical L2/order lifecycle data before production claims.
- Keep all live-financial actions blocked until separate typed confirmation and another security review.
