# Pull Request — YARA Lógica Spec Update

## Summary

**Purpose:**
<!-- Briefly describe the purpose of this change -->

**Specs touched:**
<!-- List all specification files modified and rationale for each change -->
- [ ] `lsa/spec/`
- [ ] `rag/spec/`
- [ ] `docs/`
- [ ] `infra/github/`

**Rationale:**
<!-- Explain why this change is necessary -->

---

## Integrity Verification

- [ ] **Hash ledger updated** (`infra/github/hash_ledger.json`)
- [ ] **All hashes verified** (ran `python infra/github/verify_hashes.py`)
- [ ] **KPI checks pass** (ran `python infra/github/kpi_score.py`)
- [ ] **Commit is GPG-signed** (`git log -1 --show-signature`)

### KPI Snapshot
<!-- Attach snippet or path to KPI report -->

```
Faithfulness @ Premise: ____%
Contradiction Coverage: ____%
```

---

## Governance & Decision Records

- [ ] **DecisionRecord updated** (if applicable, provide ID: `DEC-YYYY-MM-DD-##`)
- [ ] **Falsifier defined/updated** (if applicable)
- [ ] **Evidence citations included** (source ID + byte range)

**Decision ID (if applicable):**
<!-- e.g., DEC-2025-11-04-01 -->

---

## Testing & Validation

- [ ] **CI passes** (path allowlist, hash verification, KPI gates)
- [ ] **No prohibited content** (no runtime code, secrets, binaries)
- [ ] **Spec-only changes** (follows allowlist: `lsa/`, `rag/`, `docs/`, `infra/github/`, `legal/`, `.github/`)

---

## Additional Context

<!-- Any additional information, context, or screenshots -->

---

## Pre-merge Checklist

- [ ] Two reviewer approvals obtained
- [ ] All CI checks green
- [ ] Branch is up-to-date with `main`
- [ ] Commit message follows convention: `<type>(<scope>): <description>`
- [ ] No merge conflicts

---

**"No Hash, No Commit" — Integrity First**
