# frontend-dev todo — dashboard/reporting improvements

Scope: dashboard/reporting only. Do not touch transaction/live-funds code.
Branch: feature/whale-copy-backtest-research

- [x] Audit current main dashboard and whale dashboard/reporting files
- [x] Preserve main dashboard finalization block exactly in behavior
- [x] Improve dashboard/reporting UI/state so paper vs live is explicit
- [x] Add/specify blocks for whale signal quality, wallet history, risk/confidence, dry-run/live status, notification health, and backtest metrics
- [x] Add tests for dashboard rendering/state snapshots
- [x] Run relevant tests
- [x] Commit and push branch to fork remote
- [x] Attempt Telegram completion/failure route

## Review
- Main dashboard portfolio websocket now includes runtime status derived from BOT_MODE/LIVE_TRADING_ENABLED/DRY_RUN and renders a Mode card.
- Main dashboard finalization summary/table behavior was left intact and covered by existing finalization test.
- Whale dashboard snapshot now includes runtime, notification health, wallet-history summary, signal-quality summary, and env-fed backtest metrics.
- Whale dashboard renders masked wallet identifiers only in signal rows.
- Tests run: `PYTHONPATH=. venv/bin/pytest` → 174 passed, 1 warning.
- Commit: local/fork `702ae65` before todo amend; origin push failed with GitHub 403, fork push succeeded. Telegram CLI completion/failure route hung until timeout/SIGKILL twice.
