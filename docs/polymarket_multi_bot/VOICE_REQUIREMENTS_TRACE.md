# Voice requirements trace — last three voice messages

This file replays the last three voice requests and maps each requirement to TODO/status. All live-financial actions remain blocked until separate explicit typed confirmation.

## Voice 1 — status of whale-copy bot
User asked for final status, tests, liquidity deposited, currently opened trades, and potential trades if funded.

- [x] Report whale-copy status: currently paper/dry-run, not live.
- [x] Report tests performed: full/focused pytest results and backtest iterations.
- [x] Report liquidity deposited: `$0` added by assistant.
- [x] Report current live positions/orders: no live orders/fills/positions opened by whale-copy; main DB had zero live orders/fills/positions at check time.
- [x] Report paper/potential trades: one paper signal for “Will Satoshi move any Bitcoin in 2026?” outcome No, planned copy `$25`, live disabled.
- [x] State live-launch caution: current results are paper/backtest only and overfit risk remains.

## Voice 2 — multi-bot Polymarket platform
User requested a unified platform with richer research/backtests and four sub-bots.

### Whale filter
- [x] Whale if trade notional >= `$10,000`.
- [x] Whale if trade is >= `30%` of market size.
- [x] Relative 30% rule only applies when market size >= `$10,000`.
- [x] Add tests/backtest coverage for absolute and relative thresholds.

### Research
- [x] Research hedge-fund/quant/market-making docs, PDFs, technical papers, and examples.
- [x] Research traditional-finance/crypto/prediction-market examples for market making and CLOB behavior.
- [x] Write research docs in Markdown.
- [x] Convert research into concrete strategy TODO/specs.

### Four-bot architecture
- [x] Define four sub-bots: Nothing Ever Happens, Whale/ALT Copy, Market-making, Normal-distribution AMM allocator.
- [x] Add unified dashboard cards/model for all four sub-bots.
- [x] Keep all sub-bots paper/dry-run by default.
- [ ] Define final production config schema and per-bot wallet/capital allocator interfaces.

### Backtests
- [x] Build common multi-strategy backtest foundations.
- [x] Add quant validation helpers/tests.
- [ ] Download/prepare larger historical snapshots.
- [ ] Run larger backtests across more markets/trades/types for every strategy family.
- [ ] Produce final comparable `BACKTEST_RESULTS.md` with PnL, ROI, drawdown, hit rate, turnover, exposure, and skipped-signal reasons.

### Review/release
- [x] Run backend/frontend/research/quant agents.
- [x] Run security-reviewer.
- [x] Run cross/adversarial reviewer.
- [ ] Integrate final local changes into one commit stack and push to GitHub fork.
- [ ] Restart/verify paper runtimes after final tests.

### Financial/live requests — blocked
- [blocked] Close existing Nothing Ever Happens positions.
- [blocked] Move all liquidity/gas/USDC back to wallet.
- [blocked] Create fresh wallets for each bot.
- [blocked] Split roughly `$50` liquidity equally between sub-bots.
- [blocked] Enable live trading.

These require separate typed confirmation with exact scope/amounts.

## Voice 3 — specialist agents and recurring status
User asked the coordinator to create needed agents automatically, especially research and quant/math agents, and add recurring 30-minute Telegram updates.

### Agents
- [x] Define agent flow in `AGENT_FLOW.md`.
- [x] Create `AGENT_REGISTRY.md`.
- [x] Create/deploy deep research agent task.
- [x] Create actual dashboard-visible `research-agent` agent definition and launch session.
- [x] Create/deploy quant/math/finance/big-data agent task.
- [x] Create actual dashboard-visible `quant-math-agent` agent definition and launch session.
- [x] Research agent produced `RESEARCH_APPENDIX.md` and strategy additions.
- [x] Quant/math agent produced `QUANT_REVIEW.md`, quant validation helpers, and tests.
- [x] Developers implemented backend/dashboard/test foundations.
- [x] Security-reviewer ran and approved paper-only continuation.
- [x] Cross/adversarial reviewer ran and added regression coverage.

### Dashboard and recurring monitor
- [x] Add agent status to dashboard model/UI/tests.
- [x] Install 30-minute launchd monitor `com.sbot.neh-multibot-monitor`.
- [x] Monitor checks voice docs, TODOs, agent registry, dashboards, bot processes, git status, and recent commits.
- [x] Monitor generates a Telegram summary every 30 minutes via OpenClaw system event wake.
- [ ] Confirm the next scheduled 30-minute tick delivers Telegram summary end-to-end.


## Full detailed voice task list

- [x] Created `docs/polymarket_multi_bot/VOICE_TASKS_DETAILED_FROM_GS.md` with the full task extraction from all available project-relevant voice transcripts.
