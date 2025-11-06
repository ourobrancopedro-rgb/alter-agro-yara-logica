# 🧠 YARA Lógica — LSA / PICC + RAG Hybrid

> **An auditable AI reasoning framework** combining logic traceability (LSA/PICC) and verifiable evidence retrieval (RAG Hybrid).  
> Developed and maintained by **Alter Agro Ltda.**

[![View Repository](https://img.shields.io/badge/View_on_GitHub-Open-blue?logo=github)](https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica)
[![License: BUSL-1.1](https://img.shields.io/badge/License-BUSL--1.1-green.svg)](legal/LICENSE)
[![Integrity Seal](https://img.shields.io/badge/No_Hash-No_Commit-orange.svg)](infra/github/hash_ledger.json)
[![Audit Verified](https://img.shields.io/badge/Audit-Validated-blueviolet.svg)](docs/LSA_Auditor_Validation_Kit.pdf)

---

### 🔗 Official Repository
**URL:** [github.com/ourobrancopedro-rgb/alter-agro-yara-logica](https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica)  
**Visibility:** Public (specification-only)  
**License:** [BUSL-1.1 — source-available, non-commercial until 2029](legal/LICENSE)  
**Trademark:** “YARA Lógica” and “Alter Agro” — © Alter Agro Ltda. (see [TRADEMARKS.md](legal/TRADEMARKS.md))

---

### 🧮 Integrity & Verification
- Every specification file is hash-sealed in [`infra/github/hash_ledger.json`](infra/github/hash_ledger.json)  
- Commits must be **GPG-signed** and verified by CI  
- CI Workflow: “No Hash, No Commit” compliance suite  
- Auditor validation via [`docs/LSA_Auditor_Validation_Kit.pdf`](docs/LSA_Auditor_Validation_Kit.pdf)

---

### 🛡️ Contact
**General inquiries:** [hello@alteragro.com.br](mailto:hello@alteragro.com.br)  
**Security:** [security@alteragro.com.br](mailto:security@alteragro.com.br)

---

**© 2025 Alter Agro Ltda. All rights reserved.**  
_Trademark, license, and integrity protections enforced under YARA Lógica Compliance Suite._
# 🧠 YARA Lógica — LSA / PICC + RAG Hybrid (Open Specifications)

[![View on GitHub](https://img.shields.io/badge/View%20Repository-Open-blue?logo=github)](https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica)
[![License: BUSL-1.1](https://img.shields.io/badge/License-BUSL--1.1-green.svg)](legal/LICENSE)
[![Integrity Seal](https://img.shields.io/badge/No%20Hash-No%20Commit-orange.svg)](infra/github/hash_ledger.json)

> **A Logic-Sorting Architecture for auditable AI reasoning and regenerative-carbon compliance.**  
> Official public specification repository maintained by **Alter Agro Ltda.**

---

## 🔗 Repository Information

- **Main URL:** [https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica](https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica)  
- **Mirror Purpose:** Public audit, education, and reproducibility of YARA Lógica’s logic chain (LSA/PICC) and retrieval protocols (RAG Hybrid).  
- **Implementation Notice:** Proprietary runtime is maintained in private repositories under Alter Agro’s control.
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

## 🛡️ Information Security & Trade Secret Protection

### Dual-Repository Strategy

Alter Agro maintains **two separate repositories** for YARA Lógica to protect intellectual property:

| Repository | Visibility | Content | Classification |
|:-----------|:-----------|:--------|:---------------|
| **alter-agro-yara-logica** (this repo) | 🌍 Public | Specifications, audit artifacts, methodology | **P0 - Public** |
| **Private Runtime Repositories** | 🔒 Private | Code, prompts, models, customer data | **P2/P3 - Confidential/Trade Secret** |

### What's NOT in This Repository

This public repository **intentionally excludes**:

❌ **Runtime Code** — FastAPI, LangChain, backend services, APIs
❌ **Prompt Engineering** — Instruction templates, system prompts, fine-tuned models
❌ **Model Weights** — Binary files, training data, model configurations
❌ **Customer Data** — Names, contacts, contracts, usage analytics, PII
❌ **Secrets** — API keys, tokens, credentials, certificates
❌ **Infrastructure** — Deployment configs, IP addresses, internal domains
❌ **Business Logic** — Pricing algorithms, proprietary optimizations

**Why?** These assets constitute **trade secrets** under Brazilian law (Lei 9.279/1996, Art. 195) and provide competitive advantage. See [Trade Secret Protection Policy](legal/TRADE_SECRET_POLICY.md).

### Security Enforcement

This repository implements **multi-layer security**:

#### 🔍 Automated Secret Scanning
- **TruffleHog** — Industry-standard secret detection
- **GitLeaks** — Comprehensive pattern matching
- **Custom DLP Scanner** — Alter Agro-specific patterns (customers, pricing, prompts)
- **Pre-commit Hooks** — Client-side validation before push

#### 🚧 Information Barrier
- **Allowlist Enforcement** — Only approved paths accepted
- **File Type Validation** — Code files blocked outside `infra/github/`
- **Size Limits** — Prevents binary/model uploads (10MB max)
- **Content Scanning** — Forbidden terms, customer data, pricing info

#### 🔐 Integrity Verification
- **GPG-Signed Commits** — All changes cryptographically signed
- **Hash Ledger** — SHA-256 tracking in `infra/github/hash_ledger.json`
- **Branch Protection** — Required reviews + status checks
- **CI/CD Gates** — Must pass all security scans

### Reporting Security Issues

**Found a vulnerability or leak?**

📧 Email: [security@alteragro.com.br](mailto:security@alteragro.com.br)
📖 Policy: [.github/SECURITY.md](.github/SECURITY.md)
⏱️ Response: 24 hours acknowledgment, 90-day coordinated disclosure

**Safe Harbor:** We commit to not pursuing legal action against good-faith security researchers.

### Information Classification

All Alter Agro information follows a **4-level classification system**:

- **P0 - Public** → This repository (specs, docs, legal)
- **P1 - Internal** → Team wikis, meeting notes
- **P2 - Confidential** → Source code, contracts, roadmap
- **P3 - Trade Secret** → Prompts, models, secrets, customer PII

📖 Full guide: [Information Classification Guide](docs/INFORMATION_CLASSIFICATION_GUIDE.md)

### For Contributors

**Before contributing, ensure:**

✅ Content is **P0 - Public** (specifications only)
✅ No secrets, credentials, or API keys
✅ No customer data or business information
✅ Pre-commit hooks installed (`.github/scripts/install-hooks.sh`)
✅ Commits are GPG-signed
✅ Hash ledger updated (`python infra/github/verify_hashes.py --update`)

📖 Full guide: [Security Contributing Guide](.github/CONTRIBUTING_SECURITY.md)

---

## 🔍 Usage & Validation

| Action | Command |
| :------ | :------ |
| Verify hash ledger | `python infra/github/verify_hashes.py`
| Run KPI scorer | `python infra/github/kpi_score.py --min-faith-premise 0.80 --min-contradiction-coverage 0.90`
| **Scan for secrets** | `python infra/github/scan_secrets.py --strict`
| **Check allowlist** | `python infra/github/check_allowlist.py`
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

## 🔐 YARA Lógica PICC Notarization (n8n → GitHub)

**Production-ready specification for the n8n → GitHub notarization workflow.**

This repository includes a complete, audit-focused specification for the **YARA Lógica PICC Notarization** lane, which provides an immutable decision ledger using GitHub Issues as the record store, orchestrated via n8n with deterministic hashing and centralized validation.

### Key Components

| Component | Location | Description |
|:----------|:---------|:------------|
| **Setup Guide** | [`/docs/N8N_SETUP_GUIDE.md`](docs/N8N_SETUP_GUIDE.md) | **⭐ Step-by-step n8n workflow setup instructions** |
| **Setup Summary** | [`/docs/SETUP_SUMMARY.md`](docs/SETUP_SUMMARY.md) | Quick reference for setup and testing |
| **Test Script** | [`/scripts/test-webhook.sh`](scripts/test-webhook.sh) | Automated webhook validation script |
| **JSON Schema** | [`/spec/schemas/picc-1.0.schema.json`](spec/schemas/picc-1.0.schema.json) | PICC-1.0 schema with HTTPS-only evidence and FACT≥2 rule |
| **n8n Workflow** | [`/spec/workflows/n8n_yara_picc_notarization.json`](spec/workflows/n8n_yara_picc_notarization.json) | Sanitized n8n export (validation, hash, GitHub integration) |
| **API Contract** | [`/spec/contracts/notarization_api_contract.md`](spec/contracts/notarization_api_contract.md) | Request/response format, HMAC auth, canonical hash |
| **Label Taxonomy** | [`/spec/labels/taxonomy.md`](spec/labels/taxonomy.md) | GitHub label schema for idempotency and audit trails |
| **Runbooks** | [`/spec/ops/runbook_notarization.md`](spec/ops/runbook_notarization.md) | Operational procedures (DLQ, rate limits, troubleshooting) |
| **Threat Model** | [`/spec/ops/threat_model_stride.md`](spec/ops/threat_model_stride.md) | STRIDE threat analysis and mitigations |
| **Rate Limit Design** | [`/spec/ops/rate_limit_nonce_design.md`](spec/ops/rate_limit_nonce_design.md) | Redis-backed nonce deduplication and token bucket rate limiting |
| **Client Examples** | [`/examples/clients/`](examples/clients/) | JavaScript and Python client stubs with HMAC signing |

### Quick Start

**📚 Detailed Setup Guide:** See [`docs/N8N_SETUP_GUIDE.md`](docs/N8N_SETUP_GUIDE.md) for complete step-by-step instructions.

1. **Import n8n workflow:**
   ```bash
   # Import /spec/workflows/n8n_yara_picc_notarization.json into n8n
   # Configure credentials: GitHub OAuth2
   # Set environment: HMAC_SECRET, GITHUB_OWNER, GITHUB_REPO
   # See docs/N8N_SETUP_GUIDE.md for detailed instructions
   ```

2. **Test with automated script:**
   ```bash
   # Generate HMAC secret
   openssl rand -hex 32

   # Test webhook
   ./scripts/test-webhook.sh \
     "https://your-n8n.com/webhook/yara/picc/notarize" \
     "your-hmac-secret"
   ```

3. **Test with client libraries:**
   ```bash
   # JavaScript
   cd examples/clients/javascript
   npm install node-fetch
   export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"
   export HMAC_SECRET="your-secret"
   node submit_decision.js

   # Python
   cd examples/clients/python
   pip install requests
   export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"
   export HMAC_SECRET="your-secret"
   python submit_decision.py
   ```

4. **Manual smoke test (GitHub Actions):**
   - Navigate to Actions → "n8n Ping (spec smoke)"
   - Run workflow manually
   - Paste n8n webhook URL at runtime
   - Review output for connectivity validation

### Security Features

- ✅ **HMAC-SHA256 authentication** (X-Signature-256 header)
- ✅ **Timestamp window validation** (±300s, replay protection)
- ✅ **Nonce deduplication** (Redis-backed, single-use enforcement)
- ✅ **Canonical hashing** (SHA-256, deterministic idempotency)
- ✅ **HTTPS-only evidence** (schema-enforced)
- ✅ **Rate limiting** (Token bucket, 100 req/10min default)
- ✅ **GitHub API quota management** (exponential backoff)

### Operational Notes

- **No secrets in repo:** All sensitive values use placeholders (`<SET_IN_N8N>`)
- **Spec-only:** This is a specification repository; runtime deployment is private
- **Idempotency:** Duplicate decisions detected via `hash:<first16>` label
- **DLQ handling:** Failed GitHub API calls logged to Dead Letter Queue for reprocessing
- **Monitoring:** Track BAD_SIG rate, DLQ depth, GitHub quota remaining

For detailed implementation guidance, see the [API Contract](spec/contracts/notarization_api_contract.md) and [Runbook](spec/ops/runbook_notarization.md).

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
---

**Integrity Verification:**  
✅ Repository verified under YARA Lógica Compliance Suite.  
🔒 SHA-256 of current manifest:  
sha256sum infra/github/hash_ledger.json
