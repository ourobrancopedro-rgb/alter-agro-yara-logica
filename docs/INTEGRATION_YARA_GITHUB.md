# YARA Lógica ↔ GitHub Integration

This repo is the **public, auditable memory** of YARA Lógica (specs, policies, hash ledger, CI gates).
The private runtime **pins by commit**, downloads specs, **verifies SHA-256** against `infra/github/hash_ledger.json`, and stamps provenance in every high-stakes output.

## CLI

Install (editable) and expose `yara`:

```bash
pip install -e .
export GITHUB_TOKEN=ghs_***   # GitHub App installation token or PAT (least privilege)
```

### Pull pinned specs (READ-ONLY)

```bash
yara specs pull \
  --owner ourobrancopedro-rgb --repo alter-agro-yara-logica \
  --ref <commit_sha> --outdir ./specs-pin \
  --files lsa/spec/LSA_PICC.md rag/spec/RAG_POLICY.md infra/github/hash_ledger.json
```

### Verify against ledger

```bash
yara specs verify \
  --owner ourobrancopedro-rgb --repo alter-agro-yara-logica \
  --ref <commit_sha> --ledger-path infra/github/hash_ledger.json \
  --files lsa/spec/LSA_PICC.md rag/spec/RAG_POLICY.md
```

### Open PR (auto-ledger)

```bash
yara specs propose-auto-ledger \
  --owner ourobrancopedro-rgb --repo alter-agro-yara-logica \
  --base main --message "feat(lsa): tighten FreshnessGate" \
  --title "YARA: LSA update (auto-ledger)" \
  --add lsa/spec/LSA_PICC.md=local/LSA_PICC.md
```

### Promote pin (after merge)

```bash
yara specs promote \
  --owner ourobrancopedro-rgb --repo alter-agro-yara-logica \
  --commit-sha <merge_sha> > pin.json
```

**Principles**: *No Hash, No Commit* • *Signed PRs only* • *Allowlist* • *KPI gates*
