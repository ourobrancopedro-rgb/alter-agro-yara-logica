# Audit Trail Protocol

This document defines how auditors verify LSA artifacts and their cryptographic bindings within the YARA Lógica specification repository.

## 1. Cryptographic Ledger

- **Ledger File:** `infra/github/hash_ledger.json`
- **Hash Function:** SHA-256 over UTF-8 bytes of each tracked artifact.
- **Update Procedure:**
  1. Modify spec file.
  2. Run `python infra/github/verify_hashes.py --update`.
  3. Review diff of ledger changes.
  4. Commit with GPG signature.

## 2. Verification Steps

1. **Confirm ledger integrity.** Execute `python infra/github/verify_hashes.py`. The script must exit with status 0.
2. **Cross-check artifacts.** For each ledger entry, recompute SHA-256 and ensure it matches the stored value.
3. **Review KPIs.** Run `python infra/github/kpi_score.py` with CI thresholds to confirm Faithfulness@Premise and Contradiction Coverage requirements.
4. **Check signatures.** Validate that commits affecting LSA artifacts are signed and the signer is authorized.

## 3. Conflict Marking

- All contradictions must use the literal tag `FACT(CONTESTED)`.
- Auditor annotations should reference the `decision_id` and `lsa_document_sha256` when closing or escalating conflicts.

## 4. Evidence Binding

- Include `source_sha256` and `byte_range` for each premise.
- If the evidence is unavailable publicly, store reference metadata and indicate `access: private`.
- Never include proprietary runtime instructions; replace with `// PRIVATE RUNTIME — NOT IN THIS REPOSITORY` when necessary.

## 5. Reporting Findings

- Summaries go into `docs/AUDITOR_GUIDE.md` appendices.
- Escalations follow the contact pathway in `.github/SECURITY.md`.

Maintaining this protocol ensures reproducibility and protects Alter Agro's intellectual property.
