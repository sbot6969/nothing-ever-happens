# security-reviewer task: mandatory review checklist

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`  
Branch target: `feature/whale-copy-backtest-research`

## Scope
Review every module and commit related to whale-copy/backtest/notifier/dashboard before live launch. Do not perform live actions.

## Review checklist
- [ ] No secrets, private keys, `.env`, certs, logs, DBs, or ledgers committed.
- [ ] Live trading/transfer/position close gates default-off and require explicit confirmation/config.
- [ ] Notifier shell calls are injection-safe and best-effort.
- [ ] Network/API errors handled with timeouts/backoff.
- [ ] Backtest cannot be confused with live trading.
- [ ] Tests cover critical safety paths.
- [ ] Dashboard does not leak private wallet secrets.

## Success criteria
- Produce `docs/whale_copy_research/SECURITY_REVIEW.md` with findings and severity.
- Block launch if any critical/high issue remains.

## Completion route
Send completion/failure to Telegram target `@sbot_finances_bot` using `openclaw message send --channel telegram --target '@sbot_finances_bot' --message '...'`. Do not use heartbeat.
