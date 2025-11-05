#!/usr/bin/env python3
import argparse, json, hashlib, subprocess, sys
from pathlib import Path

ALLOWED_PREFIXES = (
    ".gitignore","README.md","lsa/spec/","rag/spec/","docs/","legal/","infra/github/",".github/",
)
EXCLUDED = {"infra/github/verify_hashes_strict.py"}

LEDGER = Path("infra/github/hash_ledger.json")

def is_allowed(path:str)->bool:
    return any(path==p or path.startswith(p) for p in ALLOWED_PREFIXES)

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def list_staged():
    out = subprocess.check_output(["git","diff","--name-only","--cached"], text=True)
    return [l.strip() for l in out.splitlines() if l.strip()]

def list_all():
    out = subprocess.check_output(["git","ls-files"], text=True)
    return [l.strip() for l in out.splitlines() if l.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true", help="only update staged files")
    args=ap.parse_args()

    files = list_staged() if args.staged else list_all()
    targets = sorted(p for p in files if is_allowed(p) and p not in EXCLUDED)

    ledger = {}
    if LEDGER.exists():
        try:
            ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        except Exception:
            pass

    for rel in targets:
        p=Path(rel)
        if not p.is_file(): 
            # remove if no longer exists
            if rel in ledger: 
                del ledger[rel]
            continue
        ledger[rel]=sha256_file(p)

    # Drop entries that no longer exist in tree
    existing = set(list_all())
    for k in list(ledger.keys()):
        if k not in existing or not is_allowed(k):
            del ledger[k]

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(dict(sorted(ledger.items())), indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"✅ updated {LEDGER}")

if __name__=="__main__":
    main()
