# LSA n8n Workflow Setup Guide

## Overview

This guide provides step-by-step instructions for setting up the **YARA Lógica PICC Notarization** workflow in n8n. This workflow automates the creation of audit-grade decision records in GitHub Issues with cryptographic hashing and HMAC authentication.

## Prerequisites

### Required Software

1. **n8n** (v1.0.0 or later)
   ```bash
   # Install via npm
   npm install -g n8n

   # Or use Docker
   docker run -it --rm \
     --name n8n \
     -p 5678:5678 \
     -v ~/.n8n:/home/node/.n8n \
     n8nio/n8n
   ```

2. **Ollama** (Optional - for AI-assisted decision generation)
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull recommended model
   ollama pull deepseek-coder:6.7b
   ```

3. **GitHub Account** with repository access
   - Repository: `ourobrancopedro-rgb/alter-agro-yara-logica`
   - Permissions: Issues (write), Metadata (read)

### Required Credentials

- **GitHub Personal Access Token** (classic)
  - Scopes: `repo` (full control)
  - Generate at: https://github.com/settings/tokens

- **HMAC Secret** (for webhook authentication)
  ```bash
  # Generate a secure HMAC secret
  openssl rand -hex 32
  ```

## Installation Steps

### 1. Import the n8n Workflow

1. **Start n8n**
   ```bash
   n8n start
   ```

2. **Access n8n UI**
   - Open browser: http://localhost:5678
   - Create account or log in

3. **Import Workflow**
   - Click "Workflows" → "Import from File"
   - Select: `/spec/workflows/n8n_yara_picc_notarization.json`
   - Or use the workflow at: `/lsa/workflows/n8n-lsa-workflow.json` (if available)
   - Click "Import"

### 2. Configure GitHub Credentials

1. **Create GitHub OAuth2 Credential**
   - In n8n, go to "Credentials" → "Create New"
   - Select: "GitHub OAuth2 API"
   - **OR** use "GitHub API" (Personal Access Token)

2. **For Personal Access Token:**
   - Credential Type: "GitHub API"
   - **Access Token:** Paste your GitHub PAT
   - **User:** Your GitHub username
   - Click "Save"

3. **Assign to Workflow Nodes:**
   - Open workflow
   - Click "Search Existing Issue" node
   - Select your GitHub credential
   - Click "Create GitHub Issue" node
   - Select the same credential

### 3. Configure Environment Variables

Set these environment variables in n8n:

```bash
# Add to ~/.n8n/config (or Docker environment)
export HMAC_SECRET="your-generated-hmac-secret-here"
export GITHUB_OWNER="ourobrancopedro-rgb"
export GITHUB_REPO="alter-agro-yara-logica"
```

**For Docker:**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -e HMAC_SECRET="your-hmac-secret" \
  -e GITHUB_OWNER="ourobrancopedro-rgb" \
  -e GITHUB_REPO="alter-agro-yara-logica" \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### 4. Configure File Paths (CRITICAL)

**UPDATE FILE PATH IN WORKFLOW:**

The workflow references a local file path for decision record storage. You MUST update this path:

1. Open workflow in n8n
2. Find node: **"Write to File"** or **"Read File"** (if present)
3. Update `fileSelector` parameter:
   ```
   OLD: /Users/<yourusername>/alter-agro-yara-logica/lsa/records/{{$json.filename}}
   NEW: /absolute/path/to/your/clone/alter-agro-yara-logica/lsa/records/{{$json.filename}}
   ```

**Example:**
```
# Linux/Mac
/home/youruser/projects/alter-agro-yara-logica/lsa/records/{{$json.filename}}

# Windows (WSL)
/mnt/c/Users/youruser/projects/alter-agro-yara-logica/lsa/records/{{$json.filename}}
```

### 5. Activate Webhook

1. **Enable Production Webhook:**
   - Open workflow
   - Click "Webhook Trigger" node
   - Copy the **Production URL**
   - Example: `https://your-n8n-instance.com/webhook/yara/picc/notarize`

2. **Test Webhook:**
   - Click "Webhook Trigger" node
   - Click "Listen for Test Event"
   - Use test script (see Testing section)

### 6. Configure GitHub Labels

The workflow automatically applies labels. Ensure these labels exist in your GitHub repository:

```bash
# Create labels via GitHub CLI (gh)
gh label create "lsa" --color "667eea" --description "Logic Sorting Architecture decision record" --repo ourobrancopedro-rgb/alter-agro-yara-logica
gh label create "decision-record" --color "764ba2" --description "Audit-grade decision documentation" --repo ourobrancopedro-rgb/alter-agro-yara-logica
gh label create "high-confidence" --color "28a745" --description "HIGH confidence level" --repo ourobrancopedro-rgb/alter-agro-yara-logica
gh label create "medium-confidence" --color "ffc107" --description "MEDIUM confidence level" --repo ourobrancopedro-rgb/alter-agro-yara-logica
gh label create "low-confidence" --color "dc3545" --description "LOW confidence level" --repo ourobrancopedro-rgb/alter-agro-yara-logica
gh label create "needs-review" --color "6c757d" --description "Decision requires human validation" --repo ourobrancopedro-rgb/alter-agro-yara-logica
```

**Or create manually via GitHub UI:**
- Go to repository → Issues → Labels → New Label
- Use the colors and descriptions above

## Testing

### Test with Automated Script

```bash
# Generate HMAC secret (if not done)
HMAC_SECRET=$(openssl rand -hex 32)
echo "HMAC_SECRET=$HMAC_SECRET"

# Test webhook
./scripts/test-webhook.sh \
  "https://your-n8n-instance.com/webhook/yara/picc/notarize" \
  "$HMAC_SECRET"
```

### Manual Test with curl

```bash
# Set variables
WEBHOOK_URL="https://your-n8n-instance.com/webhook/yara/picc/notarize"
HMAC_SECRET="your-secret-here"

# Create test payload
PAYLOAD=$(cat <<'EOF'
{
  "schema_version": "PICC-1.0",
  "ts": 1730000000,
  "nonce": "test-nonce-12345678",
  "decision": {
    "question": "Should we implement automated decision records?",
    "conclusion": "Yes, with HMAC authentication and hash-based idempotency",
    "confidence": "HIGH",
    "premises": [
      {
        "type": "FACT",
        "text": "Manual decision tracking has 30% error rate",
        "evidence": [
          "https://example.com/study1",
          "https://example.com/study2"
        ]
      }
    ],
    "inferences": ["Automation reduces human error"],
    "contradictions": ["Initial setup complexity"],
    "falsifier": "If error rate > 5% after 6 months, revert to manual"
  },
  "metadata": {
    "actor": "test-user",
    "context": "setup-validation"
  }
}
EOF
)

# Compute HMAC signature
SIGNATURE="sha256=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')"

# Send request
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature-256: $SIGNATURE" \
  -d "$PAYLOAD"
```

**Expected Response:**
```json
{
  "ok": true,
  "issue_url": "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues/XX",
  "hash": "abc123...",
  "idempotent": false
}
```

## Troubleshooting

### Common Issues

#### 1. "HMAC signature mismatch"
- **Cause:** HMAC_SECRET not set or incorrect
- **Fix:** Verify environment variable matches webhook secret

#### 2. "GitHub API rate limit exceeded"
- **Cause:** Too many requests
- **Fix:** Wait for rate limit reset or use authenticated API calls

#### 3. "Timestamp outside 5min window"
- **Cause:** System clock skew
- **Fix:** Sync system time with NTP
  ```bash
  sudo ntpdate -s time.nist.gov
  ```

#### 4. "File write failed"
- **Cause:** Incorrect file path or permissions
- **Fix:** Update file path in workflow, ensure directory exists and is writable

#### 5. "Schema validation failed"
- **Cause:** Invalid decision record structure
- **Fix:** Validate payload against `/spec/schemas/picc-1.0.schema.json`

### Debug Mode

Enable verbose logging in n8n:

```bash
# Set log level
export N8N_LOG_LEVEL=debug

# Restart n8n
n8n start
```

Check logs:
```bash
# Docker
docker logs n8n

# Local
tail -f ~/.n8n/logs/n8n.log
```

## Production Deployment

### Security Hardening

1. **Use HTTPS only** for webhook URLs
2. **Rotate HMAC secrets** quarterly
3. **Enable IP whitelisting** in n8n (if supported)
4. **Monitor rate limits** and set alerts
5. **Use GitHub App** instead of PAT for better security

### Monitoring

Track these metrics:
- Webhook success rate
- GitHub API quota usage
- Duplicate hash detection rate
- Average processing time

### Backup

```bash
# Export workflow regularly
n8n export:workflow --id=<workflow-id> --output=backup/

# Backup decision records
cp -r lsa/records/ backup/records-$(date +%Y%m%d)/
```

## Next Steps

1. ✅ Verify workflow imports without errors
2. ✅ Test webhook with sample payload
3. ✅ Confirm GitHub issue creation
4. ✅ Validate hash-based idempotency
5. ✅ Set up monitoring and alerts
6. ✅ Train team on decision record submission

## Support

**Questions:** See [LSA README](../README.md)
**Issues:** GitHub Issues
**Security:** [contatoalteragro@gmail.com](mailto:contatoalteragro@gmail.com)

---

**© 2025 Alter Agro Ltda.**
_Part of the YARA Lógica LSA Decision Record System_
