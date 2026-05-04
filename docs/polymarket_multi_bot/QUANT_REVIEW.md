# Quant review — Polymarket multi-bot platform

Date: 2026-05-04  
Scope: paper/backtest math review only. No live trading, funding, wallet, or position actions were taken or recommended.

## Executive verdict

- The four-bot architecture is mathematically reasonable as a **research platform**, but current evidence is not sufficient for live capital deployment.
- The existing whale-copy headline result (`235.91% ROI`, 5 copied trades) is **not trustworthy as an edge claim**. It is a tiny, hindsight-filtered calibration result and should be labeled **overfit / underpowered**.
- The broader whale baseline/variant runs with hundreds of fills (`1.4%–3.0% ROI`) are more informative, but still need walk-forward validation, category splits, order-book reconstruction, realistic latency, fees, and slippage before any claim of repeatable edge.
- Market-making and normal/AMM allocation specs are directionally sound, but current backtest code is a skeleton/proxy. They need order-book snapshots, queue/fill assumptions, inventory accounting, and model calibration before PnL evidence means anything.

## Evidence quality framework added

Added paper-only helpers in `bot/backtest/quant_validation.py` plus focused tests in `tests/test_quant_validation.py` to prevent overclaiming:

- `assess_backtest_evidence(...)` labels runs as `negative_or_no_edge`, `overfit_or_underpowered`, `fragile_positive`, or `candidate_edge_needs_oos`.
- `wilson_hit_rate_interval(...)` makes tiny perfect-hit samples visibly uncertain.
- `adverse_cost_roi_pct(...)` approximates sensitivity to extra execution/latency/fee costs.

Focused verification: `15 passed` for quant/backtest tests.

## Strategy family assessment

### 1. Nothing Ever Happens baseline

**Expected edge source**
- Conservative selection of high-probability markets where price/depth/liquidity/spread filters imply enough margin of safety.
- Dynamic sizing can harvest larger expected edge only when market quality is good.

**Statistical assumptions**
- Market-implied probability is noisy but not perfectly efficient.
- Tail/resolution shocks are rare enough that volume/liquidity/depth filters can improve expected value.
- Fill prices in backtests approximate executable prices after spread/slippage.

**Overfit risk**
- Medium. Existing config knobs can be tuned to historical winners if not walk-forwarded.
- Tail events dominate; a long quiet sample can hide crash risk.

**Expected failure modes**
- Resolution ambiguity, sudden news, category-specific regime shifts, thin-book fills, correlated exposures across similar events.
- Dynamic sizing increases losses if the score is calibrated on stale or biased market-quality fields.

**Needed data**
- Historical market snapshots with bid/ask/depth, market metadata, close/resolution timestamps, fee/tick/min-order fields, and actual skipped reasons.
- Out-of-sample category/time splits.

**Fine-tuning knobs**
- `min_market_volume`, `min_market_liquidity`, `max_bid_ask_spread`, `min_best_ask_depth_usd`, `edge_size_multiplier`, `max_trade_amount`, per-event cap, time-to-resolution guard.

**Backtest interpretation rule**
- Compare against “do nothing” and simple price-threshold baselines; require net ROI after costs, drawdown, and at least hundreds of independent markets before increasing paper allocation.

### 2. Whale / ALT copy bot

**Expected edge source**
- Large absolute trades and market-size-relative trades may reveal informed private research, superior timing, or trader specialization.
- Updated whale definition is mathematically better than pure notional because it catches dominant trades in smaller but still meaningful markets.

**Statistical assumptions**
- Public trade arrival is fast enough to copy before edge is arbitraged away.
- Whale trades are more often informed than hedging/manipulation/noise.
- Trader identity/history is stable and not sample-specific.

**Current evidence**

| Iteration | Copied | ROI | PnL | Quant label |
|---:|---:|---:|---:|---|
| 0 baseline | 313 | 2.16% | $169.07 | candidate for larger OOS testing only |
| 1 liquidity/spread | 5 | -20.74% | -$20.74 | negative / underpowered |
| 2 wallet-quality | 693 | 3.02% | $399.61 | positive but hindsight-contaminated |
| 3 category specialization | 894 | 1.41% | $205.26 | weak positive, needs OOS |
| 4 risk optimized | 14 | 48.50% | $73.41 | overfit / underpowered |
| 5 calibration overlay | 5 | 235.91% | $94.17 | overfit / underpowered |

**Trust verdict on ROI claims**
- Iteration 5 is **not trustworthy**. Five copied trades means the Wilson lower bound for a 5/5 hit-rate is wide; perfect observed hits do not imply a reliable future hit-rate. The filters also use cached-sample wallet scores and calibration overlays, which creates direct selection bias.
- Iterations 0/2/3 are more useful because they have hundreds of fills, but their low ROI can be erased by modest extra latency/slippage/fees. Iteration 2 is especially suspect because wallet quality is computed in-sample.
- No whale-copy result should be used for live trading. The correct next step is paper-only walk-forward testing.

**Expected failure modes**
- Signal arrives after price impact; copy chases the top.
- Whale is hedging, spoofing social attention, or wrong.
- Same wallet quality does not persist out-of-sample.
- Liquidity vanishes or copy consumes too much remaining depth.
- Market-relative rule overweights small markets unless the `$10k` guard and depth filters are enforced.

**Needed data**
- Pre/post-whale order books, signal latency timestamps, full trader histories before each signal only, category labels, market size/open-interest definitions, final resolutions, fee/slippage estimates.

**Fine-tuning knobs**
- Absolute threshold, relative fraction/market-size guard, copy fraction, max copy notional, max liquidity fraction, max signal age, anti-chase midpoint-move cap, spread cap, wallet reliability lookback window, category whitelist, walk-forward training window.

### 3. Inventory-aware market-making bot

**Expected edge source**
- Earn spread/rewards when quote width exceeds adverse-selection, inventory, latency, and fee costs.
- Inventory skew reduces probability of accumulating bad one-sided exposure.

**Statistical assumptions**
- Fill probability and adverse selection can be estimated from order-book/trade dynamics.
- Reservation-price and spread formulas remain meaningful despite binary jump risk.
- The bot can cancel/replace before stale quotes are picked off.

**Overfit risk**
- High without order-book replay. Trade-only data cannot prove market-making edge because queue position, cancellations, and missed fills are invisible.

**Expected failure modes**
- Filled only when quote is stale/toxic; inventory resolves to zero; API latency/rate limits prevent cancels; correlated event inventory piles up; negative-risk mechanics invalidate simple YES/NO exposure.

**Needed data**
- Historical L2 order-book snapshots, order update cadence, trades crossing book, fee/reward fields, tick/min order, timestamp/hash staleness, event correlation/negative-risk grouping.

**Fine-tuning knobs**
- Risk aversion, volatility window, quote TTL, min spread, fee/latency buffer, max inventory, max loss, inventory-size skew, toxic-flow pause threshold, queue haircut, refresh interval.

**Backtest interpretation rule**
- Do not accept proxy PnL. Require conservative fill model: quote fills only when subsequent trades cross the quote after latency and queue haircut; report skipped/stale/toxic pauses.

### 4. Normal-distribution / AMM allocator

**Expected edge source**
- Allocate capital when model probability differs from executable market probability by more than uncertainty, fees, and turnover cost.
- LMSR/AMM logic gives bounded-loss sizing and smoother portfolio-level exposure.

**Statistical assumptions**
- Model probability is calibrated; `sigma` captures real uncertainty and jump risk.
- Z-score edge maps monotonically to expected value.
- Rebalancing costs are lower than expected edge.

**Overfit risk**
- High until probability model is trained out-of-sample. Normal assumptions fail on jumpy event markets.

**Expected failure modes**
- Miscalibrated probabilities, fat tails, resolution edge cases, hidden event correlation, negative-risk placeholders/Other, turnover drag.

**Needed data**
- Calibrated probability forecasts, market prices/depth over time, outcomes, event grouping, fee/slippage, turnover, model confidence history.

**Fine-tuning knobs**
- `sigma_floor`, `z_scale`, max fraction, confidence multiplier, liquidity score, turnover cap, per-event cap, negative-risk whitelist, LMSR `b`/budget mapping.

**Backtest interpretation rule**
- Report calibration curves/Brier score/log loss in addition to PnL. PnL alone can reward miscalibrated high-conviction luck.

## Platform-level assumptions and failure modes

- **Independence is false.** Multiple bots can hold the same event risk; PnL confidence intervals must cluster by event/category, not just count trades.
- **Execution dominates theory.** A 1%–3% gross ROI can disappear with 50–150 bps of extra cost or stale fills.
- **Resolution tails dominate.** Binary payoffs turn small price edges into full-loss outcomes.
- **Data leakage is the main quant risk.** Wallet scoring, category selection, thresholds, and calibration overlays must be computed using only information available before each signal.
- **Dashboard ROI should show trust labels.** Every result card should display copied/action count, sample period, OOS/in-sample flag, cost assumptions, and quant label.

## Required next data/backtests

1. Larger historical snapshots across market categories and time, not only recent closed markets.
2. Walk-forward design: train wallet/category/calibration parameters on period/category A, test on future period/category B.
3. Order-book replay for market-making and anti-chase whale filters.
4. Latency sensitivity: 0s/5s/30s/120s signal delay; +25/+75/+150/+300 bps cost stress.
5. Clustered bootstrap by market/event for confidence intervals.
6. Negative-risk event tests with placeholder/Other exclusion.
7. Separate metrics: gross/net PnL, drawdown, turnover, exposure, skipped reasons, fill count, unique markets, unique traders.

## Recommended paper allocation until evidence improves

- Nothing Ever Happens: keep as baseline; conservative paper weight can remain highest.
- Whale copy: paper-only; use small allocation in simulations; do not trust iteration 4/5 ROI.
- Market maker: quote-plan simulator only; no live quoting.
- Normal/AMM allocator: recommendation/backtest mode only until probability calibration is measured.

## Bottom line

Current work is good research scaffolding, not a validated trading system. The only mathematically defensible claim today is: **some whale-copy variants show positive in-sample paper PnL, but the strongest ROI claims are overfit/underpowered and all four bot families need larger walk-forward, order-book-aware validation before live use.**
