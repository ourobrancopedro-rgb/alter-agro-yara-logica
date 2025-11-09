# LSA Decision Record System

## Overview

The **Logic Sorting Architecture (LSA)** decision record system provides audit-grade documentation and immutable tracking of critical decisions made within the YARA Lógica framework. This system implements a **premise-inference-contradiction-conclusion (PICC)** methodology with cryptographic hashing for tamper-proof decision governance.

## Architecture

The LSA system integrates with GitHub Issues to create an **immutable audit trail** through:

1. **Structured Decision Records** — PICC-compliant JSON documents with cryptographic hashes
2. **n8n Workflow Automation** — Automated notarization pipeline with HMAC authentication
3. **GitHub Issue Storage** — Immutable, version-controlled record repository
4. **Schema Validation** — JSON schema enforcement with evidence requirements
5. **Audit Trail Verification** — Cryptographic hash validation and integrity checks

## Directory Structure

```
lsa/
├── records/           # Decision record storage (JSON files)
├── workflows/         # n8n workflow exports and configurations
├── docs/              # LSA methodology and audit documentation
├── schema/            # JSON schema validation files
└── scripts/           # Maintenance and verification utilities
```

## Core Methodology: PICC Framework

Every LSA decision record follows the **Premise-Inference-Contradiction-Conclusion** structure:

### 1. **Premises** (P1, P2, P3...)
Foundation facts, assumptions, or expert opinions supporting the decision.

**Types:**
- **FACT** — Evidence-backed statements (requires ≥2 HTTPS sources)
- **ASSUMPTION** — Working hypotheses with explicit uncertainty
- **EXPERT_OPINION** — Authoritative but non-empirical inputs

### 2. **Inferences** (I1, I2, I3...)
Logical deductions derived from premises.

### 3. **Contradictions** (C1, C2, C3...)
Opposing evidence, limitations, or conflicting information that challenges the decision.

### 4. **Conclusion**
Final decision statement with explicit confidence level (LOW, MEDIUM, HIGH).

### 5. **Falsifier** (Popperian Validation)
Measurable criteria that would invalidate the decision if met:
- **Metric** — What to measure (e.g., "Auditor_NCs")
- **Threshold** — Falsification trigger (e.g., ">0")
- **By** — Evaluation deadline (ISO-8601 date)
- **Action** — Remediation steps if falsified

## Workflow Integration

### Automated Notarization Pipeline (n8n)

The LSA system uses an **n8n workflow** to automate decision record creation:

1. **Webhook Trigger** — Receives HMAC-authenticated decision payloads
2. **Schema Validation** — Validates PICC-1.0 compliance
3. **Canonical Hashing** — Generates SHA-256 hash for idempotency
4. **GitHub Issue Creation** — Creates immutable issue record
5. **Label Taxonomy** — Applies structured labels for categorization and search

**Key Features:**
- HMAC-SHA256 authentication (X-Signature-256 header)
- Timestamp window validation (±300s, replay protection)
- Idempotency via hash-based deduplication
- Automatic GitHub label application
- Audit trail with canonical JSON hashing

See [`/lsa/workflows/SETUP.md`](workflows/SETUP.md) for installation instructions.

## Audit-Grade Integrity

### Cryptographic Hashing
Every decision record is hashed using **SHA-256 canonical JSON** to ensure:
- **Immutability** — Any change produces a different hash
- **Idempotency** — Duplicate submissions are detected via hash labels
- **Traceability** — Hash-to-record mapping enables verification

### GitHub Integration Benefits
- **Version Control** — Full history of decision evolution via issue edits
- **Access Control** — GitHub permissions enforce who can create/modify records
- **Audit Trail** — Timestamped, signed commits with author attribution
- **Search & Discovery** — Label taxonomy enables advanced filtering

## Confidence Levels

| Level | Criteria | Use Case |
|:------|:---------|:---------|
| **LOW** | Incomplete evidence, high uncertainty | Exploratory decisions, early-stage hypotheses |
| **MEDIUM** | Partial evidence, some contradictions | Standard operational decisions |
| **HIGH** | Strong evidence, minimal contradictions | Critical governance decisions, compliance requirements |

## Usage

### Creating Decision Records

**Manual Creation:**
1. Use the [GitHub issue template](../.github/ISSUE_TEMPLATE/lsa-decision-record.md)
2. Fill in PICC structure (premises, inferences, contradictions, conclusion)
3. Add appropriate labels (lsa, decision-record, confidence level)

**Automated Creation (n8n):**
1. Configure n8n workflow (see [SETUP.md](workflows/SETUP.md))
2. Submit PICC-compliant JSON via webhook
3. System validates, hashes, and creates GitHub issue automatically

### Validating Records

```bash
# Validate all decision records against schema
./lsa/scripts/verify-records.sh

# Export records to CSV/HTML
./lsa/scripts/export-records.sh --format csv
```

## Label Taxonomy

| Label | Purpose |
|:------|:--------|
| `lsa` | Identifies LSA decision records |
| `decision-record` | Audit-grade decision documentation |
| `high-confidence` | HIGH confidence level decisions |
| `medium-confidence` | MEDIUM confidence level decisions |
| `low-confidence` | LOW confidence level decisions |
| `needs-review` | Requires human validation |
| `hash:<hash16>` | First 16 chars of SHA-256 (idempotency) |

## Evidence Requirements

### FACT Premises
- Minimum **2 HTTPS URLs** per FACT premise
- Sources must be publicly accessible
- Prefer authoritative sources (government, academic, industry standards)

### Evidence Quality Guidelines
- **Government/Regulatory** — Highest authority (laws, regulations, official guidance)
- **Academic** — Peer-reviewed research, institutional publications
- **Industry Standards** — ISO, ASTM, technical specifications
- **Technical Documentation** — Vendor docs, API references, whitepapers

## Maintenance & Operations

### Verification Scripts
- **verify-records.sh** — Schema compliance + hash integrity checks
- **export-records.sh** — Generate reports (CSV, HTML, Markdown)

### GitHub Actions Integration
Automated validation runs on every push:
- JSON schema compliance check
- Hash integrity verification
- Label taxonomy validation
- Evidence URL accessibility checks

## Security & Compliance

### Data Classification
- Decision records: **P0 - Public** (specifications only)
- No secrets, credentials, or PII permitted
- Business-sensitive decisions stored in private repositories

### Integrity Policy
- All decision records must pass schema validation
- Hash mismatches trigger automated alerts
- Manual edits require re-hashing and audit justification

## Documentation

- [Workflow Setup Guide](workflows/SETUP.md) — n8n installation and configuration
- [Audit Trail Methodology](docs/AUDIT-TRAIL.md) — Cryptographic verification procedures
- [JSON Schema](schema/decision-record.schema.json) — Validation rules
- [Decision Record Examples](../docs/DECISION_RECORD_EXAMPLES.json) — Sample records

## Support & Contact

**Questions:** See repository [README.md](../README.md)
**Security Issues:** [contatoalteragro@gmail.com](mailto:contatoalteragro@gmail.com)
**Contributing:** Follow [.github/CONTRIBUTING.md](../.github/CONTRIBUTING.md)

---

**© 2025 Alter Agro Ltda. All rights reserved.**
_LSA Decision Record System — Part of the YARA Lógica Compliance Suite_
