#!/usr/bin/env python3
"""Set Conditional Tokens setApprovalForAll for Polymarket operators.

Requires --execute and FINAL_MAINNET_APPROVED=1. Does not print private keys.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from bot.proxy_wallet import CT_ADDRESS, CT_ABI, CT_APPROVAL_OPERATORS
from bot.config import load_nothing_happens_config


def mask(a): return a[:8]+'...'+a[-6:] if a else ''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--revoke', action='store_true', help='Set approvals to false instead of true.')
    ap.add_argument('--holder', choices=['signer'], default='signer', help='Token holder to check/approve. Proxy/Safe approvals are handled by bot.proxy_wallet bootstrap, not this EOA script.')
    ap.add_argument('--confirm-operators', action='store_true', help='Required with --execute; confirms the audited CT operator allowlist printed in dry-run output.')
    ap.add_argument('--out', type=Path, default=Path('artifacts/live_ct_approvals.json'))
    args=ap.parse_args()
    load_dotenv(ROOT/'.env')
    if args.execute and os.getenv('FINAL_MAINNET_APPROVED')!='1':
        raise SystemExit('Refusing execution: set FINAL_MAINNET_APPROVED=1 with --execute')
    if args.execute and not args.confirm_operators:
        raise SystemExit('Refusing execution: pass --confirm-operators after reviewing the operator allowlist')
    cfg,_=load_nothing_happens_config()
    pk=cfg.private_key
    rpc=(os.getenv('POLYGON_RPC_URL') or '').strip()
    if not pk or not rpc: raise SystemExit('PRIVATE_KEY/POLYGON_RPC_URL missing')
    acct=Account.from_key(pk)
    w3=Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout':30}))
    try: w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ValueError: pass
    if cfg.host.rstrip('/') != 'https://clob.polymarket.com':
        raise SystemExit(f'Refusing execution: unexpected CLOB host {cfg.host!r}')
    if int(cfg.chain_id) != 137:
        raise SystemExit(f'Refusing execution: expected Polygon chain_id=137, got {cfg.chain_id!r}')
    rpc_chain_id=int(w3.eth.chain_id)
    if rpc_chain_id != 137:
        raise SystemExit(f'Refusing execution: POLYGON_RPC_URL chain_id={rpc_chain_id}, expected 137')
    ct=w3.eth.contract(address=Web3.to_checksum_address(CT_ADDRESS), abi=CT_ABI)
    rows=[]
    nonce=w3.eth.get_transaction_count(acct.address, 'pending')
    gas_price=int(w3.eth.gas_price)
    for op in CT_APPROVAL_OPERATORS:
        operator=Web3.to_checksum_address(op)
        approved=bool(ct.functions.isApprovedForAll(acct.address, operator).call())
        desired=not args.revoke
        needs_tx = approved != desired
        row={'operator':operator, 'holder':acct.address, 'already_approved':approved, 'desired_approved':desired, 'submitted':False, 'tx_hash':None, 'status':None}
        if needs_tx and args.execute:
            tx=ct.functions.setApprovalForAll(operator, desired).build_transaction({
                'from': acct.address,
                'nonce': nonce,
                'chainId': cfg.chain_id,
                'gasPrice': gas_price,
            })
            try:
                tx['gas']=int(w3.eth.estimate_gas(tx)*1.2)
            except Exception:
                tx['gas']=120000
            signed=w3.eth.account.sign_transaction(tx, pk)
            txh=w3.eth.send_raw_transaction(signed.raw_transaction)
            row['submitted']=True; row['tx_hash']=w3.to_hex(txh)
            receipt=w3.eth.wait_for_transaction_receipt(txh, timeout=180)
            row['status']=int(receipt.status); row['gas_used']=int(receipt.gasUsed)
            nonce+=1
            time.sleep(2)
        rows.append(row)
    out={'wallet': acct.address, 'dry_run': not args.execute, 'action': 'revoke' if args.revoke else 'approve', 'ct_address': CT_ADDRESS, 'operator_source': 'bot.proxy_wallet.CT_APPROVAL_OPERATORS', 'rows': rows}
    args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
    out2=dict(out); out2['wallet']=mask(out2['wallet'])
    print(json.dumps(out2, indent=2, sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
