#!/usr/bin/env python3
"""Fund locally-created wallet manifest with hard-capped Polygon USDC/MATIC.

Default is dry-run. Execution requires --execute and WALLET_FUNDING_APPROVED=1.
The script never reads child wallet private keys and never prints sender secrets.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.config import load_nothing_happens_config

USDC_POLYGON = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
ERC20_TRANSFER_ABI = [{"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}]
ERC20_BALANCE_ABI = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]


@dataclass(frozen=True)
class FundingRow:
    label: str
    address: str
    usdc_amount: float
    matic_amount: float
    status: str
    usdc_tx: str | None = None
    matic_tx: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class FundingReport:
    dry_run: bool
    sender: str
    chain_id: int
    rows: list[FundingRow]
    warnings: list[str]


def _mask(addr: str) -> str:
    return addr[:8] + "..." + addr[-6:] if addr else ""


def _load_wallets(manifest: Path) -> list[dict[str, Any]]:
    data = json.loads(manifest.read_text())
    wallets = data.get("wallets") or []
    if not wallets:
        raise SystemExit("manifest has no wallets")
    return wallets


def _balances(w3: Web3, sender: str) -> tuple[float, float]:
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_POLYGON), abi=ERC20_BALANCE_ABI)
    usdc_balance = usdc.functions.balanceOf(sender).call() / 1_000_000
    matic_balance = w3.eth.get_balance(sender) / 10**18
    return usdc_balance, matic_balance


def fund(*, manifest: Path, usdc_each: float, matic_each: float, max_total_usdc: float, max_total_matic: float, execute: bool) -> FundingReport:
    load_dotenv(ROOT / ".env")
    if execute and os.getenv("WALLET_FUNDING_APPROVED") != "1":
        raise SystemExit("Refusing funding: set WALLET_FUNDING_APPROVED=1 with --execute")
    if not (0 <= usdc_each <= 1.0 and 0 <= matic_each <= 0.1):
        raise SystemExit("Per-wallet funding caps exceeded: usdc_each<=1.0 and matic_each<=0.1 required")

    cfg, _ = load_nothing_happens_config()
    if cfg.chain_id != 137 or cfg.host != "https://clob.polymarket.com":
        raise SystemExit(f"Unexpected live config chain/host: {cfg.chain_id} {cfg.host}")
    rpc = (os.getenv("POLYGON_RPC_URL") or "").strip()
    if not cfg.private_key or not rpc:
        raise SystemExit("PRIVATE_KEY/POLYGON_RPC_URL missing")
    acct = Account.from_key(cfg.private_key)
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
    try:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ValueError:
        pass
    if w3.eth.chain_id != 137:
        raise SystemExit(f"RPC chain mismatch: {w3.eth.chain_id}")

    wallets = _load_wallets(manifest)
    total_usdc = usdc_each * len(wallets)
    total_matic = matic_each * len(wallets)
    if total_usdc > max_total_usdc + 1e-12 or total_matic > max_total_matic + 1e-12:
        raise SystemExit("Total funding cap exceeded")

    usdc_balance, matic_balance = _balances(w3, acct.address)
    # Keep reserves so this cannot strand the main wallet.
    if usdc_balance < total_usdc + 0.25:
        raise SystemExit(f"Insufficient on-chain USDC for capped funding plus reserve: have {usdc_balance}, need {total_usdc + 0.25}")
    if matic_balance < total_matic + 1.0:
        raise SystemExit(f"Insufficient MATIC for capped funding plus reserve: have {matic_balance}, need {total_matic + 1.0}")

    warnings = [
        "Hard caps enforced: per-wallet <=1 USDC and <=0.1 MATIC; total caps from CLI.",
        "This funds public addresses only; child private keys are not read here.",
    ]
    rows: list[FundingRow] = []
    if not execute:
        for wallet in wallets:
            rows.append(FundingRow(wallet.get("label", ""), wallet["address"], usdc_each, matic_each, "dry_run_ready"))
        return FundingReport(True, _mask(acct.address), 137, rows, warnings)

    nonce = w3.eth.get_transaction_count(acct.address, "pending")
    gas_price = int(w3.eth.gas_price)
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_POLYGON), abi=ERC20_TRANSFER_ABI)
    for wallet in wallets:
        to = Web3.to_checksum_address(wallet["address"])
        usdc_tx_hash = None
        matic_tx_hash = None
        if usdc_each > 0:
            tx = usdc.functions.transfer(to, int(usdc_each * 1_000_000)).build_transaction({"from": acct.address, "nonce": nonce, "chainId": 137, "gasPrice": gas_price})
            tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
            signed = w3.eth.account.sign_transaction(tx, cfg.private_key)
            txh = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(txh, timeout=180)
            if int(receipt.status) != 1:
                raise RuntimeError(f"USDC transfer failed for {to}: {w3.to_hex(txh)}")
            usdc_tx_hash = w3.to_hex(txh)
            nonce += 1
        if matic_each > 0:
            tx = {"from": acct.address, "to": to, "value": int(matic_each * 10**18), "nonce": nonce, "chainId": 137, "gasPrice": gas_price, "gas": 21000}
            signed = w3.eth.account.sign_transaction(tx, cfg.private_key)
            txh = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(txh, timeout=180)
            if int(receipt.status) != 1:
                raise RuntimeError(f"MATIC transfer failed for {to}: {w3.to_hex(txh)}")
            matic_tx_hash = w3.to_hex(txh)
            nonce += 1
        rows.append(FundingRow(wallet.get("label", ""), wallet["address"], usdc_each, matic_each, "funded", usdc_tx_hash, matic_tx_hash))
    return FundingReport(False, _mask(acct.address), 137, rows, warnings)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--usdc-each", type=float, default=0.25)
    parser.add_argument("--matic-each", type=float, default=0.05)
    parser.add_argument("--max-total-usdc", type=float, default=0.5)
    parser.add_argument("--max-total-matic", type=float, default=0.1)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", type=Path, default=Path("artifacts/wallets/latest_funding_report.json"))
    args = parser.parse_args()
    report = fund(manifest=args.manifest, usdc_each=args.usdc_each, matic_each=args.matic_each, max_total_usdc=args.max_total_usdc, max_total_matic=args.max_total_matic, execute=args.execute)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n")
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
