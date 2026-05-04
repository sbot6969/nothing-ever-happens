# frontend-dev task — unified multi-bot dashboard

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`

## Scope
Design/implement dashboard updates for one common platform dashboard with four sub-bots:
- Nothing Ever Happens.
- Whale/ALT copy.
- Market-making.
- Normal-distribution AMM allocation.

## Required work
- Add dashboard model/cards/charts for per-bot mode, health, paper/live counts, PnL/backtest metrics, error state.
- Avoid leaking secrets/wallet private data.
- Keep UI compatible with current static dashboard and whale dashboard architecture.
- Add/extend tests for dashboard HTML/data rendering.

## Verification
- Run dashboard/frontend-focused pytest.
- Run full pytest if feasible.
- Commit changes with a clear message.

## Frontend-dev completion notes
- Added a unified platform dashboard model to the main dashboard websocket payload with four paper-first bot cards: Nothing Ever Happens, Whale / ALT Copy, Market-making, and Normal-distribution AMM Allocation.
- Main dashboard HTML now renders unified platform cards plus a compact per-bot activity/PnL chart while keeping existing summary, charts, trades, positions, and finalization sections compatible.
- Per-bot status includes mode, health, paper/live counts, PnL/backtest label, and sanitized error text only. No wallet/private-key fields are included.
- Added dashboard tests for the four-bot model, sanitized errors, static HTML coverage, and existing live/paper runtime labels.
- Verification: focused `tests/test_dashboard.py tests/test_whale_copy.py` → 21 passed; full pytest → 194 passed, 1 warning.
