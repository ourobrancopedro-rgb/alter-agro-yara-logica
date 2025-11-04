# RAG Hybrid Policy

This policy defines retrieval and reasoning expectations for the YARA Lógica specification layer.

## 1. Modes of Operation

| Mode | Description | Evidence Requirement |
| :--- | :---------- | :------------------- |
| **Facts-First** | Retrieve certified documents before generating any reasoning artifacts. | Minimum 2 independent sources per claim. |
| **Reasoning-First** | Draft hypothesis using prior LSA outputs, then retrieve evidence to confirm or refute. | At least 1 corroborating source and contradiction scan. |
| **Tight-Loop** | Iteratively alternate retrieval and inference until contradiction coverage ≥ 0.90. | Hash ledger update per iteration. |

## 2. Retrieval Rules

1. **Immutable references.** Sources must be stable and include SHA-256 plus byte-range citations.
2. **Temporal freshness.** For time-sensitive data, ensure publication date is within the policy window defined in `docs/AUDITOR_GUIDE.md`.
3. **Evidence diversity.** Avoid relying on a single issuer; require multi-source corroboration when available.
4. **Conflict surfacing.** All contradictory evidence must be encoded as `FACT(CONTESTED)` entries in LSA artifacts.

## 3. Output Structure

RAG outputs reference:
- `retrieval_context`: list of sources (with SHA-256 and byte ranges)
- `reasoning_trace`: ordered array of inference steps
- `contradiction_register`: mapping of contested claims

## 4. Compliance Checklist

- [ ] Retrieval logs retained in private runtime systems (not in this repo).
- [ ] Hash ledger updated when specs reference new sources.
- [ ] KPI metrics meet Faithfulness@Premise ≥ 0.80 and Contradiction Coverage ≥ 0.90.
- [ ] Any runtime references replaced with `// PRIVATE RUNTIME — NOT IN THIS REPOSITORY`.
