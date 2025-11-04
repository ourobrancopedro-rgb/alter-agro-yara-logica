#!/usr/bin/env python3
"""Hash ledger verifier for YARA Lógica specification repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict

LEDGER_PATH = Path(__file__).resolve().parent / "hash_ledger.json"
ALLOWED_PREFIXES = (
    ".gitignore",
    "README.md",
    "lsa/spec/",
    "rag/spec/",
    "docs/",
    "infra/github/",
    "legal/",
    ".github/",
)

EXCLUDED_FILES = {
    "docs/badges/integrity_seal.svg",
}


def _strip_comments(text: str) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        line_stripped = line.lstrip()
        if line_stripped.startswith("//"):
            continue
        if "//" in line:
            prefix, _comment = line.split("//", 1)
            cleaned_lines.append(prefix.rstrip())
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def load_ledger() -> Dict[str, str]:
    if not LEDGER_PATH.is_file():
        raise SystemExit("hash_ledger.json not found; run with --update to create it.")
    text = LEDGER_PATH.read_text(encoding="utf-8")
    data = json.loads(_strip_comments(text) or "{}")
    if not isinstance(data, dict):
        raise SystemExit("hash_ledger.json must contain a JSON object.")
    return {str(key): str(value) for key, value in data.items()}


def discover_tracked_files() -> Dict[str, str]:
    files: Dict[str, str] = {}
    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        rel = path.as_posix()
        if rel == "infra/github/hash_ledger.json":
            files[rel] = ""
            continue
        if rel in EXCLUDED_FILES:
            continue
        if any(rel == prefix or rel.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            files[rel] = ""
    return files


def compute_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(ledger: Dict[str, str]) -> None:
    missing = []
    mismatched = []
    for rel_path, expected_hash in ledger.items():
        if rel_path in EXCLUDED_FILES:
            continue
        file_path = Path(rel_path)
        if not file_path.is_file():
            missing.append(rel_path)
            continue
        actual = compute_hash(file_path)
        if expected_hash and actual != expected_hash:
            mismatched.append((rel_path, expected_hash, actual))
    errors = False
    if missing:
        errors = True
        print("Missing files:")
        for rel in missing:
            print(f"  - {rel}")
    if mismatched:
        errors = True
        print("Hash mismatches:")
        for rel, expected, actual in mismatched:
            print(f"  - {rel}\n      expected: {expected}\n      actual:   {actual}")
    if errors:
        raise SystemExit(1)
    print("All tracked hashes verified.")


def update_ledger() -> None:
    tracked = discover_tracked_files()
    updated: Dict[str, str] = {}
    for rel_path in sorted(tracked):
        path = Path(rel_path)
        if rel_path == "infra/github/hash_ledger.json":
            updated[rel_path] = ""
            continue
        if rel_path in EXCLUDED_FILES:
            continue
        updated[rel_path] = compute_hash(path)
    LEDGER_PATH.write_text(
        json.dumps(updated, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Ledger updated. Remember to review and commit the changes with a GPG signature.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify or update the hash ledger.")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Recompute hashes for all tracked files and rewrite the ledger.",
    )
    args = parser.parse_args()

    if args.update:
        update_ledger()
    else:
        ledger = load_ledger()
        verify(ledger)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        raise
    except Exception as error:  # pragma: no cover
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
