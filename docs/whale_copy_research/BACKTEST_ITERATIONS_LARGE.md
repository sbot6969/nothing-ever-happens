# Whale-Copy Backtest Iteration Report

Best iteration: `5` — `iteration_5_calibration_arbitrage_addons`
Best ROI: `134.33%`; best PnL: `$222.15`

| Iteration | Strategy | Copied | Notional | PnL | ROI | Hit rate | Max DD | Notes |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 0 | iteration_0_baseline_first_visible_large_buy | 1124 | $28100.00 | $-41.32 | -0.15% | 97.2% | $131.56 | Copy first-visible large BUY signals with fixed cap. |
| 1 | iteration_1_liquidity_spread_aware | 73 | $1460.00 | $-571.71 | -39.16% | 39.7% | $582.13 | Require better market liquidity and avoid high entry prices. |
| 2 | iteration_2_wallet_quality_scored | 2721 | $51682.38 | $1891.15 | 3.66% | 88.5% | $32.24 | Keep wallets with positive realized edge inside the cached sample. Research-only; avoid overfitting. |
| 3 | iteration_3_market_type_specialization | 3508 | $57407.04 | $-668.29 | -1.16% | 68.1% | $867.70 | Specialize to best cached category: none. |
| 4 | iteration_4_portfolio_risk_optimized | 150 | $1602.78 | $-653.64 | -40.78% | 30.0% | $668.95 | Smaller Kelly-like sizing, avoid expensive entries and 5m latency-heavy markets. |
| 5 | iteration_5_calibration_arbitrage_addons | 21 | $165.38 | $222.15 | 134.33% | 95.2% | $4.95 | Calibration overlay: lower-price non-5m markets with stronger positive wallet sample score; true CEX/YES-NO arb needs order-book history. High overfit risk. |

## Feasibility notes

- Iteration 5 is a filtered calibration proxy, not proof of executable arbitrage: historical order-book snapshots and CEX candle alignment are required.
- Wallet-quality scoring uses the cached sample and can overfit; use walk-forward validation before live deployment.
- If best ROI is below 100%, keep whale-copy in paper mode and iterate. If above 100% on a small sample, still paper-test because sample bias may be severe.
