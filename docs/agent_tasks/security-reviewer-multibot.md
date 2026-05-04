# security-reviewer task — multi-bot platform review

Run after backend/research/frontend changes are integrated.

## Review focus
- Live-trading gates default off and cannot be accidentally enabled.
- No private keys/secrets in tracked code/docs/logs/dashboard.
- Financial operations (close positions, transfer funds, create/fund wallets) remain blocked pending typed confirmation.
- Backtest claims are labeled accurately; no overfit results presented as live-ready.
- Data downloaders have bounds, retry/backoff, and do not leak auth.
- Dashboard does not expose sensitive wallet/key info.
- Cross-test gaps between strategy modules.

## Deliverable
- Update `docs/polymarket_multi_bot/SECURITY_REVIEW.md` with findings, severity, and required fixes.
