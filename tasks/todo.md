# Current task — 2026-05-05 voice follow-up

- [x] Audit git status and ignore rules for env/secret/local runtime files.
- [x] Fix `.gitignore` so env/secure/local artifacts cannot be pushed.
- [x] Verify sensitive files are not tracked/staged and not picked up by git.
- [x] Re-check launch/live blockers and ensure they are evidence/strategy blockers, not gitignore noise.
- [x] Run a small verification gate and record results.


## Review — 2026-05-05 voice follow-up
- Added recursive ignore rules for real env files, key/cert formats, Solana keypair JSONs, wallet batches, encrypted local wallet state, and local state dirs.
- Verified with `git check-ignore` that `.env`, nested `.env.production`, `.secure/`, `certs/dashboard.key`, and `artifacts/wallets/wallet_batch_*.json` are ignored, while `.env.example` remains trackable.
- Verified `git ls-files` has no tracked real `.env`, key/cert, `.secure`, or wallet-batch candidates in `neh-bot`.
- Updated `CURRENT_STATUS_AND_BLOCKERS.md`: live launch remains blocked by weak strategy evidence; env/gitignore is not a blocker.
