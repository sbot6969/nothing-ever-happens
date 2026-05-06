#!/usr/bin/env python3
"""Create local encrypted EVM wallet keystores without printing secrets.

Default is dry-run. Execution requires --execute and WALLET_CREATION_APPROVED=1.
Private keys are encrypted with a generated passphrase stored in macOS Keychain
(or an env-provided passphrase). Stdout/manifest include public addresses only.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from eth_account import Account

ROOT = Path(__file__).resolve().parents[1]
SECURE_ROOT = ROOT / ".secure" / "wallets"
PUBLIC_MANIFEST_ROOT = ROOT / "artifacts" / "wallets"
KEYCHAIN_SERVICE_PREFIX = "openclaw-neh-bot-wallet-batch"


@dataclass(frozen=True)
class WalletRecord:
    label: str
    address: str
    keystore_file: str | None


@dataclass(frozen=True)
class WalletBatchReport:
    dry_run: bool
    batch_id: str
    count: int
    keychain_service: str | None
    secure_dir: str | None
    public_manifest: str | None
    wallets: list[WalletRecord]
    warnings: list[str]


def _chmod_private(path: Path) -> None:
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _ensure_secure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def _keychain_store(service: str, account: str, password: str) -> None:
    # Delete stale same service/account item if present, then add without printing secret.
    subprocess.run(
        ["security", "delete-generic-password", "-s", service, "-a", account],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        ["security", "add-generic-password", "-U", "-s", service, "-a", account, "-w", password],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )


def create_wallet_batch(*, count: int, execute: bool, label_prefix: str, out: Path, use_keychain: bool) -> WalletBatchReport:
    if count < 1 or count > 10:
        raise SystemExit("count must be between 1 and 10")
    if execute and os.getenv("WALLET_CREATION_APPROVED") != "1":
        raise SystemExit("Refusing wallet creation: set WALLET_CREATION_APPROVED=1 with --execute")

    batch_id = time.strftime("%Y%m%d_%H%M%S")
    service = f"{KEYCHAIN_SERVICE_PREFIX}-{batch_id}" if use_keychain else None
    secure_dir = SECURE_ROOT / batch_id
    public_manifest = out
    warnings = [
        "Private keys are never printed. Only encrypted keystore files are written.",
        "These wallets are unfunded; use a separate capped funding flow after review.",
        "Back up/recovery depends on the encrypted keystore plus passphrase source.",
    ]

    if not execute:
        wallets = [WalletRecord(f"{label_prefix}-{i+1}", "DRY_RUN_ADDRESS", None) for i in range(count)]
        return WalletBatchReport(True, batch_id, count, service, None, str(public_manifest), wallets, warnings)

    passphrase = os.getenv("WALLET_KEYSTORE_PASSPHRASE")
    if not passphrase:
        passphrase = secrets.token_urlsafe(48)
        if not use_keychain:
            raise SystemExit("Set WALLET_KEYSTORE_PASSPHRASE or use --use-keychain")
        _keychain_store(service or "", "keystore-passphrase", passphrase)
        warnings.append("Generated keystore passphrase was stored in macOS Keychain; it is not in the manifest.")
    else:
        warnings.append("Keystore passphrase was read from WALLET_KEYSTORE_PASSPHRASE env and not printed.")

    _ensure_secure_dir(secure_dir)
    PUBLIC_MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)

    records: list[WalletRecord] = []
    for index in range(count):
        label = f"{label_prefix}-{index+1}"
        account = Account.create(secrets.token_hex(32))
        encrypted: dict[str, Any] = Account.encrypt(account.key, passphrase)
        keystore_path = secure_dir / f"{label}-{account.address}.json"
        keystore_path.write_text(json.dumps(encrypted, indent=2, sort_keys=True) + "\n")
        _chmod_private(keystore_path)
        records.append(WalletRecord(label, account.address, str(keystore_path.relative_to(ROOT))))

    report = WalletBatchReport(False, batch_id, count, service, str(secure_dir.relative_to(ROOT)), str(public_manifest), records, warnings)
    public_manifest.parent.mkdir(parents=True, exist_ok=True)
    public_manifest.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--label-prefix", default="neh-live")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--use-keychain", action="store_true", default=True)
    parser.add_argument("--out", type=Path, default=PUBLIC_MANIFEST_ROOT / "latest_wallet_batch.json")
    args = parser.parse_args()
    report = create_wallet_batch(
        count=args.count,
        execute=args.execute,
        label_prefix=args.label_prefix,
        out=args.out,
        use_keychain=args.use_keychain,
    )
    # Manifest/stdout contain public addresses and keystore paths only, never private keys/passphrases.
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
