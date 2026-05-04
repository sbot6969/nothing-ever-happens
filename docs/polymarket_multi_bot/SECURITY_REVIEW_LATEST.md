# Latest security review — paper multi-bot changes

Date: 2026-05-04 18:55 Europe/Paris
Branch: `feature/whale-copy-backtest-research`
Scope: commits after the earlier security review, including walk-forward validation, paper market-making lifecycle simulation, probability/calibration helpers, large public snapshot reports, source audit/config docs, and monitor/TODO updates.

## Verdict

Approved for **paper/offline research and dashboard monitoring only**.

Not approved for live trading, wallet creation, position closing, funding, withdrawals, transfers, or maker/liquidity deployment. Those remain blocked until a separate typed confirmation with exact scope/amounts plus a fresh live-mode security review.

## Findings

| Severity | Finding | Evidence | Action |
|---|---|---|---|
| Critical | None in tracked latest changes. | No new wallet/funding/order-send paths were added by latest paper modules. | Continue paper-only work. |
| High | None in tracked latest changes. | Focused tracked secret scan found only placeholders: `.env.example:PRIVATE_KEY=`, `README.md:PRIVATE_KEY=<key>`, and existing review text. | No secret exposure in tracked latest changes. |
| Medium | Market-making and AMM/probability results still use proxies and not historical L2/queue replay. | Reports and code label this explicitly; `market_making_lifecycle.py` is deterministic simulation only and has no network/client usage. | Do not claim production edge; require L2/order lifecycle data before live consideration. |
| Low | Attempted delegated security-reviewer command timed out/killed before producing final report. | Local untracked `tasks/security_review_latest_todo.md` was created but no committed reviewer output. | Main completed this review directly and committed it; future long reviewer agents should run detached with sufficient timeout. |

## Checks run

- Repo state / recent commits inspected on `feature/whale-copy-backtest-research`.
- Live-finance grep reviewed for `live_send_enabled`, `BOT_MODE`, `LIVE_TRADING_ENABLED`, `DRY_RUN`, `PRIVATE_KEY`, `FUNDER_ADDRESS`, transfer/funding/close-position language.
- Focused tracked secret scan:
  - pattern: private keys, Telegram bot tokens, long hex private-key-like strings, PEM blocks
  - result: placeholders only; no real tracked token/key found.
- Paper/live labeling reviewed in generated reports and docs.
- Monitor launchd status checked: `com.sbot.neh-multibot-monitor` has `run interval = 1800 seconds`, last exit code `0`, and sends via OpenClaw message path with fallback.
- Tests after latest code changes: `217 passed, 1 warning`.

## Live-launch blockers that remain

- No typed confirmation exists for exact live action scope/amounts.
- No fresh live-mode env review with intended wallet/RPC/funder settings has been performed.
- Wallet creation/funding/closing positions/transfers/liquidity collection are intentionally blocked in the voice TODO list.
- Historical L2/order-book replay is still missing; current maker/AMM PnL remains proxy evidence only.
