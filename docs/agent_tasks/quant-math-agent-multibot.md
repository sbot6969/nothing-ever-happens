# quant-math-agent task — mathematical modeling and backtest interpretation

Repo: `/Users/sbot/.openclaw/workspace/neh-bot`

## Mission
Act as quant/math/finance/big-data analyst for the multi-bot Polymarket platform.

## Inputs
- `docs/polymarket_multi_bot/VOICE_REQUEST_2026-05-04.md`
- `docs/polymarket_multi_bot/AGENT_FLOW.md`
- `docs/polymarket_multi_bot/RESEARCH.md`
- `docs/polymarket_multi_bot/STRATEGIES.md`
- Existing backtest code/results under `bot/backtest`, `tests/`, `docs/whale_copy_research/`, and `docs/polymarket_multi_bot/`.

## Deliverables
- Create `docs/polymarket_multi_bot/QUANT_REVIEW.md` assessing each strategy family:
  - statistical assumptions
  - expected edge source
  - risks/overfit risk
  - required data
  - backtest interpretation rules
  - recommended fine-tuning knobs
- Add or propose Python tests/simulations for strategy behavior and market scenarios where feasible.
- Review existing backtest results and label which are trustworthy vs overfit.
- Recommend next backtest/data expansions.

## Constraints
- No live trading/funding/wallet actions.
- Be skeptical: do not accept small-sample ROI as evidence.
- Do not expose secrets.
