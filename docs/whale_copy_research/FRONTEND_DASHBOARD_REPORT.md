# Frontend Dashboard Verification — Whale Copy Research

Date: 2026-05-03
Branch: `feature/whale-copy-backtest-research`
Scope: dashboard/reporting only; no transaction/live-funds code changed.

## Main dashboard

- Preserves the existing finalization summary and position-table finalization column.
- Adds an explicit runtime Mode card sourced from `BOT_MODE`, `LIVE_TRADING_ENABLED`, and `DRY_RUN`.
- Displays `PAPER / DRY-RUN` unless all live-send gates are enabled.

## Whale-copy dashboard

The dashboard now exposes these reporting blocks:

- `Mode`: clear `PAPER / DRY-RUN` vs `LIVE COPY ENABLED` label.
- `Watched Signals`: count of observed whale signals.
- `Wallet History`: unique wallets checked, first-visible signals, cache size.
- `Signal Quality`: average/latest confidence and high-confidence count.
- `Risk / Confidence`: latest planned copy notional, latest confidence, and max-copy cap.
- `Expected Slippage`: configured reporting assumption via `WHALE_EXPECTED_SLIPPAGE_BPS`.
- `Notification Health`: best-effort notifier/ledger state.
- `API / Rate Limit`: API poll status and rate-limit detection from errors.
- `Backtest Best`: env-fed latest backtest iteration, ROI, PnL, and strategy label.

## Sensitive data check

- Whale signal rows render `masked_wallet` only (`0x1234…cdef` style).
- The raw wallet field is removed from websocket snapshot signal rows.
- No secrets, config files, DB dumps, certs, or logs are included in this dashboard/reporting change.

## Verification

- Focused tests: `env -u PRIVATE_KEY -u FUNDER_ADDRESS -u BOT_MODE -u LIVE_TRADING_ENABLED -u DRY_RUN PYTHONPATH=. venv/bin/pytest tests/test_whale_copy.py tests/test_dashboard.py` → 19 passed.
- Full suite: `env -u PRIVATE_KEY -u FUNDER_ADDRESS -u BOT_MODE -u LIVE_TRADING_ENABLED -u DRY_RUN PYTHONPATH=. venv/bin/pytest` → 176 passed, 1 warning.
