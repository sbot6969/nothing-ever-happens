
## Open-source Polymarket bot survey — 2026-05-03

GitHub API search snapshot saved locally at `artifacts/whale_copy/github_research.json` (ignored). Top findings:

| Repo | Stars | License | Updated | Usefulness / risk |
|---|---:|---|---|---|
| [0xFives/Polymarket-Arbitrage-Crypto-Trading-Bot-V3](https://github.com/0xFives/Polymarket-Arbitrage-Crypto-Trading-Bot-V3) | 148 | unknown | 2026-05-01T10:46:36Z | high risk / likely SEO-spam or closed-source wrapper; do not run with keys. Desc: polymarket arbitrage bot polymarket arbitrage bot polymarket arbitrage bot polymarket arbitrage bot polymarket arbitrage |
| [zkOSAI/polymarket-arbitrage-bot](https://github.com/zkOSAI/polymarket-arbitrage-bot) | 120 | unknown | 2026-04-30T01:07:14Z | high risk / likely SEO-spam or closed-source wrapper; do not run with keys. Desc: 🥇polymarket arbitrage bot polymarket trading bot polymarket arbitrage bot polymarket trading bot polymarket arbitrage bo |
| [Pompeiuss/polymarket-arbitrage-trading-bot](https://github.com/Pompeiuss/polymarket-arbitrage-trading-bot) | 79 | unknown | 2026-05-02T20:33:36Z | high risk / likely SEO-spam or closed-source wrapper; do not run with keys. Desc: polymarket trading bot, polymarket arbitrage bot, polymarket copy trading bot, polymarket trading bot, polymarket arbitr |
| [JonathanPetersonn/oracle-lag-sniper](https://github.com/JonathanPetersonn/oracle-lag-sniper) | 39 | MIT | 2026-05-03T17:10:51Z | interesting latency idea; needs code audit and execution data. Desc: Automated trading system exploiting latency between Chainlink oracle updates and Polymarket CLOB repricing on 15-min BTC |
| [LuciferForge/polymarket-btc-autotrader](https://github.com/LuciferForge/polymarket-btc-autotrader) | 12 | unknown | 2026-04-07T19:34:50Z | useful CLOB integration reference; still audit before borrowing. Desc: Autonomous BTC & SOL trading bot for Polymarket. ARB (100% WR) + SNIPE strategies. Auto-trades via py-clob-client, auto- |
| [PoDev-Juanthiago/Polymarket-Arbitrage-Bot](https://github.com/PoDev-Juanthiago/Polymarket-Arbitrage-Bot) | 393 | unknown | 2026-05-03T22:02:39Z | high risk / likely SEO-spam or closed-source wrapper; do not run with keys. Desc: Polymarket arbitrage trading bot Polymarket arbitrage trading bot Polymarket arbitrage trading bot Polymarket arbitrage  |
| [PolyScripts/polymarket-arbitrage-trading-bot-pack-5min-15min-kalshi](https://github.com/PolyScripts/polymarket-arbitrage-trading-bot-pack-5min-15min-kalshi) | 268 | unknown | 2026-05-03T17:53:04Z | high risk / likely SEO-spam or closed-source wrapper; do not run with keys. Desc: polymarket arbitrage bot polymarket arbitrage bot polymarket arbitrage bot polymarket arbitrage bot polymarket arbitrage |
| [haredoggy/Prediction-Markets-Trading-Bot-Toolkits](https://github.com/haredoggy/Prediction-Markets-Trading-Bot-Toolkits) | 242 | MIT | 2026-05-03T02:45:08Z | review required. Desc: Trading bots on Prediction markets like Polymarket, Kalshi, Limitless etc. it is also available on Predict.fun predictdo |
| [lorine93s/polymarket-btc-5min-15min-arbitrage-bot](https://github.com/lorine93s/polymarket-btc-5min-15min-arbitrage-bot) | 230 | unknown | 2026-05-03T18:33:51Z | high risk / likely SEO-spam or closed-source wrapper; do not run with keys. Desc: polymarket trading bot, arbitrage bot,  polymarket trading bot, arbitrage bot,  polymarket trading bot, arbitrage bot,   |
| [warproxxx/poly-maker](https://github.com/warproxxx/poly-maker) | 1127 | MIT | 2026-05-03T19:04:42Z | review required. Desc: An automated market making bot for Polymarket that provides liquidity by maintaining orders on both sides of the order b |
| [Polymarket/poly-market-maker](https://github.com/Polymarket/poly-market-maker) | 290 | MIT | 2026-05-03T19:02:12Z | review required. Desc: Market maker keeper for the Polymarket CLOB |
| [PolyScripts/polymarket-market-maker-bot](https://github.com/PolyScripts/polymarket-market-maker-bot) | 70 | MIT | 2026-04-29T16:50:00Z | high risk / likely SEO-spam or closed-source wrapper; do not run with keys. Desc: polymarket market maker bot polymarket market maker bot polymarket market maker polymarket market maker polymarket marke |

Takeaways:

- Many high-star “Polymarket arbitrage bot” repos look SEO-spammy/repetitive and should not be run with wallet keys.
- The useful ideas to borrow are conceptual only: oracle-lag monitoring, YES/NO price-sum checks, CLOB order-book sampling, and strict dry-run/live gates.
- Before using any external code: clone to temp, inspect dependencies, search for exfiltration, run tests offline, and never provide production private keys.
