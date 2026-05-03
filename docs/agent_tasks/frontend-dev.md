# frontend-dev task: dashboards and reports

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`  
Branch target: `feature/whale-copy-backtest-research`

## Scope
Improve dashboards/reporting for main and whale-copy bots. Do not touch transaction code or funds.

## Tasks
- [x] Audit current main dashboard and whale dashboard.
- [x] Add or specify UI blocks for whale signal quality, wallet history, risk/confidence, dry-run/live status, notification health, and backtest metrics.
- [x] Add tests for dashboard rendering/state snapshots.
- [x] Ensure main finalization block remains intact.
- [x] Produce screenshots or HTML artifact verification if possible.

## Success criteria
- Dashboard tests pass.
- UI clearly distinguishes paper vs live.
- No sensitive data rendered.

## Completion route
Send completion/failure to Telegram target `@sbot_finances_bot` using `openclaw message send --channel telegram --target '@sbot_finances_bot' --message '...'`. Do not use heartbeat.

## Frontend-dev notes
- Added `docs/whale_copy_research/FRONTEND_DASHBOARD_REPORT.md` as static reporting verification.
- Relevant test gate: `PYTHONPATH=. venv/bin/pytest tests/test_whale_copy.py tests/test_dashboard.py`.
