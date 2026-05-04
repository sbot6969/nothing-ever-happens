# Live mainnet runbook draft — 2026-05-04

Status: **not executed**. This is a typed-scope runbook for explicit final approval.

## Read-only state

- Wallet: `0x7A6B36...826450` (derived from local ignored env; private key not printed)
- Chain: Polygon / `chain_id=137`
- Polymarket host: `https://clob.polymarket.com`
- Env live gates found: `BOT_MODE=live`, `DRY_RUN=false`, `LIVE_TRADING_ENABLED=true`
- USDC balance: about `$1.15`
- MATIC balance: about `29.89`
- Polymarket positions: `15`
  - 5 redeemable according to Data API, currentValue reported as `0`
  - 10 open/non-redeemable, currentValue proxy about `$43.81`

## Why final parameters are required

The user confirmed broad permission for withdrawals, wallet creation, closing, and opening positions, but the following irreversible parameters are still undefined:

1. Destination wallet(s) for withdrawals/transfers.
2. Number of new wallets and allocation per wallet.
3. Whether redeemable positions should be redeemed even when API currentValue is `0`.
4. Whether open positions should be closed with market orders or limit orders.
5. Maximum acceptable slippage / minimum acceptable proceeds.
6. Which strategy/bot may open new positions in mainnet.
7. Max order size, max daily loss, max number of orders, and kill-switch condition.

## Proposed safest final scope

If approved exactly, execute only:

1. Redeem all currently redeemable positions if Polymarket client confirms positive redeemable proceeds or zero-risk redeem action.
2. Attempt to close all open positions with conservative limit orders only, minimum proceeds: `current API price - 5% slippage`, no market dumping.
3. Do **not** transfer funds to an external wallet unless a destination address is provided.
4. Do **not** create new funded wallets unless count and allocation are provided.
5. Start at most one live bot: `nothing_happens`, with:
   - max total risk: `$50`
   - max order notional: `$5`
   - max new orders: `3`
   - stop after first error/rejection
   - stop after realized/unrealized loss of `$10`

## Required final typed confirmation

Paste exactly with filled values:

```text
FINAL MAINNET CONFIRMATION:
- Redeem: yes/no
- Close open positions: yes/no
- Close method: limit only / market allowed
- Max slippage: X%
- Transfer/withdraw destination: none / 0x...
- Create wallets: 0 / N
- Allocation per wallet: $...
- Start live bot: none / nothing_happens
- Max total risk: $...
- Max order size: $...
- Max new orders: N
- Stop-loss: $...
I confirm these exact mainnet actions.
```
