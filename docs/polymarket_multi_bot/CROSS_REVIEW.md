# Cross / adversarial review — Polymarket multi-bot platform

Date: 2026-05-04  
Scope: adversarial review of research/quant docs, whale thresholds/backtests, dashboard paper/live indicators, and TODO accuracy. This review did not perform live trading, wallet actions, transfers, or position changes.

## Verdict

The platform is moving in the right paper-first direction, but it is **not live-ready**. The strongest contradiction is between prototype/completion language in TODOs/dashboard and the quant/research evidence that market-making, AMM allocation, and high-ROI whale-copy results are still exploratory.

## Findings and suggested fixes

### 1. Whale threshold rule is implemented, but backtest coverage needed an explicit relative-rule regression

**Status:** partially fixed in this review.

- `bot/whale_thresholds.py` implements the requested rule: whale if `notional >= $10,000` OR `market_size >= $10,000 AND notional / market_size >= 0.30`.
- `tests/test_whale_thresholds.py` covers the exact `$10,000` absolute boundary, the exact 30% relative boundary on a `$10,000` market, and the `$9,000` market-size guard.
- Gap found: the main backtest test did not explicitly prove that a sub-`$10k` trade is copied solely because it is 30% of a guarded market. `tests/test_multistrategy_backtest.py` incidentally covered this, but the whale-copy backtest suite should own it.

**Fix added:** `tests/test_whale_copy_backtest.py::test_backtest_copies_relative_market_size_whale_below_absolute_default` verifies a `$3,000` trade on a `$10,000` market is copied under the default `$10k` absolute threshold.

**Remaining concern:** rejection reason `below_min_notional` is now semantically too narrow because a trade can fail either absolute or relative whale rules. Rename to `below_whale_threshold` in a follow-up to avoid confusing logs/dashboard summaries.

### 2. Research/quant docs correctly reject live-readiness, but implementation/TODO language overstates completion

**Severity:** medium.

Research and quant review repeatedly say market-making and AMM allocation need order-book replay, inventory accounting, latency, queue assumptions, calibration, and out-of-sample validation. However `MASTER_TODO.md` marks these as done:

- `Market-making bot: design paper quote generator with inventory/spread/risk controls`
- `Normal-distribution AMM allocation bot: design capital allocation/sizing model and paper simulator`
- `Build common backtest harness for all strategy families`

The actual `bot/backtest/multistrategy.py` market-making and AMM runners are explicitly skeleton/proxy implementations using trade rows and resolved edge, not quote-plan/order-book/allocator implementations.

**Suggested fix:** split TODOs into:

- design/spec completed;
- paper proxy harness completed;
- real quote planner / allocator / order-book replay pending.

Until then, a reader may incorrectly infer that the research-derived models are implemented rather than stubbed.

### 3. Small-sample ROI is documented as overfit in quant review, but dashboard can still make ROI look like a headline metric

**Severity:** medium.

`QUANT_REVIEW.md` correctly labels the 235.91% ROI on 5 copied trades as overfit/underpowered. But dashboard bot cards accept `WHALE_BACKTEST_BEST_ROI_PCT` and render ROI/backtest label without mandatory sample size, quant label, in-sample/OOS flag, or cost assumptions.

**Suggested fix:** add dashboard fields and tests for:

- `sample_size` / copied actions;
- `quant_label` (`overfit_or_underpowered`, `candidate_edge_needs_oos`, etc.);
- `in_sample` vs `out_of_sample`;
- latency/cost stress note;
- warning badge when copied actions `< 100` or label is not `candidate_edge_needs_oos`.

### 4. Dashboard could display stale live counts while mode says paper

**Severity:** medium; fixed in this review.

`_platform_bot_card` previously rendered `live_signal_count` directly from env even when `live_send_enabled` was false. A stale or accidental `*_LIVE_SIGNALS` env value could produce a card showing `PAPER / DRY-RUN` but `Paper / Live: 0 / 4`, which is misleading.

**Fix added:** dashboard now reports `live_signal_count = 0` unless the bot's live gate is actually enabled. If a configured/stale count exists while live is disabled, it is preserved in `metrics.configured_live_signal_count` for debugging without presenting it as active live activity.

**Test added:** `tests/test_dashboard.py::test_dashboard_does_not_report_live_counts_when_live_gate_is_off`.

### 5. Agent registry and TODO ordering contradict each other

**Severity:** low/medium.

`AGENT_REGISTRY.md` says `security-reviewer` and `cross-reviewer` are both running. `MASTER_TODO.md` says run security review first, then cross/adversarial review after security review. The current cross review happened while security review was still marked running.

This is not unsafe by itself, but it weakens the workflow audit trail.

**Suggested fix:** update the workflow to allow parallel security/cross review after integration, or update registry/TODO timestamps to show the intentional ordering exception.

### 6. Backtest/proxy harness can be mistaken for strategy validation

**Severity:** medium.

`compare_strategies()` returns comparable ROI/PnL for all four strategies, but two families are proxy/skeletons that use resolved outcome edge rather than executable strategy behavior. That is fine for scaffolding, but dangerous if results feed dashboard cards or summaries without a `proxy_only` flag.

**Suggested fix:** add a result field such as `evidence_level` or `validation_level` with values like `baseline_runtime`, `paper_backtest`, `proxy_skeleton`, `order_book_replay_required`. Tests should require market-making and AMM skeletons to emit `proxy_skeleton`.

### 7. Market-size source is ambiguous

**Severity:** low/medium.

`market_size_usd()` accepts aliases including `market_volume_usd` and `liquidity_usd`. The voice requirement says “market size”; research/quant docs mention market size/open interest/liquidity separately. Treating liquidity or volume as market size may be acceptable as a fallback, but it changes the 30% whale classification semantics.

**Suggested fix:** document alias priority and prefer explicit `market_size_usd` / open-interest-style fields over volume/liquidity. Add a test that explicit `market_size_usd` wins over larger `marketVolumeUsd` if both are present.

## Tests run

```text
./venv/bin/python -m pytest -q tests/test_whale_thresholds.py tests/test_whale_copy_backtest.py tests/test_multistrategy_backtest.py tests/test_quant_validation.py tests/test_dashboard.py
33 passed in 0.15s
```

## Bottom line

Keep this platform paper-only. The absolute/relative whale rule is covered now, and one dashboard paper/live ambiguity was fixed. The next highest-value hardening is to add evidence/trust labels to every dashboard/backtest result and make TODOs distinguish real implemented strategy logic from research specs and proxy skeletons.
