#!/usr/bin/env python3
"""Build a read-only mainnet execution plan from current Polymarket positions.

This script never signs, submits, redeems, transfers, creates wallets, or posts
orders. It derives the local wallet address, fetches public positions, and
computes conservative close-order candidates for operator review.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from eth_account import Account

DATA_API_BASE = "https://data-api.polymarket.com"


@dataclass(frozen=True)
class PositionPlan:
    action: str
    title: str
    slug: str
    asset: str
    outcome: str
    size: float
    current_price: float
    current_value: float
    min_limit_price: float | None
    estimated_min_proceeds: float | None
    reason: str


@dataclass(frozen=True)
class MainnetPlan:
    wallet: str
    usdc_balance: float | None
    matic_balance: float | None
    redeemable_count: int
    open_count: int
    close_slippage_pct: float
    positions: list[PositionPlan]
    warnings: list[str]


def _rpc_call(rpc_url: str, method: str, params: list[Any], request_id: int) -> Any:
    resp = requests.post(rpc_url, json={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    if "error" in payload:
        raise RuntimeError(payload["error"])
    return payload.get("result")


def _erc20_balance(rpc_url: str, token: str, wallet: str, decimals: int) -> float:
    data = "0x70a08231" + wallet.lower().replace("0x", "").rjust(64, "0")
    result = _rpc_call(rpc_url, "eth_call", [{"to": token, "data": data}, "latest"], 1)
    return int(result or "0x0", 16) / (10**decimals)


def _native_balance(rpc_url: str, wallet: str) -> float:
    result = _rpc_call(rpc_url, "eth_getBalance", [wallet, "latest"], 2)
    return int(result or "0x0", 16) / 1e18


def _fetch_positions(wallet: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for redeemable in ("true", "false"):
        resp = requests.get(
            f"{DATA_API_BASE}/positions",
            params={"user": wallet, "redeemable": redeemable, "sizeThreshold": "0"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            for row in data:
                row["_redeemable_query"] = redeemable == "true"
                out.append(row)
    return out


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_plan(close_slippage_pct: float = 5.0) -> MainnetPlan:
    load_dotenv(Path.cwd() / ".env")
    private_key = (os.getenv("PRIVATE_KEY") or "").strip()
    if not private_key:
        raise SystemExit("PRIVATE_KEY missing; cannot derive wallet for read-only plan")
    wallet = Account.from_key(private_key).address
    rpc_url = (os.getenv("POLYGON_RPC_URL") or "").strip()

    usdc_balance = None
    matic_balance = None
    if rpc_url:
        usdc_balance = _erc20_balance(rpc_url, "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", wallet, 6)
        matic_balance = _native_balance(rpc_url, wallet)

    raw_positions = _fetch_positions(wallet)
    plans: list[PositionPlan] = []
    for p in raw_positions:
        redeemable = bool(p.get("redeemable") or p.get("_redeemable_query"))
        size = _safe_float(p.get("size"))
        cur_price = _safe_float(p.get("curPrice"))
        current_value = _safe_float(p.get("currentValue"))
        if redeemable:
            plans.append(
                PositionPlan(
                    action="redeem_candidate",
                    title=str(p.get("title") or ""),
                    slug=str(p.get("slug") or ""),
                    asset=str(p.get("asset") or ""),
                    outcome=str(p.get("outcome") or ""),
                    size=size,
                    current_price=cur_price,
                    current_value=current_value,
                    min_limit_price=None,
                    estimated_min_proceeds=None,
                    reason="Data API marks position redeemable; execution still requires live redeem path compatibility check.",
                )
            )
        else:
            min_price = max(0.001, cur_price * (1 - close_slippage_pct / 100.0)) if cur_price > 0 else None
            proceeds = round(size * min_price, 6) if min_price is not None else None
            plans.append(
                PositionPlan(
                    action="close_limit_sell_candidate",
                    title=str(p.get("title") or ""),
                    slug=str(p.get("slug") or ""),
                    asset=str(p.get("asset") or ""),
                    outcome=str(p.get("outcome") or ""),
                    size=size,
                    current_price=cur_price,
                    current_value=current_value,
                    min_limit_price=round(min_price, 6) if min_price is not None else None,
                    estimated_min_proceeds=proceeds,
                    reason=f"Candidate conservative limit sell at current price less {close_slippage_pct:.2f}% slippage; no order submitted.",
                )
            )

    warnings = [
        "READ_ONLY_PLAN_ONLY: no transactions/orders/wallet creation/transfers were executed.",
        "Wallet creation/funding requires destination/count/allocation handling and secure secret storage before implementation.",
        "Opening new live positions should remain capped by explicit max order/risk/stop-loss parameters.",
    ]
    return MainnetPlan(
        wallet=wallet,
        usdc_balance=usdc_balance,
        matic_balance=matic_balance,
        redeemable_count=sum(1 for p in raw_positions if bool(p.get("redeemable") or p.get("_redeemable_query"))),
        open_count=sum(1 for p in raw_positions if not bool(p.get("redeemable") or p.get("_redeemable_query"))),
        close_slippage_pct=close_slippage_pct,
        positions=plans,
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--close-slippage-pct", type=float, default=5.0)
    parser.add_argument("--out", type=Path, default=Path("artifacts/live_mainnet_plan.json"))
    args = parser.parse_args()
    plan = build_plan(args.close_slippage_pct)
    payload = asdict(plan)
    # Mask public wallet in stdout only; artifact keeps public address (not secret).
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stdout_payload = dict(payload)
    wallet = stdout_payload.get("wallet", "")
    if wallet:
        stdout_payload["wallet"] = wallet[:8] + "..." + wallet[-6:]
    print(json.dumps(stdout_payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
