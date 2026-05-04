# Whale-Copy Walk-Forward Iteration Validation

Paper/offline only. Iterations are selected using the train slice and then checked on validation and OOS slices.

| Iteration | Strategy | Train copied | Train ROI | Validation copied | Validation ROI | OOS copied | OOS ROI | Selected | Verdict |
|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| 0 | `iteration_0_baseline_first_visible_large_buy` | 384 | -0.63% | 440 | -0.32% | 300 | 0.73% | false | `reject_underpowered` |
| 1 | `iteration_1_liquidity_spread_aware` | 27 | -44.76% | 29 | -40.50% | 17 | -27.97% | false | `reject_underpowered` |
| 2 | `iteration_2_wallet_quality_scored` | 979 | 3.86% | 93 | 3.15% | 62 | -0.26% | false | `reject_underpowered` |
| 3 | `iteration_3_market_type_specialization` | 1152 | -2.21% | 1234 | -1.76% | 1122 | 0.77% | false | `reject_underpowered` |
| 4 | `iteration_4_portfolio_risk_optimized` | 55 | -45.07% | 44 | -77.60% | 51 | -5.50% | false | `reject_underpowered` |
| 5 | `iteration_5_calibration_arbitrage_addons` | 7 | 119.24% | 1 | -100.45% | 1 | -100.31% | true | `selected_on_train_but_rejected_oos_or_sample` |

## Rule

A whale-copy iteration remains paper-only unless train selection survives validation and OOS with enough copied actions and then passes L2/order-lifecycle replay plus live security review.
