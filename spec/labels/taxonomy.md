# YARA Lógica PICC Notarization Label Taxonomy

**Version:** 1.0
**Last Updated:** 2025-01-05
**Purpose:** GitHub Issue label schema for decision records

---

## Overview

YARA Lógica PICC decisions are stored as **GitHub Issues** with structured labels for:
- **Classification:** Categorize by system, schema, and type
- **Idempotency:** Detect duplicate submissions via hash labels
- **Audit Trail:** Track decision context, actors, and lifecycle
- **Operational Status:** Manage DLQ, resolution, and retries

---

## Label Categories

### 1. Required Labels

These labels are **automatically applied** to all PICC decision issues:

| Label | Format | Description | Example |
|:------|:-------|:------------|:--------|
| `yara-logica` | Fixed | System identifier (all YARA Lógica decisions) | `yara-logica` |
| `picc` | Fixed | Decision type (PICC = Premise-Inference-Contradiction-Conclusion) | `picc` |
| `hash:<first16>` | Dynamic | First 16 chars of SHA-256 canonical hash (idempotency) | `hash:a1b2c3d4e5f6g7h8` |

**Idempotency Mechanism:**
- Canonical JSON → SHA-256 → Take first 16 hex chars
- Before creating issue: Search for `label:hash:<first16>`
- If found → Return existing issue (idempotent response)
- If not found → Create new issue with hash label

**Collision Probability:**
- 16 hex chars = 64 bits
- Birthday attack: ~50% collision at 2^32 ≈ 4 billion decisions
- Acceptable risk for initial deployment
- Monitor collision rate; upgrade to 20-24 chars if needed

---

### 2. Optional Schema/Metadata Labels

Applied if present in the decision payload:

| Label | Format | Description | Example |
|:------|:-------|:------------|:--------|
| `schema:PICC-1.0` | `schema:<version>` | Schema version for future compatibility | `schema:PICC-1.0` |
| `actor:<id>` | `actor:<actor_id>` | Decision submitter (from `metadata.actor`) | `actor:climate-analyst-42` |
| `context:<tag>` | `context:<context_id>` | Decision context (from `metadata.context`) | `context:carbon-offset` |

**Usage:**
- **Schema versioning:** Filter decisions by schema version (e.g., find all PICC-2.0 decisions)
- **Actor tracking:** Audit which actors submitted decisions
- **Context grouping:** Group related decisions (e.g., all decisions for a specific project)

**Example Queries:**
```bash
# All decisions by actor "climate-analyst-42"
gh issue list --label "actor:climate-analyst-42" --label "picc"

# All decisions in context "carbon-offset"
gh issue list --label "context:carbon-offset" --label "yara-logica"

# All PICC-1.0 decisions
gh issue list --label "schema:PICC-1.0"
```

---

### 3. Operational Status Labels

Used for workflow management and error handling:

| Label | Description | Applied By | Example Use Case |
|:------|:------------|:-----------|:-----------------|
| `dlq` | Dead Letter Queue (issue creation failed) | n8n workflow | GitHub API quota exhausted, network failure |
| `resolved` | DLQ item successfully reprocessed | Manual/automated reprocessor | After retry succeeds, remove `dlq`, add `resolved` |
| `duplicate` | Manual duplicate detection (not caught by hash) | Human auditor | Two decisions with same content but different metadata |
| `invalid` | Schema validation failed post-creation | Auditor | Schema evolved, old decision no longer valid |
| `archived` | Decision archived for compliance | Automated archival job | Decisions older than 7 years (retention policy) |

**DLQ Workflow:**
1. n8n workflow fails to create issue (GitHub API error)
2. Workflow logs error and adds payload to DLQ (external queue or issue)
3. DLQ monitoring alerts on-call engineer
4. Engineer triggers reprocessor (manual or cron)
5. Reprocessor submits payload to webhook again
6. On success: Label original DLQ entry as `resolved`

**Example Queries:**
```bash
# List all DLQ items needing reprocessing
gh issue list --label dlq --label yara-logica

# List all resolved DLQ items
gh issue list --label resolved --label dlq

# Count invalid decisions
gh issue list --label invalid --label picc --json number | jq length
```

---

## Label Color Scheme

**Recommended GitHub Label Colors:**

| Label Pattern | Color (Hex) | Visual Group |
|:--------------|:------------|:-------------|
| `yara-logica` | `#0E8A16` | Green (system) |
| `picc` | `#1D76DB` | Blue (type) |
| `hash:*` | `#FBCA04` | Yellow (idempotency) |
| `schema:*` | `#D876E3` | Purple (metadata) |
| `actor:*` | `#C5DEF5` | Light blue (metadata) |
| `context:*` | `#BFD4F2` | Light blue (metadata) |
| `dlq` | `#D93F0B` | Red (operational) |
| `resolved` | `#0E8A16` | Green (operational) |
| `duplicate` | `#EDEDED` | Gray (audit) |
| `invalid` | `#B60205` | Dark red (audit) |
| `archived` | `#CCCCCC` | Light gray (lifecycle) |

**Setup Script (GitHub CLI):**
```bash
#!/bin/bash
# create_labels.sh - Setup labels for YARA Lógica PICC repo

REPO="<ORG>/<REPO>"

# Required labels
gh label create "yara-logica" --color "0E8A16" --description "YARA Lógica system" --repo "$REPO"
gh label create "picc" --color "1D76DB" --description "PICC decision type" --repo "$REPO"

# Operational labels
gh label create "dlq" --color "D93F0B" --description "Dead Letter Queue (failed creation)" --repo "$REPO"
gh label create "resolved" --color "0E8A16" --description "DLQ item reprocessed successfully" --repo "$REPO"
gh label create "duplicate" --color "EDEDED" --description "Duplicate decision (manual detection)" --repo "$REPO"
gh label create "invalid" --color "B60205" --description "Schema validation failed" --repo "$REPO"
gh label create "archived" --color "CCCCCC" --description "Archived decision (retention policy)" --repo "$REPO"

echo "Labels created successfully. Schema/metadata/hash labels are created dynamically."
```

---

## Label Queries & Search Patterns

### Idempotency Check (Automated)

**n8n Workflow Node:**
```javascript
// Search for existing issue with same hash
const hashLabel = `hash:${hash.substring(0, 16)}`;

const searchResults = await githubApi.searchIssues({
  owner: process.env.GITHUB_OWNER,
  repo: process.env.GITHUB_REPO,
  q: `label:${hashLabel} label:picc is:issue`
});

if (searchResults.total_count > 0) {
  // Idempotent: decision already exists
  return {
    ok: true,
    code: 'IDEMPOTENT',
    issue_url: searchResults.items[0].html_url,
    issue_number: searchResults.items[0].number
  };
}
```

**GitHub CLI Equivalent:**
```bash
# Check if decision with hash "a1b2c3d4e5f6g7h8" exists
gh issue list --label "hash:a1b2c3d4e5f6g7h8" --label "picc" --json number,url
```

---

### Audit Queries

**All decisions by schema version:**
```bash
gh issue list --label "schema:PICC-1.0" --label "yara-logica" --state all
```

**Decisions submitted in last 24 hours:**
```bash
gh issue list --label "yara-logica" --created "$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)"
```

**Decisions by specific actor:**
```bash
gh issue list --label "actor:climate-analyst-42" --label "picc" --json number,title,createdAt
```

**Decisions in specific context:**
```bash
gh issue list --label "context:carbon-offset" --label "yara-logica"
```

**Collision detection (multiple issues with same hash):**
```bash
# Find all hash labels
gh issue list --label "yara-logica" --state all --json labels \
  | jq -r '.[].labels[] | select(.name | startswith("hash:")) | .name' \
  | sort | uniq -d

# If output is non-empty → collision detected
```

---

### Operational Queries

**DLQ backlog:**
```bash
gh issue list --label dlq --label yara-logica --json number,title,createdAt,labels
```

**Reprocessed DLQ items (audit):**
```bash
gh issue list --label resolved --label dlq --state all
```

**Invalid decisions (schema compliance audit):**
```bash
gh issue list --label invalid --label picc --json number,title,url
```

**Archived decisions (retention compliance):**
```bash
gh issue list --label archived --state closed --json number,closedAt
```

---

## Label Best Practices

### DO:
✅ Use consistent casing (lowercase for label names)
✅ Apply required labels (`yara-logica`, `picc`, `hash:*`) to all decisions
✅ Include schema version for forward compatibility
✅ Use actor/context labels for audit trails
✅ Monitor DLQ labels daily
✅ Archive old issues periodically (>7 years)

### DON'T:
❌ Manually edit hash labels (breaks idempotency)
❌ Reuse hash labels across different decisions
❌ Delete labels without archival (breaks audit trail)
❌ Create custom labels outside taxonomy (use issue comments instead)
❌ Use PII in actor/context labels (hash or anonymize)

---

## Schema Evolution

### Adding New Label Types (Non-Breaking)

**Example: Add `priority` label**

1. Document new label in taxonomy:
   - Format: `priority:<level>` (e.g., `priority:high`)
   - Description: Decision priority (optional)
   - Color: `#FF6B6B` (red for high, etc.)

2. Update n8n workflow to apply label if present in payload

3. Add to payload schema (optional field):
   ```json
   {
     "metadata": {
       "priority": "high"
     }
   }
   ```

4. No migration needed (backward compatible)

### Removing Label Types (Breaking)

**Example: Deprecate `actor` label**

1. Announce deprecation (90-day notice)
2. Update workflow to stop applying label
3. Keep existing labels intact (audit trail)
4. After 90 days, optionally bulk-remove from old issues:
   ```bash
   gh issue list --label "actor:*" --json number | jq -r '.[].number' \
     | xargs -I{} gh issue edit {} --remove-label "actor:*"
   ```

---

## Label Monitoring & Alerts

### Metrics to Track

| Metric | Query | Threshold | Alert |
|:-------|:------|:----------|:------|
| Total PICC decisions | `gh issue list --label picc \| wc -l` | N/A | Informational |
| DLQ depth | `gh issue list --label dlq \| wc -l` | >10 | Warning |
| Hash collisions | Collision detection script | >0 | Critical |
| Invalid decisions | `gh issue list --label invalid \| wc -l` | >5 | Warning |
| Unresolved DLQ (>7 days) | Custom query | >3 | Warning |

### Automated Monitoring (GitHub Actions)

```yaml
# .github/workflows/label-monitoring.yml
name: Label Monitoring

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Check DLQ depth
        run: |
          DLQ_COUNT=$(gh issue list --label dlq --json number | jq length)
          if [ "$DLQ_COUNT" -gt 10 ]; then
            echo "::error::DLQ depth is $DLQ_COUNT (threshold: 10)"
            # Send alert (Slack, PagerDuty, etc.)
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Check for hash collisions
        run: |
          # Collision detection script
          COLLISIONS=$(gh issue list --label yara-logica --state all --json labels \
            | jq -r '.[].labels[] | select(.name | startswith("hash:")) | .name' \
            | sort | uniq -d | wc -l)
          if [ "$COLLISIONS" -gt 0 ]; then
            echo "::error::Hash collision detected!"
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Example Decision Issue

**Title:**
```
[PICC] Should we adopt regenerative agriculture practices?
```

**Labels:**
```
yara-logica
picc
hash:a1b2c3d4e5f6g7h8
schema:PICC-1.0
actor:climate-analyst-42
context:carbon-offset
```

**Body:**
```markdown
## Decision Record

**Question:** Should we adopt regenerative agriculture practices?

**Conclusion:** Yes, based on carbon sequestration evidence

**Confidence:** HIGH

---

## Premises

### FACT
Regenerative agriculture increases soil carbon by 0.5-1.5 tC/ha/yr
**Evidence:**
- https://doi.org/10.1038/s41558-020-0738-9
- https://www.sciencedirect.com/science/article/pii/S0167880920301584

### ASSUMPTION
Farmers will adopt practices if economically viable

---

## Inferences
- Carbon markets can provide economic incentive
- Policy support accelerates adoption

## Contradictions
- Initial costs may deter small farmers

## Falsifier
If peer-reviewed studies show no carbon benefit, conclusion is invalid

---

## Metadata

- **Actor:** climate-analyst-42
- **Context:** carbon-offset
- **Timestamp:** 1730820000 (2024-11-05T10:00:00Z)
- **Nonce:** unique-nonce-12345
- **Schema:** PICC-1.0

---

## Hash

```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

**Canonical JSON:**
```json
{"decision":{...},"metadata":{...},"nonce":"unique-nonce-12345","schema_version":"PICC-1.0","ts":1730820000}
```
```

**GitHub Search:**
```bash
gh issue view <issue_number>
# Or search by hash
gh issue list --label "hash:a1b2c3d4e5f6g7h8"
```

---

## References

- **API Contract:** `/spec/contracts/notarization_api_contract.md`
- **JSON Schema:** `/spec/schemas/picc-1.0.schema.json`
- **n8n Workflow:** `/spec/workflows/n8n_yara_picc_notarization.json`
- **Runbook:** `/spec/ops/runbook_notarization.md`

---

**Taxonomy Maintained by:** Alter Agro Data Governance Team
**Next Review:** 2025-04-01
**Schema Evolution Log:** None (initial version)
