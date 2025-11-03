# alter-agro-yara-logica
YARA Logica (LSA)

⸻


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

## 🧩 Repository Structure

yara-logica/
├─ lsa/spec/            # LSA / PICC schemas & logic templates
├─ rag/spec/            # RAG Hybrid policies & manifests
├─ infra/github/        # Hash ledger, KPI scorers, integrity scripts
├─ legal/               # LICENSE (BUSL-1.1), NOTICE, TRADEMARKS.md
├─ docs/                # Whitepapers & validation kits
└─ .github/             # Workflows, CODEOWNERS, SECURITY, CONTRIBUTING

---

## ⚙️ Integrity Workflow

1. **Spec-only publishing** → Schemas and policies are tracked by SHA-256.  
2. **Hash-sealed ledger** → `infra/github/hash_ledger.json` records every artifact.  
3. **CI gates check** each PR:  
   - Ledger present and valid  
   - No runtime keywords or secrets  
   - **Faithfulness @ Premise ≥ 0.80**  
   - **Contradiction Coverage ≥ 0.90**  
4. **Branch protection** → Signed commits + two approvals (Security + Engineering).

---

## 🔍 Usage & Validation

| Action | Command |
| :------ | :------ |
| Verify hash ledger | `python infra/github/verify_hashes.py` |
| Run KPI scorer | `python infra/github/kpi_score.py --min-faith-premise 0.80 --min-contradiction-coverage 0.90` |
| Add new spec | Edit file → generate SHA-256 → update `hash_ledger.json` |
| Submit PR | `git commit -S -m "Spec:<scope> [evidence:<source_id@span>]"` |

> ❗ **Never** push runtime code, model weights, prompts, datasets, or credentials.  
> This repository is for **documentation and specifications only**.

---

## 🚫 Out-of-Scope / Prohibited Content

- Application or runtime code (FastAPI, LangChain, Ollama, etc.)  
- Model binaries / weights / training data  
- Secrets or tokens of any kind  
- Business logic or contracts not approved for public release  

---

## 📚 Documentation & References

- `lsa/spec/LSA_PICC.md` — LSA / PICC methodology  
- `rag/spec/RAG_POLICY.md` — RAG Hybrid policy  
- `docs/LSA_Auditor_Validation_Kit.pdf` — auditor toolkit  
- `docs/ops/RUNBOOK.md` — operator guide  
- `docs/samples/cpr_cra_demo.md` — byte-range evidence example  

---

## 🔒 Security & Change Control

- **Security contact:** [contatoalteragro@gmail.com](mailto:contatoalteragro@gmail.com)  
- **PGP / Git signing:** All commits must be GPG-signed.  
- **Change window:** Quarterly ( post-audit ). Proposals must include diff + rationale + falsifier.  
- **Integrity rule:** “**No hash, no commit.**”

---

## 🧑‍💻 Contributing

External contributors may propose documentation or spec improvements only.  
See [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md).

**PR Checklist**
- [ ] Spec-only changes  
- [ ] Updated `hash_ledger.json`  
- [ ] Evidence references included  
- [ ] Signed commit + two review approvals  

---

## 🧾 Citations & Audit Evidence

Each claim must include:  

source_authority, document_id, paragraph_or_line_range, pubdate, sha256_span

Missing evidence → CI failure. Conflicts → mark **FACT(CONTESTED)**.

---

## ⚖️ License & Trademarks

- **License:** [Business Source License 1.1 (BUSL-1.1)](legal/LICENSE)  
  → Research use permitted / commercial use restricted until **2029-01-01**.  
- **Trademarks:** “**YARA Lógica**” and “**Alter Agro**” are marks of **Alter Agro Ltda.**  
  See `legal/TRADEMARKS.md` for permitted nominative use.

---

## 🪶 Footer

**Integrity Seal:** Operated under the YARA Lógica Compliance Suite — all commits GPG-signed and hash-verified.  
**Contact:** [contatoalteragro@gmail.com](mailto:contatoalteragro@gmail.com)  
© 2025 Alter Agro Ltda. All rights reserved.


⸻

✅ Paste this as README.md in your repo root before first push.
Would you like me to generate matching CONTRIBUTING.md, SECURITY.md, and a minimal Python integrity-checker (verify_hashes.py + kpi_score.py) next?
