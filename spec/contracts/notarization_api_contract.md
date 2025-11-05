# YARA Lógica PICC Notarization API Contract

**Version:** 1.0
**Schema:** PICC-1.0
**Protocol:** HTTPS only
**Authentication:** HMAC-SHA256

---

## Endpoint

```
POST /webhook/yara/picc/notarize
```

**Base URL:** Configured in n8n webhook (production endpoint set at deployment time)

---

## Request Format

### Headers

| Header | Required | Description |
|:-------|:---------|:------------|
| `Content-Type` | Yes | Must be `application/json` |
| `X-Signature-256` | Yes | HMAC signature: `sha256=<hex(HMAC-SHA256(body, secret))>` |

### Body

JSON payload conforming to **PICC-1.0 schema** (see `/spec/schemas/picc-1.0.schema.json`).

**Required fields:**
- `schema_version`: Must be `"PICC-1.0"`
- `ts`: Unix timestamp (integer, seconds since epoch)
- `nonce`: Unique string (8-128 characters)
- `decision`: Object containing:
  - `question` (string, 3-400 chars)
  - `conclusion` (string, 1-400 chars)
  - `confidence` (enum: `LOW`, `MEDIUM`, `HIGH`)
  - `premises` (array of objects, ≥1 item)
    - Each premise: `type` (`FACT`, `ASSUMPTION`, `EXPERT_OPINION`), `text`
    - **FACT premises:** Require `evidence` array with ≥2 HTTPS URLs
  - `inferences` (optional array of strings)
  - `contradictions` (optional array of strings)
  - `falsifier` (string, 10-1000 chars)
- `metadata` (optional object):
  - `actor` (string, max 120 chars)
  - `context` (string, max 200 chars)

---

## Request Examples

### Example 1: Valid Request

```bash
curl -X POST https://<n8n-webhook-url>/webhook/yara/picc/notarize \
  -H 'Content-Type: application/json' \
  -H 'X-Signature-256: sha256=a1b2c3d4...' \
  -d '{
    "schema_version": "PICC-1.0",
    "ts": 1730820000,
    "nonce": "unique-nonce-12345",
    "decision": {
      "question": "Should we adopt regenerative agriculture practices?",
      "conclusion": "Yes, based on carbon sequestration evidence",
      "confidence": "HIGH",
      "premises": [
        {
          "type": "FACT",
          "text": "Regenerative agriculture increases soil carbon by 0.5-1.5 tC/ha/yr",
          "evidence": [
            "https://doi.org/10.1038/s41558-020-0738-9",
            "https://www.sciencedirect.com/science/article/pii/S0167880920301584"
          ]
        },
        {
          "type": "ASSUMPTION",
          "text": "Farmers will adopt practices if economically viable"
        }
      ],
      "inferences": [
        "Carbon markets can provide economic incentive",
        "Policy support accelerates adoption"
      ],
      "contradictions": [
        "Initial costs may deter small farmers"
      ],
      "falsifier": "If peer-reviewed studies show no carbon benefit, conclusion is invalid"
    },
    "metadata": {
      "actor": "climate-analyst-42",
      "context": "carbon-offset-evaluation"
    }
  }'
```

**Canonical JSON (for hash):**
```json
{"decision":{"conclusion":"Yes, based on carbon sequestration evidence","confidence":"HIGH","contradictions":["Initial costs may deter small farmers"],"falsifier":"If peer-reviewed studies show no carbon benefit, conclusion is invalid","inferences":["Carbon markets can provide economic incentive","Policy support accelerates adoption"],"premises":[{"evidence":["https://doi.org/10.1038/s41558-020-0738-9","https://www.sciencedirect.com/science/article/pii/S0167880920301584"],"text":"Regenerative agriculture increases soil carbon by 0.5-1.5 tC/ha/yr","type":"FACT"},{"text":"Farmers will adopt practices if economically viable","type":"ASSUMPTION"}],"question":"Should we adopt regenerative agriculture practices?"},"metadata":{"actor":"climate-analyst-42","context":"carbon-offset-evaluation"},"nonce":"unique-nonce-12345","schema_version":"PICC-1.0","ts":1730820000}
```

**Hash (SHA-256 of canonical JSON):**
```
e7f4a2b9c8d1... (full 64-char hex)
```

---

## Response Format

### Success: Created (201 / 200)

```json
{
  "ok": true,
  "code": "CREATED",
  "msg": "Decision notarized",
  "issue_url": "https://github.com/<ORG>/<REPO>/issues/42",
  "issue_number": 42,
  "hash": "e7f4a2b9c8d1..."
}
```

### Success: Idempotent (200)

If a decision with the same hash already exists (detected via `hash:<first16>` label):

```json
{
  "ok": true,
  "code": "IDEMPOTENT",
  "msg": "Decision already notarized",
  "issue_url": "https://github.com/<ORG>/<REPO>/issues/42",
  "issue_number": 42,
  "hash": "e7f4a2b9c8d1..."
}
```

### Error: Bad Signature (401)

```json
{
  "ok": false,
  "code": "BAD_SIG",
  "msg": "HMAC signature mismatch"
}
```

### Error: Timestamp Window (401)

```json
{
  "ok": false,
  "code": "TS_WINDOW",
  "msg": "Timestamp outside 5min window"
}
```

### Error: Schema Validation (400)

```json
{
  "ok": false,
  "code": "SCHEMA_VERSION",
  "msg": "Invalid or missing schema_version"
}
```

### Error: Nonce Invalid (400)

```json
{
  "ok": false,
  "code": "NONCE_INVALID",
  "msg": "Nonce must be 8-128 chars"
}
```

### Error: FACT Evidence (400)

```json
{
  "ok": false,
  "code": "FACT_EVIDENCE",
  "msg": "FACT premises require ≥2 evidence URLs"
}
```

### Error: HTTPS Enforcement (400)

```json
{
  "ok": false,
  "code": "EVIDENCE_HTTPS",
  "msg": "Evidence URLs must be HTTPS"
}
```

### Error: Rate Limit (429)

```json
{
  "ok": false,
  "code": "RATE_LIMIT",
  "msg": "Too many requests. Retry after <seconds>s"
}
```

---

## Canonicalization & Hashing

### Algorithm

1. **Canonicalize JSON**: Sort all object keys recursively, no whitespace
2. **Hash**: SHA-256 of canonical string → 64-char hex digest
3. **Label**: First 16 characters of hash → `hash:<first16>`

### Canonical JSON Rules

- Object keys sorted alphabetically
- No extra whitespace
- Arrays preserve order
- Strings double-quoted
- Numbers unquoted
- Booleans/null lowercase

### Reference Implementation (JavaScript)

```javascript
function canonical(obj) {
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonical).join(',') + ']';
  }
  if (obj && typeof obj === 'object') {
    const keys = Object.keys(obj).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + canonical(obj[k])).join(',') + '}';
  }
  return JSON.stringify(obj);
}

const canonicalStr = canonical(payload);
const hash = crypto.createHash('sha256').update(canonicalStr).digest('hex');
```

---

## HMAC Authentication

### Signature Generation

```javascript
const crypto = require('crypto');

const body = JSON.stringify(payload); // Original JSON, NOT canonical
const secret = process.env.HMAC_SECRET;
const signature = 'sha256=' + crypto.createHmac('sha256', secret).update(body).digest('hex');

// Send as header
headers['X-Signature-256'] = signature;
```

### Server-Side Validation

```javascript
const receivedSig = headers['x-signature-256'];
const expectedSig = 'sha256=' + crypto.createHmac('sha256', secret).update(bodyStr).digest('hex');

if (receivedSig !== expectedSig) {
  return { ok: false, code: 'BAD_SIG' };
}
```

**Important:** HMAC is computed on the **raw request body** (as sent), NOT the canonical form. Canonicalization is only for hashing/idempotency.

---

## Security Notes

### 1. Timestamp Window (Replay Protection)

- Requests must have `ts` within **±300 seconds** (5 minutes) of server time
- Prevents replay attacks with old signatures
- Clients should sync time via NTP

### 2. Nonce (Single-Use Enforcement)

- Each `nonce` can only be used **once**
- Server should track nonces in Redis with TTL (e.g., 600s)
- Key pattern: `yara:nonce:<nonce>`, SET NX EX 600
- If nonce exists → reject with `NONCE_REUSE` error

### 3. HMAC Secret Management

- **Never commit secrets** to repositories
- Store in environment variables or secret manager (e.g., AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets periodically (e.g., every 90 days)
- Use different secrets for dev/staging/prod

### 4. HTTPS Enforcement

- All evidence URLs must use `https://` (enforced by schema)
- Webhook endpoint must be HTTPS (enforced by n8n config)
- No downgrades to HTTP allowed

### 5. Rate Limiting

- Recommended: 100 requests per 10 minutes per IP/actor
- Implementation via Redis token bucket (see `/spec/ops/rate_limit_nonce_design.md`)
- Return `429 Too Many Requests` with `Retry-After` header

### 6. GitHub Quota Management

- GitHub API has rate limits (5000/hour authenticated, 60/hour unauthenticated)
- Monitor `X-RateLimit-Remaining` header
- Use authenticated requests (OAuth2 token)
- Implement exponential backoff on 403/rate limit errors

---

## Idempotency Behavior

### Detection Method

1. After validation, compute canonical hash
2. Extract first 16 hex chars → `hash:<first16>`
3. Search GitHub Issues with label `hash:<first16>`
4. If found → return existing issue URL with `code: IDEMPOTENT`
5. If not found → create new issue with labels:
   - `yara-logica`
   - `picc`
   - `hash:<first16>`
   - `schema:PICC-1.0`
   - `actor:<actor_id>` (if provided)
   - `context:<context>` (if provided)

### Collision Probability

- First 16 hex chars = 64 bits
- Collision probability (birthday paradox): ~1% after 600M decisions
- Acceptable risk for initial deployment
- Monitor collision rate; upgrade to 20-24 chars if needed

---

## Error Handling & DLQ

### Dead Letter Queue (DLQ)

If GitHub API fails (network, quota, etc.):

1. Log error to monitoring system (e.g., Sentry, CloudWatch)
2. Add label `dlq` to retry queue
3. Trigger reprocessor workflow (manual or cron)
4. After successful retry, replace `dlq` → `resolved`

See `/spec/ops/runbook_notarization.md` for operational procedures.

---

## Monitoring & Observability

### Key Metrics

| Metric | Threshold | Alert |
|:-------|:----------|:------|
| Request rate | >100/10min per IP | Potential abuse |
| Error rate (4xx) | >5% | Schema issues |
| Error rate (5xx) | >1% | GitHub API issues |
| Latency (p95) | >2s | Performance degradation |
| DLQ depth | >10 | Backlog accumulation |

### Logs

- All requests logged with: `ts`, `nonce`, `hash`, `actor`, `outcome`
- Failed requests include: `code`, `msg`
- Successful requests include: `issue_url`, `issue_number`

---

## Versioning & Evolution

### Schema Version

- Current: `PICC-1.0`
- Future versions: `PICC-2.0`, etc.
- Backward compatibility: Server validates `schema_version` field
- Breaking changes require new endpoint or version negotiation

### API Contract Changes

- Non-breaking: Add optional fields, new error codes
- Breaking: Change required fields, remove fields, change validation rules
- Process: Announce 90 days in advance, maintain old version during migration

---

## References

- **JSON Schema:** `/spec/schemas/picc-1.0.schema.json`
- **n8n Workflow:** `/spec/workflows/n8n_yara_picc_notarization.json`
- **Label Taxonomy:** `/spec/labels/taxonomy.md`
- **Runbooks:** `/spec/ops/runbook_notarization.md`
- **Threat Model:** `/spec/ops/threat_model_stride.md`
- **Rate Limit Design:** `/spec/ops/rate_limit_nonce_design.md`

---

**Last Updated:** 2025-01-05
**Maintained by:** Alter Agro Ltda.
**Contact:** security@alteragro.com.br
