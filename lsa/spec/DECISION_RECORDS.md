# Decision Records Specification

Decision records encapsulate conclusions derived from LSA / PICC runs and bind them to cryptographic evidence. This file defines the schema and authoring protocol.

## 1. Record Schema

| Field | Type | Notes |
| :---- | :--- | :---- |
| `decision_id` | string | Stable identifier (e.g., `DR-2025-001`). |
| `lsa_document_sha256` | string | SHA-256 of the associated LSA artifact. |
| `summary` | string | High-level conclusion summary. |
| `status` | enum | `approved`, `pending`, or `rejected`. |
| `reviewers` | array | Objects with `name`, `role`, `pgp_fingerprint`. |
| `verdict` | object | Contains `criteria_met` (array), `conflicts_flagged` (array of `FACT(CONTESTED)` IDs), `timestamp`. |
| `signatures` | array | GPG signatures over the decision payload. |

## 2. YAML Template

```yaml
decision_id: DR-2025-001
lsa_document_sha256: "<sha256-value>"
summary: |
  Regenerative carbon allocation remains provisional pending contradiction resolution.
status: pending
reviewers:
  - name: Ana Silva
    role: LSA Lead
    pgp_fingerprint: "ABCD 1234 EFGH 5678"
  - name: Bruno Costa
    role: Compliance Auditor
    pgp_fingerprint: "1122 3344 5566 7788"
verdict:
  criteria_met:
    - "faithfulness-premise >= 0.80"
  conflicts_flagged:
    - contradiction-001
  timestamp: "2025-01-11T00:00:00Z"
signatures:
  - type: openpgp
    signer: Ana Silva
    signature_sha256: "<sha256-sig>"
  - type: openpgp
    signer: Bruno Costa
    signature_sha256: "<sha256-sig>"
```

## 3. Publication Rules

1. **Hash binding.** `lsa_document_sha256` must appear in `infra/github/hash_ledger.json`.
2. **Dual attestation.** At least two reviewers must sign every record.
3. **Conflict transparency.** All unresolved contradictions are listed under `conflicts_flagged`.
4. **BUSL compatibility.** Do not include proprietary runtime instructions; if required, insert `// PRIVATE RUNTIME — NOT IN THIS REPOSITORY`.

## 4. Validation Checklist

- [ ] SHA-256 matches associated LSA artifact.
- [ ] Signatures captured and stored in secure key vault.
- [ ] Reviewers have active compliance roles.
- [ ] Record added to hash ledger with updated checksum.
