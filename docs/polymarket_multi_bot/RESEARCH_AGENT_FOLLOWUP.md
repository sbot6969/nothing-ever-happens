# Research-agent follow-up — source coverage verification

Date: 2026-05-04
Agent: research-agent
Scope: verify whether the current research docs cover the voice-requested source-backed strategy research, and identify missing primary sources / strategy gaps. This is documentation-only; no live trading, wallet, transfer, position-closing, secret reading, or external posting was performed.

## Coverage verdict

The current research set (`RESEARCH.md`, `RESEARCH_APPENDIX.md`, `STRATEGIES.md`) substantially covers the user's requested areas:

- Prediction-market market making: covered through LMSR / convex-cost AMM work and Polymarket CLOB mechanics.
- Inventory-risk-aware quoting: covered through Avellaneda-Stoikov, Guéant/Lehalle/Fernandez-Tapia, Glosten-Milgrom, Kyle, and crypto inventory-skew practice.
- Statistical / arbitrage logic for binary markets: partially covered through YES-equivalent exposure, negative-risk treatment, LMSR/normal allocation, Kelly sizing, and overfit controls.
- Portfolio allocation across strategy bots: covered at design level via cross-bot capital weights, event caps, drawdown kill switch, and exposure netting.
- Traditional finance / crypto market-making examples: covered through canonical market microstructure papers plus Hummingbot and Uniswap-inspired layering/range ideas.

## Spot-checks performed

- Confirmed Polymarket docs endpoints are reachable for trading overview, create order, and rate limits (`200`, markdown).
- Confirmed Avellaneda-Stoikov NYU PDF is reachable, redirecting to NYU memorial host (`200`, PDF).
- Confirmed Hanson LMSR PDF is reachable (`200`, PDF).
- Found one stale/broken citation: `https://jmlr.org/papers/volume14/abernethy13a/abernethy13a.pdf` returned `404`. Keep the Abernethy/Chen/Vaughan concept, but replace with a verified JMLR title page/PDF or author-hosted copy before treating it as primary-source-backed.

## Missing or weak primary-source coverage

1. **Polymarket historical data provenance:** backtest docs need a primary-source note for where `closed_recent_150` snapshots came from, what endpoints/files were used, and what is missing versus live order-book state.
2. **Polymarket market-size definition:** the 30%-of-market-size whale rule needs a primary-source-backed definition of `market_size` / liquidity / volume / open interest proxy, plus fallback behavior when fields disagree.
3. **Order lifecycle and cancellation details:** current docs cite create-order basics, but maker simulation should also cite verified cancel, open-orders, trades/fills, websocket/realtime, and auth/order-status docs.
4. **Liquidity rewards / maker incentives:** research mentions rewards config but does not yet cite the specific Polymarket rewards/liquidity program docs; this matters for maker economics.
5. **Negative-risk conversion implementation:** current negative-risk coverage is good conceptually, but live-readiness needs primary docs or contract references for conversion mechanics, adapters, and placeholder/Other handling edge cases.
6. **Nothing Ever Happens baseline:** strategy docs still do not source or document the baseline's original hypothesis, filters, historical sample, or failure modes enough to compare it fairly against new bots.
7. **Probability-model sources:** normal-distribution allocator is specified as a sizing framework, but the source of `p_model`, calibration method, and category priors remain under-specified.
8. **Regulatory / terms constraints:** CFTC event-contract material is only broad context; add Polymarket terms/API usage constraints if any future live mode is considered.

## Strategy gaps to feed back into TODOs

- Add a source-verification pass that replaces stale citations and records fetch date/status for each primary source.
- Add `BacktestProvenance` fields to `BACKTEST_RESULTS.md`: data source, endpoint/snapshot path, collection time, market categories, missing book fields, fill model, latency model, fee source, and trial count.
- Define `market_size_source` explicitly for whale detection and add tests for missing/stale/inconsistent market-size data.
- Promote maker simulation from quote formulas to order lifecycle modeling: place-paper, queue haircut, stale cancel, cancel-before-replace, would-fill, and missed-fill events.
- Require adverse-selection metrics for market making and whale copy: mark-to-next-midpoint, mark-to-resolution, midpoint jump after signal, remaining depth after whale trade.
- Add calibration gates for the normal/AMM allocator: no probability-driven sizing above dust size unless calibration sample size and confidence are recorded.
- Add a comparable Nothing Ever Happens baseline report with the same PnL/ROI/drawdown/turnover/exposure/skipped-reason schema as the new bots.

## Recommended next research actions

1. Replace/verify the broken Abernethy/Chen/Vaughan citation.
2. Add a short `SOURCE_AUDIT.md` table with URL, source type, fetch status, primary/secondary classification, and strategy area covered.
3. Add primary Polymarket docs for historical data/provenance, order lifecycle, websockets, cancellations, rewards, and market metadata fields.
4. Update `STRATEGIES.md` and `MASTER_TODO.md` with explicit `market_size_source`, `BacktestProvenance`, and baseline-documentation tasks.

## Safety note

All recommendations remain paper/dry-run only. Live orders, wallet funding, transfers, position closing, wallet creation, and per-bot capital deployment remain blocked until separate typed confirmation with exact scope and amounts.
