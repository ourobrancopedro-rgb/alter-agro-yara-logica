# Contributing to YARA Lógica — Public Specifications

Thank you for helping maintain the **spec-only** public repository for YARA Lógica. Runtime code, models, and deployment assets belong exclusively in private infrastructure and **must not** be committed here.

## 📌 Scope

✅ Allowed directories:
- `lsa/spec/`
- `rag/spec/`
- `docs/`
- `infra/github/`
- `legal/`
- `.github/`
- `README.md`

🚫 Prohibited content includes (non-exhaustive): runtime services, APIs, Docker artifacts, infrastructure manifests, datasets, model weights, secrets, prompts, or configuration that enables execution.

If you need to reference a runtime component, replace it with the literal text:

```text
// PRIVATE RUNTIME — NOT IN THIS REPOSITORY
```

## 🛡️ Integrity Requirements

1. **GPG-signed commits only.** Unsigned commits will be rejected.
2. **Hash ledger enforcement.** Run `python infra/github/verify_hashes.py --update` after changes and commit the updated `infra/github/hash_ledger.json`.
3. **Evidence-ready diffs.** Every modification must cite its supporting sources with byte-range or equivalent precision.
4. **CI compliance.** Ensure your PR passes the scope gate, prohibited-content scan, legal checks, and KPI thresholds.

## 🔄 Pull Request Template

Include the following sections in every PR description:

1. **Summary of Changes** — concise description.
2. **Rationale & Evidence** — cite sources with byte ranges or document IDs.
3. **Integrity Impact** — expected change to KPIs (Faithfulness@Premise, Contradiction Coverage).
4. **Testing** — commands run locally (e.g., hash verifier, KPI scorer).

## 🧭 Review Process

- Minimum of **two reviewers** (Security + Engineering).
- Reviewers verify scope, evidence, KPI status, and signed commits.
- Merges require CI passing and adherence to the allowlist above.

Thank you for safeguarding Alter Agro's intellectual property while advancing transparent specifications.
