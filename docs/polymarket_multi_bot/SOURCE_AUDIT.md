# Source audit for multi-bot Polymarket work

Safety: this audit covers public documentation/data sources only. It contains no secrets, wallet keys, live funds, or private trading instructions.

| Source | URL / endpoint | Fetch status | Classification | Covered area | Notes / production use |
|---|---|---:|---|---|---|
| Polymarket CLOB docs | `https://docs.polymarket.com/developers/CLOB/introduction` | 200 in research-agent run | Primary | CLOB mechanics, order lifecycle entry point | Use for executable order semantics before any live code. |
| Polymarket API rate limits | `https://docs.polymarket.com/api-reference/rate-limits.md` | 200 in research-agent run | Primary | API safety, throttling | Downloader/monitor must keep bounded retries and respect 429/Retry-After. |
| Polymarket create order docs | `https://docs.polymarket.com/trading/orders/create` | 200 via redirected primary docs | Primary | Order creation semantics | Required before any live or paper-runtime order adapter; current work does not send orders. |
| Polymarket cancel order docs | `https://docs.polymarket.com/trading/orders/cancel` | 200 via redirected primary docs | Primary | Cancel / lifecycle safety | Used to shape paper lifecycle simulator; live cancellation remains blocked. |
| Polymarket order overview | `https://docs.polymarket.com/trading/orders/overview` | 200 via redirected primary docs | Primary | Order lifecycle / status concepts | Primary reference for future order-state replay. |
| Polymarket market-data websocket overview | `https://docs.polymarket.com/market-data/websocket/overview` | 200 via redirected primary docs | Primary | Websocket/order-book event stream | Needed for future L2/order-book replay; not used for current proxy PnL claims. |
| Polymarket fetching markets docs | `https://docs.polymarket.com/market-data/fetching-markets` | 200 via redirected primary docs | Primary | Market metadata | Supports Gamma/market metadata provenance. |
| Polymarket rewards docs | `https://docs.polymarket.com/developers/rewards/overview` | 404 in spot check | Unverified | Maker rewards | Do not cite as implemented; reward economics remain a bounded proxy until a valid primary source is verified. |
| Polymarket Data API trades | `https://data-api.polymarket.com/trades?market=<conditionId>` | Used by local downloader | Primary data endpoint | Historical public trades | Backtests use public trades only; not a complete order-book replay. |
| Polymarket Gamma markets | `https://gamma-api.polymarket.com/markets?closed=true` | Used by local downloader | Primary data endpoint | Market metadata, token ids, closed prices, volume/liquidity | `market_size_usd` currently uses `volumeNum` as a historical activity proxy, not executable depth. |
| Local backtest snapshot manifest | `artifacts/whale_copy/closed_recent_150/manifest.json` | Local cached ignored artifact | Derived | Snapshot provenance | 150 recent closed markets, 20,979 trades, 300 resolution assets from public endpoints. |
| Research follow-up | `docs/polymarket_multi_bot/RESEARCH_AGENT_FOLLOWUP.md` | Local generated doc | Secondary/derived | Docs summary, source leads | Good for direction; primary docs above should govern implementation. |
| Quant follow-up | `docs/polymarket_multi_bot/QUANT_AGENT_FOLLOWUP.md` | Local generated doc | Secondary/derived | Model validation, OOS requirements | Use for validation checklist, not as empirical edge proof. |
| Multi-strategy report | `docs/polymarket_multi_bot/BACKTEST_RESULTS.md` | Local generated report | Derived | PnL/ROI/proxy evidence | Paper-only; market-making/AMM/NEH rows remain proxy until L2 replay. |

## Stale/broken citation policy

- Treat any blog/forum/repo claim as secondary until reproduced with public data and tests.
- Do not run random open-source Polymarket bots with wallet keys.
- Replace broken URLs with primary Polymarket docs or mark the item as `unverified` instead of silently citing it. Current broken rewards URL is explicitly marked `Unverified`.

## Market size/provenance decision

For current offline backtests, `market_size_usd` is explicitly defined as:

> Polymarket Gamma API closed-market `volumeNum` copied into each trade row as a historical activity proxy.

This is acceptable for whale-filter research/backtesting, but it is **not** sufficient for live sizing. Live/paper-runtime executable sizing must use current order-book depth/liquidity and risk limits.
