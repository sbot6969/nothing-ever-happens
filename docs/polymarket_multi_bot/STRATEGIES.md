# Polymarket multi-bot strategy specs

Date: 2026-05-04

These are concrete paper-mode strategy ideas for the requested four-bot platform. They intentionally stop short of live trading: no wallet actions, no funding, no position closing, and no live orders without separate typed confirmation.

## Shared platform model

### Bot families

1. `nothing_ever_happens` — existing baseline / conservative edge filter.
2. `whale_alt_copy` — copy large or market-size-relative informed trades.
3. `market_maker` — inventory-aware CLOB quoting.
4. `normal_amm_allocator` — portfolio allocation from normal/z-score and AMM cost-curve logic.

### Common interfaces

```text
MarketSnapshot
  condition_id, token_id, outcome, event_id, category
  best_bid, best_ask, midpoint, spread, depth_by_level
  tick_size, min_order_size, fee_bps, neg_risk, close_time
  timestamp, source_hash

StrategySignal
  bot_id, market_id, token_id, side, fair_probability
  expected_edge_bps, confidence, max_notional, reason
  data_quality_flags, paper_only

QuotePlan
  bot_id, token_id, bid_price, bid_size, ask_price, ask_size
  order_type=GTD/GTC, ttl_seconds, cancel_replace_policy
  inventory_after_fill, max_loss_after_fill, skip_reason

RiskBudget
  total_paper_capital, per_bot_capital, per_market_cap, per_event_cap
  max_daily_drawdown, max_inventory_yes_equivalent, max_turnover
```

### Cross-bot capital allocator

Initial safe allocation for paper tests:

| Bot | Paper capital weight | Rationale |
| --- | ---: | --- |
| Nothing Ever Happens | 35% | Existing known baseline; conservative filters already present. |
| Whale/ALT copy | 25% | Strong signal hypothesis, but high overfit/adverse-selection risk. |
| Market-making | 20% | Needs latency/inventory validation before larger risk. |
| Normal/AMM allocator | 20% | Useful for diversification and sizing; execution edge still unproven. |

Allocator rules:
- Per-market cap: max 10% of total paper bankroll.
- Per-event cap: max 20% of bankroll, stricter for correlated/negative-risk events.
- Daily drawdown kill switch: stop new signals after 5% paper drawdown; cancel maker quotes in live mode if ever enabled.
- Cross-bot exposure netting: if multiple bots want the same YES exposure, allocator should downscale lower-confidence signals rather than stack blindly.

## Strategy 1 — Nothing Ever Happens baseline

### Thesis

The existing strategy assumes many high-priced, apparently likely events do not resolve in a surprising way; it filters for markets where the price/cap/depth relationship gives enough safety margin. It should become the baseline yardstick for all other bot ideas.

### Logic

Inputs:
- Market price/midpoint.
- Volume/liquidity/depth.
- Spread.
- Time to close/resolution.
- Existing position/inventory.

Signal:
- Consider a trade only when market passes configured volume/liquidity/depth/spread filters.
- Score entries using existing cap-edge/depth/liquidity/volume logic.
- Size dynamically but cap by per-market and total risk budgets.

Paper implementation TODOs:
- [ ] Wrap existing strategy output into `StrategySignal`.
- [ ] Emit standardized skipped reasons.
- [ ] Backtest with the same gross/net metrics used by the other bots.
- [ ] Add cross-bot exposure check so baseline does not add risk if whale/MM/AMM bots already hold the same side.

Risks:
- Model edge may be regime-specific.
- Resolution tail risk dominates small spread/edge assumptions.
- Thin-market fills can be unrealistic in trade-only backtests.

## Strategy 2 — Whale / ALT trader copy bot

### Thesis

Large trades can reveal informed conviction, especially when the trade is large relative to market size. The updated whale rule should catch both absolute whales and small-market dominant trades:

```text
is_whale = notional >= 10_000
        OR (market_size >= 10_000 AND notional / market_size >= 0.30)
```

### Logic

Inputs:
- Public trades by market/trader.
- Market size / volume / open interest proxy.
- Order book snapshot immediately before/after signal where available.
- Trader reliability features: realized past PnL, category specialization, average entry timing, signal decay.

Signal scoring:

```text
raw_score = log1p(notional) * market_relative_multiplier
quality_score = trader_reliability * liquidity_score * timing_score
anti_chase_penalty = spread_blowout + midpoint_move_after_whale + depth_consumed
copy_score = raw_score * quality_score - anti_chase_penalty
```

Execution idea:
- Paper-copy only if expected edge remains after estimated slippage/fees.
- Prefer passive or bounded FAK copy depending on book state:
  - If book still deep and spread tight: small FAK with worst-price limit.
  - If spread widened: place passive bid/ask near pre-signal fair price or skip.
- Never chase if whale consumed too much depth or the midpoint already moved beyond allowed slippage.

Implementation TODOs:
- [ ] Update whale threshold tests for absolute and 30%-of-market-size rules.
- [ ] Add `market_size` / `market_size_source` to whale signal records.
- [ ] Add trader reliability table from historical public trades.
- [ ] Add anti-chase filters: max spread, max midpoint jump, min remaining depth, max signal age.
- [ ] Run walk-forward backtests by market category and trader cohort.

Risks:
- Whales can be hedging, manipulating, or wrong.
- Public trade data may arrive too late for profitable copying.
- Large trades cause adverse price moves; followers pay worse prices.
- Small sample overfit is severe; report confidence intervals and signal counts.

Safe paper-test priority: **high**, because it extends existing paper infrastructure.

## Strategy 3 — Inventory-aware market-making bot

### Thesis

Provide CLOB liquidity only when spread/depth/fee conditions compensate for inventory and adverse-selection risk. Use Avellaneda-Stoikov-style reservation-price skew plus simpler inventory-size skew.

### Logic

Inputs:
- MarketSnapshot with live/paper book data.
- Fair probability estimate from midpoint, recent trades, baseline model, and optional external category priors.
- Inventory: YES shares, NO shares, net YES-equivalent exposure, max loss.
- Risk params: risk aversion, volatility estimate, quote TTL, max inventory, max loss.

Reservation price:

```text
fair = clipped_probability_estimate
inventory_penalty = net_yes_equivalent * risk_aversion * variance * time_to_resolution_factor
reservation_price = clamp(fair - inventory_penalty, min_tick, 1 - min_tick)
```

Quote spread:

```text
base_half_spread = max(observed_spread / 2, tick_size)
risk_half_spread = base_half_spread + volatility_buffer + fee_buffer + latency_buffer
bid = floor_to_tick(reservation_price - risk_half_spread)
ask = ceil_to_tick(reservation_price + risk_half_spread)
```

Size skew:
- If long YES, reduce bid size and increase/keep ask size.
- If short/underexposed, reduce ask size and allow bid size.
- Stop quoting a side that would breach max inventory or max loss.

Quote controls:
- Use GTD quotes with short TTL in paper mode; if live ever enabled, cancel stale quotes before replacing.
- Pause after toxic-flow triggers: large directional trade, fast midpoint jump, repeated one-sided fills, market entering final resolution window.
- Require min depth and max spread; skip thin books.

Implementation TODOs:
- [ ] Build `InventoryAwareQuoteEngine` returning `QuotePlan` only; no live order posting.
- [ ] Add `InventoryState` and max-loss calculations for binary payouts.
- [ ] Add quote simulator with latency, queue haircut, and conservative fill assumptions.
- [ ] Add dashboard cards: active quote count, inventory skew, stale quote count, toxic-flow pauses, net exposure.
- [ ] Backtest by category with sensitivity to latency and fill probability.

Risks:
- Highest adverse-selection risk of all bot families.
- Queue position and cancellation data may be missing from historical snapshots.
- Frequent cancel/replace can hit rate limits or create operational risk.
- Inventory can become correlated across markets/events.

Safe paper-test priority: **medium/last**. Implement quote plans and simulator first; live quoting should be last.

## Strategy 4 — Normal-distribution / AMM allocation bot

### Thesis

Use a probability model to allocate capital across markets like a bounded-loss AMM/portfolio optimizer. This bot does not need to continuously quote; it can propose target exposures and rebalance when market prices deviate enough from fair probability.

### Logic

Inputs:
- Market implied probability `p_market` from midpoint or conservative bid/ask.
- Model probability `p_model` from baseline features, trader signals, category priors, or external manual priors.
- Uncertainty `sigma` from model confidence, market volatility, and time to resolution.
- Risk budget per event/category.

Z-score edge:

```text
z = (p_model - p_market) / max(sigma, sigma_floor)
edge = p_model - executable_price - fee_slippage_buffer
```

Normal allocation curve:

```text
target_fraction = max_fraction * tanh(z / z_scale)
target_notional = bankroll * target_fraction * confidence * liquidity_score
```

AMM/LMSR benchmark:
- Use LMSR liquidity parameter `b` as a bounded-loss budget.
- Compare target exposure from normal curve to LMSR-implied cost/price impact.
- Choose the smaller/more conservative exposure.

Execution idea:
- Paper-generate rebalance signals only when edge exceeds fee/slippage/turnover threshold.
- Trade less near resolution unless confidence is high and book is deep.
- For negative-risk events, allocate at event level and avoid placeholders/Other unless explicitly enabled.

Implementation TODOs:
- [ ] Build `NormalDistributionAllocator` with configurable `sigma_floor`, `z_scale`, `max_fraction`, and turnover cap.
- [ ] Build `LMSRAllocator` benchmark with budget-to-`b` mapping.
- [ ] Add event-level exposure netting, especially for negative-risk markets.
- [ ] Add rebalancing backtest that includes fees/slippage and max turnover.
- [ ] Compare allocation bot vs baseline buy/hold and vs whale-copy signals.

Risks:
- Probability model can be badly calibrated.
- Normal assumptions break on jump events, lawsuits, sports injuries, breaking news, and resolution ambiguity.
- Rebalancing costs can eat edge.
- Multi-outcome/negative-risk mechanics can create hidden correlations.

Safe paper-test priority: **medium-high**, because it can run as recommendations/backtest without live orders.

## Combined strategy orchestration

### Signal arbitration

When bots conflict:
- Prefer higher net expected edge after fee/slippage.
- Penalize bot if it would increase event-level concentration.
- Do not let copy bot force market-maker to quote against a toxic-flow pause.
- If normal allocator says target exposure is already full, downscale baseline/whale signals.

### Bot health dashboard fields

For every bot:
- Mode: disabled / paper / live-blocked / live-enabled.
- Signals generated, accepted, skipped.
- Top skipped reasons.
- Paper PnL gross/net, ROI, drawdown, exposure, turnover.
- Current allocated capital and remaining budget.
- Data freshness: last market snapshot, last trade ingest, stale count.
- Risk state: kill switch, drawdown limit, inventory cap, latency guard.

### Common backtest protocol

Minimum acceptable report before claiming improvement:
- Separate train/calibration and out-of-sample windows.
- Category-level results, not only aggregate ROI.
- Gross and net PnL after fees/slippage assumptions.
- Conservative and optimistic fill assumptions.
- Signal count and confidence interval / bootstrap where possible.
- Max drawdown and worst market loss.
- List of skipped reasons to expose data/strategy brittleness.

## Implementation TODO rollup

### Phase 1 — paper-safe architecture
- [ ] Create shared strategy/backtest dataclasses and config schema.
- [ ] Add market metadata cache for tick/min order/fee/neg-risk/reward fields.
- [ ] Add standard metrics and skipped-reason reporting.
- [ ] Wire all four bot families into a dashboard data model with live gates defaulting to disabled.

### Phase 2 — strategy adapters
- [ ] Wrap Nothing Ever Happens into standard signal/backtest interface.
- [ ] Update whale/ALT copy threshold and anti-chase filters.
- [ ] Implement normal/LMSR allocation simulator.
- [ ] Implement market-maker quote planner without live posting.

### Phase 3 — validation
- [ ] Download larger ignored historical datasets across more categories.
- [ ] Run walk-forward backtests with latency/slippage/fee sensitivity.
- [ ] Run adversarial tests: stale book, missing fee data, placeholder negative-risk outcome, extreme spread, repeated one-sided fills.
- [ ] Require security review before any runtime restart or live gate change.

### Phase 4 — future live-readiness gate (blocked)
- [blocked] Live orders, wallet funding, position closing, transfers, or per-bot wallet creation require separate explicit typed confirmation with exact scope and amounts.
- [blocked] Before live: secret scan, key-handling review, dry-run dashboard verification, cancel-all safety path, and typed approval.
