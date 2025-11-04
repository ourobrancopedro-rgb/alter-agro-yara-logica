#!/usr/bin/env python3
"""Validate that the integrity seal reflects the current ledger hash."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "infra/github/hash_ledger.json"
SEAL = ROOT / "docs/badges/integrity_seal.svg"


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_timestamp(svg_text: str) -> None:
    match = re.search(r"Updated: ([0-9TZ:-]+) ·", svg_text)
    if not match:
        raise SystemExit("Could not find Updated timestamp in seal SVG.")
    timestamp = match.group(1)
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def main() -> None:
    if not LEDGER.is_file():
        raise SystemExit("hash_ledger.json not found.")
    if not SEAL.is_file():
        raise SystemExit("integrity_seal.svg not found.")

    ledger_hash = compute_sha256(LEDGER)
    expected_fragment = ledger_hash[:40] + "…"
    seal_text = SEAL.read_text(encoding="utf-8")

    if expected_fragment not in seal_text:
        raise SystemExit(
            "Integrity seal is out of date: expected fragment"
            f" {expected_fragment} but did not find it."
        )

    ensure_timestamp(seal_text)
    print("Integrity seal is up to date.")


if __name__ == "__main__":
    main()
