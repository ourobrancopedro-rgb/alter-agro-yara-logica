# infra/github/verify_hashes.py
import sys, json, hashlib, pathlib

def sha256_path(path):
    b = pathlib.Path(path).read_bytes()
    return hashlib.sha256(b).hexdigest()

def main():
    args = sys.argv[1:]
    if "--ledger" not in args:
        print("Usage: verify_hashes.py --ledger infra/github/hash_ledger.json [--strict]")
        sys.exit(2)
    ledger_path = args[args.index("--ledger") + 1]
    strict = "--strict" in args

    ledger = json.loads(pathlib.Path(ledger_path).read_text(encoding="utf-8"))
    errors = []
    for e in ledger:
        p = e.get("path"); h = e.get("sha256")
        if not p or not h:
            if strict: errors.append(f"Malformed entry: {e}")
            continue
        calc = sha256_path(p)
        if calc != h:
            errors.append(f"{p}: ledger {h} != calc {calc}")

    if errors:
        print("❌ Hash mismatches:\n" + "\n".join(errors))
        sys.exit(1)
    print("✅ Ledger hashes verified.")
    sys.exit(0)

if __name__ == "__main__":
    main()
