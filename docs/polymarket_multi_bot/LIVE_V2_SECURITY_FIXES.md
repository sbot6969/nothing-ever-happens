# Live CLOB V2 security fixes — 2026-05-04

Implemented after security-reviewer findings:

- `scripts/live_mainnet_execute.py`
  - Added `--max-usdc-per-order` and `--max-total-usdc` caps.
  - Added repeatable `--allow-asset` allowlist.
  - Made resting GTC fallback opt-in via `--allow-resting-gtc` instead of default.
  - Bounded `--close-slippage-pct` to `0..25`.
  - Added expected CLOB host and Polygon chain id checks; live execution requires `POLYGON_RPC_URL` chain verification.
- `scripts/live_set_ct_approvals.py`
  - Added Polygon chain/RPC/host checks.
  - Added `--confirm-operators` requirement for execution.
  - Added `--revoke` path for approval rollback.
  - Documented that this script handles signer/EOA approvals; Safe/proxy approvals remain in `bot.proxy_wallet` bootstrap.
- Dependency provenance
  - Added `requirements-live-lock.txt` with hash for `py-clob-client-v2==1.0.0`.
- Runbook
  - Added `WALLET_ALLOCATION_RUNBOOK.md` with public wallet mapping, caps, reserve, and revoke notes.

Remaining caution: these helpers are safer, but any live execution should still use dry-run first, inspect artifact output, and keep low caps.
