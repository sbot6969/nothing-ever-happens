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
