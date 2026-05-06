# Current status and real blockers — 2026-05-04 23:05 CEST

This file is the monitor source of truth for user-facing open/blocked status. It replaces stale “blocked until typed confirmation” wording: the user has given broad approval to proceed, but execution still must pass concrete engineering, chain, secret, and venue-safety checks.

## Completed / no longer blocked by permission wording

- [x] Multi-bot platform docs, strategy specs, research, quant review, dashboard integration, agent registry, security/cross review, and recurring monitor were built and verified.
- [x] Whale filter update implemented: notional >= $10k OR trade >= 30% of market size when market size >= $10k.
- [x] Larger cached/public backtests and comparable report were generated.
- [x] Durable `research-agent` and `quant-math-agent` were created and launched; follow-up outputs were integrated.
- [x] Existing nonzero CLOB position tails that were safe/correct to close were closed with bounded V2 FAK sells.
- [x] CLOB open orders were verified empty after the close pass.
- [x] Local encrypted wallet generation flow was implemented; secrets are ignored and not printed.
- [x] Initial small wallet funding was executed through the gated funding script.
- [x] `order_version_mismatch` was fixed by moving the live CLOB path to `py-clob-client-v2`; fresh runtime checks after restart show zero new `order_version_mismatch`, `PolyApiException`, `HTTP/2 429`, `1015`, or `ERROR`.

## Real blockers / why they are still blockers

- [x] **Live order/recovery pressure cooldown observed clean.** CLOB/Cloudflare `1015` and `HTTP/2 429` appeared after recovery spam; mitigation remains applied (ambiguous recovery worker disabled, due rows postponed, price cycle capped to 10 markets, request concurrency lowered). Fresh log check shows 14 clean price cycles and zero `order_version_mismatch`, `PolyApiException`, `HTTP/2 429`, `1015`, or `ERROR`.
- [x] **Security-reviewer live V2 script fixes implemented.** Added hard notional caps, opt-in resting GTC fallback, slippage bounds, chain/RPC/host verification, approval allowlist confirmation, revoke path, holder note, dependency hash pin, and wallet allocation runbook. Live execution still requires dry-run + low caps before use.
- [blocked] **Launching/expanding live trading is blocked by strategy evidence, not permission.** Reason: safe whale-copy cached sanity backtests were negative (`closed_recent_150` ROI -1.2011%, `closed_recent_300` ROI -0.1470%); these are not profitability proof. Need stronger OOS/walk-forward/stress evidence and per-bot caps before allocating more capital.
- [x] **Wallet allocation/runbook gap documented.** Public wallet mapping, current caps, reserve rule, and revoke/rollback notes are in `WALLET_ALLOCATION_RUNBOOK.md`. Larger allocation remains strategically blocked by weak backtest evidence, not by missing permission wording.
- [x] **Private GitHub env/gitignore blocker cleared for `neh-bot`.** Real envs, encrypted wallet state, local keys, logs, certs, and generated artifacts are ignored; `.env.example` remains intentionally trackable. A git name audit confirms no real `.env*` is tracked in `neh-bot`. Private backup pushes should use sanitized staging, but env files themselves are no longer a blocker.

## Next actions

- [x] Implement the live V2 security-review fixes or disable the live helper scripts until they meet the review.
- [x] Keep live runtime monitored for clean cycles after the recovery throttle/cooldown changes.
- [x] Update wallet allocation runbook with exact per-bot wallet/address/cap/reserve/revoke plan before moving more funds.
- [x] Replace monitor wording so Telegram summaries show only these real blockers, not stale “typed confirmation” blockers.
- [x] Continue the private GitHub backup inventory as a separate workstream.


## External-write blockers after inventory

- [blocked] Create/push private GitHub backups. Reason: external write still needs the intended private repo target/project selection. Env files are handled by `.gitignore`; remaining per-project non-env private files such as `expenses.json` / `task_flags.json` still require sanitized staging if those projects are included.
