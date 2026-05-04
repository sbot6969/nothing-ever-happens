# backend-dev task — multi-bot Polymarket backend/backtests

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`
Branch: `feature/whale-copy-backtest-research` or a sub-branch from it.

## Scope
Implement/prepare backend foundations for a four-strategy paper platform:
1. Nothing Ever Happens baseline.
2. Whale/ALT copy bot.
3. Market-making bot.
4. Normal-distribution AMM allocation bot.

## Required work
- [x] Update whale classification logic: whale if notional >= $10,000 OR notional >= 30% of market size when market size >= $10,000.
- [x] Add deterministic tests for whale threshold logic and edge cases.
- [x] Design/add shared strategy result/backtest data structures where small and clean.
- [x] Extend backtest harness enough to compare multiple strategy families in paper simulation.
- [x] Do not add live trading/funding/wallet actions.
- [x] Keep all new runtime paths dry-run/paper by default.

## Verification
- [x] Run relevant focused pytest.
- [x] Run full pytest if feasible.
- [x] Commit changes with a clear message.

## Completion notes
- Added `bot/whale_thresholds.py` with pure threshold classification: absolute `$10,000` OR relative `>=30%` of market size when market size is `>= $10,000`.
- Integrated threshold classification into whale runtime filtering and whale-copy backtest rejection logic.
- Added safe `bot/backtest/multistrategy.py` comparison skeleton for `nothing_happens`, `whale_copy`, `market_making`, and `normal_distribution_amm`; all paths are deterministic/paper-only.
- Focused pytest: `24 passed`.
- Full pytest: `192 passed, 1 warning`.

## Completion
Report what changed, tests run, any blockers. Do not perform live financial actions.
