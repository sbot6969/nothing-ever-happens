#!/usr/bin/env python3
"""Execute the approved conservative mainnet close plan via Polymarket CLOB V2.

Default is dry-run. Execution requires --execute and FINAL_MAINNET_APPROVED=1.
It never prints private keys. It skips zero-value redeem candidates to avoid gas
burn and submits only bounded SELL orders:
- First tries FAK at the approved min price.
- If FAK cannot match because there is no bid at/above the min price, optionally
  places a resting GTC sell at that same approved min price.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.config import load_nothing_happens_config
from scripts.live_mainnet_plan import MainnetPlan, PositionPlan, build_plan


@dataclass(frozen=True)
class ExecutionRow:
    action: str
    slug: str
    asset: str
    requested_size: float
    reference_price: float | None
    min_price: float | None
    status: str
    reason: str
    order_id: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExecutionReport:
    wallet: str
    dry_run: bool
    started_at: float
    rows: list[ExecutionRow]


def _mask_wallet(wallet: str) -> str:
    return wallet[:8] + "..." + wallet[-6:] if wallet else ""


def _sell_rows(plan: MainnetPlan) -> list[PositionPlan]:
    return [row for row in plan.positions if row.action == "close_limit_sell_candidate"]


def _round_sell_price_to_tick(price: float, tick_size: float) -> float:
    if tick_size <= 0:
        return price
    ticks = math.floor((float(price) + 1e-12) / tick_size)
    return max(tick_size, round(ticks * tick_size, 6))


def _normalize_tick_size(raw: Any) -> str:
    value = float(raw or 0.01)
    # py-clob-client-v2 typing accepts string literals like "0.01".
    return (f"{value:.6f}").rstrip("0").rstrip(".")


def _is_no_fak_match(exc: Exception) -> bool:
    text = str(exc).lower()
    return "no orders found to match with fak order" in text or "partially filled or killed" in text


def _extract_order_id_from_error(exc: Exception) -> str | None:
    err = getattr(exc, "error_msg", None) or getattr(exc, "error_message", None)
    if isinstance(err, dict):
        oid = err.get("orderID") or err.get("order_id") or err.get("id")
        return str(oid) if oid else None
    return None


def _human_balance_snapshot(client: Any, params: Any) -> dict[str, float]:
    raw = client.get_balance_allowance(params)
    if not isinstance(raw, dict):
        raise ValueError(f"Expected balance/allowance dict, got {type(raw).__name__}: {raw!r}")
    balance = float(raw.get("balance") or 0) / 1_000_000
    allowances = raw.get("allowances")
    if isinstance(allowances, dict) and allowances:
        allowance_raw = max(float(v or 0) for v in allowances.values())
    else:
        allowance_raw = float(raw.get("allowance") or 0)
    return {"balance": balance, "allowance": allowance_raw / 1_000_000}


def _make_v2_client(exchange_cfg: Any) -> tuple[Any, Any, Any, Any, Any, Any, Any]:
    try:
        from py_clob_client_v2 import (
            AssetType,
            BalanceAllowanceParams,
            ClobClient,
            MarketOrderArgs,
            OrderArgs,
            OrderType,
            PartialCreateOrderOptions,
            Side as V2Side,
        )
    except ImportError as exc:
        raise RuntimeError("Missing dependency py-clob-client-v2. Install requirements.txt") from exc

    kwargs: dict[str, Any] = {
        "chain_id": exchange_cfg.chain_id,
        "key": exchange_cfg.private_key,
        "signature_type": exchange_cfg.signature_type,
    }
    if exchange_cfg.funder_address:
        kwargs["funder"] = exchange_cfg.funder_address
    client = ClobClient(exchange_cfg.host, **kwargs)
    creds = client.derive_api_key()
    client.set_api_creds(creds)
    return client, AssetType, BalanceAllowanceParams, MarketOrderArgs, OrderArgs, OrderType, PartialCreateOrderOptions, V2Side


def _verify_execution_environment(exchange_cfg: Any, *, execute: bool) -> None:
    if exchange_cfg.host.rstrip("/") != "https://clob.polymarket.com":
        raise SystemExit(f"Refusing execution: unexpected CLOB host {exchange_cfg.host!r}")
    if int(exchange_cfg.chain_id) != 137:
        raise SystemExit(f"Refusing execution: expected Polygon chain_id=137, got {exchange_cfg.chain_id!r}")
    if execute:
        rpc = (os.getenv("POLYGON_RPC_URL") or "").strip()
        if not rpc:
            raise SystemExit("Refusing execution: POLYGON_RPC_URL is required for chain verification")
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
        rpc_chain_id = int(w3.eth.chain_id)
        if rpc_chain_id != 137:
            raise SystemExit(f"Refusing execution: POLYGON_RPC_URL chain_id={rpc_chain_id}, expected 137")


def execute_plan(
    *,
    close_slippage_pct: float,
    execute: bool,
    max_orders: int,
    out: Path,
    place_resting_if_no_match: bool,
    max_usdc_per_order: float,
    max_total_usdc: float,
    allow_assets: set[str] | None = None,
) -> ExecutionReport:
    load_dotenv(ROOT / ".env")
    if close_slippage_pct < 0 or close_slippage_pct > 25:
        raise SystemExit("Refusing: --close-slippage-pct must be between 0 and 25")
    if max_orders < 1:
        raise SystemExit("Refusing: --max-orders must be >= 1")
    if max_usdc_per_order <= 0 or max_total_usdc <= 0:
        raise SystemExit("Refusing: max USDC caps must be positive")
    if execute and os.getenv("FINAL_MAINNET_APPROVED") != "1":
        raise SystemExit("Refusing execution: set FINAL_MAINNET_APPROVED=1 with --execute")

    plan = build_plan(close_slippage_pct)
    exchange_cfg, _strategy_cfg = load_nothing_happens_config()
    _verify_execution_environment(exchange_cfg, execute=execute)
    client, AssetType, BalanceAllowanceParams, MarketOrderArgs, OrderArgs, OrderType, PartialCreateOrderOptions, V2Side = _make_v2_client(exchange_cfg)
    wallet = Account.from_key(exchange_cfg.private_key).address if exchange_cfg.private_key else ""
    rows: list[ExecutionRow] = []

    for pos in [p for p in plan.positions if p.action == "redeem_candidate"]:
        rows.append(
            ExecutionRow(
                action="redeem_skipped_zero_value",
                slug=pos.slug,
                asset=pos.asset,
                requested_size=pos.size,
                reference_price=None,
                min_price=None,
                status="skipped",
                reason="Data API currentValue=0; redeeming would likely burn gas for no proceeds.",
            )
        )

    submitted = 0
    total_usdc_cap_used = 0.0
    normalized_allow_assets = {a.strip() for a in (allow_assets or set()) if a.strip()}
    for pos in _sell_rows(plan):
        if submitted >= max_orders:
            rows.append(
                ExecutionRow(
                    "close_sell_skipped_max_orders",
                    pos.slug,
                    pos.asset,
                    pos.size,
                    pos.current_price,
                    pos.min_limit_price,
                    "skipped",
                    f"max_orders={max_orders} reached",
                )
            )
            continue
        if normalized_allow_assets and pos.asset not in normalized_allow_assets:
            rows.append(
                ExecutionRow(
                    "close_sell_skipped_asset_not_allowlisted",
                    pos.slug,
                    pos.asset,
                    pos.size,
                    pos.current_price,
                    pos.min_limit_price,
                    "skipped",
                    "Asset is not present in --allow-asset allowlist",
                )
            )
            continue
        if pos.current_price <= 0 or not pos.min_limit_price:
            rows.append(
                ExecutionRow(
                    "close_sell_skipped_no_price",
                    pos.slug,
                    pos.asset,
                    pos.size,
                    pos.current_price,
                    pos.min_limit_price,
                    "skipped",
                    "No positive current price",
                )
            )
            continue

        try:
            order_book = client.get_order_book(pos.asset)
            tick_size = float(order_book.get("tick_size") or 0.01)
            min_price = _round_sell_price_to_tick(float(pos.min_limit_price), tick_size)
            neg_risk = bool(order_book.get("neg_risk"))
            opts = PartialCreateOrderOptions(tick_size=_normalize_tick_size(tick_size), neg_risk=neg_risk)

            balance_params = BalanceAllowanceParams(
                asset_type=AssetType.CONDITIONAL,
                token_id=pos.asset,
                signature_type=exchange_cfg.signature_type,
            )
            client.update_balance_allowance(balance_params)
            time.sleep(1.0)
            snapshot = _human_balance_snapshot(client, balance_params)
            required_size = min(float(pos.size), snapshot["balance"])
            estimated_usdc = required_size * min_price
            if estimated_usdc > max_usdc_per_order + 1e-9:
                rows.append(
                    ExecutionRow(
                        "close_sell_skipped_order_cap",
                        pos.slug,
                        pos.asset,
                        required_size,
                        pos.current_price,
                        min_price,
                        "skipped",
                        f"estimated_usdc={estimated_usdc:.6f} exceeds max_usdc_per_order={max_usdc_per_order:.6f}",
                        raw=snapshot,
                    )
                )
                continue
            if total_usdc_cap_used + estimated_usdc > max_total_usdc + 1e-9:
                rows.append(
                    ExecutionRow(
                        "close_sell_skipped_total_cap",
                        pos.slug,
                        pos.asset,
                        required_size,
                        pos.current_price,
                        min_price,
                        "skipped",
                        f"total estimated_usdc would exceed max_total_usdc={max_total_usdc:.6f}",
                        raw={**snapshot, "estimated_usdc": estimated_usdc, "total_usdc_cap_used": total_usdc_cap_used},
                    )
                )
                continue
            if required_size + 1e-9 < 5.0:
                rows.append(
                    ExecutionRow(
                        "close_sell_not_ready",
                        pos.slug,
                        pos.asset,
                        pos.size,
                        pos.current_price,
                        min_price,
                        "not_ready",
                        f"Conditional balance below min usable order size: {snapshot['balance']}",
                        raw=snapshot,
                    )
                )
                continue
            if snapshot["allowance"] + 1e-9 < required_size:
                rows.append(
                    ExecutionRow(
                        "close_sell_not_ready",
                        pos.slug,
                        pos.asset,
                        pos.size,
                        pos.current_price,
                        min_price,
                        "not_ready",
                        "Insufficient conditional allowance for CLOB V2 order",
                        raw=snapshot,
                    )
                )
                continue

            if not execute:
                rows.append(
                    ExecutionRow(
                        "close_sell_dry_run_ready_v2",
                        pos.slug,
                        pos.asset,
                        required_size,
                        pos.current_price,
                        min_price,
                        "ready",
                        "Dry-run: CLOB V2 readiness passed; no order submitted.",
                        raw=snapshot,
                    )
                )
                continue

            fak_args = MarketOrderArgs(
                token_id=pos.asset,
                amount=required_size,
                side=V2Side.SELL,
                price=min_price,
                order_type=OrderType.FAK,
            )
            try:
                signed = client.create_market_order(fak_args, opts)
                response = client.post_order(signed, OrderType.FAK)
                submitted += 1
                total_usdc_cap_used += estimated_usdc
                rows.append(
                    ExecutionRow(
                        "close_sell_submitted_v2_fak",
                        pos.slug,
                        pos.asset,
                        required_size,
                        pos.current_price,
                        min_price,
                        str(response.get("status") or "submitted"),
                        "Submitted bounded CLOB V2 FAK sell order.",
                        response.get("orderID") or response.get("order_id") or response.get("id"),
                        response,
                    )
                )
                continue
            except Exception as exc:
                if not (place_resting_if_no_match and _is_no_fak_match(exc)):
                    raise
                raw_error = {"error": str(exc)[:500]}
                oid = _extract_order_id_from_error(exc)
                if oid:
                    raw_error["fak_order_id"] = oid

            gtc_args = OrderArgs(
                token_id=pos.asset,
                price=min_price,
                size=required_size,
                side=V2Side.SELL,
            )
            signed = client.create_order(gtc_args, opts)
            response = client.post_order(signed, OrderType.GTC)
            submitted += 1
            total_usdc_cap_used += estimated_usdc
            rows.append(
                ExecutionRow(
                    "close_sell_submitted_v2_gtc_resting",
                    pos.slug,
                    pos.asset,
                    required_size,
                    pos.current_price,
                    min_price,
                    str(response.get("status") or "submitted"),
                    "FAK had no executable bid; submitted bounded resting CLOB V2 GTC sell at the same approved min price.",
                    response.get("orderID") or response.get("order_id") or response.get("id"),
                    {**raw_error, "resting_response": response},
                )
            )
        except Exception as exc:
            rows.append(
                ExecutionRow(
                    "close_sell_error_v2",
                    pos.slug,
                    pos.asset,
                    pos.size,
                    pos.current_price,
                    pos.min_limit_price,
                    "error",
                    str(exc)[:500],
                )
            )

    report = ExecutionReport(wallet=_mask_wallet(wallet), dry_run=not execute, started_at=time.time(), rows=rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--close-slippage-pct", type=float, default=5.0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-orders", type=int, default=1)
    parser.add_argument("--max-usdc-per-order", type=float, default=10.0)
    parser.add_argument("--max-total-usdc", type=float, default=10.0)
    parser.add_argument("--allow-asset", action="append", default=[], help="Optional conditional token id allowlist; repeatable.")
    parser.add_argument("--out", type=Path, default=Path("artifacts/live_mainnet_execution_report.json"))
    parser.add_argument(
        "--allow-resting-gtc",
        action="store_true",
        help="Opt in to bounded resting GTC fallback when FAK has no executable bid.",
    )
    args = parser.parse_args()
    report = execute_plan(
        close_slippage_pct=args.close_slippage_pct,
        execute=args.execute,
        max_orders=args.max_orders,
        out=args.out,
        place_resting_if_no_match=args.allow_resting_gtc,
        max_usdc_per_order=args.max_usdc_per_order,
        max_total_usdc=args.max_total_usdc,
        allow_assets=set(args.allow_asset or []),
    )
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
