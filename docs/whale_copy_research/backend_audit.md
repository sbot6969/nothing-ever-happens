# Backend audit: whale-copy tests/backtest/live gates

Scope: backend tests, offline whale scanner validation, and deterministic backtest framework for `feature/whale-copy-backtest-research`.

## Transaction/order submission paths reviewed

- `bot/main.py`
  - `_build_exchange()` returns `PaperExchangeClient` unless `exchange.live_send_enabled` is true.
  - Existing tests cover paper-vs-live construction and live runtime requirements.
- `bot/exchange/polymarket_clob.py`
  - `place_limit_order()` and `place_market_order()` both fail closed with `RuntimeError("Order transmission is disabled")` when `allow_trading` is false.
  - Client initialization requires `PRIVATE_KEY` when live order transmission is enabled.
  - `bootstrap_live_trading()` performs allowance/bootstrap work only when a private key exists and live client path is selected.
- `bot/strategy/nothing_happens.py`
  - Uses exchange abstraction; live submission depends on the exchange produced by `_build_exchange()`.
- `bot/redeemer.py` / `bot/live_recovery.py`
  - Settlement/recovery code is separate from whale-copy backtest work and must remain outside any offline backtest path.
- `bot/whale_copy.py`
  - Default mode is paper: `WHALE_COPY_LIVE_ENABLED` defaults false.
  - `_handle_signal()` records `whale_copy_paper_trade` by default.
  - With live gate true, it still records `live_not_implemented_without_wallet_confirmation`; it does not submit exchange orders or touch wallets.
- `bot/backtest/whale_copy.py`
  - Offline-only simulator. Reads cached JSON fixtures/artifacts and deterministic resolution inputs.
  - No network calls, no exchange client, no private-key usage, no wallet creation, no transfers, no live orders.

## Added validation coverage

- Whale scanner parsing/cache/safety:
  - Data API response validation rejects non-list payloads.
  - User-Agent/Accept headers are asserted for public API calls.
  - Wallet history lookup cache avoids repeated user-history calls.
  - Signal handling is verified as paper by default and non-submitting even with live gate true.
- Backtest framework:
  - Parses Polymarket Data API trade rows with strict validation for wallet, side, asset, timestamp, size, and price.
  - Dedupe key is `transactionHash + asset + timestamp`.
  - Rejects non-BUY trades, small trades, prior-history wallets, duplicate trades, startup bootstrap trades, stale signals, and missing resolutions.
  - Simulator includes spread, slippage, explicit fee bps, gas cost, and liquidity cap assumptions.
  - CLI can run fully offline against fixtures and write a JSON report.

## Cost assumptions encoded

- Polymarket explicit trading fee defaults to 0 bps but is configurable as `explicit_fee_bps`.
- Spread and slippage costs are modeled as execution-price degradation for copied BUYs.
- Liquidity caps limit copy notional to a fraction of provided cached `liquidity_usd`.
- Gas/network cost defaults to a small fixed USD amount per simulated copy.

## Remaining blockers / follow-up

- Historical downloader/cache and market-resolution acquisition are not implemented in this focused backend slice.
- Five strategy improvement iterations still need reproducible historical snapshots and reports.
- Live whale-copy execution remains intentionally not implemented until explicit user approval and a separate security review.
