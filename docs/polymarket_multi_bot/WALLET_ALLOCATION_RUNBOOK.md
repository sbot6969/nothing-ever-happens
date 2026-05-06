# Wallet allocation runbook — 2026-05-04

Purpose: make further fund movement explicit and inspectable. No private keys or passphrases are stored here.

## Current local wallets

Encrypted keystores are local-only under ignored `.secure/wallets/20260504_222008/` with `0600` files. Public addresses:

| Label | Address | Intended role | Current cap until changed |
|---|---|---|---|
| `neh-live-1` | `0x1196BaBe96B89Ab902662aD076A0831713FF9892` | candidate Nothing Ever Happens / conservative live wallet | tiny test funding only |
| `neh-live-2` | `0xb1bD9719165E2eCDA360E413923F2AD2D0d27143` | candidate experimental/paper-to-live wallet | tiny test funding only |

## Allocation rule before moving more funds

Before any additional transfer, write the exact intended movement into the funding script/run output:

1. Source wallet masked in output; never print private key.
2. Destination address must match the table above or an explicitly added address.
3. Per-transfer cap: default `$0.25` unless raised in code/config and reviewed.
4. Total run cap: default `$0.50` unless raised in code/config and reviewed.
5. Keep source wallet reserve for gas and existing bot operations.
6. Record tx hash, amount, destination label, and reason in ignored artifact JSON.

## Revoke / rollback

- Conditional-token approvals can now be revoked with `scripts/live_set_ct_approvals.py --revoke` after reviewing dry-run output.
- Any broader live launch must verify CLOB open orders are empty before and after execution.
- Zero-value redeem candidates remain skipped; do not burn gas for `$0` currentValue.

## Current recommendation

Do not increase allocation yet. Live runtime has just recovered from CLOB `order_version_mismatch` and `1015`/`429`, and non-NEH cached backtests are not profitable enough to justify expansion.
