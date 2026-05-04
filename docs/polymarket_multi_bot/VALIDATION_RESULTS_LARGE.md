# Multi-Bot Walk-Forward / Cohort Validation

Paper/offline validation only. These tables do not authorize live trading, wallet funding, position closing, or transfers.

## Walk-forward / OOS slices

### `train_early` (14000 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 5851 | $-333.05 | -5.12% | `negative_or_no_edge` |
| `whale_copy` | 8 | $2.76 | 1.38% | `overfit_or_underpowered` |
| `market_making` | 1236 | $-2.24 | -0.33% | `negative_or_no_edge` |
| `normal_distribution_amm` | 14000 | $-161.87 | -2.87% | `negative_or_no_edge` |

### `validation_middle` (14000 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 4606 | $-359.96 | -6.94% | `negative_or_no_edge` |
| `whale_copy` | 9 | $0.05 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1030 | $-13.32 | -2.70% | `negative_or_no_edge` |
| `normal_distribution_amm` | 14000 | $-117.83 | -2.39% | `negative_or_no_edge` |

### `oos_late` (14000 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 5418 | $-236.29 | -3.74% | `negative_or_no_edge` |
| `whale_copy` | 4 | $0.02 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 2094 | $68.81 | 6.23% | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 14000 | $25.16 | 0.32% | `candidate_edge_needs_oos` |

### `category:unknown` (42000 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 15875 | $-929.30 | -5.16% | `negative_or_no_edge` |
| `whale_copy` | 21 | $2.82 | 0.54% | `overfit_or_underpowered` |
| `market_making` | 4360 | $53.25 | 2.35% | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 42000 | $-254.54 | -1.37% | `negative_or_no_edge` |

### `liquidity:liquidity_missing_or_zero` (42000 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 15875 | $-929.30 | -5.16% | `negative_or_no_edge` |
| `whale_copy` | 21 | $2.82 | 0.54% | `overfit_or_underpowered` |
| `market_making` | 4360 | $53.25 | 2.35% | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 42000 | $-254.54 | -1.37% | `negative_or_no_edge` |

### `time:time_early` (14001 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 5851 | $-333.05 | -5.12% | `negative_or_no_edge` |
| `whale_copy` | 8 | $2.76 | 1.38% | `overfit_or_underpowered` |
| `market_making` | 1236 | $-2.24 | -0.33% | `negative_or_no_edge` |
| `normal_distribution_amm` | 14001 | $-161.87 | -2.87% | `negative_or_no_edge` |

### `time:time_middle` (14000 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 4606 | $-359.96 | -6.94% | `negative_or_no_edge` |
| `whale_copy` | 9 | $0.05 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1030 | $-13.32 | -2.70% | `negative_or_no_edge` |
| `normal_distribution_amm` | 14000 | $-117.82 | -2.39% | `negative_or_no_edge` |

### `time:time_late` (13999 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 5418 | $-236.29 | -3.74% | `negative_or_no_edge` |
| `whale_copy` | 4 | $0.02 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 2094 | $68.81 | 6.23% | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 13999 | $25.15 | 0.32% | `candidate_edge_needs_oos` |

## Latency / cost stress grid

| Strategy | Extra cost bps | Base ROI | Stressed ROI |
|---|---:|---:|---:|
| `nothing_happens` | 0 | -5.16% | -5.16% |
| `nothing_happens` | 25 | -5.16% | -5.41% |
| `nothing_happens` | 50 | -5.16% | -5.66% |
| `nothing_happens` | 100 | -5.16% | -6.16% |
| `nothing_happens` | 200 | -5.16% | -7.16% |
| `whale_copy` | 0 | 0.54% | 0.54% |
| `whale_copy` | 25 | 0.54% | 0.29% |
| `whale_copy` | 50 | 0.54% | 0.04% |
| `whale_copy` | 100 | 0.54% | -0.46% |
| `whale_copy` | 200 | 0.54% | -1.46% |
| `market_making` | 0 | 2.35% | 2.35% |
| `market_making` | 25 | 2.35% | 2.10% |
| `market_making` | 50 | 2.35% | 1.85% |
| `market_making` | 100 | 2.35% | 1.35% |
| `market_making` | 200 | 2.35% | 0.35% |
| `normal_distribution_amm` | 0 | -1.37% | -1.37% |
| `normal_distribution_amm` | 25 | -1.37% | -1.62% |
| `normal_distribution_amm` | 50 | -1.37% | -1.87% |
| `normal_distribution_amm` | 100 | -1.37% | -2.37% |
| `normal_distribution_amm` | 200 | -1.37% | -3.37% |

## Interpretation

- Any strategy whose result only appears in one cohort is treated as underpowered/possibly overfit.
- Extra cost bps approximates fees, slippage, queue loss, and latency decay; true market-making validation still needs L2/order-book replay.
- Live finance remains blocked until typed confirmation plus fresh security/secret/wallet review.
