# Polymarket multi-bot research appendix

Date: 2026-05-04
Agent: research-agent

Scope: additional source-backed technical research for paper-mode design of the Polymarket multi-bot platform. This appendix focuses on sources that translate into implementation details for market making, prediction-market allocation, CLOB mechanics, AMMs, adverse selection, and bankroll/risk control. No secrets were read or exposed; no third-party bots were run; no live trading/funds/wallet actions were touched.

## Highest-value additions

1. **Use a two-layer market-maker control loop:** reservation-price/inventory skew for quote placement plus explicit size skew and side shutoff. Inventory-aware papers give the math; Hummingbot/crypto practice shows the operational guardrail.
2. **Backtests must model order state, not only trades.** Quote strategies require cancel/replace TTL, queue haircut, stale-book detection, and missed-fill accounting; otherwise simulated spread capture is fantasy.
3. **Binary markets need event-level accounting.** Kalshi and Polymarket docs both imply YES/NO complementarity; Polymarket negative-risk markets add conversion mechanics. Exposure and arbitrage checks should be event-aware, not isolated by token.
4. **Allocation should be fractional-Kelly / capped-loss, not raw edge sizing.** Prediction-market outcomes are jumpy and resolution risk is discontinuous; use Kelly only as an upper bound, then haircut aggressively.
5. **AMM math is useful even on a CLOB.** LMSR/convex-cost/CFMM sources can drive target inventory and fair-price curves while execution remains Polymarket limit-order paper simulation.

## Source notes and applicability

### A. Market making and inventory risk

#### Guéant, Lehalle & Fernandez-Tapia — inventory-risk solution for market making

- Source: Olivier Guéant, Charles-Albert Lehalle, Joaquin Fernandez-Tapia, “Dealing with the Inventory Risk. A solution to the market making problem,” arXiv:1105.3115, https://arxiv.org/abs/1105.3115
- Source type: academic paper / arXiv, market microstructure.
- Key finding: extends Avellaneda-Stoikov-style market making into practical inventory-risk controls and approximations for quote placement.
- Applicability:
  - Implement `InventoryAwareQuoteEngine` with separate knobs for risk aversion, inventory penalty, and quote width.
  - Quote engine should output **no quote** when incremental fill would breach max loss or event exposure.
  - Inventory penalty should scale with binary payoff exposure, not only mark-to-market USDC.
- TODO translation:
  - Add tests where long-YES inventory lowers/blocks further bids and makes asks more aggressive.
  - Add sensitivity report over risk-aversion values; do not tune on one ROI result.

#### Guilbaud & Pham — optimal HFT with limit and market orders

- Source: Fabien Guilbaud and Huyen Pham, “Optimal High Frequency Trading with limit and market orders,” arXiv:1106.5040, https://arxiv.org/abs/1106.5040
- Source type: academic paper / arXiv, market microstructure.
- Key finding: market-making decisions are a control problem over limit orders and market orders with inventory and order-book state; order type choice matters.
- Applicability:
  - Polymarket maker bot should remain quote-plan only at first, but simulator should represent order type (`GTC`, `GTD`, `FAK`, `FOK`) and cancellation rules.
  - Whale-copy taker logic should be separate from maker quoting; do not let maker logic cross the spread.
- TODO translation:
  - Add `OrderIntent`/`QuotePlan` fields for `maker_only`, `ttl_seconds`, `cancel_before_replace`, `max_cross_bps`.
  - In backtests, report maker fills separately from taker/copy fills.

#### Glosten & Milgrom — adverse selection in bid/ask spreads

- Source: Lawrence R. Glosten and Paul R. Milgrom, “Bid, ask and transaction prices in a specialist market with heterogeneously informed traders,” Journal of Financial Economics 14(1), 1985, DOI: https://doi.org/10.1016/0304-405X(85)90044-3
- Source type: canonical market microstructure paper.
- Key finding: spreads compensate liquidity providers for trading against informed flow; observed fills can be bad news, not proof of edge.
- Applicability:
  - In Polymarket, informed flow includes large/whale trades, news shocks, and final-resolution information.
  - A market-making bot should widen/pause after large directional trades instead of automatically re-quoting.
- TODO translation:
  - Add `toxic_flow_score`: large trade notional, market-relative notional, midpoint jump, one-sided fill streak, time-to-resolution.
  - Backtest adverse-selection PnL: mark each maker fill to next midpoint and to resolution.

#### Kyle — price impact and informed trading

- Source: Albert S. Kyle, “Continuous Auctions and Insider Trading,” Econometrica 53(6), 1985, JSTOR stable URL: https://www.jstor.org/stable/1913210
- Source type: canonical market microstructure paper.
- Key finding: informed order flow has price impact; trade size can reveal information but also decays as liquidity absorbs it.
- Applicability:
  - Whale-copy signal score should include notional, market-relative notional, and subsequent price impact.
  - Copying after the impact has already occurred is likely negative EV.
- TODO translation:
  - Add `post_trade_midpoint_move_bps` and `remaining_depth_after_trade` to whale-copy filters.
  - Reject copy signals after the book has moved more than allowed slippage from pre-trade midpoint.

### B. Prediction-market and AMM design

#### Othman & Sandholm — liquidity-sensitive automated market makers

- Source: Abraham Othman and Tuomas Sandholm, “Automated Market Makers That Enable New Settings: Extending LMSR to Combinatorial Prediction Markets,” ACM EC-era work; CMU author/research page: https://www.cs.cmu.edu/~sandholm/
- Source type: academic research line; source URL is a research homepage when direct PDFs move.
- Key finding: fixed-liquidity LMSR can be extended or adapted when liquidity needs vary across outcomes/states.
- Applicability:
  - Normal/AMM allocator should not use one global `b`; use market/event-specific liquidity based on volume, time-to-resolution, uncertainty, and bankroll.
  - Thin markets should receive smaller `b`/target exposure even if the edge looks large.
- TODO translation:
  - Implement `liquidity_budget = f(bankroll, market_depth, volume, confidence, event_cap)` and map that to LMSR/normal allocation parameters.
  - Compare fixed-`b` vs adaptive-`b` allocation in paper backtests.

#### Abernethy, Chen & Vaughan — convex optimization view of market making

- Source: Jacob Abernethy, Yiling Chen, and Jennifer Wortman Vaughan, “Efficient Market Making via Convex Optimization, and a Connection to Online Learning,” JMLR 14, 2013. JMLR index: https://www.jmlr.org/papers/ ; paper title page may move across mirrors.
- Source type: academic paper / JMLR.
- Key finding: market makers can be represented as convex cost functions; risk/liquidity tradeoffs become explicit design choices.
- Applicability:
  - Define a common `CostFunctionAllocator` interface so LMSR, quadratic, and normal/z-score allocation can share metrics.
  - Treat cost-function output as desired exposure, not immediate execution.
- TODO translation:
  - Add `target_exposure()` and `marginal_price()` interfaces with unit tests for monotonicity, bounded loss, and budget conservation.

#### Hanson — LMSR bounded-loss market scoring rule

- Source: Robin Hanson, “Logarithmic Market Scoring Rules for Modular Combinatorial Information Aggregation,” author PDF: https://mason.gmu.edu/~rhanson/mktscore.pdf
- Source type: primary academic PDF.
- Key finding: LMSR gives continuous prices and bounded worst-case loss controlled by liquidity parameter `b`.
- Applicability:
  - Use LMSR as a sizing/fair-price benchmark for binary market exposure.
  - Maximum loss bound is useful for paper capital accounting and dashboard risk display.
- TODO translation:
  - Dashboard should show allocator `b`, remaining budget, worst-case loss, and target-vs-current exposure.

#### Angeris & Chitra — constant-function market makers as price oracles

- Source: Guillermo Angeris and Tarun Chitra, “Improved Price Oracles: Constant Function Market Makers,” arXiv:2003.10001, https://arxiv.org/abs/2003.10001
- Source type: academic paper / arXiv, DeFi AMM microstructure.
- Key finding: CFMM prices can act as oracle-like summaries but are sensitive to liquidity and arbitrage assumptions.
- Applicability:
  - AMM-derived fair prices should be treated as model outputs with confidence/latency assumptions, not truth.
  - For Polymarket CLOB, use AMM math for target inventory curves and compare against executable book prices.
- TODO translation:
  - Record model price, executable bid/ask, and `oracle_gap_bps`; only trade when gap survives fees/slippage and liquidity haircut.

#### Uniswap v3 concentrated liquidity and range orders

- Sources:
  - Uniswap concentrated liquidity docs: https://docs.uniswap.org/concepts/protocol/concentrated-liquidity
  - Uniswap range order docs: https://docs.uniswap.org/concepts/protocol/range-orders
- Source type: primary protocol documentation.
- Key finding: liquidity can be concentrated in price intervals; range orders resemble passive execution over a chosen band.
- Applicability:
  - For Polymarket, layered CLOB quotes can mimic concentrated liquidity: quote small near fair, larger only within a safe price band.
  - Normal/AMM allocator can produce bands rather than single target prices.
- TODO translation:
  - Add quote layers: `{distance_from_fair, size_fraction}` with max total loss and min depth checks.
  - Add backtest metrics for layer fill distribution and inventory after price exits the band.

### C. Prediction-market CLOB mechanics and binary-market accounting

#### Polymarket rate-limit documentation

- Source: Polymarket rate limits, https://docs.polymarket.com/api-reference/rate-limits.md
- Source type: primary platform docs.
- Key finding: endpoints have Cloudflare sliding-window throttles; market data and trading endpoints have explicit request budgets.
- Applicability:
  - Quote refresh/cancel loops must be rate-limited and batched; backtests should not assume infinite refresh speed.
  - Dashboard should show throttling/skipped-refresh counters.
- TODO translation:
  - Add `RateLimitBudget` and `max_refresh_hz` config; simulate missed quote updates under slower refresh.

#### Polymarket negative-risk markets

- Source: Polymarket negative risk docs, https://docs.polymarket.com/advanced/neg-risk.md
- Source type: primary platform docs.
- Key finding: in negative-risk events, a No share in one market can convert into Yes shares in other outcomes; docs warn about placeholder/Other handling.
- Applicability:
  - Event-level exposure netting is mandatory before any allocation/market-making live path.
  - Placeholder/Other outcomes should default to disabled in allocator and cross-market arbitrage logic.
- TODO translation:
  - Add `event_id`, `neg_risk`, `outcome_group`, `is_placeholder` fields to market metadata cache.
  - Add tests where naive per-token exposure underestimates event-level max loss.

#### Polymarket hybrid CLOB overview and audited exchange contract links

- Source: Polymarket CLOB overview, https://docs.polymarket.com/trading/overview.md
- Source type: primary platform docs.
- Key finding: Polymarket uses offchain matching with onchain non-custodial settlement; orders are signed messages.
- Applicability:
  - Paper/live gate separation should be absolute: strategy code can produce plans, but signing/submission modules require explicit typed approval.
  - Logs must never include keys, raw signatures, or API credentials.
- TODO translation:
  - Keep `paper_only=True` in all new bot plans; add tests that live order path refuses to run without explicit gate.

#### Kalshi order book docs — YES/NO complementarity

- Source: Kalshi “Get Market Orderbook,” https://docs.kalshi.com/api-reference/market/get-market-orderbook
- Source type: primary prediction-market exchange docs.
- Key finding: a YES bid at price X is equivalent to a NO ask at 100-X; Kalshi exposes binary book levels through this complementarity.
- Applicability:
  - Polymarket binary bots should normalize YES/NO exposures into one canonical YES-equivalent basis.
  - Market-maker spread logic can infer equivalent opposite-side prices to detect crossed/inconsistent books.
- TODO translation:
  - Add `yes_equivalent_price(side, outcome, price)` helpers and unit tests.
  - Dashboard exposure should show YES-equivalent and max-resolution-loss, not just token counts.

### D. Bankroll sizing, portfolio risk, and overfit control

#### Kelly — growth-optimal capital allocation

- Source: J. L. Kelly Jr., “A New Interpretation of Information Rate,” Bell System Technical Journal 35(4), 1956, DOI: https://doi.org/10.1002/j.1538-7305.1956.tb03809.x
- Source type: foundational academic paper.
- Key finding: optimal bet fraction depends on edge and odds under strong assumptions; estimation error makes full Kelly dangerous.
- Applicability:
  - For binary markets, Kelly fraction can bound `target_notional`, but use fractional Kelly and hard caps.
  - Prediction-market edges are noisy; if `p_model` calibration is unknown, target size should collapse toward zero.
- TODO translation:
  - Implement `fractional_kelly_cap(edge, price, confidence)` as an upper bound, then apply liquidity/event/drawdown caps.
  - Quant agent should validate calibration before allowing allocator to size from model probability.

#### Bailey et al. / López de Prado — backtest overfitting and Deflated Sharpe Ratio

- Source: David H. Bailey and Marcos López de Prado research on backtest overfitting / deflated Sharpe ratio; institutional paper index: https://www.davidhbailey.com/dhbpapers/
- Source type: academic/institutional quant research.
- Key finding: repeated strategy trials make apparently good backtest performance likely by chance; performance needs deflation for trials and non-normal returns.
- Applicability:
  - The previous five-trade whale-copy ROI should be labelled exploratory, not evidence of live edge.
  - Multi-bot experiments should report number of trials, out-of-sample split, signal count, and confidence intervals.
- TODO translation:
  - Add `trial_count`, `in_sample`, `out_of_sample`, `bootstrap_ci`, and `deflated_metric_note` fields to backtest reports.
  - Dashboard should avoid “best ROI” leaderboards without sample-size warning.

#### CFTC event-contract / prediction-market public materials

- Source: CFTC event contracts public topic page, https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/understanding_eventcontracts.html
- Source type: U.S. regulator public education.
- Key finding: event contracts have binary payoff and regulated-market framing; manipulation/integrity questions matter.
- Applicability:
  - Strategy docs and dashboards should clearly distinguish paper-mode research from live financial advice/execution.
  - Avoid public claims of robust profitability until out-of-sample evidence exists.
- TODO translation:
  - Add dashboard labels: `paper`, `experimental`, `live_blocked`; include regulatory/risk warning in reports.

## Implementation ideas to feed into strategy docs

### Data model additions

- `CanonicalBinaryExposure`: YES-equivalent shares, NO-equivalent shares, worst-case payout, worst-case loss, event-level group id.
- `OrderLifecycleEvent`: planned, placed-paper, would_fill, would_cancel, stale_cancel, rejected_by_gate, skipped.
- `ToxicFlowState`: rolling large-trade score, midpoint jump score, one-sided fill streak, time-to-resolution risk.
- `BacktestProvenance`: data window, market categories, fill assumption, latency assumption, fee source, number of strategy trials.

### Strategy TODOs

- Market maker:
  - [ ] Add layered quotes inspired by concentrated liquidity bands.
  - [ ] Add toxic-flow pause after whale/copy signals to avoid quoting into informed flow.
  - [ ] Mark fills to next midpoint and resolution to measure adverse selection.
- Whale/ALT copy:
  - [ ] Add Kyle-style price-impact features and skip if copy trade is late.
  - [ ] Separate “whale is informed” from “copy is executable” in signal scoring.
- Normal/AMM allocator:
  - [ ] Use adaptive LMSR `b` based on market/event liquidity and fractional-Kelly cap.
  - [ ] Add event-aware negative-risk exposure netting and placeholder exclusions.
- Shared validation:
  - [ ] Add overfit controls: walk-forward split, bootstrap CI, trial count, and sample-size warnings.
  - [ ] Add rate-limit/latency stress tests for quote refresh and cancel/replace loops.

## Weak/speculative sources intentionally not used as evidence

- Random GitHub “Polymarket bot” repositories and SEO/blogspam bot tutorials remain weak until code is audited and provenance is clear.
- Social-media strategy threads are useful for hypotheses only, not citations.
- Any third-party bot requiring wallet keys should not be run or imported into this project.
