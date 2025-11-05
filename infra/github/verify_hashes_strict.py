#!/usr/bin/env python3
import json, hashlib, sys, os, re
from pathlib import Path

ALLOWED_PREFIXES = (
    ".gitignore","README.md","lsa/spec/","rag/spec/","docs/","legal/","infra/github/",".github/",
)
EXCLUDED_FILES = {
    ".gitignore",
    "infra/github/verify_hashes_strict.py",  # this script isn't ledger-tracked
}

LEDGER_PATH = Path("infra/github/hash_ledger.json")

def is_allowed(p: Path) -> bool:
    rp = str(p).replace("\\","/")
    return any(rp == pref or rp.startswith(pref) for pref in ALLOWED_PREFIXES)

def discover_tracked_files():
    files=[]
    for p in Path(".").rglob("*"):
        if not p.is_file(): 
            continue
        rp=str(p).replace("\\","/")
        if is_allowed(p) and rp not in EXCLUDED_FILES:
            files.append(rp)
    return sorted(files)

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if not LEDGER_PATH.is_file():
        print("❌ ledger missing: infra/github/hash_ledger.json", file=sys.stderr)
        sys.exit(1)
    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ invalid JSON: {e}", file=sys.stderr); sys.exit(1)

    expected_files = discover_tracked_files()
    ledger_files = sorted(ledger.keys())

    missing_in_ledger = [f for f in expected_files if f not in ledger]
    extra_in_ledger   = [f for f in ledger_files if f not in expected_files]

    errors = False
    if missing_in_ledger:
        errors=True
        print("❌ missing in ledger:"); 
        for f in missing_in_ledger: print("  -", f)
    if extra_in_ledger:
        errors=True
        print("❌ extra entries in ledger (no longer in tree):");
        for f in extra_in_ledger: print("  -", f)

    mismatches=[]
    for f in expected_files:
        if f in EXCLUDED_FILES: 
            continue
        p=Path(f)
        got=sha256_file(p)
        want=ledger.get(f)
        if want is None or got != want:
            mismatches.append((f, want, got))

    if mismatches:
        errors=True
        print("❌ hash mismatches:")
        for f, want, got in mismatches:
            print(f"  - {f}\n      expected: {want}\n      actual:   {got}")

    if errors:
        sys.exit(1)
    print("✅ strict ledger verified (parity + hashes)")

if __name__=="__main__":
    main()
