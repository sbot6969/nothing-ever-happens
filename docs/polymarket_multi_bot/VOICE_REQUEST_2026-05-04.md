# Voice request — 2026-05-04 multi-bot Polymarket system

## User-requested direction
Build a unified Polymarket bot platform with four sub-bots/strategy families:

1. **Nothing Ever Happens** — existing/base strategy.
2. **Whale / ALT trader copy bot** — whale copy-trading strategy.
3. **Market-making bot** — provide/adjust liquidity on Polymarket markets.
4. **Normal-distribution / AMM allocation bot** — portfolio/liquidity allocation based on probability distribution / normal-distribution style sizing.

## Whale classification update
A trade should count as a whale candidate if either:

- Trade notional is **>= $10,000**, OR
- Trade notional is **>= 30% of the market size**, with an additional guard that market size must be **>= $10,000**.

This should replace/extend the first-pass whale filter and must be reflected in scanner tests and backtests.

## Research request
Research hedge-fund / quant / market-making technical docs, papers, PDFs, and real-market examples. Use findings to propose alternative strategy logic for the Polymarket bot beyond simple whale copy-trading, especially:

- Prediction-market specific market making.
- Inventory-risk-aware quoting.
- Statistical/arbitrage logic for binary markets.
- Portfolio allocation across multiple strategy bots.
- Cross-market examples from traditional finance and crypto market making.

Write research outputs as Markdown docs and convert them into implementation TODOs.

## Backtest request
Run richer backtests:

- More markets.
- More trades.
- More market categories/types.
- Per-strategy backtests for each sub-bot/family.
- Validate previous whale-copy results; do not rely on overfit five-trade results.

## Dashboard request
Build one common dashboard for the overall platform that breaks down status/results by sub-bot.

## Agent / review request
Create task lists in Markdown, distribute work across subagents, then:

- Integrate outputs.
- Push to GitHub/fork.
- Re-read TODOs and verify completion.
- Run security-reviewer.
- Run cross-tests/adversarial validation between agents/code paths.

## Runtime / monitoring request
Create a recurring 30-minute check that:

- Re-reads/re-validates this voice request.
- Checks subagent status.
- Checks bot process/dashboard status.
- Continues task tracking in Markdown.

## Financial actions requested but blocked pending typed confirmation
The voice asks to close existing positions, collect USDC/gas/liquidity, create fresh wallets for each bot, distribute roughly $50 equally, and launch.

These are **financial/irreversible external actions** and remain blocked until a separate explicit typed confirmation is received with exact scope and amounts. Until then, all new bot logic must remain **paper/dry-run only**.
