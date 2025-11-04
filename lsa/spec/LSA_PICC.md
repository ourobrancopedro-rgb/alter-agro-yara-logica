# LSA / PICC Specification

The Logic-Sorting Architecture (LSA) follows the **Premise → Inference → Contradiction → Conclusion (PICC)** reasoning loop. This document defines the schema and provides JSON exemplars for spec authors.

## 1. Schema Overview

| Field | Type | Description |
| :---- | :--- | :---------- |
| `premises` | array of objects | Verified inputs containing `id`, `statement`, `source_sha256`, `byte_range` |
| `inferences` | array of objects | Derived statements with `id`, `supports`, `methodology`, and `confidence` |
| `contradictions` | array of objects | Explicit conflicts marked as `FACT(CONTESTED)` with references to `premises` or `inferences` |
| `conclusions` | array of objects | Final positions that cite both supportive and contesting evidence |
| `audit` | object | Integrity metadata (`author`, `timestamp`, `hash`, `signing_key`) |

## 2. JSON Template

```json
{
  "premises": [
    {
      "id": "premise-001",
      "statement": "Soil organic carbon increased by 2.1%.",
      "source_sha256": "<sha256-of-source-document>",
      "byte_range": "123-231"
    }
  ],
  "inferences": [
    {
      "id": "inference-001",
      "supports": ["premise-001"],
      "methodology": "LSA::delta-carbon",
      "confidence": 0.82,
      "statement": "Regenerative practice achieved the targeted carbon gain."
    }
  ],
  "contradictions": [
    {
      "id": "contradiction-001",
      "targets": ["inference-001"],
      "statement": "Independent audit recorded only 1.2% gain.",
      "source_sha256": "<sha256-audit>",
      "byte_range": "88-141",
      "label": "FACT(CONTESTED)"
    }
  ],
  "conclusions": [
    {
      "id": "conclusion-001",
      "supports": ["inference-001"],
      "contested_by": ["contradiction-001"],
      "statement": "Claim remains under review pending reconciliation of audit variance.",
      "decision_state": "pending"
    }
  ],
  "audit": {
    "author": "spec-author@alteragro",
    "timestamp": "2025-01-11T00:00:00Z",
    "hash": "<sha256-of-document>",
    "signing_key": "GPG:ABCD1234"
  }
}
```

## 3. Authoring Guidance

1. **Atomic statements.** Each `statement` must be self-contained and cite its evidence.
2. **Confidence bounds.** Provide numeric confidence (0.0–1.0) with methodology tags.
3. **Contradiction discipline.** Conflicts must be explicitly linked and labeled `FACT(CONTESTED)`.
4. **Cryptographic linkage.** Always include `source_sha256` and `byte_range` for verifiable binding.

## 4. Validation Checklist

- [ ] Premises reference immutable sources.
- [ ] Inferences reference one or more premises or prior inferences.
- [ ] Contradictions cite audited evidence and carry `FACT(CONTESTED)` labels.
- [ ] Conclusions enumerate both supporting and contesting references.
- [ ] Audit metadata matches the entry recorded in `infra/github/hash_ledger.json`.
