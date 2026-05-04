# Multi-bot agent flow — research, math, development, review

Captured from the 2026-05-04 follow-up voice note.

## Goal
Create a durable agent workflow for the Polymarket multi-bot platform. The workflow should not depend on the user manually deciding every subtask; the coordinator should split work, create/launch required agents, collect results, run backtests, ask math/quant review to interpret results, then run security review.

## Required specialist agents

### 1. Deep research agent
Purpose: heavy internet/source research.

Responsibilities:
- Search for hedge-fund, quant, market-making, AMM, prediction-market, and CLOB technical material.
- Prefer primary docs, PDFs, papers, university/Harvard-style research, institutional/hedge-fund notes, exchange docs, and reputable technical explainers.
- Produce source-linked Markdown reports.
- Feed useful findings into the strategy/spec TODOs.

### 2. Quant/math/finance/big-data agent
Purpose: mathematically evaluate strategies and backtest results.

Responsibilities:
- Read research outputs and historical/backtest data.
- Model market behavior and strategy behavior.
- Propose mathematically grounded strategy variants.
- Write Python tests/simulations for market behavior and strategy edge cases.
- Evaluate PnL/ROI/drawdown/hit-rate/turnover/exposure results and say whether they are trustworthy or overfit.
- Recommend fine-tuning based on backtest evidence.
- Read additional mathematical/financial documentation from the internet where useful.

### 3. Backend/dev agent
Purpose: implement strategy code, scanner logic, backtest harness, data models, and tests.

### 4. Frontend/dashboard agent
Purpose: expose platform, sub-bots, agents, tasks, and backtest/health state on dashboards.

### 5. Security-reviewer agent
Purpose: review live gates, secrets, financial safety, dashboard leaks, overfit claims, and code safety.

### 6. Cross/adversarial review agent
Purpose: try to break assumptions, tests, dashboards, and strategy claims from the other agents.

## Required workflow
1. Coordinator captures voice requirements and writes TODO/spec files.
2. Deep research agent produces source-backed research docs.
3. Quant/math agent reads research + data and produces modeling/tests/strategy recommendations.
4. Developers implement safe paper-mode strategy/backtest/dashboard code.
5. Backtests run across all strategy families.
6. Quant/math agent reviews backtest results and labels them trustworthy / overfit / needs more data.
7. Security-reviewer runs after integration.
8. Cross/adversarial reviewer tries to falsify assumptions and code paths.
9. Coordinator integrates, pushes, restarts paper-only runtimes, and reports status.

## 30-minute monitor requirement
A recurring job should:
- Re-read/revalidate voice request docs and TODOs.
- Check agent registry/status.
- Check bot/dashboard process health.
- Append status to monitor logs and daily memory.
- Nudge/launch follow-up checks only when safe and useful.

## Safety boundary
No live financial action is part of this agent flow. Position closing, wallet creation/funding, fund transfers, splitting capital, and live trading require separate explicit typed confirmation.
