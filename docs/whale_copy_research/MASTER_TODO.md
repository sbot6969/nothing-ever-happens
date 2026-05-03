# Whale-Copy Polymarket Bot: Master TODO / Research / Backtest Plan

Status: active planning and execution.  
Safety gate: **no live capital transfer, wallet funding, position closing, or live trading without a separate explicit confirmation**.

## 0. Non-negotiable constraints

- [ ] Keep main bot live safety intact; do not break current `nothing_happens` runtime.
- [ ] Whale-copy bot must stay paper/dry-run until explicit approval.
- [ ] Never commit secrets, `.env`, private keys, wallets, DB dumps, logs, certs, or runtime artifacts.
- [ ] All trading/live actions must be behind config flags and default-off.
- [ ] Backtests must include fees, spread/slippage assumptions, failed fills, and liquidity caps.
- [ ] Claims about PnL must be based on reproducible data snapshots and scripts, not intuition.
- [ ] Target metric requested by user: report after **5 improvement iterations** and show the best PnL/ROI discovered.
- [ ] If ROI is below 100%, iterate strategy design and rerun backtests before recommending live mode.

## 1. Repository hygiene / branch / git

- [x] Create feature branch `feature/whale-copy-backtest-research`.
- [ ] Update `.gitignore` to exclude runtime artifacts: `bot.log`, `*.db`, `certs/`, whale runtime logs/ledgers.
- [ ] Commit only source/docs/tests/config examples; exclude `config.json`, live DBs, logs, certs.
- [ ] Push branch after local tests pass.
- [ ] Prepare PR or branch summary for review.

## 2. Current bot audit: modules and transaction paths

- [ ] Inventory all modules in `bot/` and classify as strategy, exchange, risk, dashboard, persistence, notifier, recovery, utility.
- [ ] Identify all code paths that can create transactions/orders:
  - [ ] `bot/main.py`
  - [ ] `bot/exchange/polymarket_clob.py`
  - [ ] `bot/strategy/nothing_happens.py`
  - [ ] `bot/redeemer.py`
  - [ ] `bot/live_recovery.py`
  - [ ] whale-copy module(s)
- [ ] Verify live transaction paths require `live_send_enabled`/live gate and cannot accidentally run in paper mode.
- [ ] Add tests proving dry-run/paper mode does not submit real orders.
- [ ] Add tests proving live mode uses explicit config and wallet/client initialization.
- [ ] Add tests for notifier failure isolation: Telegram/OpenClaw message errors cannot stop trading hot path.

## 3. Full test plan by module

- [ ] Run all existing tests.
- [ ] Add/expand tests for:
  - [ ] config parsing and env overrides
  - [ ] order sizing limits
  - [ ] market filters: volume, liquidity, spread, depth
  - [ ] dynamic sizing score monotonicity
  - [ ] risk controls and daily exposure accounting
  - [ ] position sync/reconciliation
  - [ ] redeemer/settlement paths
  - [ ] dashboard finalization statuses
  - [ ] finance notifier formatting/rate limiting
  - [ ] whale scanner: API parsing, user-agent, pagination, duplicate suppression
  - [ ] whale scanner: wallet-history filter for first-visible traders
  - [ ] whale-copy planner: copy fraction, caps, slippage, liquidity constraints
  - [ ] whale-copy dashboard state and websocket snapshots
- [ ] Add fixtures for Polymarket Data API sample trades.
- [ ] Add property-style tests for edge cases where practical.

## 4. Whale scanner validation

- [ ] Document Polymarket Data API endpoints used:
  - [ ] `/trades?limit=N`
  - [ ] `/trades?user=<wallet>`
  - [ ] any market/event metadata endpoint needed for outcomes/resolution.
- [ ] Verify wallet identification field: `proxyWallet` vs `user` vs maker/taker fields.
- [ ] Verify pagination/time-window parameters for historical pulls.
- [ ] Define “first-time whale” precisely:
  - [ ] first visible trade ever from wallet in Data API
  - [ ] first trade in a market
  - [ ] first large trade after wallet inactivity
  - [ ] exclude sybil/noise wallets if needed
- [ ] Add dedupe: transaction hash + asset + timestamp.
- [ ] Add stale-signal rejection: ignore old trades after startup bootstrap.
- [ ] Add minimum notional threshold and market liquidity filters.
- [ ] Add wash-trade/noise filters if evidence supports them.

## 5. Backtest framework

- [ ] Build reproducible historical data downloader/cache:
  - [ ] raw whale trades
  - [ ] wallet history snapshots
  - [ ] market metadata
  - [ ] outcomes/resolutions
  - [ ] price/order-book snapshots if available
- [ ] Store cached data in ignored artifact directory, with metadata manifest.
- [ ] Implement event-driven simulator:
  - [ ] observe whale trade at timestamp
  - [ ] decide whether signal passes filters
  - [ ] simulate delayed copy execution
  - [ ] apply price impact/slippage/spread
  - [ ] cap by available liquidity and configured max position size
  - [ ] mark-to-market and/or resolve to final outcome
  - [ ] compute PnL, ROI, drawdown, hit rate, Sharpe-like metric where meaningful
- [ ] Include fees/costs:
  - [ ] Polymarket no explicit trading fee assumption must be documented/verified
  - [ ] spread and slippage
  - [ ] gas/network costs if wallet operations require them
  - [ ] failed/cancelled orders
- [ ] Add CLI entrypoint, e.g. `python -m bot.backtest.whale_copy --days 30 --out ...`.
- [ ] Add unit tests for simulator accounting.

## 6. Five strategy improvement iterations

### Iteration 0 — Baseline
- [ ] Rule: copy first-visible large BUY trades above threshold.
- [ ] Fixed copy fraction and max notional cap.
- [ ] Backtest and record metrics.

### Iteration 1 — Liquidity/spread-aware copy
- [ ] Add order-book/liquidity/spread filters.
- [ ] Reduce size when book depth is shallow.
- [ ] Backtest vs baseline.

### Iteration 2 — Wallet quality scoring
- [ ] Track wallet historical profitability if enough history exists.
- [ ] Score wallets by ROI/hit rate/market type.
- [ ] Penalize wallets with rapid reversals or tiny/noisy trade history.
- [ ] Backtest vs previous.

### Iteration 3 — Market type specialization
- [ ] Separate buckets:
  - [ ] crypto 5m up/down markets
  - [ ] politics/news unknown-outcome markets
  - [ ] sports/pop-culture/noisy markets
- [ ] Test whether unknown-outcome markets show better distribution/edge.
- [ ] Backtest each market bucket.

### Iteration 4 — Portfolio/risk optimization
- [ ] Kelly-fraction-inspired sizing with hard caps.
- [ ] Max correlated exposure per event/category.
- [ ] Stop-loss / take-profit / time-to-resolution rules.
- [ ] Backtest vs previous.

### Iteration 5 — Arbitrage and calibration add-ons
- [ ] Research and prototype CEX vs Polymarket 5m BTC/ETH arbitrage signals.
- [ ] Research cross-outcome/YES-NO normalization/arbitrage on Polymarket.
- [ ] Backtest only if historical data supports it; otherwise produce feasibility report.

## 7. Internet/open-source research

- [ ] Survey open-source Polymarket bots and tools:
  - [ ] GitHub repositories using Polymarket CLOB/Data API
  - [ ] arbitrage bots
  - [ ] market-making bots
  - [ ] copy-trading/whale-monitoring bots
  - [ ] resolution/redeemer bots
- [ ] For each candidate repo, record:
  - [ ] URL/name/license/activity
  - [ ] strategy type
  - [ ] whether code is actually usable/profile/profitable-looking
  - [ ] risk/security concerns
  - [ ] ideas worth borrowing
- [ ] Research fees/costs and document current assumptions with sources.
- [ ] Research CLOB matching/fill behavior and minimum order constraints.
- [ ] Research Data API limitations/rate limits.

## 8. Strategy research topics

- [ ] Whale-copy edge: why first-time wallets may have informational advantage or may be noise/sybil.
- [ ] CEX ↔ 5-minute Polymarket BTC/ETH arbitrage:
  - [ ] latency requirements
  - [ ] oracle/settlement definitions
  - [ ] spread/fill risk
  - [ ] CEX fees/funding/transfer irrelevant vs hedging costs
- [ ] YES/NO price normalization:
  - [ ] detect sum(YES prices) below/above 1 after spread
  - [ ] executable arbitrage constraints
  - [ ] inventory/settlement risk
- [ ] Unknown-event markets:
  - [ ] normal distribution intuition vs binary market pricing reality
  - [ ] calibration/overround/mispricing detection
  - [ ] category filters.

## 9. Dashboard / reporting

- [x] Main dashboard keeps finalization block.
- [x] Whale dashboard should show:
  - [x] live/paper status
  - [x] watched wallets/signals
  - [x] copied wallet and wallet history count
  - [x] risk/confidence score
  - [x] simulated order size and expected slippage
  - [x] PnL/backtest summary
  - [x] notification health
  - [x] last API error and rate-limit status
- [x] Add backtest reports as static HTML/Markdown artifacts.

## 10. Telegram finance notifier

- [ ] Validate events from both bots:
  - [ ] startup/shutdown
  - [ ] error/feed crash/feed dead
  - [ ] order opened
  - [ ] order closed/sold
  - [ ] settlement/redeem/PnL
  - [ ] whale signal
  - [ ] paper/live copy event
- [ ] Add tests for message formatting and action filtering.
- [ ] Add cooldown/rate limit behavior for repeated errors.
- [ ] Confirm notifier is best-effort and cannot break hot path.

## 11. Security review checklist

- [ ] No secrets committed.
- [ ] No shell injection in notifier/openclaw calls.
- [ ] No unsafe deserialization.
- [ ] API failures handled with backoff.
- [ ] Live trading gates are default-off for whale bot.
- [ ] Financial actions require explicit user confirmation.
- [ ] Position closing/transfer scripts are reviewed separately before use.

## 12. Launch checklist, after user explicitly approves live funds

Blocked until explicit typed confirmation.

- [ ] Create/secure new wallet for whale bot.
- [ ] Back up private key/seed according to user-approved storage method.
- [ ] Transfer approved amount only, e.g. `$20 USDC`, from main wallet.
- [ ] Close/trim only positions that are liquid and rational to close; record reason.
- [ ] Configure whale bot with new wallet and live flag.
- [ ] Start with very low cap and observe.
- [ ] Confirm Telegram finance notifications for real orders.

## 13. Final deliverables

- [ ] Branch pushed.
- [ ] Source commits separated logically.
- [ ] Agent task files completed.
- [ ] Cross-review notes.
- [ ] Security review notes.
- [ ] Full test output.
- [ ] Backtest iteration table, including best PnL/ROI.
- [ ] Recommendation: do not launch / paper longer / launch with capped $20.
