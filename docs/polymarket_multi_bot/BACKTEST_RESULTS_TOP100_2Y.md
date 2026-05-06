# Multi-Bot Backtest Results

Generated: `2026-05-04T22:26:12.805010+00:00`

## Safety / interpretation

- Paper/offline report only; no live orders, wallet creation, transfers, position closes, or live-trading toggles were performed.
- Market-making and normal/AMM rows are conservative skeleton/proxy simulations until historical order-book/queue data exists.
- `candidate_edge_needs_oos` means larger out-of-sample validation is justified; it is **not** live-trading approval.
- `overfit_or_underpowered` is expected for small or heavily filtered samples and must not be marketed as real edge.

## Snapshot

- Snapshot dir: `artifacts/whale_copy/top100_two_year`
- Created at: `2026-05-04T22:26:02.031905+00:00`
- Market limit: `100`; markets saved: `100`
- Trades per market cap: `2000`; trades saved: `200000`
- Resolution assets: `200`
- Note: Public Gamma/Data API paper-only snapshot; no secrets, wallets, or live trading paths used.
- Note: Two-year window: 2024-05-04T22:23:19.783709+00:00 to 2026-05-04T22:23:19.783709+00:00.
- Note: Selected top markets by Gamma volumeNum from 500 closed-market candidates; target top markets saved: 100.
- Note: Trades are paginated from Data API with max 2000 rows per market, then globally sorted by timestamp.
- Note: history_count is first-visible within this downloaded two-year snapshot, not proof of wallet lifetime outside the snapshot.
- Note: Market-making and AMM results remain trade-snapshot proxy backtests without historical L2 order book queue/depth.

## Comparable metrics

| Strategy | Actions | Notional | PnL | ROI | Hit rate | 95% hit-rate interval | Max DD | Turnover | Max exposure | Skipped | Evidence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `nothing_happens` | 78790 | $96,259.04 | $-1,809.22 | -1.88% | 0.55% | 0.5–0.6% | $1,809.22 | $96,259.04 | $5.00 | 121210 | `negative_or_no_edge` |
| `whale_copy` | 567 | $14,175.00 | $-46.44 | -0.33% | 99.47% | 98.5–99.8% | $63.39 | $14,175.00 | $25.00 | 199433 | `negative_or_no_edge` |
| `market_making` | 2688 | $3,637.16 | $-535.83 | -14.73% | 28.57% | 26.9–30.3% | $535.83 | $7,274.32 | $5.00 | 197312 | `negative_or_no_edge` |
| `normal_distribution_amm` | 200000 | $11,111.19 | $-896.62 | -8.07% | 60.82% | 60.6–61.0% | $896.62 | $11,111.19 | $2.52 | 0 | `negative_or_no_edge` |

## Skipped / rejected signal reasons

### `nothing_happens`

- Top reasons: outside_max_entry_price: 121210
- Evidence reasons: non-positive net PnL/ROI
- Notes: Executable paper adapter for existing entry gates using public trade snapshots as an order-book-free proxy; needs L2 replay before production claims.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum top-100-by-volume two-year snapshot (200000)"}

### `whale_copy`

- Top reasons: below_min_notional: 130520; non_buy_trade: 67235; prior_wallet_history: 1678
- Evidence reasons: non-positive net PnL/ROI
- Notes: Copies qualified whale BUY signals using paper sizing and conservative execution costs.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum top-100-by-volume two-year snapshot (200000)"}

### `market_making`

- Top reasons: outside_centered_price_band: 197312
- Evidence reasons: non-positive net PnL/ROI
- Notes: Paper skeleton for inventory/spread-aware quoting; needs historical order books before production claims.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum top-100-by-volume two-year snapshot (200000)"}

### `normal_distribution_amm`

- Top reasons: —
- Evidence reasons: non-positive net PnL/ROI
- Notes: Paper allocation skeleton using probability-centered sizing; requires calibrated distributions before live use.
- Provenance: {"market_size_source": "Polymarket Gamma API closed-market volumeNum top-100-by-volume two-year snapshot (200000)"}

## Next backtest work

- Add historical order-book snapshots to replace market-making and AMM proxy fills with queue/depth-aware simulations.
- Split results by category, close-time bucket, liquidity bucket, and whale-wallet cohort.
- Run walk-forward/OOS validation instead of scoring wallets on the same cached sample used for reporting.
- Replace trade-snapshot proxies with historical L2/order lifecycle data before production claims.
- Keep live-financial expansion blocked until strategy evidence, per-bot caps, security review, and runbook checks are all green.
