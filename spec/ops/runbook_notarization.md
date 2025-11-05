# YARA Lógica PICC Notarization Runbook

**Version:** 1.0
**Last Updated:** 2025-01-05
**Audience:** DevOps, SRE, On-Call Engineers

---

## Overview

This runbook covers operational procedures for the **YARA Lógica PICC Notarization** workflow, which:

1. Receives signed decision payloads via n8n webhook
2. Validates schema, HMAC signature, timestamp, and nonce
3. Computes canonical hash for idempotency
4. Creates GitHub Issues as immutable decision records

**Key Components:**
- **n8n workflow:** Orchestrates validation and GitHub API calls
- **Redis:** Stores nonces and rate limit counters
- **GitHub API:** Issues endpoint for decision storage
- **HMAC secret:** Shared between clients and n8n (stored in environment)

---

## Common Issues & Troubleshooting

### 1. `401 BAD_SIG` - HMAC Signature Mismatch

**Symptom:** Client receives `{"ok": false, "code": "BAD_SIG", "msg": "HMAC signature mismatch"}`

**Causes:**
- Client using wrong HMAC secret
- Secret mismatch between client and n8n environment
- Client computing signature incorrectly (e.g., using canonical JSON instead of raw body)
- Secret rotation not synced

**Resolution:**
1. Verify n8n environment variable `HMAC_SECRET` matches client config
2. Test HMAC computation with known payload:
   ```bash
   echo -n '{"test":"payload"}' | openssl dgst -sha256 -hmac "<SECRET>"
   ```
3. Check client HMAC implementation (must use raw request body, not canonical)
4. If secret was rotated, notify all clients and update simultaneously

**Monitoring:**
- Alert if `BAD_SIG` rate > 5% of total requests
- Log client identifier (if available) to identify misconfigured clients

---

### 2. `401 TS_WINDOW` - Timestamp Outside 5-Minute Window

**Symptom:** `{"ok": false, "code": "TS_WINDOW", "msg": "Timestamp outside 5min window"}`

**Causes:**
- Client clock skew (not synced with NTP)
- Client using cached timestamp
- Server time drift
- Network latency > 5 minutes (unlikely)

**Resolution:**
1. Check client system time:
   ```bash
   date -u +%s  # Unix timestamp
   ntpdate -q pool.ntp.org  # Check NTP sync
   ```
2. Verify n8n server time:
   ```bash
   docker exec <n8n-container> date -u +%s
   ```
3. Ensure client generates fresh `ts` for each request:
   ```javascript
   const ts = Math.floor(Date.now() / 1000);
   ```
4. If server drift detected, sync with NTP:
   ```bash
   sudo ntpdate -s pool.ntp.org
   ```

**Prevention:**
- Configure NTP on all client and server systems
- Monitor clock skew metrics
- Consider increasing window to 600s (10min) if legitimate clients have issues

---

### 3. `400 NONCE_INVALID` - Nonce Format Error

**Symptom:** `{"ok": false, "code": "NONCE_INVALID", "msg": "Nonce must be 8-128 chars"}`

**Causes:**
- Nonce too short (<8 chars) or too long (>128 chars)
- Nonce missing from payload
- Nonce contains invalid characters (unlikely, as schema accepts strings)

**Resolution:**
1. Check payload `nonce` field:
   ```bash
   echo "$PAYLOAD" | jq -r '.nonce | length'
   ```
2. Verify nonce generation logic:
   ```javascript
   const nonce = crypto.randomBytes(16).toString('hex'); // 32 chars, valid
   ```
3. Update client to use 16-32 character nonces (UUIDs, hex strings, etc.)

---

### 4. `400 NONCE_REUSE` - Nonce Already Used

**Symptom:** `{"ok": false, "code": "NONCE_REUSE", "msg": "Nonce has already been used"}`

**Causes:**
- Client retrying request with same nonce
- Client not generating unique nonces
- Redis nonce TTL expired but request is within timestamp window

**Resolution:**
1. Check Redis for nonce key:
   ```bash
   redis-cli GET "yara:nonce:<nonce>"
   ```
2. If found, nonce is still active (TTL not expired)
3. Client must generate fresh nonce for each request:
   ```javascript
   const { v4: uuidv4 } = require('uuid');
   const nonce = uuidv4(); // Guaranteed unique
   ```
4. If legitimate retry (network failure), client should use exponential backoff + new nonce

**Prevention:**
- Educate clients on nonce uniqueness requirement
- Monitor nonce reuse rate (should be near 0%)

---

### 5. `400 FACT_EVIDENCE` - FACT Premises Missing Evidence

**Symptom:** `{"ok": false, "code": "FACT_EVIDENCE", "msg": "FACT premises require ≥2 evidence URLs"}`

**Causes:**
- FACT premise has 0 or 1 evidence URL
- Evidence field missing from FACT premise
- Client using wrong premise type (should be ASSUMPTION or EXPERT_OPINION if no evidence)

**Resolution:**
1. Review payload `decision.premises`:
   ```bash
   echo "$PAYLOAD" | jq '.decision.premises[] | select(.type == "FACT")'
   ```
2. Ensure each FACT has ≥2 URLs in `evidence` array
3. If evidence not available, change premise type to `ASSUMPTION`

**Client Guidance:**
- FACT = objectively verifiable claim → requires ≥2 evidence URLs
- ASSUMPTION = working hypothesis → no evidence required
- EXPERT_OPINION = authoritative statement → evidence optional

---

### 6. `400 EVIDENCE_HTTPS` - Evidence URLs Not HTTPS

**Symptom:** `{"ok": false, "code": "EVIDENCE_HTTPS", "msg": "Evidence URLs must be HTTPS"}`

**Causes:**
- Evidence URL uses `http://` instead of `https://`
- Typo in URL scheme

**Resolution:**
1. Check evidence URLs:
   ```bash
   echo "$PAYLOAD" | jq '.decision.premises[].evidence[]?'
   ```
2. Update all URLs to `https://`
3. If source only available over HTTP, archive with HTTPS-enabled service (e.g., archive.org)

**Security Rationale:**
- HTTPS prevents MITM tampering of evidence
- Ensures integrity of audit trail

---

### 7. `429 RATE_LIMIT` - Too Many Requests

**Symptom:** `{"ok": false, "code": "RATE_LIMIT", "msg": "Too many requests. Retry after <seconds>s"}`

**Causes:**
- Client exceeding rate limit (default: 100 requests per 10 minutes)
- DDoS attack or abuse
- Retry loop without backoff

**Resolution:**
1. Check rate limit counter in Redis:
   ```bash
   redis-cli GET "yara:rl:<client_ip>"
   ```
2. Review client request patterns in logs
3. If legitimate traffic spike, consider:
   - Increasing rate limit for specific clients (whitelist)
   - Batching requests (submit multiple decisions in background job)
4. If abuse detected, block IP or actor at firewall level

**Prevention:**
- Implement exponential backoff in clients
- Use `Retry-After` header value for retry scheduling
- Monitor rate limit hit rate per client

---

### 8. GitHub API Quota Exhausted

**Symptom:** Workflow fails with GitHub API error `403 Forbidden` or `rate limit exceeded`

**Causes:**
- Too many GitHub API calls (5000/hour authenticated, 60/hour unauthenticated)
- Large burst of notarization requests
- Multiple n8n workflows sharing same GitHub token

**Resolution:**
1. Check GitHub rate limit status:
   ```bash
   curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     https://api.github.com/rate_limit
   ```
2. Response includes:
   ```json
   {
     "resources": {
       "core": {
         "limit": 5000,
         "remaining": 42,
         "reset": 1730823600
       }
     }
   }
   ```
3. If `remaining` near 0, wait until `reset` timestamp
4. Implement exponential backoff in n8n workflow (Add "Wait" node after GitHub API failure)

**Prevention:**
- Use authenticated requests (OAuth2 token with higher limits)
- Monitor `X-RateLimit-Remaining` header in workflow
- Cache search results (idempotency check) if possible
- Distribute load across multiple GitHub Apps/tokens if high volume

---

### 9. DLQ Backlog Accumulation

**Symptom:** Dead Letter Queue (DLQ) depth increasing, issues not created

**Causes:**
- GitHub API downtime
- Network issues between n8n and GitHub
- Invalid GitHub credentials
- Repository permissions changed (n8n token revoked)

**Resolution:**
1. Check DLQ depth:
   ```bash
   # Label search for 'dlq' in GitHub Issues
   gh issue list --label dlq --repo <ORG/REPO>
   ```
2. Review n8n execution logs for errors:
   ```bash
   docker logs <n8n-container> | grep -i "error"
   ```
3. Verify GitHub token permissions:
   ```bash
   gh auth status
   ```
4. Reprocess DLQ items:
   - Trigger manual n8n workflow with DLQ payloads
   - After success, relabel `dlq` → `resolved`

**DLQ Reprocessor (Manual):**
```bash
# Export DLQ items
gh issue list --label dlq --json number,body > dlq_export.json

# Resubmit each
jq -c '.[]' dlq_export.json | while read item; do
  ISSUE_NUM=$(echo "$item" | jq -r '.number')
  BODY=$(echo "$item" | jq -r '.body')

  # Extract canonical JSON from issue body
  # Re-submit to webhook
  curl -X POST "$WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -H "X-Signature-256: sha256=$(compute_hmac "$BODY")" \
    -d "$BODY"

  # If success, remove dlq label
  gh issue edit "$ISSUE_NUM" --remove-label dlq --add-label resolved
done
```

**Prevention:**
- Monitor GitHub API health (https://www.githubstatus.com/)
- Set up alerts for DLQ depth > 10
- Implement automatic retry with exponential backoff in n8n

---

## Monitoring & Alerts

### Key Metrics

| Metric | Source | Threshold | Alert Severity |
|:-------|:-------|:----------|:---------------|
| Request rate | n8n logs | >200/min sustained | Warning |
| Error rate (4xx) | n8n logs | >5% | Warning |
| Error rate (5xx) | n8n logs | >1% | Critical |
| HMAC failures | n8n logs | >10/hour | Warning |
| DLQ depth | GitHub labels | >10 | Warning |
| DLQ depth | GitHub labels | >50 | Critical |
| GitHub API quota remaining | GitHub headers | <500 | Warning |
| GitHub API quota remaining | GitHub headers | <100 | Critical |
| Workflow execution time (p95) | n8n metrics | >3s | Warning |
| Redis connection failures | Redis logs | >0 | Critical |

### Dashboard Widgets

1. **Request volume** (time series): Requests/minute over 24h
2. **Error breakdown** (pie chart): 200, 4xx, 5xx distribution
3. **Top error codes** (bar chart): BAD_SIG, TS_WINDOW, RATE_LIMIT, etc.
4. **DLQ depth** (gauge): Current count of issues with `dlq` label
5. **GitHub quota remaining** (gauge): Real-time remaining requests
6. **Latency distribution** (histogram): p50, p90, p95, p99

---

## Operational Procedures

### Deploying n8n Workflow Updates

1. **Export current workflow** from n8n UI (backup)
2. **Import updated workflow** from `/spec/workflows/n8n_yara_picc_notarization.json`
3. **Configure credentials** (GitHub OAuth2, Redis connection)
4. **Set environment variables:**
   - `HMAC_SECRET`: Shared secret for HMAC validation
   - `GITHUB_OWNER`: GitHub organization/user
   - `GITHUB_REPO`: Repository name for issues
5. **Test with sample payload** (use `/examples/clients/javascript/submit_decision.js`)
6. **Activate workflow** and monitor logs for 30 minutes
7. **Rollback** if error rate > 5%

### Rotating HMAC Secret

**Procedure:**
1. Generate new secret:
   ```bash
   openssl rand -hex 32
   ```
2. Update n8n environment variable `HMAC_SECRET` (dual secrets: old + new)
3. Notify all clients of new secret (90-day migration window)
4. Update client configurations with new secret
5. After 90 days, remove old secret from n8n

**Dual-Secret Validation (Interim):**
```javascript
const secret1 = process.env.HMAC_SECRET_OLD;
const secret2 = process.env.HMAC_SECRET_NEW;

const sig1 = 'sha256=' + crypto.createHmac('sha256', secret1).update(body).digest('hex');
const sig2 = 'sha256=' + crypto.createHmac('sha256', secret2).update(body).digest('hex');

if (receivedSig !== sig1 && receivedSig !== sig2) {
  return { ok: false, code: 'BAD_SIG' };
}
```

### Scaling Considerations

**Current capacity:**
- ~100 requests/10min per IP (rate limit)
- ~5000 GitHub API calls/hour (authenticated)
- ~1000 decisions/hour sustainable (2 API calls per decision: search + create)

**If traffic exceeds capacity:**
1. **Horizontal scaling:** Deploy multiple n8n instances behind load balancer
2. **GitHub quota:** Use multiple GitHub Apps with separate tokens
3. **Redis:** Use Redis Cluster for distributed rate limiting
4. **Batching:** Aggregate decisions and create fewer, larger issues (trade-off: granularity)

---

## Maintenance Windows

- **Preferred:** Sundays 02:00-06:00 UTC (lowest traffic)
- **Notification:** 48-hour advance notice to clients
- **Rollback plan:** Keep previous n8n workflow version ready for instant revert

---

## Contacts

- **On-Call Engineer:** Use PagerDuty rotation
- **Security Issues:** security@alteragro.com.br
- **n8n Admin:** devops@alteragro.com.br
- **GitHub Admin:** platform@alteragro.com.br

---

## References

- **API Contract:** `/spec/contracts/notarization_api_contract.md`
- **Threat Model:** `/spec/ops/threat_model_stride.md`
- **Rate Limit Design:** `/spec/ops/rate_limit_nonce_design.md`
- **n8n Workflow:** `/spec/workflows/n8n_yara_picc_notarization.json`

---

**Runbook maintained by:** Alter Agro DevOps Team
**Last incident:** None (pre-production)
**Next review:** 2025-04-01
