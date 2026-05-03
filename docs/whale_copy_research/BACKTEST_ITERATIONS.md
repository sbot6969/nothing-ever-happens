# Whale-Copy Backtest Iteration Report

Best iteration: `5` — `iteration_5_calibration_arbitrage_addons`
Best ROI: `235.91%`; best PnL: `$94.17`

| Iteration | Strategy | Copied | Notional | PnL | ROI | Hit rate | Max DD | Notes |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | iteration_0_baseline_first_visible_large_buy | 313 | $7825.00 | $169.07 | 2.16% | 99.4% | $25.02 | Copy first-visible large BUY signals with fixed cap. |
| 1 | iteration_1_liquidity_spread_aware | 5 | $100.00 | $-20.74 | -20.74% | 60.0% | $29.05 | Require better market liquidity and avoid high entry prices. |
| 2 | iteration_2_wallet_quality_scored | 693 | $13231.37 | $399.61 | 3.02% | 87.4% | $32.24 | Keep wallets with positive realized edge inside the cached sample. Research-only; avoid overfitting. |
| 3 | iteration_3_market_type_specialization | 894 | $14527.95 | $205.26 | 1.41% | 65.3% | $52.73 | Specialize to best cached category: none. |
| 4 | iteration_4_portfolio_risk_optimized | 14 | $151.35 | $73.41 | 48.50% | 64.3% | $24.93 | Smaller Kelly-like sizing, avoid expensive entries and 5m latency-heavy markets. |
| 5 | iteration_5_calibration_arbitrage_addons | 5 | $39.92 | $94.17 | 235.91% | 100.0% | $0.00 | Calibration overlay: lower-price non-5m markets with stronger positive wallet sample score; true CEX/YES-NO arb needs order-book history. High overfit risk. |

## Feasibility notes

- Iteration 5 is a filtered calibration proxy, not proof of executable arbitrage: historical order-book snapshots and CEX candle alignment are required.
- Wallet-quality scoring uses the cached sample and can overfit; use walk-forward validation before live deployment.
- If best ROI is below 100%, keep whale-copy in paper mode and iterate. If above 100% on a small sample, still paper-test because sample bias may be severe.
