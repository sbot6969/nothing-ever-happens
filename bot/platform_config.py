"""Paper-first multi-bot platform config and capital allocation primitives.

This module defines typed interfaces for the requested four-bot platform without
adding any live order-submission path. Live mode is deliberately double-gated at
bot and platform level and should still require an external typed confirmation
process before being used by runtime code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

BOT_IDS = (
    "nothing_happens",
    "whale_copy",
    "market_making",
    "normal_distribution_amm",
)

DEFAULT_CAPITAL_WEIGHTS = {
    "nothing_happens": 0.35,
    "whale_copy": 0.25,
    "market_making": 0.20,
    "normal_distribution_amm": 0.20,
}


@dataclass(frozen=True)
class BotRuntimeGate:
    bot_id: str
    enabled: bool = True
    dry_run: bool = True
    live_trading_enabled: bool = False

    @property
    def live_send_enabled(self) -> bool:
        return self.enabled and self.live_trading_enabled and not self.dry_run

    def validate(self) -> None:
        if self.bot_id not in BOT_IDS:
            raise ValueError(f"unknown bot_id: {self.bot_id}")
        if self.live_send_enabled:
            raise ValueError(
                f"{self.bot_id} has live_send_enabled=true; live financial actions require separate typed confirmation and are not allowed by this config loader"
            )


@dataclass(frozen=True)
class BotCapitalConfig:
    bot_id: str
    weight: float
    per_market_cap_fraction: float = 0.10
    per_event_cap_fraction: float = 0.20
    max_daily_drawdown_fraction: float = 0.05
    min_order_notional_usd: float = 1.0
    max_order_notional_usd: float = 25.0

    def validate(self) -> None:
        if self.bot_id not in BOT_IDS:
            raise ValueError(f"unknown bot_id: {self.bot_id}")
        if self.weight < 0:
            raise ValueError(f"{self.bot_id}.weight must be non-negative")
        for name in ("per_market_cap_fraction", "per_event_cap_fraction", "max_daily_drawdown_fraction"):
            value = float(getattr(self, name))
            if not 0 <= value <= 1:
                raise ValueError(f"{self.bot_id}.{name} must be between 0 and 1")
        if self.min_order_notional_usd < 0 or self.max_order_notional_usd < self.min_order_notional_usd:
            raise ValueError(f"{self.bot_id} order notional bounds are invalid")


@dataclass(frozen=True)
class MultiBotPlatformConfig:
    total_paper_capital_usd: float = 50.0
    runtime_gates: dict[str, BotRuntimeGate] = field(default_factory=dict)
    capital: dict[str, BotCapitalConfig] = field(default_factory=dict)
    live_finance_locked: bool = True

    def validate(self) -> None:
        if self.total_paper_capital_usd < 0:
            raise ValueError("total_paper_capital_usd must be non-negative")
        missing_gates = set(BOT_IDS) - set(self.runtime_gates)
        missing_capital = set(BOT_IDS) - set(self.capital)
        if missing_gates:
            raise ValueError(f"missing runtime gates for: {sorted(missing_gates)}")
        if missing_capital:
            raise ValueError(f"missing capital configs for: {sorted(missing_capital)}")
        for gate in self.runtime_gates.values():
            gate.validate()
        for capital in self.capital.values():
            capital.validate()
        weight_sum = sum(item.weight for item in self.capital.values())
        if weight_sum <= 0:
            raise ValueError("capital weights must sum to a positive value")
        if not self.live_finance_locked:
            raise ValueError("live_finance_locked must remain true until explicit typed confirmation")


def default_platform_config(total_paper_capital_usd: float = 50.0) -> MultiBotPlatformConfig:
    cfg = MultiBotPlatformConfig(
        total_paper_capital_usd=total_paper_capital_usd,
        runtime_gates={bot_id: BotRuntimeGate(bot_id=bot_id) for bot_id in BOT_IDS},
        capital={bot_id: BotCapitalConfig(bot_id=bot_id, weight=DEFAULT_CAPITAL_WEIGHTS[bot_id]) for bot_id in BOT_IDS},
        live_finance_locked=True,
    )
    cfg.validate()
    return cfg


def load_platform_config(raw: dict[str, Any]) -> MultiBotPlatformConfig:
    platform = raw.get("platform", raw)
    if not isinstance(platform, dict):
        raise ValueError("platform config must be an object")
    total = float(platform.get("total_paper_capital_usd", 50.0))
    gates_raw = platform.get("runtime_gates", {})
    capital_raw = platform.get("capital", {})
    gates = {
        bot_id: BotRuntimeGate(bot_id=bot_id, **dict(gates_raw.get(bot_id, {})))
        for bot_id in BOT_IDS
    }
    capital = {
        bot_id: BotCapitalConfig(bot_id=bot_id, weight=float(dict(capital_raw.get(bot_id, {})).get("weight", DEFAULT_CAPITAL_WEIGHTS[bot_id])), **{k: v for k, v in dict(capital_raw.get(bot_id, {})).items() if k != "weight"})
        for bot_id in BOT_IDS
    }
    cfg = MultiBotPlatformConfig(
        total_paper_capital_usd=total,
        runtime_gates=gates,
        capital=capital,
        live_finance_locked=bool(platform.get("live_finance_locked", True)),
    )
    cfg.validate()
    return cfg


def allocate_paper_capital(config: MultiBotPlatformConfig) -> dict[str, float]:
    """Allocate paper bankroll by normalized weights."""
    config.validate()
    total_weight = sum(item.weight for item in config.capital.values())
    return {
        bot_id: round(config.total_paper_capital_usd * item.weight / total_weight, 6)
        for bot_id, item in config.capital.items()
    }


def max_signal_notional_usd(config: MultiBotPlatformConfig, bot_id: str, *, market_exposure_usd: float = 0.0, event_exposure_usd: float = 0.0) -> float:
    """Return remaining paper notional cap for a new signal under bot/market/event caps."""
    config.validate()
    if bot_id not in config.capital:
        raise ValueError(f"unknown bot_id: {bot_id}")
    allocation = allocate_paper_capital(config)[bot_id]
    capital = config.capital[bot_id]
    market_remaining = max(0.0, allocation * capital.per_market_cap_fraction - market_exposure_usd)
    event_remaining = max(0.0, allocation * capital.per_event_cap_fraction - event_exposure_usd)
    return round(max(0.0, min(capital.max_order_notional_usd, market_remaining, event_remaining)), 6)


def platform_config_to_dict(config: MultiBotPlatformConfig) -> dict[str, Any]:
    config.validate()
    return asdict(config)
