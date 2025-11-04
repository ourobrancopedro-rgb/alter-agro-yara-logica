# 🧠 YARA Lógica — LSA / PICC + RAG Hybrid (Open Specifications)

> **A Logic-Sorting Architecture for auditable AI reasoning and regenerative-carbon compliance.**
> Public specifications and validation artifacts of the **YARA Lógica System**, developed and maintained by **Alter Agro Ltda.**

> **Scope:** methodological layer only — runtime implementation is private and secured.

---

## 📜 Overview

YARA Lógica is a **logic-auditable AI stack** combining:

| Layer | Function | Core Feature |
| :---- | :-------- | :----------- |
| **LSA (PICC)** | Structured reasoning — Premise → Inference → Contradiction → Conclusion | Traceable logic chain |
| **RAG Hybrid** | Retrieval + evidence binding + byte-range validation | “**No hash, no commit**” policy |
| **GitHub CI** | Cryptographic audit trail + KPI scoring | Reproducible compliance metrics |

Only the **specifications and audit rules** are open-sourced here.

---

## 🗂️ Path Allowlist & Scope Guard

Only the following paths are permitted in this public repository:

- `lsa/spec/`
- `rag/spec/`
- `docs/`
- `infra/github/`
- `legal/`
- `.github/`
- `README.md`

Any contribution outside this allowlist is rejected by policy and continuous integration.

---

## 🧩 Repository Structure

yara-logica/
├─ lsa/spec/            # LSA / PICC schemas & logic templates
├─ rag/spec/            # RAG Hybrid policies & manifests
├─ infra/github/        # Hash ledger, KPI scorers, integrity scripts
├─ legal/               # LICENSE (BUSL-1.1), TRADEMARKS.md
├─ docs/                # Whitepapers & validation kits
└─ .github/             # Workflows, SECURITY, CONTRIBUTING

---

## ⚙️ Integrity Workflow

1. **Spec-only publishing** → Schemas and policies are tracked by SHA-256.
2. **Hash-sealed ledger** → `infra/github/hash_ledger.json` records every artifact.
3. **CI gates check** each PR:
   - Scope guard (allowlist enforcement)
   - Prohibited keyword & secret scan
   - Legal artifacts present
   - **Faithfulness @ Premise ≥ 0.80**
   - **Contradiction Coverage ≥ 0.90**
4. **Branch protection** → Signed commits + required checks (Security + Engineering review).

---

## 🔍 Usage & Validation

| Action | Command |
| :------ | :------ |
| Verify hash ledger | `python infra/github/verify_hashes.py`
| Run KPI scorer | `python infra/github/kpi_score.py --min-faith-premise 0.80 --min-contradiction-coverage 0.90`
| Update ledger after edits | `python infra/github/verify_hashes.py --update`
| Submit PR | `git commit -S -m "Spec:<scope> [evidence:<source_id@span>]"`

> ❗ **Never** push runtime code, model weights, prompts, datasets, or credentials. This repository is for **documentation and specifications only**.

---

## 🚫 Out-of-Scope / Prohibited Content

- Application or runtime code (FastAPI, LangChain, Ollama, etc.)
- Model binaries / weights / training data
- Secrets or tokens of any kind
- Deployment assets (Dockerfiles, compose, infrastructure)
- Business logic or contracts not approved for public release

---

## 📚 Documentation & References

- `lsa/spec/LSA_PICC.md` — LSA / PICC methodology
- `lsa/spec/DECISION_RECORDS.md` — Hash-sealed decision schema
- `lsa/spec/AUDIT_TRAIL.md` — Cryptographic verification protocol
- `rag/spec/RAG_POLICY.md` — RAG Hybrid policy
- `rag/spec/SOURCE_VERIFICATION.md` — Source verification policy
- `docs/README_ARCH.md` — Architecture overview
- `docs/AUDITOR_GUIDE.md` — Auditor validation workflow
- `docs/samples/cpr_cra_demo.md` — Byte-range evidence example

---

## 🔒 Security & Change Control

- **Security contact:** [contatoalteragro@gmail.com](mailto:contatoalteragro@gmail.com)
- **PGP / Git signing:** All commits must be GPG-signed.
- **Change window:** Quarterly (post-audit). Proposals must include diff + rationale + falsifier.
- **Integrity rule:** “**No hash, no commit.**”

---

## 🧑‍💻 Contributing

External contributors may propose documentation or spec improvements only. See [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md).

**PR Checklist**
- [ ] Spec-only changes
- [ ] Updated `infra/github/hash_ledger.json`
- [ ] Evidence references included
- [ ] Signed commit + two review approvals

---

## 🧾 Citations & Audit Evidence

Each claim must include:

```
source_authority, document_id, paragraph_or_line_range, pubdate, sha256_span
```

Missing evidence → CI failure. Conflicts → mark **FACT(CONTESTED)**.

---

## ⚖️ License & Trademarks

- **License:** [Business Source License 1.1 (BUSL-1.1)](legal/LICENSE)
  → Research use permitted / commercial use restricted until **2029-01-01**.
- **Trademarks:** “**YARA Lógica**” and “**Alter Agro**” are marks of **Alter Agro Ltda.** See `legal/TRADEMARKS.md` for permitted nominative use.

---

## ✅ Next Steps

1. `python infra/github/verify_hashes.py --update`
2. `git add . && git commit -S -m "init: spec repo with integrity gates" && git push`
3. Enable GitHub Branch Protection: require signed commits + required checks (CI)

---

## 🪶 Footer

**Integrity Seal:** Operated under the YARA Lógica Compliance Suite — all commits GPG-signed and hash-verified.
**Contact:** [contatoalteragro@gmail.com](mailto:contatoalteragro@gmail.com)
© 2025 Alter Agro Ltda. All rights reserved.
