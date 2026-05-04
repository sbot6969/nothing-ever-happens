from __future__ import annotations

import pytest

from bot.platform_config import BOT_IDS, allocate_paper_capital, default_platform_config, load_platform_config, max_signal_notional_usd


def test_default_platform_config_allocates_requested_four_bots() -> None:
    cfg = default_platform_config(total_paper_capital_usd=50)
    allocation = allocate_paper_capital(cfg)

    assert tuple(allocation) == BOT_IDS
    assert allocation["nothing_happens"] == 17.5
    assert allocation["whale_copy"] == 12.5
    assert allocation["market_making"] == 10.0
    assert allocation["normal_distribution_amm"] == 10.0
    assert all(gate.dry_run and not gate.live_send_enabled for gate in cfg.runtime_gates.values())


def test_load_platform_config_normalizes_custom_weights() -> None:
    cfg = load_platform_config(
        {
            "platform": {
                "total_paper_capital_usd": 100,
                "capital": {
                    "nothing_happens": {"weight": 1},
                    "whale_copy": {"weight": 1},
                    "market_making": {"weight": 1},
                    "normal_distribution_amm": {"weight": 1},
                },
            }
        }
    )

    assert allocate_paper_capital(cfg) == {
        "nothing_happens": 25.0,
        "whale_copy": 25.0,
        "market_making": 25.0,
        "normal_distribution_amm": 25.0,
    }


def test_live_gate_is_rejected_even_if_raw_config_sets_it() -> None:
    with pytest.raises(ValueError, match="live financial actions require separate typed confirmation"):
        load_platform_config({"runtime_gates": {"whale_copy": {"dry_run": False, "live_trading_enabled": True}}})


def test_live_finance_lock_must_stay_enabled() -> None:
    with pytest.raises(ValueError, match="live_finance_locked"):
        load_platform_config({"live_finance_locked": False})


def test_max_signal_notional_respects_market_and_event_caps() -> None:
    cfg = default_platform_config(total_paper_capital_usd=100)

    assert max_signal_notional_usd(cfg, "whale_copy") == 2.5
    assert max_signal_notional_usd(cfg, "whale_copy", market_exposure_usd=2.0) == 0.5
    assert max_signal_notional_usd(cfg, "whale_copy", event_exposure_usd=5.0) == 0.0
