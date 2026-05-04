# Multi-bot agent registry

| Agent | Session / launch target | Role | Current status | Output docs |
|---|---|---|---|---|
| backend-dev | `backend-dev` / exec `marine-bloom` | Backend, whale filter, backtests | completed initial pass: commit `e96a6b2`, full pytest `192 passed, 1 warning` | `docs/agent_tasks/backend-dev-multibot.md` |
| frontend-dev | `frontend-dev` / exec `fresh-atlas` | Unified dashboard | completed initial pass: commit `b44553a` | dashboard code/tests |
| research-agent | `backend-dev` session `research-agent-multibot` / exec `salty-nudibranch` | Deep internet/source research | running follow-up | `docs/polymarket_multi_bot/RESEARCH_APPENDIX.md`, strategy TODO updates |
| quant-math-agent | `backend-dev` session `quant-math-agent-multibot` / exec `delta-crest` | Quant/math/finance modeling and backtest interpretation | completed quant review: added `QUANT_REVIEW.md`, paper-only quant validation helpers/tests, focused pytest `15 passed` | `docs/polymarket_multi_bot/QUANT_REVIEW.md`, `bot/backtest/quant_validation.py`, `tests/test_quant_validation.py` |
| security-reviewer | `security-reviewer` | Security review after integration | pending | `docs/polymarket_multi_bot/SECURITY_REVIEW.md` |
| cross-reviewer | TBD, likely `backend-dev` or `security-reviewer` session | Adversarial/cross-tests | pending | `docs/polymarket_multi_bot/CROSS_REVIEW.md` |
