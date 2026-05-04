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
- [x] Research hedge-fund / quant / market-making PDFs and technical docs.
- [x] Research prediction-market and binary-option market-making techniques.
- [x] Research Polymarket/CLOB liquidity constraints and practical execution risks.
- [x] Write source-backed findings to `docs/polymarket_multi_bot/RESEARCH.md`.
- [x] Convert research into implementable strategy specs in `docs/polymarket_multi_bot/STRATEGIES.md`.

## 4. Strategy families
- [ ] Existing Nothing Ever Happens strategy: document baseline and backtest metrics.
- [ ] Whale/ALT copy bot: improve whale filter, validation, paper runtime.
- [x] Market-making bot: design paper quote generator with inventory/spread/risk controls.
- [x] Normal-distribution AMM allocation bot: design capital allocation/sizing model and paper simulator.

## 5. Backtesting
- [x] Build common backtest harness for all strategy families.
- [ ] Download/prepare larger ignored historical data snapshots.
- [ ] Run per-strategy backtests across more markets/trades/types.
- [ ] Produce comparable metrics: PnL, ROI, hit rate, drawdown, turnover, exposure, skipped-signal reasons.
- [ ] Record results in `docs/polymarket_multi_bot/BACKTEST_RESULTS.md`.

## 6. Unified dashboard
- [x] Add platform dashboard section/cards for all four sub-bots.
- [x] Show per-bot mode, capital allocation, paper/live signal counts, PnL/backtest metrics, health/errors.
- [x] Keep sensitive wallet/key data out of dashboard and logs.

## 7. Agent work and reviews
- [x] Backend agent: strategy interfaces, whale filter, backtest harness, tests.
- [x] Research agent: source-backed research docs and strategy ideas.
- [x] Frontend agent: unified dashboard design and implementation.
- [x] Security reviewer: final review of code, configs, logging, live gates, secret handling.
- [x] Cross-test/adversarial review: one agent validates assumptions/test gaps from another.

## 8. Release/push/runtime
- [x] Run focused and full tests.
- [x] Commit and push to GitHub fork branch.
- [x] Restart paper runtimes only after tests pass.
- [x] Verify dashboards respond: main HTTPS 8765=200, whale HTTPS 8766=200.
- [ ] Report status and blockers to user.

## 9. Recurring monitoring
- [x] Install 30-minute recurring safe monitor/check job via launchd (`com.sbot.neh-multibot-monitor`).
- [x] Monitor re-validates this voice request, checks agent registry, checks dashboards/processes, and appends logs to daily memory/task docs.

## 10. Specialist agent system
- [x] Define durable agent workflow in `docs/polymarket_multi_bot/AGENT_FLOW.md`.
- [x] Create multi-bot agent registry in `docs/polymarket_multi_bot/AGENT_REGISTRY.md`.
- [x] Create deep research agent task in `docs/agent_tasks/research-agent-multibot.md`.
- [x] Create quant/math agent task in `docs/agent_tasks/quant-math-agent-multibot.md`.
- [x] Deep research agent: produce appendix and updated implementation ideas.
- [x] Quant/math agent: produce quant review and simulations/tests.
- [x] Add agent/task status into dashboard.
- [x] Run security-reviewer after research/math/dev/dashboard integration.
- [x] Run cross/adversarial review (completed in parallel with security review; see `CROSS_REVIEW.md` ordering note).


## 11. Voice requirements trace
- [x] Re-listened/revalidated the last three voice-message transcripts into `docs/polymarket_multi_bot/VOICE_REQUIREMENTS_TRACE.md`.
- [x] Map status-request voice to answered checklist.
- [x] Map multi-bot platform voice to implementation/research/backtest/financial-safety checklist.
- [x] Map specialist-agent voice to agent-flow/dashboard/monitor checklist.
- [ ] Continue open non-financial TODOs from the trace (larger backtests/config schema/final runtime verification remain).
- [blocked] Live financial items require separate explicit typed confirmation.
