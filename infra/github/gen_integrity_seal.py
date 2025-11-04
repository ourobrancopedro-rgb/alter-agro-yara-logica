#!/usr/bin/env python3
import hashlib, json, pathlib, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
tpl = ROOT / "docs/badges/integrity_seal.svg.tpl"
out = ROOT / "docs/badges/integrity_seal.svg"
ledger = ROOT / "infra/github/hash_ledger.json"

if not tpl.exists():
    print("Template not found:", tpl, file=sys.stderr); sys.exit(1)
if not ledger.exists():
    print("Ledger not found:", ledger, file=sys.stderr); sys.exit(1)

sha = hashlib.sha256(ledger.read_bytes()).hexdigest()
ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

svg = tpl.read_text(encoding="utf-8")
svg = svg.replace("{{LEDGER_SHA256}}", sha[:40] + "…")  # abreviação segura
svg = svg.replace("{{UPDATED_ISO}}", ts)
out.write_text(svg, encoding="utf-8")

print("Wrote:", out)
print("SHA256(hash_ledger.json):", sha)
