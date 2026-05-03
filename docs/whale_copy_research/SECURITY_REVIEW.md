# Whale Copy / Backtest Security Review

Review date: 2026-05-03 22:28 GMT+2  
Reviewer: security-reviewer  
Repo/branch: `/Users/sbot/.openclaw/workspace/neh-bot` / `feature/whale-copy-backtest-research`  
Scope: current branch through `702ae65` and current working tree, against `docs/agent_tasks/security-reviewer.md`.  
Launch decision: **BLOCKED** until the Critical item below is resolved.

## Summary

The current branch has improved since the previous review: the focused whale-copy/backtest/dashboard tests now pass, finance notifications default to `@sbot_finances_bot`, whale dashboard snapshots mask wallet addresses, and the main dashboard explicitly reports paper/live runtime status.

The branch still must not launch while the current working tree contains a plaintext private key in an untracked helper script. That violates the reviewer checklist even though the key is not committed.

## Findings

### CRITICAL-01 — Plaintext private key in untracked working-tree script

- A redacted working-tree scan found a private-key assignment in `daily_report.sh:8`.
- `daily_report.sh` is untracked and is not ignored by `.gitignore`, so it is one accidental `git add .` away from being committed.
- The same untracked helper script also contains a legacy numeric Telegram target, conflicting with the current required completion/finance route.
- Additional ignored local secrets/artifacts are present under the repo (`.env`, `certs/dashboard.key`, `certs/dashboard.crt`, `bot.log`, `trades.db`, `trades.jsonl`). They are currently ignored, but they increase blast radius if copied or if ignore rules drift.

Impact: exposure of an EVM/Polymarket private key can lead to loss of funds for the associated wallet/proxy wallet.  
Recommendation:
1. Treat the key as compromised unless proven otherwise; rotate/migrate funds using an operator-controlled process outside this review.
2. Remove the literal key from `daily_report.sh`; read secrets only from `.env` or a secret manager.
3. Remove or update the legacy numeric Telegram target in local helper scripts.
4. Add `daily_report.sh`, `start.sh`, `*.bak-*`, and other machine-local helper scripts to `.gitignore`, or move them outside the repo.
5. Re-run a redacted secret scan before launch.

### MEDIUM-01 — Whale dashboard still binds to `0.0.0.0` without authentication

- `bot/whale_copy.py` starts the whale dashboard with `web.TCPSite(runner, "0.0.0.0", port)`.
- Dashboard snapshots now mask wallets and escape rendered values, which reduces leakage.
- The dashboard still exposes strategy telemetry, signal quality, paper/live mode, notification health, backtest metadata, markets, and transaction links to anyone who can reach the port.

Impact: operational/strategy privacy leak if deployed on a public host without network controls.  
Recommendation: bind to `127.0.0.1` by default, require explicit `DASHBOARD_HOST=0.0.0.0` for exposed deployments, and place public deployments behind auth/TLS/reverse proxy.

### MEDIUM-02 — Finance Telegram notifications are still default-enabled

- `bot/finance_notifier.py` now defaults `FINANCE_TG_TARGET` to `@sbot_finances_bot`, matching the current completion/finance route.
- The notifier remains default-enabled (`FINANCE_TG_ENABLED` defaults true).
- Shell invocation is injection-safe (`subprocess.run([...], shell=False)`) and best-effort (`check=False`, timeout, background queue).

Impact: trade events, wallet identifiers in ledger records, errors, and PnL/status can still be sent externally by default in reused deployments.  
Recommendation: consider defaulting `FINANCE_TG_ENABLED=false` and requiring explicit deployment config for external notifications.

### LOW-01 — Whale API polling has timeouts but no explicit exponential backoff

- `_fetch_json()` uses an aiohttp request timeout of 15 seconds.
- `poll_whales()` catches exceptions and sleeps `WHALE_POLL_INTERVAL_SEC`, but does not implement exponential backoff or explicit 429/5xx handling.

Impact: repeated failures can cause noisy logs/notifications and unnecessary API pressure.  
Recommendation: add bounded exponential backoff with jitter and special handling for HTTP 429/5xx.

## Positive observations

- Checked-in git scan did not find committed private keys, cert private keys, `.env`, DBs, logs, or ledgers.
- `.gitignore` includes important runtime artifacts such as `.env`, `config.json`, `trades.jsonl`, `bot.log`, `*.db`, `certs/`, and `backtest_artifacts/`.
- `bot/whale_copy.py` defaults to paper mode: `WHALE_COPY_LIVE_ENABLED` defaults false.
- Even when `WHALE_COPY_LIVE_ENABLED=true`, `_handle_signal()` only records a `whale_copy_live_trade` ledger event with status `live_not_implemented_without_wallet_confirmation`; it does not submit orders, create wallets, transfer funds, close positions, sell, or redeem.
- `bot/backtest/whale_copy.py` is offline-only: it reads cached JSON fixtures and writes optional JSON reports; it contains no network calls or order submission paths.
- Notifier command construction is injection-safe, has a timeout, and is best-effort.
- Whale dashboard snapshots remove raw wallet addresses and expose only `masked_wallet`; browser rendering escapes dynamic strings and uses `rel="noreferrer"` on outbound links.
- Main dashboard now reports runtime status (`PAPER / DRY-RUN` vs `LIVE SEND ENABLED`) from `BOT_MODE`, `LIVE_TRADING_ENABLED`, and `DRY_RUN`.

## Verification performed

- Reviewed current branch/head state: `702ae65` on `feature/whale-copy-backtest-research`.
- Reviewed security-sensitive files and current diffs involving whale-copy, backtest, notifier, dashboard, config, ledger, and tests.
- Ran committed-file grep for secret-related names, private-key/cert patterns, and Telegram route identifiers.
- Ran redacted working-tree scan excluding `.git`, `venv`, `__pycache__`, and `.pytest_cache`.
- Ran focused tests: `./venv/bin/python -m pytest tests/test_config.py tests/test_nothing_happens.py tests/test_dashboard.py tests/test_whale_copy.py tests/test_backtest_whale_copy.py tests/test_whale_copy_backtest.py tests/test_whale_copy_scanner_validation.py -q` → `79 passed`.
- No live trades, transfers, wallet creation, position closing, system events, or heartbeat actions were performed.

## Checklist status

- [x] No secrets/private keys/certs/logs/DBs/ledgers committed in tracked git files.
- [ ] No secrets/private keys/certs/logs/DBs/ledgers in current working tree. **Blocked by CRITICAL-01.**
- [x] Live trading/transfer/position-close gates default-off for whale-copy and do not perform live orders.
- [x] Notifier shell calls are injection-safe and best-effort.
- [ ] Network/API errors handled with timeouts/backoff. **Timeouts yes; explicit backoff missing (LOW-01).**
- [x] Backtest cannot be confused with live trading.
- [x] Tests cover critical safety paths for current branch scope (`79 passed`).
- [x] Dashboard does not leak private wallet secrets in reviewed code paths.

## Final launch decision

**BLOCK LAUNCH.** Do not proceed to live whale-copy launch until the plaintext private key is removed from the working tree, any real exposed key is rotated/migrated, and the local helper scripts/artifacts are ignored or moved outside the repo.
