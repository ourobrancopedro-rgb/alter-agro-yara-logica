#!/usr/bin/env python3
"""Hash ledger verifier for YARA Lógica specification repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Set

LEDGER_PATH = Path(__file__).resolve().parent / "hash_ledger.json"

EXCLUDED_FILES = {
    ".gitignore",
    ".gitattributes",
}

# Allowlist de publicação (spec-only). Ajuste conforme política do repo.
ALLOWLIST_DIRS = (
    "lsa/spec/",
    "rag/spec/",
    "docs/",
    "legal/",
    "infra/github/",
    ".github/",
    "tests/",
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
)

ALLOWLIST_EXT = (
    ".md", ".json", ".yml", ".yaml", ".py", ".txt",
    ".mermaid", ".svg",  # svg permitido para diagramas públicos
)


def is_allowed(path: Path) -> bool:
    """Check if a file path is allowed to be published according to the allowlist."""
    p = str(path).replace("\\", "/")
    if p in EXCLUDED_FILES:
        return False
    # Check if it's an exact match or starts with an allowed directory
    if any(p == d for d in ALLOWLIST_DIRS):
        return True
    if any(p.startswith(d) for d in ALLOWLIST_DIRS if d.endswith("/")):
        # Extension check for files in allowed directories
        return path.suffix in ALLOWLIST_EXT or path.is_dir()
    return False


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


def discover_tracked_files() -> Set[str]:
    """Discover all files that should be tracked in the hash ledger."""
    files: Set[str] = set()
    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        rel = path.as_posix()
        # Always include the ledger itself (with empty hash)
        if rel == "infra/github/hash_ledger.json":
            files.add(rel)
            continue
        # Check if file is allowed
        if is_allowed(path):
            files.add(rel)
    return files


def compute_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(ledger: Dict[str, str]) -> None:
    """Verify that the ledger is complete and all hashes match."""
    # 1) Discover files that should be tracked (source of truth)
    expected = discover_tracked_files()
    ledger_keys = set(ledger.keys())

    missing_in_ledger = sorted(expected - ledger_keys)
    extra_in_ledger = sorted(ledger_keys - expected)

    mismatched = []
    present_missing = []

    # 2) Report if ledger doesn't cover expected files OR has stale entries
    errors = False
    if missing_in_ledger:
        errors = True
        print("Ledger is missing entries for allowed files:")
        for rel in missing_in_ledger:
            print(f"  - {rel}")
    if extra_in_ledger:
        errors = True
        print("Ledger contains entries for files not allowed or not present:")
        for rel in extra_in_ledger:
            print(f"  - {rel}")

    # 3) Verify hashes only for intersection (files in both sets)
    for rel_path in sorted(expected & ledger_keys):
        if rel_path in EXCLUDED_FILES:
            continue
        file_path = Path(rel_path)
        if not file_path.is_file():
            present_missing.append(rel_path)
            continue
        actual = compute_hash(file_path)
        expected_hash = ledger.get(rel_path, "")
        if expected_hash and actual != expected_hash:
            mismatched.append((rel_path, expected_hash, actual))

    if present_missing:
        errors = True
        print("Files listed but not found on disk:")
        for rel in present_missing:
            print(f"  - {rel}")
    if mismatched:
        errors = True
        print("Hash mismatches:")
        for rel, expected_h, actual_h in mismatched:
            print(f"  - {rel}\n      expected: {expected_h}\n      actual:   {actual_h}")
    if errors:
        raise SystemExit(1)
    print("All expected files covered by ledger and all hashes verified.")


def update_ledger() -> None:
    """Recompute hashes for all tracked files and update the ledger."""
    tracked = discover_tracked_files()
    updated: Dict[str, str] = {}
    for rel_path in sorted(tracked):
        path = Path(rel_path)
        if rel_path == "infra/github/hash_ledger.json":
            updated[rel_path] = ""
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
