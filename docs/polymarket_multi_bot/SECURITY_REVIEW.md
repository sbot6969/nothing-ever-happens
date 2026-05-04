# Security review — Polymarket multi-bot platform

Date: 2026-05-04  
Reviewer: security-reviewer  
Scope: current `feature/whale-copy-backtest-research` work after backend/frontend/research/quant/monitor changes.

## Verdict

**Approved for paper-only continuation.**

No critical/high blockers were found for continuing research, paper trading, backtests, dashboard work, and the 30-minute monitor. Live trading/funding/position-closing/wallet actions remain **blocked** until separate explicit typed confirmation and a fresh security review.

## Findings

| Severity | Finding | Evidence / impact | Required action |
|---|---|---|---|
| Critical | None | No accidental live-trading path or new irreversible financial action found in the multi-bot changes. | None for paper-only continuation. |
| High | None | Focused secret scan did not find real tokens/private keys in tracked files; only placeholder documentation references such as `PRIVATE_KEY=<key>`. | None for paper-only continuation. |
| Medium | Pre-existing live/redeemer/proxy approval code remains powerful if the original three-part live gate is deliberately enabled. | `bot/config.py` defaults to `BOT_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `DRY_RUN=true`; live order client/redeemer/proxy approval paths require `live_send_enabled` plus key/RPC/funder prerequisites. This is pre-existing functionality, not newly added multi-bot live execution. | Before any live launch: repeat review with actual intended env/config, verify typed approval scope, and confirm redeemer/approval behavior is desired. |
| Low | Monitor detailed log records process command lines and git status locally. | `scripts/multibot_monitor.sh` writes `pgrep -af 'bot\.main|bot\.whale_copy|openclaw agent'` and `git status` into ignored `tasks/multibot_monitor.log`. Focused grep found no secret patterns in current logs. Telegram summary sends only commits, agent status rows, dashboard codes, process count, TODO count, and live-finance blocked state. | Keep monitor logs ignored, avoid launching agents with secrets in CLI arguments, and periodically grep logs before sharing. |
| Low | Dashboard agent status is environment-sourced text, truncated but not semantically classified. | `_platform_agent_card()` exposes status env values truncated to 80 chars. This should not contain secrets under normal use, and tests assert no key/wallet fields in platform cards. | Do not put secrets in `*_AGENT_STATUS` env vars; consider allow-listed statuses before public exposure. |
| Low | Backtest results still include in-sample/underpowered research outputs. | `QUANT_REVIEW.md` correctly labels the 5-trade 235.91% whale-copy ROI as overfit/underpowered and says all strategies need larger walk-forward/order-book validation. | Keep dashboard/docs showing trust labels, sample sizes, and paper-only language before increasing capital or public claims. |

## Review checks performed

- Read required specs:
  - `docs/polymarket_multi_bot/VOICE_REQUEST_2026-05-04.md`
  - `docs/polymarket_multi_bot/AGENT_FLOW.md`
  - `docs/polymarket_multi_bot/AGENT_REGISTRY.md`
  - `docs/polymarket_multi_bot/MASTER_TODO.md`
  - `docs/agent_tasks/security-reviewer-multibot.md`
- Inspected branch/status/recent commits and current diffs.
- Grepped tracked files for live gates, wallet/private-key/token strings, transfer/close/funding/wallet creation language, and Telegram monitor contents.
- Checked ignored monitor log/summary with focused secret patterns: current matches = 0.
- Reviewed dashboard platform model and HTML rendering for wallet/private-key leakage.
- Reviewed whale-copy live flag behavior: default false; if true, current standalone whale-copy path records ledger status `live_not_implemented_without_wallet_confirmation` and does not submit orders.
- Reviewed downloader bounds/failure handling: fixed public HTTPS endpoints, bounded `market_limit` 1–500, bounded `trades_per_market` 1–1000, bounded `sleep_sec` 0–10, retry/backoff for 429/5xx/timeouts, ignored artifact output.
- Reviewed quant evidence labeling and overfit warnings.

## Test / command evidence

Focused tests with live/secrets env unset:

```bash
env -u PRIVATE_KEY -u FUNDER_ADDRESS -u BOT_MODE -u LIVE_TRADING_ENABLED -u DRY_RUN -u WHALE_COPY_LIVE_ENABLED \
  PYTHONPATH=. ./venv/bin/python -m pytest -q \
  tests/test_config.py tests/test_dashboard.py tests/test_whale_copy.py \
  tests/test_whale_copy_backtest.py tests/test_backtest_whale_copy.py \
  tests/test_whale_copy_scanner_validation.py tests/test_whale_copy_data_downloader.py \
  tests/test_multistrategy_backtest.py tests/test_quant_validation.py tests/test_whale_thresholds.py
```

Result: `67 passed in 0.12s`.

Focused tracked-file secret grep found only placeholder documentation text:

- `README.md:82` contains `PRIVATE_KEY=<key>` placeholder.

Current local monitor files checked:

- `tasks/multibot_monitor_summary.txt`: 0 focused secret-pattern hits.
- `tasks/multibot_monitor.log`: 0 focused secret-pattern hits.

## Approval boundary

Approved actions:

- Continue paper/dry-run strategy development.
- Continue research docs and quant validation.
- Continue downloader/backtest work using bounded public APIs and ignored artifacts.
- Continue dashboard/monitor work that does not expose secrets or private wallet/key material.

Not approved / still blocked:

- Live trading or live market making.
- Closing positions or redeeming/settling positions as part of this multi-bot rollout.
- Creating, importing, funding, or distributing funds across wallets.
- Transfers, approvals, or signing transactions for the new multi-bot system.
- Public profitability claims based on current backtests.

Before any live work, require: explicit typed confirmation with exact scope/amounts, actual env/config review, key-handling review, secret scan, dry-run-to-live diff review, and final focused tests.
