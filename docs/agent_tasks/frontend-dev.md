# frontend-dev task: dashboards and reports

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`  
Branch target: `feature/whale-copy-backtest-research`

## Scope
Improve dashboards/reporting for main and whale-copy bots. Do not touch transaction code or funds.

## Tasks
- [ ] Audit current main dashboard and whale dashboard.
- [ ] Add or specify UI blocks for whale signal quality, wallet history, risk/confidence, dry-run/live status, notification health, and backtest metrics.
- [ ] Add tests for dashboard rendering/state snapshots.
- [ ] Ensure main finalization block remains intact.
- [ ] Produce screenshots or HTML artifact verification if possible.

## Success criteria
- Dashboard tests pass.
- UI clearly distinguishes paper vs live.
- No sensitive data rendered.

## Completion route
Send completion/failure to Telegram target `707939820` using `openclaw message send --channel telegram --target '707939820' --message '...'`. Do not use heartbeat.
