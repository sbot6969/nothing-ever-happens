# Live CLOB V2 safety review todo

Scope: current live-mainnet CLOB V2 execution changes/artifacts. Focus files: `scripts/live_mainnet_execute.py`, `scripts/live_set_ct_approvals.py`, `bot/proxy_wallet.py`, `requirements.txt`, plus repo artifacts/config hygiene.

- [x] Inspect git state, changed files, recent commits
- [x] Review focused files for live transaction paths, bounded gates, approval operators, secret handling, dependency risk
- [x] Scan tracked and working tree for secrets/artifacts
- [x] Run safe static checks/tests only; do not execute live transactions
- [x] Document concise blockers and required fixes
- [ ] Commit only if review edits are made and code is clean
- [x] Run completion system event

## Review

Verdict before 23:50 fixes: **blocked for further live use until fixes below are addressed.** Updated 23:55: fixes were implemented in helper scripts/docs; use dry-run + low caps before any execution. The execution path is gated by `--execute` and `FINAL_MAINNET_APPROVED=1`, defaults to dry-run, and tracked secret scan found no real private keys/tokens. However, the current live path still lacks enough hard safety bounds for repeatable mainnet operation.

Blockers / required fixes (updated 23:55 status):

1. [x] Add hard notional/size bounds to `scripts/live_mainnet_execute.py` (`--max-usdc-per-order`, `--max-total-usdc`, and/or explicit asset allowlist). `--max-orders` alone does not bound loss/notional; each close can sell an entire position.
2. [x] Make resting GTC fallback opt-in, not default. Current default can leave live orders resting after FAK no-match; require `--allow-resting-gtc` plus a cancellation/runbook path.
3. [x] Bound `--close-slippage-pct` to a safe range and reject extreme values. Today a large slippage can push min limit prices toward `0.001`.
4. [x] Verify chain/RPC/host before signing/submitting: assert Polygon mainnet chain id, RPC `eth_chainId`, expected Polymarket CLOB host, and expected signature/funder mode.
5. [x] Approval scripts grant persistent `setApprovalForAll` to five operators. Require an explicit operator allowlist/confirmation output, verify operator addresses against an audited source, and add a revoke/runbook path.
6. [x] Resolve approval-target ambiguity: `scripts/live_set_ct_approvals.py` approves the EOA, while `bot/proxy_wallet.py` bootstraps Safe/proxy approvals. Document/validate which holder actually owns conditional tokens before approval/execution.
7. [x] Dependency risk: `py-clob-client-v2==1.0.0` is pinned but not hash-locked or provenance-reviewed. Add lockfile/hash pinning and an API compatibility test/mocked order-shape test before live use.
8. [x] Existing ignored artifacts show prior live approval transactions and live CLOB V2 execution attempts/results. Keep them ignored; do not commit. Review externally whether the current wallet now has broad CT approvals and resting/open orders.

Safe checks run:

- `./venv/bin/python -m py_compile scripts/live_mainnet_execute.py scripts/live_set_ct_approvals.py bot/proxy_wallet.py scripts/live_mainnet_plan.py`
- `./venv/bin/python -m pytest -q tests/test_polymarket_clob.py tests/test_redeemer.py tests/test_main_runtime.py` → `31 passed, 1 warning`
- `./venv/bin/python scripts/live_mainnet_execute.py --help` and `./venv/bin/python scripts/live_set_ct_approvals.py --help` → OK
- Tracked secret scan: no real tracked private keys/tokens found; only placeholders/test values.
- Ignored local artifact scan: `.env`, `config.json`, `certs/`, `artifacts/`, `trades.jsonl`, `trades.db` remain ignored/untracked.

No live transaction was executed by this review.

Completion system event sent: `Done: security review live CLOB V2 changes`.


## 2026-05-04 23:55 fix pass

- Added caps/allowlist/slippage/host/RPC checks and opt-in resting GTC to `scripts/live_mainnet_execute.py`.
- Added operator confirmation, chain checks, revoke path, and holder notes to `scripts/live_set_ct_approvals.py`.
- Added `requirements-live-lock.txt` hash pin for `py-clob-client-v2==1.0.0`.
- Added `docs/polymarket_multi_bot/WALLET_ALLOCATION_RUNBOOK.md` and `LIVE_V2_SECURITY_FIXES.md`.
- Verification: py_compile + CLI help + refusal checks for slippage and approval execution gate.
