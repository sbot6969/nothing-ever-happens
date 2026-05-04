# Multi-bot production config schema — paper-first draft

This is the typed production-shape config for the requested four-bot platform. It is intentionally paper-first: the loader rejects live-send gates and requires `live_finance_locked=true` until a separate typed confirmation and fresh security review happen.

Implemented primitives:

- `bot/platform_config.py`
- `tests/test_platform_config.py`

## Bot ids

```text
nothing_happens
whale_copy
market_making
normal_distribution_amm
```

## Default paper allocation

For a `$50` paper bankroll:

| Bot | Weight | Paper allocation |
|---|---:|---:|
| `nothing_happens` | 35% | `$17.50` |
| `whale_copy` | 25% | `$12.50` |
| `market_making` | 20% | `$10.00` |
| `normal_distribution_amm` | 20% | `$10.00` |

## Runtime gate

Per bot:

```json
{
  "enabled": true,
  "dry_run": true,
  "live_trading_enabled": false
}
```

Derived:

```text
live_send_enabled = enabled && live_trading_enabled && !dry_run
```

Current loader behavior: if `live_send_enabled` would be true, validation fails. This prevents accidental live orders from config changes alone.

## Capital config

Per bot:

```json
{
  "weight": 0.25,
  "per_market_cap_fraction": 0.10,
  "per_event_cap_fraction": 0.20,
  "max_daily_drawdown_fraction": 0.05,
  "min_order_notional_usd": 1.0,
  "max_order_notional_usd": 25.0
}
```

Allocator behavior:

- Normalize weights across all four bots.
- Allocate from `total_paper_capital_usd`.
- Cap each proposed signal by:
  - bot `max_order_notional_usd`
  - remaining per-market cap
  - remaining per-event cap
- Keep live finance locked unless separately approved.

## Example platform block

```json
{
  "platform": {
    "total_paper_capital_usd": 50,
    "live_finance_locked": true,
    "runtime_gates": {
      "nothing_happens": { "enabled": true, "dry_run": true, "live_trading_enabled": false },
      "whale_copy": { "enabled": true, "dry_run": true, "live_trading_enabled": false },
      "market_making": { "enabled": true, "dry_run": true, "live_trading_enabled": false },
      "normal_distribution_amm": { "enabled": true, "dry_run": true, "live_trading_enabled": false }
    },
    "capital": {
      "nothing_happens": { "weight": 0.35 },
      "whale_copy": { "weight": 0.25 },
      "market_making": { "weight": 0.20 },
      "normal_distribution_amm": { "weight": 0.20 }
    }
  }
}
```

## Remaining integration work

- Wire the config into runtime startup only after strategy adapters emit common `StrategySignal` objects.
- Persist capital/exposure state by bot/market/event before using allocator decisions in live code.
- Add a typed-confirmation workflow separate from config files before live send can be enabled.
- Re-run security review before any live-financial path is connected.
