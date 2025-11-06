# YARA Lógica PICC Notarization - Setup Summary

**Date:** 2025-01-06
**Session:** claude/setup-n8n-yara-picc-workflow-011CUqr3mkTSiBixErwaQaam

---

## Overview

This document provides a quick reference for setting up and testing the **YARA Lógica PICC Notarization** workflow in n8n. The workflow enables cryptographically-sealed decision records to be stored as GitHub Issues with full audit traceability.

---

## Quick Start

### 1. Prerequisites

```bash
# Required
- n8n instance (self-hosted or cloud)
- GitHub account with repository access
- GitHub OAuth App or Personal Access Token

# Generate HMAC secret
openssl rand -hex 32
```

### 2. Import Workflow

1. Open n8n UI
2. Navigate to **Workflows** → **Import from File**
3. Select: `spec/workflows/n8n_yara_picc_notarization.json`

### 3. Configure Credentials

**GitHub OAuth2:**
- Create OAuth App at: https://github.com/settings/developers
- Add credentials to n8n workflow nodes:
  - "GitHub Search (Idempotency)"
  - "GitHub Create Issue"

**Environment Variables:**
```bash
HMAC_SECRET=<generated-secret>
GITHUB_OWNER=ourobrancopedro-rgb
GITHUB_REPO=alter-agro-yara-logica
```

### 4. Activate Workflow

1. Toggle workflow to "Active"
2. Copy the Production Webhook URL
3. Share with authorized clients

### 5. Test Webhook

**Using the test script:**
```bash
./scripts/test-webhook.sh \
  "https://your-n8n.com/webhook/yara/picc/notarize" \
  "your-hmac-secret"
```

**Using JavaScript client:**
```bash
cd examples/clients/javascript
npm install node-fetch
export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"
export HMAC_SECRET="your-secret-here"
node submit_decision.js
```

**Using Python client:**
```bash
cd examples/clients/python
pip install requests
export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"
export HMAC_SECRET="your-secret-here"
python submit_decision.py
```

---

## Workflow Architecture

```
┌─────────────────┐
│ Webhook Trigger │  POST /webhook/yara/picc/notarize
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validate + Hash │  HMAC, timestamp, schema, canonical hash
└────────┬────────┘
         │
         ▼
   ┌────┴────┐
   │ IF Valid│
   └────┬────┘
        │
    ┌───┴───┐
    │       │
    ▼       ▼
  Valid   Error
    │       │
    ▼       └─────► Respond: Error (401)
┌─────────────────┐
│ Format Markdown │  Convert to GitHub Issue format
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ GitHub Search       │  Check for existing issue (idempotency)
│ (hash:first16 label)│
└────────┬────────────┘
         │
         ▼
   ┌────┴──────────┐
   │ IF Not Exists │
   └────┬──────────┘
        │
    ┌───┴───┐
    │       │
    ▼       ▼
  New    Exists
    │       │
    ▼       └─────► Respond: Idempotent (200)
┌─────────────────┐
│ GitHub Create   │  Create new issue
│ Issue           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Respond: Created│  Return issue URL + hash (200)
└─────────────────┘
```

---

## Key Files Created/Modified

| File | Purpose |
|:-----|:--------|
| `docs/N8N_SETUP_GUIDE.md` | Comprehensive setup guide (step-by-step) |
| `scripts/test-webhook.sh` | Automated webhook testing script |
| `docs/SETUP_SUMMARY.md` | This quick reference guide |

---

## Existing Specification Files

| File | Description |
|:-----|:------------|
| `spec/workflows/n8n_yara_picc_notarization.json` | n8n workflow definition |
| `spec/contracts/notarization_api_contract.md` | API contract (request/response format) |
| `spec/ops/runbook_notarization.md` | Operational runbook (troubleshooting) |
| `spec/ops/threat_model_stride.md` | Security threat model |
| `spec/ops/rate_limit_nonce_design.md` | Rate limiting design |
| `spec/schemas/picc-1.0.schema.json` | JSON schema for PICC-1.0 |
| `examples/clients/javascript/submit_decision.js` | JavaScript client library |
| `examples/clients/python/submit_decision.py` | Python client library |

---

## Security Checklist

- [ ] HMAC_SECRET generated securely (32+ bytes)
- [ ] Environment variables not committed to Git
- [ ] GitHub credentials use OAuth2 with minimal scopes
- [ ] Webhook URL uses HTTPS (not HTTP)
- [ ] n8n instance protected with authentication
- [ ] Workflow execution logs reviewed for sensitive data
- [ ] GitHub repository has proper access controls
- [ ] Test webhook with `scripts/test-webhook.sh`
- [ ] Verify GitHub issue creation with correct labels

---

## Workflow Nodes Summary

| Node | Type | Purpose |
|:-----|:-----|:--------|
| Webhook Trigger | Webhook | Receive POST requests at `/yara/picc/notarize` |
| Validate + Hash | Function | HMAC validation, timestamp check, schema validation, SHA-256 hash |
| IF Valid | IF | Route to success or error path |
| Format → Markdown | Function | Convert decision to GitHub Issue markdown |
| GitHub Search (Idempotency) | GitHub API | Search for existing issue by hash label |
| IF Not Exists | IF | Route to create or idempotent response |
| GitHub Create Issue | GitHub API | Create new issue with decision record |
| Respond: Created | Respond to Webhook | Return success with issue URL (code: CREATED) |
| Respond: Idempotent | Respond to Webhook | Return existing issue URL (code: IDEMPOTENT) |
| Respond: Error | Respond to Webhook | Return error response (401) |

---

## Environment Variables Required

| Variable | Example | Description |
|:---------|:--------|:------------|
| `HMAC_SECRET` | `a1b2c3d4...` | Shared secret for HMAC authentication (64 hex chars) |
| `GITHUB_OWNER` | `ourobrancopedro-rgb` | GitHub organization or username |
| `GITHUB_REPO` | `alter-agro-yara-logica` | Repository name for issues |

---

## API Endpoint Details

**Endpoint:**
```
POST /webhook/yara/picc/notarize
```

**Headers:**
```
Content-Type: application/json
X-Signature-256: sha256=<hmac_sha256(body, secret)>
```

**Request Body:**
```json
{
  "schema_version": "PICC-1.0",
  "ts": 1735689600,
  "nonce": "unique-nonce-12345",
  "decision": {
    "question": "...",
    "conclusion": "...",
    "confidence": "HIGH",
    "premises": [...],
    "inferences": [...],
    "contradictions": [...],
    "falsifier": "..."
  },
  "metadata": {
    "actor": "...",
    "context": "..."
  }
}
```

**Success Response (201/200):**
```json
{
  "ok": true,
  "code": "CREATED",
  "msg": "Decision notarized",
  "issue_url": "https://github.com/org/repo/issues/42",
  "issue_number": 42,
  "hash": "e7f4a2b9c8d1..."
}
```

**Error Response (401/400):**
```json
{
  "ok": false,
  "code": "BAD_SIG",
  "msg": "HMAC signature mismatch"
}
```

---

## Validation Rules

| Rule | Description |
|:-----|:------------|
| **HMAC Signature** | Must match `sha256=<hmac_sha256(body, secret)>` |
| **Timestamp Window** | Must be within ±300 seconds (5 minutes) of server time |
| **Nonce** | Must be 8-128 characters, unique per request |
| **Schema Version** | Must be `"PICC-1.0"` |
| **FACT Evidence** | FACT premises require ≥2 evidence URLs |
| **HTTPS-only** | All evidence URLs must use `https://` |

---

## Idempotency

The workflow implements **hash-based idempotency**:

1. Compute SHA-256 hash of canonical JSON payload
2. Extract first 16 hex characters → `hash:<first16>`
3. Search GitHub Issues for label `hash:<first16>`
4. If found → return existing issue (code: IDEMPOTENT)
5. If not found → create new issue (code: CREATED)

**Collision probability:**
- 16 hex chars = 64 bits
- ~1% collision after 600M decisions (acceptable for MVP)

---

## Client Configuration

**Provide to authorized clients:**

1. **Webhook URL** (Production):
   ```
   https://your-n8n.com/webhook/yara/picc/notarize
   ```

2. **HMAC Secret** (via secure channel):
   ```
   <generated-secret>
   ```

3. **Client Libraries:**
   - JavaScript: `examples/clients/javascript/submit_decision.js`
   - Python: `examples/clients/python/submit_decision.py`

4. **Documentation:**
   - API Contract: `spec/contracts/notarization_api_contract.md`
   - JSON Schema: `spec/schemas/picc-1.0.schema.json`

---

## Testing Checklist

- [ ] Import workflow into n8n
- [ ] Configure GitHub OAuth2 credentials
- [ ] Set environment variables (HMAC_SECRET, GITHUB_OWNER, GITHUB_REPO)
- [ ] Activate workflow
- [ ] Test with `scripts/test-webhook.sh`
- [ ] Test with JavaScript client (`examples/clients/javascript/submit_decision.js`)
- [ ] Test with Python client (`examples/clients/python/submit_decision.py`)
- [ ] Verify GitHub issue created with correct labels
- [ ] Verify idempotency (submit same payload twice)
- [ ] Test error cases (bad signature, invalid timestamp, etc.)
- [ ] Review n8n execution logs

---

## Troubleshooting Quick Reference

| Error | Cause | Solution |
|:------|:------|:---------|
| `401 BAD_SIG` | HMAC mismatch | Verify HMAC_SECRET matches between client/n8n |
| `401 TS_WINDOW` | Clock skew | Sync time with NTP: `sudo ntpdate -s pool.ntp.org` |
| `400 NONCE_INVALID` | Nonce format | Use 8-128 character unique string |
| `400 FACT_EVIDENCE` | Missing evidence | FACT premises require ≥2 HTTPS URLs |
| `400 EVIDENCE_HTTPS` | Non-HTTPS URL | Use `https://` for all evidence URLs |
| `403 Rate Limit` | GitHub quota | Use OAuth2, wait until rate limit resets |
| `404 Not Found` | Webhook inactive | Activate workflow in n8n |

**Full troubleshooting guide:** `spec/ops/runbook_notarization.md`

---

## Monitoring

**Key metrics to track:**

- Request rate (requests/minute)
- Error rate (4xx, 5xx)
- HMAC failure rate
- GitHub API quota remaining
- DLQ depth (failed GitHub API calls)
- Workflow execution time (p95)

**Recommended alerts:**

- Error rate > 5% → Warning
- GitHub quota < 100 → Critical
- DLQ depth > 10 → Warning

---

## Next Steps

1. **Deploy workflow** - Follow `docs/N8N_SETUP_GUIDE.md`
2. **Test thoroughly** - Use `scripts/test-webhook.sh`
3. **Share credentials** - Provide webhook URL + HMAC secret to clients (securely)
4. **Monitor** - Track metrics and set up alerts
5. **Document** - Update internal wiki with webhook URL and setup notes

---

## References

- **Detailed Setup Guide:** `docs/N8N_SETUP_GUIDE.md`
- **API Contract:** `spec/contracts/notarization_api_contract.md`
- **Runbook:** `spec/ops/runbook_notarization.md`
- **Threat Model:** `spec/ops/threat_model_stride.md`
- **Client Examples:** `examples/clients/`

---

## Support

- **Documentation Issues:** Open issue in this repository
- **Security Questions:** security@alteragro.com.br
- **Technical Support:** devops@alteragro.com.br

---

**Setup completed by:** Claude (claude/setup-n8n-yara-picc-workflow-011CUqr3mkTSiBixErwaQaam)
**Date:** 2025-01-06
**Status:** ✅ Ready for deployment
