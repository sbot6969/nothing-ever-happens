# Multi-Bot Walk-Forward / Cohort Validation

Paper/offline validation only. These tables do not authorize live trading, wallet funding, position closing, or transfers.

## Walk-forward / OOS slices

### `train_early` (6993 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 2792 | $-135.09 | -4.19% | `negative_or_no_edge` |
| `whale_copy` | 1 | $0.01 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1090 | $7.54 | 1.43% | `overfit_or_underpowered` |
| `normal_distribution_amm` | 6993 | $-112.19 | -2.71% | `negative_or_no_edge` |

### `validation_middle` (6993 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 2763 | $-117.97 | -3.55% | `negative_or_no_edge` |
| `whale_copy` | 1 | $0.01 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1187 | $44.68 | 6.33% | `overfit_or_underpowered` |
| `normal_distribution_amm` | 6993 | $18.41 | 0.42% | `candidate_edge_needs_oos` |

### `oos_late` (6993 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 3001 | $-161.18 | -4.53% | `negative_or_no_edge` |
| `whale_copy` | 3 | $0.02 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1267 | $3.13 | 0.51% | `overfit_or_underpowered` |
| `normal_distribution_amm` | 6993 | $-27.97 | -0.62% | `negative_or_no_edge` |

### `category:unknown` (20979 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 8556 | $-414.24 | -4.10% | `negative_or_no_edge` |
| `whale_copy` | 5 | $0.03 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 3544 | $55.34 | 3.00% | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 20979 | $-121.75 | -0.93% | `negative_or_no_edge` |

### `liquidity:liquidity_missing_or_zero` (20979 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 8556 | $-414.24 | -4.10% | `negative_or_no_edge` |
| `whale_copy` | 5 | $0.03 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 3544 | $55.34 | 3.00% | `candidate_edge_needs_oos` |
| `normal_distribution_amm` | 20979 | $-121.75 | -0.93% | `negative_or_no_edge` |

### `time:time_early` (6994 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 2792 | $-135.09 | -4.19% | `negative_or_no_edge` |
| `whale_copy` | 1 | $0.01 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1091 | $7.57 | 1.44% | `overfit_or_underpowered` |
| `normal_distribution_amm` | 6994 | $-111.73 | -2.70% | `negative_or_no_edge` |

### `time:time_middle` (6993 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 2764 | $-118.29 | -3.56% | `negative_or_no_edge` |
| `whale_copy` | 1 | $0.01 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1187 | $44.64 | 6.33% | `overfit_or_underpowered` |
| `normal_distribution_amm` | 6993 | $17.34 | 0.39% | `candidate_edge_needs_oos` |

### `time:time_late` (6992 rows)

| Strategy | Actions | PnL | ROI | Evidence |
|---|---:|---:|---:|---|
| `nothing_happens` | 3000 | $-160.86 | -4.52% | `negative_or_no_edge` |
| `whale_copy` | 3 | $0.02 | 0.02% | `overfit_or_underpowered` |
| `market_making` | 1266 | $3.13 | 0.51% | `overfit_or_underpowered` |
| `normal_distribution_amm` | 6992 | $-27.36 | -0.61% | `negative_or_no_edge` |

## Latency / cost stress grid

| Strategy | Extra cost bps | Base ROI | Stressed ROI |
|---|---:|---:|---:|
| `nothing_happens` | 0 | -4.10% | -4.10% |
| `nothing_happens` | 25 | -4.10% | -4.35% |
| `nothing_happens` | 50 | -4.10% | -4.60% |
| `nothing_happens` | 100 | -4.10% | -5.10% |
| `nothing_happens` | 200 | -4.10% | -6.10% |
| `whale_copy` | 0 | 0.02% | 0.02% |
| `whale_copy` | 25 | 0.02% | -0.23% |
| `whale_copy` | 50 | 0.02% | -0.48% |
| `whale_copy` | 100 | 0.02% | -0.98% |
| `whale_copy` | 200 | 0.02% | -1.98% |
| `market_making` | 0 | 3.00% | 3.00% |
| `market_making` | 25 | 3.00% | 2.75% |
| `market_making` | 50 | 3.00% | 2.50% |
| `market_making` | 100 | 3.00% | 2.00% |
| `market_making` | 200 | 3.00% | 1.00% |
| `normal_distribution_amm` | 0 | -0.93% | -0.93% |
| `normal_distribution_amm` | 25 | -0.93% | -1.18% |
| `normal_distribution_amm` | 50 | -0.93% | -1.43% |
| `normal_distribution_amm` | 100 | -0.93% | -1.93% |
| `normal_distribution_amm` | 200 | -0.93% | -2.93% |

## Conservative simulation coverage added

- Market-making lifecycle simulator covers quote placed, replaced, cancelled, stale, would-fill, missed-fill, and queue-ahead cases.
- Liquidity reward economics are modeled only as a bounded proxy; not a real maker-reward claim.
- Probability/AMM helpers require `p_model` confidence gates and report Brier/log-loss calibration.
- Negative-risk/`Other` placeholder detection is tested so allocation logic does not silently assume a complete binary pair.

## Interpretation

- Any strategy whose result only appears in one cohort is treated as underpowered/possibly overfit.
- Extra cost bps approximates fees, slippage, queue loss, and latency decay; true market-making validation still needs L2/order-book replay.
- Live finance remains blocked until typed confirmation plus fresh security/secret/wallet review.
