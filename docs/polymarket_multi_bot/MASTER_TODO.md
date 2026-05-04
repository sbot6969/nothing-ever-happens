# Multi-bot Polymarket platform — MASTER TODO

## Safety gate
- [x] Keep all new strategy bots in paper/dry-run mode by default.
- [ ] Do **not** close positions, transfer funds, create/fund wallets, or enable live trading without separate explicit typed confirmation.
- [ ] Before any live launch: rerun security review, secret scan, wallet/key handling review, and final typed confirmation.

## 1. Requirements/spec
- [x] Capture voice request in `docs/polymarket_multi_bot/VOICE_REQUEST_2026-05-04.md`.
- [ ] Define unified platform architecture for four sub-bots.
- [ ] Define shared strategy interface, capital allocator interface, and dashboard data model.
- [ ] Define per-bot config schema and dry-run/live gates.

## 2. Whale-copy improvements
- [x] Update whale filter: whale if notional >= $10k OR notional >= 30% of market size when market size >= $10k.
- [x] Add unit tests for both whale criteria and edge cases.
- [x] Update scanner validation/backtest code to include market-size-relative signals.
- [ ] Re-run whale-copy backtests on larger public historical snapshots.

## 3. Research
- [ ] Research hedge-fund / quant / market-making PDFs and technical docs.
- [ ] Research prediction-market and binary-option market-making techniques.
- [ ] Research Polymarket/CLOB liquidity constraints and practical execution risks.
- [ ] Write source-backed findings to `docs/polymarket_multi_bot/RESEARCH.md`.
- [ ] Convert research into implementable strategy specs in `docs/polymarket_multi_bot/STRATEGIES.md`.

## 4. Strategy families
- [ ] Existing Nothing Ever Happens strategy: document baseline and backtest metrics.
- [ ] Whale/ALT copy bot: improve whale filter, validation, paper runtime.
- [ ] Market-making bot: design paper quote generator with inventory/spread/risk controls.
- [ ] Normal-distribution AMM allocation bot: design capital allocation/sizing model and paper simulator.

## 5. Backtesting
- [x] Build common backtest harness for all strategy families.
- [ ] Download/prepare larger ignored historical data snapshots.
- [ ] Run per-strategy backtests across more markets/trades/types.
- [ ] Produce comparable metrics: PnL, ROI, hit rate, drawdown, turnover, exposure, skipped-signal reasons.
- [ ] Record results in `docs/polymarket_multi_bot/BACKTEST_RESULTS.md`.

## 6. Unified dashboard
- [ ] Add platform dashboard section/cards for all four sub-bots.
- [ ] Show per-bot mode, capital allocation, paper/live signal counts, PnL/backtest metrics, health/errors.
- [ ] Keep sensitive wallet/key data out of dashboard and logs.

## 7. Agent work and reviews
- [x] Backend agent: strategy interfaces, whale filter, backtest harness, tests.
- [ ] Research agent: source-backed research docs and strategy ideas.
- [ ] Frontend agent: unified dashboard design and implementation.
- [ ] Security reviewer: final review of code, configs, logging, live gates, secret handling.
- [ ] Cross-test/adversarial review: one agent validates assumptions/test gaps from another.

## 8. Release/push/runtime
- [ ] Run focused and full tests.
- [ ] Commit and push to GitHub fork branch.
- [ ] Restart paper runtimes only after tests pass.
- [ ] Verify dashboards respond.
- [ ] Report status and blockers to user.

## 9. Recurring monitoring
- [x] Install 30-minute recurring safe monitor/check job via launchd (`com.sbot.neh-multibot-monitor`).
- [ ] Monitor re-validates this voice request, checks agents, checks dashboards/processes, and appends logs to daily memory/task docs.
