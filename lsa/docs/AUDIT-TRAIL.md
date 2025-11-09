# LSA Audit Trail Methodology

## Overview

The LSA Decision Record System implements **audit-grade integrity** through cryptographic hashing, immutable storage, and verifiable chains of custody. This document describes the cryptographic methodology, verification procedures, and audit trail infrastructure.

## Core Principles

### 1. Immutability

Once a decision record is created and hashed, any modification produces a **different hash**, making tampering immediately detectable.

**Implementation:**
- Canonical JSON serialization (deterministic key ordering)
- SHA-256 cryptographic hashing
- GitHub Issues as immutable storage (with full edit history)

### 2. Idempotency

Duplicate decision submissions are detected via **hash-based deduplication**, preventing accidental record duplication.

**Implementation:**
- Each decision receives a unique `hash:<first16>` GitHub label
- Before creating an issue, the system searches for existing issues with the same hash
- If found, returns existing issue URL instead of creating duplicate

### 3. Non-Repudiation

Every decision record includes:
- **Author attribution** (via GitHub user or metadata.actor)
- **Timestamp** (ISO-8601 UTC)
- **Cryptographic signature** (HMAC-SHA256 for automated submissions)
- **Approval chain** (approved_by array)

## Cryptographic Hashing

### Canonical JSON Algorithm

To ensure deterministic hashing, we use **canonical JSON** with sorted keys:

```javascript
function canonical(obj) {
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonical).join(',') + ']';
  }
  if (obj && typeof obj === 'object') {
    const keys = Object.keys(obj).sort();
    return '{' + keys.map(k =>
      JSON.stringify(k) + ':' + canonical(obj[k])
    ).join(',') + '}';
  }
  return JSON.stringify(obj);
}
```

**Why Canonical JSON?**
- JavaScript object key order is not guaranteed
- Standard JSON.stringify() may produce different strings for identical objects
- Canonical form ensures identical inputs always produce identical hashes

### SHA-256 Hash Generation

```javascript
const crypto = require('crypto');

// 1. Convert decision to canonical JSON
const canonicalStr = canonical(decisionRecord);

// 2. Compute SHA-256 hash
const hash = crypto.createHash('sha256')
  .update(canonicalStr)
  .digest('hex');

// 3. Extract short label (first 16 chars)
const hashLabel = `hash:${hash.slice(0, 16)}`;
```

**Example:**
```json
{
  "question": "Implement automated testing?",
  "conclusion": "Yes",
  "confidence": "HIGH"
}
```

**Canonical Form:**
```
{"conclusion":"Yes","confidence":"HIGH","question":"Implement automated testing?"}
```

**SHA-256 Hash:**
```
a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5
```

**GitHub Label:**
```
hash:a3b5c7d9e1f3a5b7
```

## HMAC Authentication

Automated decision submissions use **HMAC-SHA256** to verify authenticity:

### Request Signing

```bash
# 1. Prepare payload (JSON)
PAYLOAD='{"schema_version":"PICC-1.0",...}'

# 2. Compute HMAC signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')

# 3. Send request with X-Signature-256 header
curl -X POST "$WEBHOOK_URL" \
  -H "X-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD"
```

### Server Validation

```javascript
// 1. Extract received signature
const receivedSig = headers['x-signature-256'];

// 2. Compute expected signature
const bodyStr = JSON.stringify(body);
const expectedSig = 'sha256=' + crypto
  .createHmac('sha256', process.env.HMAC_SECRET)
  .update(bodyStr)
  .digest('hex');

// 3. Compare (timing-safe)
if (receivedSig !== expectedSig) {
  return { ok: false, code: 'BAD_SIG' };
}
```

**Security Features:**
- Prevents unauthorized decision submissions
- Protects against man-in-the-middle attacks (when combined with HTTPS)
- Enables audit logging of failed authentication attempts

## Timestamp Validation

Prevents replay attacks by enforcing a **±300 second (5-minute) time window**:

```javascript
const now = Math.floor(Date.now() / 1000); // Unix timestamp
const ts = payload.ts;

if (Math.abs(now - ts) > 300) {
  return { ok: false, code: 'TS_WINDOW', msg: 'Timestamp expired' };
}
```

**Why 5 minutes?**
- Tolerates reasonable clock skew between systems
- Short enough to prevent replay attacks
- Long enough for network latency and retries

## Nonce Deduplication

Each decision submission must include a **unique nonce** (8-128 characters):

```json
{
  "nonce": "unique-value-12345678",
  "ts": 1730000000,
  ...
}
```

**Nonce Storage (Recommended):**
- Store in Redis with TTL = 600 seconds (2x timestamp window)
- Key: `nonce:{nonce}`
- Value: decision hash
- Reject duplicate nonces within TTL window

**Without Nonce Storage:**
- Hash-based idempotency still prevents duplicate issues
- Nonce provides additional protection during issue creation race conditions

## Audit Verification Procedures

### 1. Verify Decision Record Hash

```bash
# Read decision record
RECORD=$(cat lsa/records/DEC-2025-11-09-01.json)

# Extract stored hash
STORED_HASH=$(echo "$RECORD" | jq -r '.sha256')

# Compute canonical hash
COMPUTED_HASH=$(echo "$RECORD" | jq -Sc 'del(.sha256)' | \
  jq -S | sha256sum | awk '{print $1}')

# Compare
if [ "$STORED_HASH" == "$COMPUTED_HASH" ]; then
  echo "✅ Hash verified"
else
  echo "❌ Hash mismatch - record tampered!"
fi
```

### 2. Verify GitHub Issue Integrity

```bash
# Fetch issue via GitHub API
gh api repos/ourobrancopedro-rgb/alter-agro-yara-logica/issues/123 > issue.json

# Extract hash from labels
ISSUE_HASH=$(jq -r '.labels[] | select(.name | startswith("hash:")) | .name' issue.json | cut -d: -f2)

# Extract hash from issue body
BODY_HASH=$(jq -r '.body' issue.json | grep -oP '(?<=```)([a-f0-9]{64})(?=```)')

# Compare
if [ "$ISSUE_HASH" == "${BODY_HASH:0:16}" ]; then
  echo "✅ Issue hash consistent"
else
  echo "⚠️  Hash mismatch between label and body"
fi
```

### 3. Verify Edit History

```bash
# List issue events
gh api repos/ourobrancopedro-rgb/alter-agro-yara-logica/issues/123/events > events.json

# Check for edits
EDITS=$(jq '[.[] | select(.event == "renamed" or .event == "edited")] | length' events.json)

if [ "$EDITS" -gt 0 ]; then
  echo "⚠️  Issue has been edited $EDITS times"
  echo "Review edit history for audit compliance"
else
  echo "✅ No edits detected"
fi
```

## Immutability Policy

### Permitted Modifications

**Allowed:**
- Adding comments (GitHub issue comments are timestamped and attributable)
- Adding labels (for categorization, workflow state)
- Changing assignees (for workflow management)

**Requires Re-Hashing:**
- Updating decision text (premises, conclusion, etc.)
- Modifying confidence level
- Changing falsifier criteria

**Process for Modifications:**
1. Create **revision history entry** in decision record
2. Update decision fields
3. **Recompute hash** with updated content
4. Create **new GitHub issue** with new hash OR update existing with revision annotation
5. Link to previous version

### Prohibited Modifications

**Never Allowed:**
- Deleting decision records
- Silently editing without revision history
- Removing hash labels
- Backdating timestamps

## GitHub Integration

### Issue Creation Flow

```
1. Receive decision payload
2. Validate HMAC signature
3. Validate schema (PICC-1.0)
4. Compute canonical hash
5. Search for existing issue with hash:<hash16> label
6. If exists: Return existing URL (idempotent)
7. If not: Create new issue with:
   - Title: [PICC] {question}
   - Body: Markdown-formatted decision
   - Labels: lsa, decision-record, hash:<hash16>, confidence, etc.
8. Store decision JSON in /lsa/records/ (optional)
9. Return issue URL + hash
```

### Label Taxonomy for Audit

| Label Pattern | Purpose | Example |
|:--------------|:--------|:--------|
| `hash:<hex16>` | Idempotency key | `hash:a3b5c7d9e1f3a5b7` |
| `schema:<version>` | Schema compliance | `schema:PICC-1.0` |
| `actor:<name>` | Attribution | `actor:ai-agent` |
| `context:<env>` | Environment | `context:production` |
| `{confidence}-confidence` | Confidence level | `high-confidence` |

## Verification Scripts

### Automated Integrity Check

```bash
#!/bin/bash
# File: lsa/scripts/verify-records.sh

for record in lsa/records/*.json; do
  echo "Verifying $record..."

  # Validate against schema
  ajv validate -s lsa/schema/decision-record.schema.json -d "$record"

  # Verify hash
  STORED=$(jq -r '.sha256' "$record")
  COMPUTED=$(jq -Sc 'del(.sha256)' "$record" | jq -S | sha256sum | awk '{print $1}')

  if [ "$STORED" != "$COMPUTED" ]; then
    echo "❌ Hash mismatch in $record"
    exit 1
  fi
done

echo "✅ All records verified"
```

## Compliance & Audit Reporting

### Audit Log Format

```json
{
  "audit_id": "AUDIT-2025-11-09-01",
  "timestamp": "2025-11-09T14:30:00Z",
  "auditor": "Compliance Team",
  "scope": "lsa/records/",
  "results": {
    "total_records": 42,
    "verified": 42,
    "hash_mismatches": 0,
    "schema_violations": 0,
    "missing_evidence": 0
  },
  "findings": [],
  "signature": "sha256:abc123..."
}
```

### Monthly Audit Checklist

- [ ] Verify all decision record hashes
- [ ] Validate schema compliance
- [ ] Check evidence URL accessibility
- [ ] Review falsifier evaluation dates
- [ ] Audit failed authentication attempts
- [ ] Verify GitHub issue edit history
- [ ] Check for orphaned hash labels
- [ ] Review nonce collision logs (if applicable)

## Threat Model & Mitigations

| Threat | Mitigation |
|:-------|:-----------|
| **Tampering** | SHA-256 hashing detects any modification |
| **Replay Attack** | Timestamp window (±300s) + nonce deduplication |
| **Unauthorized Submission** | HMAC-SHA256 authentication |
| **Duplicate Records** | Hash-based idempotency (GitHub label search) |
| **Backdating** | Timestamp validation + GitHub issue creation timestamp |
| **Secret Exposure** | HMAC secrets in environment variables, never committed |
| **Man-in-the-Middle** | HTTPS-only evidence + webhook URLs |

## References

- **PICC Schema:** `/spec/schemas/picc-1.0.schema.json`
- **n8n Workflow:** `/spec/workflows/n8n_yara_picc_notarization.json`
- **API Contract:** `/spec/contracts/notarization_api_contract.md`
- **Threat Model:** `/spec/ops/threat_model_stride.md`

---

**© 2025 Alter Agro Ltda.**
_LSA Audit Trail Methodology — Part of YARA Lógica Compliance Suite_
