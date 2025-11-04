# Information Classification Guide
**YARA Lógica — Alter Agro Ltda.**

---

## Quick Reference

| Level | Name | Description | Examples | Repository |
|:------|:-----|:------------|:---------|:-----------|
| **P0** | Public | Intended for public release | Specs, docs, marketing | Public repo |
| **P1** | Internal | Internal use only | Team notes, processes | Internal wiki |
| **P2** | Confidential | Competitive harm if disclosed | Source code, contracts | Private repos |
| **P3** | Trade Secret | Severe harm if disclosed | Prompts, models, secrets | Encrypted storage |

---

## Classification Decision Tree

```
START: Need to share/store information?
  ↓
[1] Is this already public or intended for publication?
  YES → P0 (Public)
  NO  ↓
[2] Would disclosure harm Alter Agro financially or competitively?
  NO  → P1 (Internal)
  YES ↓
[3] Could disclosure cause SEVERE competitive harm or legal liability?
  YES → P3 (Trade Secret)
  NO  → P2 (Confidential)
```

**Rule of thumb:** When uncertain, classify one level higher.

---

## P0 - Public

### Definition
Information explicitly intended for public consumption. No competitive harm from disclosure.

### Examples (10+)

**Documentation:**
1. LSA/PICC methodology specifications
2. RAG policy documents
3. Audit trail schemas
4. Architecture diagrams (high-level)
5. API reference docs (public endpoints only)

**Marketing:**
6. Blog posts and whitepapers
7. Press releases
8. Product feature announcements
9. Case studies (anonymized, approved)
10. Conference presentations

**Legal:**
11. BUSL-1.1 license text
12. Trademark usage guidelines
13. Public security policy

**Code (spec-only):**
14. Hash verification scripts
15. KPI scoring tools
16. Allowlist checkers

### Handling Requirements

| Aspect | Requirement |
|:-------|:------------|
| **Storage** | No restrictions; public GitHub allowed |
| **Transmission** | No restrictions |
| **Access** | Open to anyone |
| **Marking** | Optional: "PUBLIC" or no marking |
| **Retention** | Standard IT policies |
| **Disposal** | No special requirements |

### Downgrade From
- P1 → P0: Requires manager approval + legal review
- P2/P3 → P0: Requires CTO approval + legal review + business justification

---

## P1 - Internal

### Definition
Information for Alter Agro personnel only. Minimal risk if disclosed, but not intended for external sharing.

### Examples (10+)

**Documentation:**
1. Internal wiki pages
2. Team meeting notes
3. Project planning documents
4. Internal process guides
5. Training materials

**Communications:**
6. Internal announcements
7. Team Slack conversations
8. Employee handbook sections
9. Internal FAQs
10. Onboarding checklists

**Data:**
11. Non-sensitive analytics
12. Internal dashboards (non-financial)
13. Bug reports (non-security)
14. Feature requests (non-confidential)

### Handling Requirements

| Aspect | Requirement |
|:-------|:------------|
| **Storage** | Company systems only (Google Drive, Slack, internal wiki) |
| **Transmission** | Company email; avoid personal email |
| **Access** | Alter Agro personnel only |
| **Marking** | "INTERNAL" footer recommended |
| **Retention** | 3 years standard, then review |
| **Disposal** | Standard IT deletion procedures |

### Common Mistakes
- ❌ Sharing in public Slack channels
- ❌ Posting to external forums/blogs
- ❌ Using personal email for work discussions
- ✅ Keeping to company systems
- ✅ Assuming external people shouldn't see it

---

## P2 - Confidential

### Definition
Sensitive business information that provides competitive advantage. Disclosure would harm Alter Agro's business position.

### Examples (10+)

**Code & Implementation:**
1. Runtime source code (FastAPI, backend)
2. Database schemas
3. API implementations (internal)
4. Infrastructure-as-code (Terraform, K8s)
5. Deployment scripts

**Business Information:**
6. Customer contracts and pricing
7. Financial projections and budgets
8. Partnership agreements
9. Vendor contracts
10. Roadmap (unreleased features)

**Technical:**
11. Security audit reports
12. Architecture decision records (internal)
13. Performance benchmarks
14. Competitive analysis
15. Prompt templates (non-production)

### Handling Requirements

| Aspect | Requirement |
|:-------|:------------|
| **Storage** | Encrypted cloud storage (GitHub private repos, Google Drive with encryption) |
| **Transmission** | Encrypted email (GPG, ProtonMail) or secure file sharing |
| **Access** | Need-to-know basis; manager approval required |
| **Marking** | "CONFIDENTIAL" header/footer mandatory |
| **Retention** | 7 years minimum (legal/business requirements) |
| **Disposal** | Secure deletion (shred, srm, wipe tools) |

### External Sharing
- ✅ **NDA required** (5-10 year term)
- ✅ Need business justification
- ✅ Manager approval
- ✅ Track who has access
- ❌ Never commit to public repos
- ❌ Never send via unencrypted channels

### Common Mistakes
- ❌ Committing to public GitHub
- ❌ Sharing via regular email
- ❌ Discussing in public Slack channels
- ❌ Leaving printouts unattended
- ✅ Using private repos with access control
- ✅ Encrypting files before sharing
- ✅ Verifying recipient has NDA

---

## P3 - Trade Secret

### Definition
Crown jewels. Information that, if disclosed, would cause SEVERE competitive harm or legal liability. Maximum protection required.

### Examples (10+)

**AI/ML Systems:**
1. Production prompt engineering systems
2. Fine-tuned model weights
3. Training datasets (proprietary)
4. RAG retrieval algorithms (implementation)
5. Model selection criteria (internal)

**Security:**
6. API keys, tokens, credentials
7. Private keys and certificates
8. Security vulnerability details (pre-disclosure)
9. Penetration test reports
10. Incident response playbooks

**Business Critical:**
11. Customer PII (emails, phone, tax IDs)
12. Strategic partnerships (pre-announcement)
13. M&A discussions
14. Pricing algorithms
15. Core differentiating algorithms

### Handling Requirements

| Aspect | Requirement |
|:-------|:------------|
| **Storage** | Mandatory encryption at rest; HSM-backed for secrets; access logging |
| **Transmission** | Encrypted channels only; logged |
| **Access** | Explicit authorization; CTO/CEO approval; MFA required; audit trail |
| **Marking** | "TRADE SECRET" watermark on every page/screen |
| **Retention** | Indefinite (or as required by law) |
| **Disposal** | DoD 5220.22-M wiping; certificate of destruction |

### External Sharing
- ✅ **NDA mandatory** (10+ year term or perpetual)
- ✅ CTO/CEO approval required
- ✅ Legal review mandatory
- ✅ Watermarking/tracking
- ✅ Access logging
- ❌ **NEVER** commit to any repository without security review
- ❌ **NEVER** send via email (even encrypted) without explicit approval
- ❌ **NEVER** discuss in public or semi-public forums

### Common Mistakes
- ❌ Hard-coding secrets in code
- ❌ Committing .env files
- ❌ Sharing prompts in demo videos
- ❌ Accidentally including in screenshots
- ❌ Discussing customer names in public issues
- ✅ Using secrets managers (AWS Secrets, Vault)
- ✅ Sanitizing demos and screenshots
- ✅ Using placeholders in examples

---

## Specific Guidance for YARA Lógica

### Prompts & Prompt Engineering

| Type | Classification | Reasoning |
|:-----|:---------------|:----------|
| Methodology description | P0 | High-level approach is public spec |
| General templates | P1-P2 | Depends on specificity |
| Production prompts | **P3** | Core competitive advantage |
| Fine-tuned system prompts | **P3** | Trade secret |

### Model Information

| Type | Classification | Reasoning |
|:-----|:---------------|:----------|
| "We use GPT-4" | P0-P1 | General model choice is not secret |
| Model weights | **P3** | Proprietary if fine-tuned |
| Training data | **P3** | Competitive advantage |
| Inference parameters | P2-P3 | Depends on specificity |

### Customer Data

| Type | Classification | Reasoning |
|:-----|:---------------|:----------|
| Customer names | **P3** | PII, competitive intelligence |
| Anonymized case studies | P0 | If approved by customer |
| Usage statistics | P2 | Aggregate may be P1 |
| Contract terms | P2-P3 | Depends on sensitivity |

### Code & Implementation

| Type | Classification | Reasoning |
|:-----|:---------------|:----------|
| Public spec files | P0 | Intentionally open |
| Runtime code | P2 | Competitive advantage |
| Core algorithms | **P3** | Trade secret |
| CI/CD scripts | P0-P1 | Tooling is less sensitive |

### Infrastructure

| Type | Classification | Reasoning |
|:-----|:---------------|:----------|
| High-level architecture | P0 | Public documentation |
| Cloud provider choice | P0-P1 | "We use AWS" is fine |
| Specific configurations | P2 | Security risk |
| IP addresses, domains | **P3** | Security vulnerability |

---

## Decision Examples

### Example 1: Blog Post About LSA Methodology

**Q:** Writing blog post explaining LSA/PICC. What classification?

**Decision Tree:**
1. Is this public? YES → **P0**

**Result:** P0 (Public)
**Action:** Post freely. Ensure accuracy.

---

### Example 2: Customer Pricing Spreadsheet

**Q:** Excel file with customer pricing and contract terms.

**Decision Tree:**
1. Is this public? NO
2. Would disclosure harm us? YES (customer names + pricing = competitive harm)
3. SEVERE harm? YES (customers + pricing = trade secret)

**Result:** **P3** (Trade Secret)
**Action:** Encrypted storage, access logging, NDA for any sharing

---

### Example 3: Internal Team Retrospective Notes

**Q:** Notes from sprint retrospective about team process improvements.

**Decision Tree:**
1. Is this public? NO
2. Would disclosure harm us? NO (process notes, no business info)

**Result:** P1 (Internal)
**Action:** Store in internal wiki, share with team only

---

### Example 4: Prompt Template for RAG

**Q:** Production prompt used in YARA Lógica RAG system.

**Decision Tree:**
1. Is this public? NO
2. Would disclosure harm us? YES
3. SEVERE harm? YES (core differentiator)

**Result:** **P3** (Trade Secret)
**Action:** Encrypted private repo, no screenshots, watermark if printed

---

## Marking Files

### File Headers

Add classification to file headers:

**P0 (Optional):**
```markdown
<!-- PUBLIC SPECIFICATION -->
```

**P1:**
```markdown
<!-- CLASSIFICATION: P1-Internal -->
<!-- DISTRIBUTION: Alter Agro Personnel Only -->
```

**P2:**
```markdown
# CLASSIFICATION: P2-Confidential
# OWNER: Alter Agro Ltda.
# DISTRIBUTION: Need-to-Know Only
# REVIEW DATE: 2026-01-01
```

**P3:**
```markdown
# CLASSIFICATION: P3-TRADE SECRET
# OWNER: Alter Agro Ltda.
# AUTHORIZED RECIPIENTS ONLY
# UNAUTHORIZED DISCLOSURE PROHIBITED
# REVIEW DATE: 2026-01-01
```

### Email Footers

**P2:**
```
CONFIDENTIAL: This email contains confidential information. Unauthorized disclosure prohibited.
```

**P3:**
```
TRADE SECRET: This email contains trade secret information of Alter Agro Ltda.
Unauthorized disclosure, copying, or use is strictly prohibited and may result in legal action.
```

---

## Reclassification

### Upgrading Classification

**If information needs higher protection:**

1. **Immediately** reclassify
2. Notify all current recipients
3. Apply new handling requirements
4. Retrieve/secure existing copies if possible

**Example:** Internal roadmap doc (P1) now includes customer commitments → Upgrade to P2

### Downgrading Classification

**If information can be less restricted:**

1. Submit request to Security Team
2. Provide business justification
3. Obtain approvals (see matrix below)
4. Update markings
5. Communicate change

**Approval Matrix:**

| Downgrade | Approval Required |
|:----------|:------------------|
| P3 → P2 | CTO + Legal |
| P2 → P1 | Manager + Security Team |
| P1 → P0 | Manager + Legal Review |

---

## FAQs

**Q: Can I share P1 info with contractors?**
A: Yes, if they've signed employment/contractor agreement and NDA.

**Q: What if I'm unsure between P2 and P3?**
A: Choose P3 (higher protection). Consult Security Team for guidance.

**Q: Can I demo production prompts in customer calls?**
A: No. Prompts are P3. Use sanitized examples or high-level descriptions.

**Q: Are Git commit messages classified?**
A: Yes! If in private repo, assume P2. Never include P3 data in commit messages.

**Q: Can I mention customer names in internal Slack?**
A: In private channels, yes (P2 handling). Not in public channels.

**Q: What about open-source dependencies?**
A: The dependencies themselves are P0, but our specific configurations may be P2.

**Q: How long must I protect P3 information after leaving?**
A: **Indefinitely.** Trade secret obligations are perpetual.

**Q: What if I accidentally commit P3 data to public repo?**
A: **Immediately** email security@alteragro.com.br. Do not attempt fix yourself.

**Q: Can I use customer logos in presentations?**
A: Only with explicit customer permission. Even with permission, classify deck as P2.

**Q: Are draft documents classified?**
A: Yes. Classify based on final intended content level.

---

## Contact for Classification Help

**Email:** [security@alteragro.com.br](mailto:security@alteragro.com.br)
**Subject:** `[CLASSIFICATION] <brief question>`

**Response time:** 24 hours (business days)

**For urgent questions:** Slack #security (internal)

---

**Last Updated:** 2025-11-04
**Next Review:** 2026-01-01 (annual)

**© 2025 Alter Agro Ltda.**
