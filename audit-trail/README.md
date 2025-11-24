# Audit Trail

**Purpose:** Immutable storage of LSA decision records and review artifacts.

All decision records in this directory are committed to Git, providing:
- **Immutability:** Git SHA ensures tamper-evident history
- **Traceability:** Every decision linked to sources (with SHA provenance)
- **Auditability:** Full history of decisions, reviews, and validations

---

## Directory Structure

```
audit-trail/
├── decisions/          # Decision records (JSON)
│   ├── 2025-11/        # Organized by year-month
│   │   ├── DEC-20251124-001.json
│   │   ├── DEC-20251124-002.json
│   │   └── ...
│   ├── 2025-12/
│   └── ...
├── reviews/            # Human review artifacts
│   ├── 2025-11/
│   └── ...
└── README.md           # This file
```

---

## Decision Records (`/decisions/`)

### File Naming Convention

`DEC-{YYYYMMDD}-{NNN}.json`

- **DEC:** Decision record prefix
- **YYYYMMDD:** Date (ISO 8601 format, no separators)
- **NNN:** Sequential number (001, 002, ...)

**Example:** `DEC-20251124-001.json`

### Schema

Decision records follow the **PICC-1.0** schema (Premise-Inference-Contradiction-Conclusion).

**Required Fields:**

```json
{
  "id": "DEC-20251124-001",
  "timestamp": "2025-11-24T10:30:00Z",
  "version": "PICC-1.0",
  "query": "Original user question",
  "domain": "carbon_markets",
  "premises": [...],
  "inferences": [...],
  "contradictions": [...],
  "conclusion": {...},
  "falsifier": {...},
  "metadata": {...}
}
```

See `/lsa/schema/decision-record.schema.json` for full schema.

### Storage Process

Decision records are created via **n8n Workflow 2** (YARA Lógica RAG-enabled):

1. User submits query
2. n8n calls RAG service for evidence
3. n8n builds LLM prompt (LARA + RTOA + domain rules)
4. LLM generates decision record (JSON)
5. n8n validates schema, calculates risk score
6. n8n commits decision record to `audit-trail/decisions/YYYY-MM/DEC-{timestamp}.json`
7. Git commit message: `LSA: DEC-{id} - {short summary}`

### Metadata

Every decision record includes:

```json
"metadata": {
  "git_commit": "ef23dbf...",        // Commit SHA of this decision
  "config_version": "abc123...",      // Git SHA of lsa-config.yaml used
  "domain_config_version": "def456...", // Git SHA of domain config
  "rag_chunks_used": 8,               // Number of RAG chunks cited
  "risk_level": "low",                // Risk assessment result
  "auto_approved": true,              // Auto-approved or human review required
  "review_status": "approved"         // If human review: pending/approved/rejected
}
```

---

## Human Reviews (`/reviews/`)

### When Reviews Are Created

Reviews are required for:
- **MEDIUM risk** decisions (per `lsa-config.yaml`)
- **HIGH risk** decisions
- **Domain-specific overrides** (e.g., methodology selection always requires review)

### Review Process

1. n8n creates **GitHub issue** with:
   - Title: `[LSA Review] DEC-{id}: {summary}`
   - Body: Decision record + RAG chunks + risk rationale
   - Labels: `lsa`, `needs-review`, `risk-{level}`, `domain-{name}`

2. Domain expert reviews:
   - Validates premises (sources correct, citations accurate)
   - Validates inferences (logical steps sound)
   - Validates contradictions (opposing evidence considered)
   - Validates conclusion (confidence justified)
   - Validates falsifier (measurable, time-bound)

3. Expert adds comment on GitHub issue:
   - **APPROVED:** Decision is sound, proceed
   - **APPROVED WITH CONDITIONS:** Decision sound, but add caveats
   - **REJECTED:** Decision flawed, re-analyze with new evidence

4. n8n updates decision record metadata:
   ```json
   "metadata": {
     "review_status": "approved",
     "reviewed_by": "jane.doe@alteragro.com",
     "reviewed_at": "2025-11-24T15:30:00Z",
     "review_comments": "Validated VM0047 eligibility. Recommend emphasizing C2 in PDD."
   }
   ```

5. Review artifact stored in `audit-trail/reviews/YYYY-MM/REVIEW-{id}.json`

### Review Artifact Schema

```json
{
  "review_id": "REVIEW-20251124-001",
  "decision_id": "DEC-20251124-001",
  "reviewed_by": "jane.doe@alteragro.com",
  "reviewed_at": "2025-11-24T15:30:00Z",
  "status": "approved",
  "comments": "Validated methodology selection. Recommend highlighting contradiction C2 in PDD.",
  "evidence_checked": true,
  "logic_validated": true,
  "falsifier_appropriate": true,
  "github_issue": "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues/123"
}
```

---

## Falsifier Validation

### Periodic Checks

A **cron job** (n8n or external) runs periodically (default: quarterly) to check falsifiers:

1. Fetch all decision records from `audit-trail/decisions/`
2. For each decision with `falsifier.by` date in the past:
   - Fetch metric (external system or manual input)
   - Compare to threshold
   - If threshold exceeded: **falsifier triggered**

3. If falsifier triggered:
   - Create GitHub issue: `[FALSIFIER TRIGGERED] DEC-{id}`
   - Notify team (Slack/email)
   - Mark decision as **invalidated** in metadata
   - Trigger remediation workflow

### Example Falsifier Check

**Decision:** DEC-20251124-001 recommends VM0047.

**Falsifier:**
- Metric: Auditor non-conformances on methodology selection
- Threshold: >0
- By: 2026-06-01

**Check (2026-06-15):**
- Auditor report received 2026-06-10
- Non-conformances: 0 (methodology selection validated)
- **Result:** Falsifier NOT triggered, decision validated ✅

**Update decision record:**
```json
"metadata": {
  "falsifier_checked": true,
  "falsifier_check_date": "2026-06-15",
  "falsifier_triggered": false,
  "falsifier_result": "Auditor validated methodology selection (0 NCs). Decision confirmed."
}
```

---

## Querying Decision Records

### Search by Domain

```bash
# Find all carbon markets decisions
grep -r '"domain": "carbon_markets"' audit-trail/decisions/
```

### Search by Confidence

```bash
# Find all HIGH confidence decisions
grep -r '"confidence": "HIGH"' audit-trail/decisions/
```

### Search by Risk Level

```bash
# Find all decisions requiring human review
grep -r '"auto_approved": false' audit-trail/decisions/
```

### Export to CSV

Use the LSA export script:

```bash
./lsa/scripts/export-records.sh --format csv --output audit-trail-export.csv
```

---

## Integrity Verification

### Hash Validation

Every decision record has a canonical SHA-256 hash (computed from sorted JSON, no whitespace).

**Verify integrity:**

```bash
# Compute current hash
jq -S -c . audit-trail/decisions/2025-11/DEC-20251124-001.json | sha256sum

# Compare to Git SHA
git log --format="%H" --all -- audit-trail/decisions/2025-11/DEC-20251124-001.json
```

If hashes don't match → file tampered (investigate).

### Schema Validation

Validate all records against schema:

```bash
./lsa/scripts/verify-records.sh
```

This checks:
- JSON syntax validity
- PICC-1.0 schema compliance
- Evidence source URLs accessibility
- Falsifier criteria completeness

---

## Retention Policy

**Minimum Retention:** 7 years (per audit standards)

**Maximum Retention:** Indefinite (Git history preserved)

**Deletion:** Decision records are NEVER deleted from Git history. If a decision is superseded or invalidated, add metadata:

```json
"metadata": {
  "status": "superseded",
  "superseded_by": "DEC-20260115-045",
  "superseded_reason": "New evidence invalidated P2; re-analyzed with updated methodology."
}
```

---

## Security & Compliance

### Data Classification

- **Internal (P1):** Decision records for internal projects
- **Confidential (P2):** Decision records with business-sensitive data (use private repo)

### Access Control

- **Read:** Alter Agro team + approved auditors
- **Write:** Automated (n8n workflows) + Technical lead only
- **Modify:** NEVER (except via Git with audit trail)

### Encryption

- **At rest:** GitHub default encryption
- **In transit:** HTTPS (Git + API calls)

---

## Troubleshooting

### Issue: Decision record not committed

**Cause:** n8n workflow error, GitHub API failure

**Solution:**
1. Check n8n execution log
2. Verify GitHub credentials in n8n
3. Manually commit if needed: `git add audit-trail/decisions/... && git commit -m "LSA: Manual commit DEC-{id}"`

### Issue: Invalid JSON

**Cause:** LLM generated malformed JSON

**Solution:**
1. Check LLM output in n8n logs
2. Fix JSON manually (if minor error)
3. If systematic: adjust LLM prompt to emphasize JSON validity

### Issue: Falsifier never checked

**Cause:** Cron job not running

**Solution:**
1. Verify cron job schedule
2. Manually run falsifier check script
3. Update decision record metadata

---

## Support

**Questions:** See [THREE_LAYER_ARCHITECTURE.md](/docs/THREE_LAYER_ARCHITECTURE.md)
**Issues:** Create GitHub issue with label `audit-trail`
**Contact:** contatoalteragro@gmail.com

---

**Last Updated:** 2025-11-24
**Maintained By:** Alter Agro Technical Team

© 2025 Alter Agro Ltda. All rights reserved.
