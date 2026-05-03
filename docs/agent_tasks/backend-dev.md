# backend-dev task: tests, whale scanner, backtest framework

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`  
Branch target: `feature/whale-copy-backtest-research`

## Scope
Implement and validate backend/test/backtest parts for the whale-copy Polymarket bot. Do **not** perform live trades, transfers, or position closing.

## Tasks
- [ ] Audit transaction/order submission paths and document live gates.
- [ ] Add/extend unit tests for dry-run safety, config gates, notifier isolation, whale scanner parsing/dedupe/history filter.
- [ ] Build a backtest module under `bot/backtest/` or similar with deterministic simulator accounting.
- [ ] Add CLI for whale-copy backtests with cached input artifacts ignored by git.
- [ ] Include fees/spread/slippage/liquidity assumptions in code and docs.
- [ ] Run all tests and record commands/results.

## Success criteria
- Full pytest suite passes.
- Backtest can run on a small sample fixture without network.
- No secrets/runtime files committed.
- Completion report includes files changed and remaining blockers.

## Completion route
Send completion/failure to Telegram target `707939820` using `openclaw message send --channel telegram --target '707939820' --message '...'`. Do not use heartbeat.
