# n8n YARA PICC Notarization Workflow - Setup Guide

**Version:** 1.1
**Last Updated:** 2025-11-06
**Audience:** DevOps, System Administrators

---

## Overview

This guide provides step-by-step instructions for importing and configuring the **YARA Lógica PICC Notarization** workflow in your n8n instance. The workflow enables cryptographically-sealed decision records to be stored as GitHub Issues with full audit traceability.

---

## Prerequisites

Before starting, ensure you have:

- ✅ n8n instance (self-hosted or cloud)
- ✅ GitHub account with repository access
- ✅ GitHub OAuth App or Personal Access Token
- ✅ HMAC secret for webhook authentication (generate using `openssl rand -hex 32`)
- ✅ Access to this repository: `ourobrancopedro-rgb/alter-agro-yara-logica`

---

## Step 1: Prepare GitHub Credentials

### Option A: GitHub OAuth2 App (Recommended)

1. Navigate to **GitHub Settings** → **Developer settings** → **OAuth Apps**
2. Click **New OAuth App**
3. Fill in the details:
   - **Application name:** `YARA Logica n8n Notarization`
   - **Homepage URL:** `https://your-n8n-instance.com`
   - **Authorization callback URL:** `https://your-n8n-instance.com/rest/oauth2-credential/callback`
4. Click **Register application**
5. Save the **Client ID** and **Client Secret**

### Option B: Personal Access Token

1. Navigate to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Set token name: `YARA Logica n8n Notarization`
4. Select scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `public_repo` (access to public repositories)
5. Click **Generate token**
6. Save the token (you won't see it again!)

---

## Step 2: Import n8n Workflow

1. **Access your n8n instance** at `https://your-n8n-instance.com`

2. **Navigate to Workflows** (left sidebar)

3. **Click "Add workflow" → "Import from File"**

4. **Select the workflow JSON:**
   ```bash
   spec/workflows/n8n_yara_picc_notarization.json
   ```

5. **The workflow will import with 12 nodes:**
   - Webhook Trigger
   - Validate + Hash
   - IF Valid
   - Format → Markdown
   - Search Existing Issue (HTTP Request)
   - Rate Limit Guard
   - Issue Exists?
   - Create GitHub Issue (HTTP Request with retry)
   - Return Created
   - Return Existing
   - Respond – Success
   - Respond: Error

---

## Step 3: Configure Webhook Trigger

1. **Click on "Webhook Trigger" node**

2. **Verify settings:**
   - **HTTP Method:** POST
   - **Path:** `yara/picc/notarize`
   - **Response Mode:** "Using 'Respond to Webhook' node"

3. **Activate the workflow temporarily** (toggle at top-right)

4. **Copy the Production Webhook URL:**
   ```
   Example: https://your-n8n.com/webhook/yara/picc/notarize
   ```

5. **Save this URL** - you'll provide it to clients later

---

## Step 4: Configure GitHub Credentials

The workflow uses **HTTP Request nodes** for GitHub API calls, providing better control over retries and rate limiting.

### Using Personal Access Token (Recommended):

1. **Click on "Search Existing Issue" node**

2. **In the Credentials section, click "Create New"**

3. **Select "GitHub API"**

4. **Fill in:**
   - **Access Token:** (from Step 1)

5. **Test the connection**

6. **Repeat for "Create GitHub Issue" node** (select the same credential)

### For OAuth2 (Alternative):

If your n8n instance already has GitHub OAuth2 configured:

1. **Click on "Search Existing Issue" node**

2. **Update credential type to OAuth2 if needed**

3. **Select your existing OAuth2 credential**

4. **Repeat for "Create GitHub Issue" node**

**Note:** Personal Access Token is simpler and provides the same functionality for this workflow.

---

## Step 5: Set Environment Variables

n8n supports environment variables for secure configuration. Set the following:

### Required Variables:

| Variable | Description | Example |
|:---------|:------------|:--------|
| `HMAC_SECRET` | Shared secret for HMAC authentication | `a1b2c3d4e5f6...` (64 hex chars) |
| `GITHUB_OWNER` | GitHub organization or username | `ourobrancopedro-rgb` |
| `GITHUB_REPO` | Repository name for issues | `alter-agro-yara-logica` |

### Setting Environment Variables:

#### Docker (docker-compose.yml):
```yaml
services:
  n8n:
    image: n8nio/n8n
    environment:
      - HMAC_SECRET=your-secret-here
      - GITHUB_OWNER=ourobrancopedro-rgb
      - GITHUB_REPO=alter-agro-yara-logica
```

#### n8n Cloud:
1. Navigate to **Settings** → **Environment Variables**
2. Add each variable with its value
3. Restart the workflow

#### Self-Hosted (systemd):
```bash
sudo systemctl edit n8n
```
Add:
```ini
[Service]
Environment="HMAC_SECRET=your-secret-here"
Environment="GITHUB_OWNER=ourobrancopedro-rgb"
Environment="GITHUB_REPO=alter-agro-yara-logica"
```
Restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart n8n
```

---

## Step 6: Generate HMAC Secret

Generate a secure HMAC secret that will be shared with clients:

```bash
openssl rand -hex 32
```

Output example:
```
a1b2c3d4e5f6789abcdef0123456789abcdef0123456789abcdef0123456789
```

**Security Notes:**
- ⚠️ Never commit this secret to Git
- ⚠️ Store in environment variables or secret manager
- ⚠️ Use different secrets for dev/staging/prod
- ⚠️ Rotate every 90 days

---

## Step 7: Test the Workflow

### Manual Test (n8n UI):

1. **Click "Execute Workflow" (bottom-right)**

2. **In "Webhook Trigger" node, click "Listen for test event"**

3. **Use the test URL provided**

### Test with cURL:

```bash
# Generate test payload
HMAC_SECRET="your-secret-here"
WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"

# Create payload
PAYLOAD=$(cat <<'EOF'
{
  "schema_version": "PICC-1.0",
  "ts": 1735689600,
  "nonce": "test-nonce-12345678",
  "decision": {
    "question": "Is this a test decision?",
    "conclusion": "Yes, this is a test",
    "confidence": "HIGH",
    "premises": [
      {
        "type": "FACT",
        "text": "This is a test premise",
        "evidence": [
          "https://example.com/test1",
          "https://example.com/test2"
        ]
      }
    ],
    "inferences": ["Test inference"],
    "contradictions": [],
    "falsifier": "This is a test falsifier"
  },
  "metadata": {
    "actor": "test-user",
    "context": "setup-test"
  }
}
EOF
)

# Compute HMAC signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')

# Send request
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD"
```

**Expected Response (New Issue):**
```json
{
  "ok": true,
  "created": true,
  "issue_number": 42,
  "issue_url": "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues/42",
  "hash": "e7f4a2b9c8d1..."
}
```

**Expected Response (Existing Issue - Idempotent):**
```json
{
  "ok": true,
  "idempotent": true,
  "issue_number": 42,
  "issue_url": "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues/42",
  "message": "Existing issue returned (idempotency)"
}
```

### Test with JavaScript Client:

```bash
cd examples/clients/javascript
npm install node-fetch
export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"
export HMAC_SECRET="your-secret-here"
node submit_decision.js
```

### Test with Python Client:

```bash
cd examples/clients/python
pip install requests
export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/yara/picc/notarize"
export HMAC_SECRET="your-secret-here"
python submit_decision.py
```

---

## Step 8: Verify GitHub Issue Creation

1. **Navigate to your GitHub repository:**
   ```
   https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues
   ```

2. **Look for a new issue** with labels:
   - `yara-logica`
   - `picc`
   - `hash:<first16chars>`
   - `schema:PICC-1.0`
   - `actor:<actor_id>`
   - `context:<context>`

3. **Verify the issue body** contains:
   - Decision question
   - Conclusion
   - Premises with evidence
   - Inferences and contradictions
   - Falsifier
   - Metadata
   - SHA-256 hash
   - Canonical JSON

---

## Step 9: Activate and Monitor

1. **Activate the workflow** (toggle at top-right)

2. **Monitor execution logs:**
   - Go to **Executions** tab
   - Check for errors or failures
   - Review execution time (should be < 2 seconds)

3. **Set up monitoring alerts** (optional):
   - Error rate > 5%
   - GitHub API quota < 100 remaining
   - DLQ depth > 10

---

## Client Configuration

### Provide to Clients:

1. **Webhook URL:**
   ```
   https://your-n8n.com/webhook/yara/picc/notarize
   ```

2. **HMAC Secret:**
   ```
   (Send securely via encrypted channel)
   ```

3. **Client Libraries:**
   - JavaScript: `examples/clients/javascript/submit_decision.js`
   - Python: `examples/clients/python/submit_decision.py`

4. **API Documentation:**
   - Contract: `spec/contracts/notarization_api_contract.md`
   - Schema: `spec/schemas/picc-1.0.schema.json`

### Example Client Configuration:

**JavaScript (.env):**
```bash
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/yara/picc/notarize
HMAC_SECRET=a1b2c3d4e5f6...
```

**Python (.env):**
```bash
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/yara/picc/notarize
HMAC_SECRET=a1b2c3d4e5f6...
```

---

## Troubleshooting

### Common Issues:

| Error | Solution |
|:------|:---------|
| `401 BAD_SIG` | Verify HMAC_SECRET matches between client and n8n |
| `401 TS_WINDOW` | Check client/server time sync (NTP) |
| `400 FACT_EVIDENCE` | Ensure FACT premises have ≥2 HTTPS evidence URLs |
| `403 GitHub API Rate Limit` | Check GitHub quota, use OAuth2 for higher limits |
| Webhook not found (404) | Verify workflow is active and webhook path is correct |

See full runbook: `spec/ops/runbook_notarization.md`

---

## Security Checklist

- [ ] HMAC_SECRET generated securely (32+ bytes)
- [ ] Environment variables not committed to Git
- [ ] GitHub credentials use OAuth2 (recommended) or PAT with minimal scopes
- [ ] Webhook URL uses HTTPS (not HTTP)
- [ ] n8n instance protected with authentication
- [ ] Workflow execution logs reviewed for sensitive data
- [ ] Rate limiting configured (if available)
- [ ] GitHub repository has proper access controls

---

## Next Steps

1. **Deploy to production** - Activate workflow and notify clients
2. **Monitor metrics** - Track request rate, error rate, GitHub quota
3. **Set up alerts** - Configure notifications for failures
4. **Document webhook URL** - Share with authorized clients securely
5. **Review audit trail** - Verify GitHub Issues are created correctly

---

## Idempotency Guarantees

The workflow implements **search-before-create idempotency** to prevent duplicate issue creation on retries:

### How It Works:

1. **Canonical Hash Generation:**
   - The workflow computes a stable SHA-256 hash of the request payload
   - Uses sorted keys to ensure consistent hashing regardless of JSON field order
   - Creates a unique label: `hash:{first16chars}`

2. **Search Before Create:**
   - Before creating an issue, searches GitHub for existing issues with the same hash label
   - Uses GitHub Search API: `is:issue label:"hash:abc123..."`
   - Continues on API failure to handle rate limiting gracefully

3. **Rate-Limit Guardrails:**
   - Validates `total_count` from search results
   - Defaults to 0 if search API returns rate-limit errors (403)
   - Prevents false positives from malformed responses

4. **Conditional Branching:**
   - **If issue exists** (`total_count > 0`): Returns existing issue with `idempotent: true`
   - **If issue doesn't exist** (`total_count = 0`): Creates new issue with hash label

5. **Automatic Retries:**
   - Issue creation uses HTTP Request with **4 retry attempts** at 2-second intervals
   - Handles transient GitHub API failures gracefully

### Testing Idempotency:

```bash
# Send the same payload twice
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD"

# First run: Returns created: true
# Second run: Returns idempotent: true (no new issue)
```

### Benefits:

- ✅ Safe retries - clients can retry failed requests without duplicate issues
- ✅ Network resilience - handles transient failures gracefully
- ✅ Audit integrity - prevents duplicate decision records
- ✅ Cost efficiency - reduces GitHub API usage on retries

---

## References

- **Workflow JSON:** `/spec/workflows/n8n_yara_picc_notarization.json`
- **API Contract:** `/spec/contracts/notarization_api_contract.md`
- **Runbook:** `/spec/ops/runbook_notarization.md`
- **Threat Model:** `/spec/ops/threat_model_stride.md`
- **Client Examples:** `/examples/clients/`

---

## Support

- **Documentation Issues:** Open issue in this repository
- **Security Questions:** security@alteragro.com.br
- **Technical Support:** devops@alteragro.com.br

---

**Setup Guide maintained by:** Alter Agro DevOps Team
**Last tested:** 2025-11-06
**Next review:** 2026-02-01
