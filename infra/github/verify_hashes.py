#!/usr/bin/env python3
"""
Hash Ledger Verification Script
================================

Verifies that all files in the hash ledger match their recorded SHA-256 hashes.
Supports self-referential ledger entries (empty hash string).

Usage:
    python verify_hashes.py --ledger infra/github/hash_ledger.json [--strict]

Author: Alter Agro Ltda.
License: BUSL-1.1
"""
import sys, json, hashlib, pathlib

def sha256_path(path):
    """Calculate SHA-256 hash of a file"""
    b = pathlib.Path(path).read_bytes()
    return hashlib.sha256(b).hexdigest()

def main():
    args = sys.argv[1:]
    if "--ledger" not in args:
        print("Usage: verify_hashes.py --ledger infra/github/hash_ledger.json [--strict]")
        sys.exit(2)
    ledger_path = args[args.index("--ledger") + 1]
    strict = "--strict" in args

    # Load ledger - format is {path: hash, ...}
    ledger = json.loads(pathlib.Path(ledger_path).read_text(encoding="utf-8"))

    errors = []
    checked = 0
    skipped_self_ref = 0

    for path, expected_hash in ledger.items():
        # Handle self-referential entry (empty hash means skip verification)
        if path == ledger_path or expected_hash == "":
            skipped_self_ref += 1
            continue

        # Check if file exists
        if not pathlib.Path(path).is_file():
            errors.append(f"❌ {path}: file not found")
            continue

        # Calculate and compare hash
        try:
            calc_hash = sha256_path(path)
            if calc_hash != expected_hash:
                errors.append(f"❌ {path}: ledger {expected_hash[:16]}... != calc {calc_hash[:16]}...")
            else:
                checked += 1
        except Exception as e:
            errors.append(f"❌ {path}: error reading file: {e}")

    if errors:
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("❌ HASH VERIFICATION FAILED")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"\nChecked: {checked} files")
        print(f"Errors: {len(errors)}")
        print(f"Self-references skipped: {skipped_self_ref}")
        print("\nHash mismatches:")
        for error in errors:
            print(f"  {error}")
        print("\n💡 To fix:")
        print("   1. Run: python infra/github/update_ledger.py")
        print("   2. Commit the updated ledger")
        print("   3. Re-run verification")
        sys.exit(1)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ HASH VERIFICATION PASSED")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\nChecked: {checked} files")
    print(f"Self-references skipped: {skipped_self_ref}")
    print(f"Total entries: {len(ledger)}")
    print("\n✅ All file hashes match the ledger")
    print("🔒 No unauthorized modifications detected")
    sys.exit(0)

if __name__ == "__main__":
    main()
