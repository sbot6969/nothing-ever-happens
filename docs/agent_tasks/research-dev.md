# research-dev task: Polymarket strategy and open-source bot research

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`  
Branch target: `feature/whale-copy-backtest-research`

## Scope
Research mathematically/strategically plausible improvements for Polymarket bots and summarize evidence. Do not change live config or touch funds.

## Tasks
- [ ] Survey open-source Polymarket bots/tools on GitHub and web.
- [ ] Document strategy type, freshness, usability, risks, and ideas worth borrowing.
- [ ] Research Polymarket fees/cost assumptions, CLOB fill constraints, Data API limits.
- [ ] Analyze whale-copy, CEX↔5m BTC/ETH arbitrage, YES/NO normalization/arbitrage, and unknown-outcome market calibration.
- [ ] Produce `docs/whale_copy_research/RESEARCH.md` with citations/links.
- [ ] Propose 5 concrete strategy iterations for backtesting.

## Success criteria
- Research is source-linked.
- Recommendations are testable and conservative.
- No claims of profitability without data.

## Completion route
Send completion/failure to Telegram target `707939820` using `openclaw message send --channel telegram --target '707939820' --message '...'`. Do not use heartbeat.
