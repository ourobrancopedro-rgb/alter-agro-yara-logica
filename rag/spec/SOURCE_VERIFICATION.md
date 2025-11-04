# Source Verification Policy

This policy governs how evidence sources are validated before inclusion in YARA Lógica specifications.

## 1. Metadata Requirements

Every source entry must include:
- `source_id`
- `title`
- `publisher`
- `publication_date`
- `sha256`
- `byte_range`
- `access_level` (`public` or `restricted`)

## 2. Verification Steps

1. **Checksum confirmation.** Compute SHA-256 over the original byte stream. If a source cannot be hashed publicly, record `sha256: private` and document handling in the runtime repository.
2. **Byte-range binding.** Record the exact byte offsets that support the claim. Use inclusive ranges (e.g., `128-244`).
3. **Freshness window.** Ensure sources are updated within policy windows:
   - Agronomic data: ≤ 24 months old
   - Emissions reports: ≤ 12 months old
   - Regulatory filings: latest available version
4. **Chain of custody.** Maintain private evidence packages with notarized timestamps (stored outside this repo).

## 3. Contradiction Handling

- Contradictions discovered during verification must be logged in `contradiction_register` with status `FACT(CONTESTED)`.
- Escalate unresolved conflicts to the decision record workflow.

## 4. Automation Hooks

- Hash verification: `python infra/github/verify_hashes.py`
- KPI scoring: `python infra/github/kpi_score.py`
- When integrating with runtime retrieval pipelines, substitute actual code with `// PRIVATE RUNTIME — NOT IN THIS REPOSITORY`.

Adhering to this policy ensures that published specifications remain verifiable without leaking proprietary runtime logic.
