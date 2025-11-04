# Architecture Overview (Specification Layer)

This document summarizes the public specification architecture for YARA Lógica.

## 1. LSA / PICC Layer

- **Purpose:** Provide transparent reasoning chains from Premise to Conclusion with explicit contradictions.
- **Artifacts:** `lsa/spec/*.md`
- **Integrity Controls:**
  - SHA-256 hashes recorded in `infra/github/hash_ledger.json`
  - GPG-signed commits
  - Contradictions labeled `FACT(CONTESTED)`

## 2. RAG Hybrid Layer

- **Modes:** Facts-First, Reasoning-First, Tight-Loop (see `rag/spec/RAG_POLICY.md`).
- **Evidence Binding:** Every claim references a source ID, byte range, and hash.
- **Freshness:** Governed by `rag/spec/SOURCE_VERIFICATION.md`.

## 3. GitHub-Native Audit

- **CI Workflow:** `.github/workflows/ci.yml` enforces scope gate, prohibited-content scan, legal checks, hash verification, and KPI scoring.
- **Hash Ledger:** `infra/github/verify_hashes.py` ensures tracked files match stored hashes.
- **KPI Gates:** `infra/github/kpi_score.py` enforces Faithfulness@Premise ≥ 0.80 and Contradiction Coverage ≥ 0.90.

## 4. Separation of Concerns

- **Public Repo (this):** Specifications, policies, validation artifacts.
- **Private Runtime:** Implementation, deployment, and operational logic. Replace any runtime references with `// PRIVATE RUNTIME — NOT IN THIS REPOSITORY`.

## 5. Compliance Workflow

1. Draft or update spec artifacts.
2. Update hash ledger and KPI report.
3. Submit GPG-signed PR with evidence citations.
4. CI validates scope, KPIs, hashes, and legal requirements.
5. Branch protection requires signed commits and reviewer approval before merge.

This layered approach delivers public transparency while protecting Alter Agro's runtime intellectual property.
