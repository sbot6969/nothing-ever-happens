# Polymarket multi-bot research — source-backed notes

Date: 2026-05-04

Scope: technical research for alternative strategy logic for a four-bot Polymarket platform. This is research/design only. No third-party bots were run, no secrets were read or exposed, and every recommendation remains paper/dry-run until separately approved.

## Executive takeaways

1. **Market making should be inventory-aware, not just “quote both sides”.** Avellaneda-Stoikov style quoting gives a practical backbone: compute a reservation price that moves against current inventory, then widen/narrow quotes based on volatility, time-to-resolution, and fill intensity. For Polymarket binary markets, inventory should be measured in net YES-equivalent exposure and maximum loss at resolution, not only USDC notional.
2. **Prediction-market AMMs are useful for allocation logic even if execution is on a CLOB.** LMSR and convex-cost market-maker papers provide a principled way to allocate capital across outcomes/markets with bounded loss and liquidity parameters. We can borrow their math for paper sizing and fair-value curves while still placing/canceling CLOB limit orders.
3. **Polymarket’s CLOB constraints matter more than elegant formulas.** Orders are limit orders; market orders are marketable limit orders with FOK/FAK; tick size/min order size/fee/reward parameters vary by market; the API has documented rate limits; negative-risk markets add conversion/arbitrage mechanics.
4. **The first safe implementation should be a simulator/quote generator.** Before live quoting, build a common backtester that consumes public market metadata, order book snapshots/trades, fees, tick size, and latency assumptions, then reports skipped signals, adverse-selection losses, inventory, turnover, and drawdown.

## Source-backed findings

### 1. Inventory-risk-aware market making

**Avellaneda & Stoikov — “High-frequency trading in a limit order book” (Quantitative Finance, 2008).**
Source: PDF hosted by NYU, https://www.math.nyu.edu/~avellane/HighFrequencyTrading.pdf

Key ideas relevant here:
- A market maker should optimize expected utility of terminal wealth, not just collect spread.
- Quotes are centered around a **reservation price** that shifts away from the mid-price when inventory grows.
- Spread width should increase with risk aversion, volatility, and time horizon; quote aggressiveness depends on order-arrival intensity.
- Implementation translation: `reservation_price = fair_value - inventory * risk_aversion * variance * time_to_close`, then post bid/ask around it with tick-size rounding and max-inventory guards.

Polymarket adaptation:
- Binary payoff bounds prices to `[0, 1]`; terminal payoff is discontinuous at resolution.
- `variance` should combine order-book volatility, recent trade volatility, and event/time hazard: sports/election/news markets can jump on external information.
- Inventory should be net YES/NO exposure per market plus correlated exposure across event groups, especially negative-risk events.

### 2. Prediction-market automated market makers

**Hanson — “Logarithmic Market Scoring Rules for Modular Combinatorial Information Aggregation” (Journal of Prediction Markets, 2007).**
Source: author PDF, https://mason.gmu.edu/~rhanson/mktscore.pdf

Key ideas:
- LMSR gives a cost function for outcome shares with bounded worst-case loss controlled by liquidity parameter `b`.
- Larger `b` increases liquidity and lowers price impact, but raises maximum loss.
- Implementation translation: use LMSR as a **paper allocator/fair-value curve**: capital budget maps to `b`; quote sizes decline as price moves away from target or budget depletes.

Polymarket adaptation:
- Polymarket is CLOB, not LMSR, so LMSR is not the execution venue. Use LMSR internally to decide how much inventory the bot is willing to hold at each probability level.
- For binary markets, the LMSR price can be compared to CLOB midpoint/book prices; trade only when edge after fees/slippage exceeds thresholds.

**Abernethy, Chen & Vaughan — “Efficient Market Making via Convex Optimization, and a Connection to Online Learning” (JMLR, 2013).**
Source: JMLR PDF, https://jmlr.org/papers/volume14/abernethy13a/abernethy13a.pdf

Key ideas:
- Market makers can be represented with convex cost functions; liquidity/risk trade-offs can be specified formally.
- Cost-function design is connected to regularization/online learning.
- Implementation translation: keep a generic `CostFunctionAllocator` interface so LMSR, quadratic, and normal-distribution allocation can share one simulator.

### 3. CLOB mechanics and Polymarket-specific constraints

**Polymarket CLOB overview.**
Source: https://docs.polymarket.com/trading/overview.md

Relevant documented facts:
- Polymarket is a hybrid CLOB: offchain matching with onchain settlement; orders are EIP-712 signed; matched trades settle atomically on Polygon.
- The docs recommend official SDKs and describe L1 private-key signing to derive L2 API credentials, then HMAC L2 authentication for trading.
- Safety implication: strategy/backtest code must not log keys, derived secrets, signatures, or funder addresses beyond masked identifiers.

**Polymarket order docs.**
Source: https://docs.polymarket.com/trading/orders/create.md

Relevant documented facts:
- All orders are limit orders.
- GTC/GTD rest on the book; FOK/FAK execute immediately against resting liquidity.
- GTD orders include a security threshold buffer; docs show `now + 60 + lifetime` logic.
- Implementation implication: live/paper quote generator should support GTC/GTD for maker quotes and FAK/FOK only for explicit taker/copy logic with slippage limits.

**Polymarket order book endpoint.**
Source: https://docs.polymarket.com/api-reference/market-data/get-order-book.md

Relevant documented facts:
- `/book` returns bids, asks, market, asset id, timestamp, hash, min order size, tick size, neg-risk flag, and last trade price.
- Implementation implication: every quote/backtest event must use `tick_size`, `min_order_size`, and `neg_risk`; stale timestamps/hash changes should be logged.

**Polymarket CLOB market-info endpoint.**
Source: https://docs.polymarket.com/api-reference/markets/get-clob-market-info.md

Relevant documented facts:
- Market info includes tokens, minimum tick size, minimum order size, maker/taker base fees, rewards, RFQ flag, fee details, and minimum order age.
- Implementation implication: do not hard-code fee/tick/reward assumptions. Cache by condition id and invalidate on failures.

**Polymarket fee-rate endpoint.**
Source: https://docs.polymarket.com/api-reference/market-data/get-fee-rate.md

Relevant documented facts:
- Fee rate is returned per token id as base fee in basis points.
- Implementation implication: backtests must subtract fees and strategy comparisons should report gross vs net edge.

**Polymarket rate limits.**
Source: https://docs.polymarket.com/api-reference/rate-limits.md

Relevant documented facts:
- CLOB market data endpoints have published request limits (`/book`, `/price`, `/midpoint` at 1,500 req/10s; batch endpoints lower); trading endpoints have burst and sustained limits.
- Implementation implication: quote refresh must be batched, rate-limited, and degrade gracefully. Backtests should include a configurable quote-refresh interval rather than assuming zero latency/infinite API capacity.

**Polymarket negative-risk markets.**
Source: https://docs.polymarket.com/advanced/neg-risk.md

Relevant documented facts:
- Negative-risk events allow conversion of a No share in one outcome into Yes shares in every other outcome in the event.
- Augmented negative-risk markets can include placeholders/Other, and docs warn to trade only named outcomes.
- Implementation implication: cross-outcome arbitrage/allocation must be event-aware; normal-distribution allocation should exclude unnamed placeholder outcomes and treat “Other” as high model-risk unless explicitly supported.

### 4. Practical crypto market-making patterns

**Hummingbot inventory-skew concept.**
Source: Hummingbot docs site / strategy configuration pages, https://hummingbot.org/

Relevant pattern:
- Inventory skew adjusts bid/ask order sizes so the strategy buys less when already long and sells less when already short.
- Implementation translation: add an `inventory_skew_factor` to quote size, independent of reservation-price skew. This is simpler and safer than only moving prices.

**Common CLOB market-making practice from crypto/traditional venues.**
Useful patterns to implement in paper mode first:
- Order layering: quote small size near top-of-book, larger size farther away only when inventory is healthy.
- Join-or-improve rules: never cross the spread unless a separate taker strategy fires.
- Cancel/replace discipline: do not churn orders faster than fill data and rate limits justify.
- Toxic-flow guard: widen or pause after large directional trades, news jumps, rapid midpoint changes, or repeated fills on one side.

## Risks and limitations

- **Adverse selection:** the bot can get filled just before informed price moves. Mitigation: stale-book checks, volatility/news jump guards, post-fill cooldowns, wider spreads around known event times, and toxicity metrics.
- **Overfitting:** previous whale-copy result used too few copied trades. Mitigation: walk-forward tests, market-category splits, out-of-sample validation, and reporting confidence intervals rather than headline ROI.
- **Inventory risk:** binary markets can resolve to 0/1; a small mark-to-market edge can become a total loss. Mitigation: per-market max loss, per-event correlated exposure caps, inventory-skew sizing, and resolution-time decay.
- **Latency/stale quotes:** offchain CLOB updates and external news can move faster than the bot. Mitigation: timestamp/hash checks, maximum quote age, cancel-on-stale, and simulated latency in backtests.
- **CLOB liquidity constraints:** thin books can make fair theoretical prices non-tradable. Mitigation: min depth, max spread, min volume/open interest, fill-probability models, and skipped-reason reporting.
- **Fees/slippage/rewards:** fee/tick/reward parameters vary by market; ignoring them can turn positive gross edge negative. Mitigation: fetch market-info/fee-rate per token and record gross/net PnL.
- **Data-quality limitations:** public historical snapshots may miss order-book state, queue priority, cancellations, API throttling, and exact fill ordering. Mitigation: use conservative fill assumptions and separate trade-only vs order-book backtests.

## Concrete implementation TODOs derived from research

### Shared infrastructure
- [ ] Add `StrategySignal`, `QuotePlan`, `ExecutionAssumption`, and `BacktestFill` dataclasses with explicit `paper_only` mode.
- [ ] Add market metadata cache keyed by condition/token id: tick size, min order size, fee rates, neg-risk flags, reward config, market close/resolution time.
- [ ] Add common skipped-reason taxonomy: `thin_book`, `wide_spread`, `stale_book`, `fee_negative_edge`, `inventory_cap`, `latency_guard`, `data_missing`, `neg_risk_placeholder`, `live_gate_blocked`.
- [ ] Add backtest metrics common to all bots: gross/net PnL, ROI, drawdown, turnover, exposure, fill count, quote count, cancel count, skipped reasons, latency sensitivity.

### Market-making bot
- [ ] Implement paper `InventoryAwareQuoteEngine` using Avellaneda-Stoikov-style reservation price and configurable risk aversion.
- [ ] Add binary-market inventory model: net YES-equivalent shares, max payout exposure, max loss at resolution, event-level correlation caps.
- [ ] Add quote-size inventory skew: reduce bid size when long YES; reduce ask size when short/underhedged; stop quoting side that worsens capped inventory.
- [ ] Add stale/toxic-flow guard: pause or widen after large trade, fast midpoint move, or repeated one-sided fills.
- [ ] Backtest with conservative fill models: top-of-book fill only when subsequent trades cross our quote; include latency and queue haircut.

### Normal-distribution / AMM allocation bot
- [ ] Implement a `NormalDistributionAllocator` that maps fair probability vs market probability z-score to target exposure.
- [ ] Implement LMSR-style bounded-loss allocator as a benchmark; compare capital curves against normal allocation.
- [ ] Event-aware allocation: enforce total budget per event and exclude augmented negative-risk placeholders/Other unless whitelisted.
- [ ] Backtest allocation rebalancing with fees, slippage, and max turnover constraints.

### Whale/ALT copy bot
- [ ] Update whale detection to include `notional >= $10,000 OR (market_size >= $10,000 AND notional / market_size >= 0.30)`.
- [ ] Add copied-trader reliability score: realized historical PnL, market category, time-to-resolution, trade direction, and liquidity consumed.
- [ ] Add anti-copy filters: reject signals where whale trade caused spread blowout, consumed too much depth, or arrives after midpoint has already moved.
- [ ] Run walk-forward backtests across larger snapshots and report signal count confidence, not just ROI.

### Nothing Ever Happens baseline
- [ ] Re-document baseline edge assumptions and filters.
- [ ] Add comparable backtest adapter so baseline metrics appear beside other bots.
- [ ] Add risk-budget allocator so baseline can be downweighted when market-making/AMM bots already hold correlated exposure.

## Paper-test recommendation order

1. **Metadata/backtest harness first** — lowest risk and unlocks all bots.
2. **Nothing Ever Happens comparable baseline** — already exists; needs consistent reporting.
3. **Whale/ALT copy improved filter** — close to existing code, but must avoid overfit claims.
4. **Normal/LMSR allocation simulator** — useful for sizing even before execution.
5. **Market-making quote generator** — paper only; live market making should be last because adverse selection, latency, and inventory risk are highest.
