# frontend-dev todo — dashboard/reporting improvements

Scope: dashboard/reporting only. Do not touch transaction/live-funds code.
Branch: feature/whale-copy-backtest-research
Completion route: Telegram `@sbot_finances_bot` only. Do not use Telegram chat `707939820`.

- [x] Audit current main dashboard and whale dashboard/reporting files
- [x] Preserve main dashboard finalization block exactly in behavior
- [x] Improve dashboard/reporting UI/state so paper vs live is explicit
- [x] Add/specify blocks for whale signal quality, wallet history, risk/confidence, dry-run/live status, notification health, and backtest metrics
- [x] Add expected slippage and API/rate-limit reporting
- [x] Add tests for dashboard rendering/state snapshots
- [x] Produce static dashboard verification artifact
- [x] Run relevant tests
- [x] Commit and push branch to fork remote
- [blocked] Send completion/failure to Telegram `@sbot_finances_bot` — `openclaw message send` failed: recipient could not be resolved to a numeric chat ID / chat not found

## Review
- Main dashboard portfolio websocket includes runtime status derived from BOT_MODE/LIVE_TRADING_ENABLED/DRY_RUN and renders a Mode card.
- Main dashboard finalization summary/table behavior was left intact and covered by existing finalization test.
- Whale dashboard snapshot includes runtime, notification health, wallet-history summary, signal-quality summary, risk summary, API/rate-limit status, expected slippage, and env-fed backtest metrics.
- Whale dashboard renders masked wallet identifiers only in signal rows.
- Static verification artifact: `docs/whale_copy_research/FRONTEND_DASHBOARD_REPORT.md`.
- Focused tests: `env -u PRIVATE_KEY -u FUNDER_ADDRESS -u BOT_MODE -u LIVE_TRADING_ENABLED -u DRY_RUN PYTHONPATH=. venv/bin/pytest tests/test_whale_copy.py tests/test_dashboard.py` → 19 passed.
- Full tests: `env -u PRIVATE_KEY -u FUNDER_ADDRESS -u BOT_MODE -u LIVE_TRADING_ENABLED -u DRY_RUN PYTHONPATH=. venv/bin/pytest` → 176 passed, 1 warning.

## Completion send attempts
- `openclaw message send --channel telegram --target '@sbot_finances_bot' ...` failed: recipient could not be resolved to a numeric chat ID (`getChat` 400 chat not found).
- Per latest operator instruction, no messages were sent to Telegram chat `707939820`.

## 2026-05-03 — Continue all voice-note tasks

Goal: finish whale-copy validation/backtest/research work without live financial actions.

- [x] Build/reuse historical Polymarket data downloader/cache for closed markets and market trades.
- [x] Run reproducible backtests across baseline + 5 improvement iterations.
- [x] Record PnL/ROI, drawdown, hit-rate, and recommendation.
- [x] Expand tests for downloader/experiment logic.
- [x] Update MASTER_TODO/backtest report/research docs.
- [x] Run full pytest.
- [ ] Commit and push.
- [x] Keep main/whale bots alive and paper/live safety intact.

Safety: no wallet funding, position closing, transfer, or live copy order.


Review / result:
- Downloaded public snapshot: 80 closed markets, 7,697 trades, 160 resolution assets.
- Ran baseline + 5 iterations. Best cached-sample result: iteration 5, ROI 235.91%, PnL $94.17 on 5 copied trades.
- Caveat: high overfit/small sample; recommendation remains paper-only until walk-forward/order-book validation.
- Full pytest: 183 passed, 1 warning.
- Runtime verified: main_count=1, whale_count=1, both dashboards OK.

Review 2026-05-04 dashboards:
- Diagnosed 8766: service was listening, but only HTTP; opening it as HTTPS caused TLS/protocol error. Updated whale-copy dashboard to support DASHBOARD_SSL_CERT/DASHBOARD_SSL_KEY and restarted it on HTTPS.
- Added charts to main 8765 dashboard: market stats, portfolio value, trade-flow ledger counts.
- Added charts to whale-copy 8766 dashboard: runtime activity, signal notional/planned copy, and backtest iteration ROI bars from iteration_report.json.
- Safety unchanged: whale-copy remains paper/dry-run unless WHALE_COPY_LIVE_ENABLED is explicitly enabled.
- Verification: targeted pytest passed (26 passed); HTTP(S) checks returned 200 for 8765/8766; WebSocket smoke passed for both dashboards.

# Current task — 2026-05-04 multi-bot Polymarket platform

- [x] Capture voice request and financial safety boundary.
- [x] Create master TODO and per-agent task specs.
- [x] Spawn backend-dev for whale filter + backtest harness + tests. Session: marine-bloom.
- [x] Spawn research/default agent for hedge-fund/market-making research docs. research-dev id unavailable; default fallback failed; using backend-dev research session: kind-kelp.
- [x] Spawn frontend-dev for unified dashboard. Session: fresh-atlas.
- [ ] research-dev: create source-backed `docs/polymarket_multi_bot/RESEARCH.md`.
- [ ] research-dev: create concrete `docs/polymarket_multi_bot/STRATEGIES.md` and implementation TODOs.
- [ ] research-dev: commit docs changes with clear message.
- [x] backend-dev: implement whale threshold helper ($10k absolute OR >=30% market size with market >=$10k), tests, and backtest integration.
- [x] backend-dev: add safe multi-strategy backtest comparison skeleton for nothing_happens, whale_copy, market_making, normal_distribution_amm.
- [x] backend-dev: run focused/full pytest and commit. Full pytest passed: `192 passed, 1 warning`.
- [ ] Integrate agent outputs and run focused/full tests.
- [ ] Run security-reviewer and cross/adversarial review.
- [ ] Commit/push safe paper-mode work to GitHub fork.
- [ ] Restart/verify paper-only bots/dashboard after tests pass.
- [x] Install 30-minute recurring safe monitor job via launchd: com.sbot.neh-multibot-monitor.
- [blocked] Close positions, create/fund wallets, transfer/split $50, enable live mode — requires separate explicit typed confirmation with exact scope.
