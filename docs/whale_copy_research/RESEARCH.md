# Polymarket Bot / Strategy Research

Generated: 2026-05-03. Initial desk research; profitability requires reproducible backtesting.

## Executive read

- The most credible reusable code is official/client infrastructure, not random “profitable arbitrage bot” repos.
- Official/near-official useful repos:
  - `Polymarket/py-clob-client` — Python CLOB client.
  - `Polymarket/clob-client` / `clob-client-v2` — TypeScript CLOB client.
  - `Polymarket/poly-market-maker` — market-maker keeper; useful for inventory/spread/risk patterns.
  - `Polymarket/go-order-utils` — signing/order utilities.
- Copy-trading tools exist, e.g. `os-underground/polymarket-trading-tool`, but live profitability is not established by stars/descriptions.
- Many “arbitrage bot” repos look SEO/spammy: repeated keywords, no credible description, and should not be trusted without source audit.
- Strongest immediate engineering path: improve this bot’s safety + backtest framework before chasing live strategies.

## Search snapshot

### Open-source repos worth reviewing first

| Repo | Type | Why it matters | Risk |
|---|---|---|---|
| https://github.com/Polymarket/py-clob-client | Python CLOB client | canonical order/auth patterns | dependency/API changes |
| https://github.com/Polymarket/clob-client | TS CLOB client | official TS behavior reference | JS-only |
| https://github.com/Polymarket/poly-market-maker | market maker | spread/inventory/risk patterns | strategy may not fit small capital |
| https://github.com/os-underground/polymarket-trading-tool | account monitor/copy-trading | directly relevant to copy monitoring | must audit before using |
| https://github.com/sterlingcrispin/nothing-ever-happens | current base | current bot | strategy edge unproven |
| https://github.com/ThinkEnigmatic/polymarket-bot-arena | BTC 5m strategy arena | may provide backtest/benchmark ideas | needs audit |
| https://github.com/JonathanPetersonn/oracle-lag-sniper | oracle lag sniper | relevant to crypto short-term markets | likely high latency/competition risk |

### Suspicious/requires caution

Repos with repetitive keyword-stuffed descriptions, e.g. many “polymarket arbitrage bot” repos, should be treated as untrusted until source is audited. They may be marketing funnels, malware, or low-quality forks.

## Fees/cost assumptions to verify

Backtest must model costs even if explicit Polymarket trading fee is zero/near-zero:

- Bid/ask spread.
- Slippage and partial fills.
- Stale book risk and latency.
- Minimum order sizes and rejected orders.
- Polygon/network gas for approvals/transfers/redeems where applicable.
- Opportunity cost of locked capital until resolution.
- Liquidation/exit cost before resolution.

## Strategy directions

### 1. Whale-copy / first-time wallet signals

Hypothesis: a new wallet placing a large first visible Polymarket trade may represent informed flow, but also may be sybil/noise.

Backtest filters:
- first visible wallet trade only, then compare with first trade in market and first large trade after inactivity;
- minimum notional;
- minimum market liquidity/depth;
- ignore old startup signals;
- avoid markets too close to resolution unless specifically tested;
- track whether copied side resolves profitably.

Main risk: wallets can split, hide history, or be arbitrage/hedging rather than directional alpha.

### 2. CEX ↔ Polymarket BTC/ETH short-window arbitrage

Possible edge: Polymarket 5m/15m crypto markets may lag CEX prices or oracle-like reference prices.

Reality check:
- latency matters a lot;
- fill risk dominates small edge;
- market close/resolution rules must match the CEX reference precisely;
- fees/spread can erase edge;
- high competition likely.

Backtest needs tick/CEX historical data + Polymarket book snapshots. Without book snapshots, results are only indicative.

### 3. YES/NO normalization / outcome arbitrage

Detect when buyable YES + buyable NO < 1 after spreads and costs, or sellable inventory combinations > 1.

Constraints:
- executable depth at both legs;
- partial fill risk;
- locked capital until resolution;
- settlement/redeem reliability;
- cross-market linked outcomes require careful legal/event semantics.

### 4. Unknown-event/category specialization

User suggested unknown-outcome markets where distributions should be “normal.” Binary markets are not normally distributed in price; prices are implied probabilities plus risk/liquidity premia. Useful version of the idea:

- bucket markets by category and uncertainty;
- test calibration: do 20c/40c/60c/80c buckets resolve at roughly those frequencies?
- avoid markets where information asymmetry is extreme unless following informed flow;
- prefer liquid markets with stable spread and enough time to exit.

### 5. Risk/math improvements

- Conservative Kelly-style sizing only after empirical hit-rate/payoff estimate; otherwise fixed small caps.
- Cap correlated exposure by event/category/wallet.
- Penalize wide spreads and shallow book depth.
- Use delayed-execution sensitivity tests: 0s/5s/30s/120s after whale signal.
- Track drawdown, not only ROI; small capital can show misleading >100% ROI from a few trades.

## Recommended five backtest iterations

1. Baseline first-visible large BUY copy.
2. Add liquidity/spread/depth filters and delayed execution sensitivity.
3. Add wallet quality scoring and sybil/noise penalties.
4. Add market category specialization: crypto short-window vs politics/news/unknown-event markets.
5. Add portfolio sizing and optional arbitrage detectors if data quality supports them.

## Bottom line

Do not fund live whale-copy until the backtest framework can reproduce signal selection and settlement PnL. The likely highest-value work now is not adding more live features, but making results falsifiable.

## Backtest iteration update — 2026-05-03

A public-data snapshot was downloaded from Gamma closed markets + Data API market trades:

- Markets saved: 80 recent closed binary markets with final 0/1 outcome prices.
- Trades saved: 7,697 market trades.
- Resolution assets: 160 CLOB token IDs.
- Snapshot artifact: `artifacts/whale_copy/closed_recent_80/` (ignored local artifact; not committed).

Important caveats:

- `history_count` in this snapshot is first-visible inside the downloaded sample, not a global “wallet first trade ever” proof.
- Closed markets often report current liquidity as zero after settlement, so the backtest avoids using post-close liquidity as a zero execution cap; volume is only a rough activity proxy.
- Iteration 5 crosses 100% ROI only on 5 copied signals. Treat it as an overfit research lead, not launch evidence.
- Real CEX/Polymarket 5m arbitrage and YES/NO normalization need timestamped order-book snapshots; this snapshot does not prove executable arbitrage.

Recommendation: keep whale-copy paper-only; expand to larger walk-forward snapshots and order-book history before any live funding.
