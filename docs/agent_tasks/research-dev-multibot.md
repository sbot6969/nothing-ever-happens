# research-dev task — hedge-fund/market-making research for Polymarket strategy design

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`

## Scope
Find and summarize source-backed material for alternative Polymarket strategy logic beyond simple whale copy-trading.

## Required research areas
- Hedge-fund/quant market-making technical PDFs/papers/docs.
- Inventory-risk-aware market making (Avellaneda-Stoikov, spread control, inventory skew).
- Prediction-market / binary-market making and arbitrage.
- Traditional finance and crypto examples relevant to CLOB liquidity provision.
- Risk controls: adverse selection, latency, drawdown, capital allocation, stale quotes.

## Deliverables
- `docs/polymarket_multi_bot/RESEARCH.md`: source-backed notes with links/citations.
- `docs/polymarket_multi_bot/STRATEGIES.md`: concrete proposed strategies and implementation TODOs.
- Recommendations for which strategy families are safe to paper-test first.

## Constraints
- Do not run unknown third-party bots with keys.
- Do not expose secrets.
- Do not recommend live launch without robust validation.
