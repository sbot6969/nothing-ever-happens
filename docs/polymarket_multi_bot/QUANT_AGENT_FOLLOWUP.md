# Quant agent follow-up

## 2026-05-04 follow-up — voice/backtest coverage audit

Scope: paper/offline quant review only. No live trading, wallets, transfers, position-closing, secrets, or external posting were touched.

### Coverage verified

- Voice requirements trace is consistent with the current backtest state: whale thresholds, research docs, four-bot architecture/dashboard foundations, quant helpers, and first comparable multi-strategy report are present; larger historical/OOS backtests, production allocator/wallet interfaces, final push/runtime restart, and end-to-end monitor delivery remain open.
- Whale classification is implemented and tested for both requested rules: `>= $10,000` absolute notional and `>= 30%` of market size with the `$10,000` market-size guard. Backtest coverage also copies a `$3,000` / `$10,000` relative-market-size whale below the absolute threshold.
- Multi-strategy backtest scaffolding covers all four requested bot families in one report shape: `nothing_happens`, `whale_copy`, `market_making`, and `normal_distribution_amm`.
- Report output includes the requested comparable metrics fields: actions, notional, PnL, ROI, hit rate plus Wilson interval, max drawdown, turnover, max exposure, skipped/rejected reasons, and quant evidence label.
- Quant validation helpers prevent overclaiming by flagging tiny/extreme ROI as `overfit_or_underpowered`, negative runs as `negative_or_no_edge`, drawdown-sensitive positives as `fragile_positive`, and larger in-sample positives only as `candidate_edge_needs_oos`.

### Remaining quant gaps

- Sample size: latest comparable snapshot is only 150 recent closed markets / 20,979 trades; `nothing_happens` has no executable adapter yet, whale-copy has only 5 actions in the comparable report, and no category/time/liquidity cohort expansion is complete.
- Overfit/leakage: whale iteration code still contains in-sample wallet scoring, best-category selection, and calibration overlays; these are documented as research-only but need walk-forward train/test splits before any edge claim.
- Order book/execution: market-making and normal/AMM results are proxy fills from trade rows, not historical L2 replay. Queue position, cancellations, stale quote pickup, fee/reward mechanics, latency, and depth-aware fill probability are still missing.
- Latency/cost robustness: no full delay grid (`0s/5s/30s/120s`) or adverse cost stress grid (`+25/+75/+150/+300 bps`) is wired into the generated report yet.
- Independence/risk: no clustered bootstrap by event/category, event-correlation cap validation, negative-risk/Other placeholder exclusion test, or per-bot portfolio allocator/wallet interface validation is complete.
- Calibration: normal/AMM has no out-of-sample probability model, Brier/log-loss reporting, sigma calibration, or turnover-cost sensitivity; PnL-only evaluation is not acceptable for that family.

### Recommended next quant tasks

1. Implement a real `Nothing Ever Happens` `StrategySignal` adapter and rerun the comparable report with actual skipped reasons instead of `baseline_not_wrapped_yet`.
2. Add walk-forward fixtures/reporting: train wallet/category/calibration parameters only on earlier markets, test on later markets, and mark all rows as in-sample vs OOS.
3. Add L2 order-book snapshot ingestion/replay before treating market-making or AMM PnL as evidence.
4. Extend `BACKTEST_RESULTS.md` generation with category/time/liquidity/wallet-cohort splits, latency/cost grids, and clustered confidence intervals.
5. Keep all four strategy families paper-only until the above passes and a separate security review re-approves any typed live-trading scope.
