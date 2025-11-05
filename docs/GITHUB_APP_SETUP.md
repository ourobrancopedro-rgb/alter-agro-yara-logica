# GitHub App Setup Guide — YARA Runtime Integration

This guide walks through creating a GitHub App with least-privilege permissions for YARA runtime to interact with this specification repository.

---

## Why GitHub App (Not PAT)?

**Benefits:**
- **Least privilege** — Grant only necessary permissions
- **Better rate limits** — 5,000 requests/hour per installation
- **Audit trail** — All actions logged as the App
- **Revocable** — Can be revoked without affecting other integrations
- **Organization-wide** — Can be installed across multiple repos

---

## Step 1: Create GitHub App

1. Navigate to **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**

2. **Basic Information:**
   - **App name**: `YARA Runtime Integration`
   - **Description**: `Read-only access to YARA Lógica specifications for runtime pinning`
   - **Homepage URL**: `https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica`

3. **Webhook:**
   - **Active**: ✓ (if you need real-time updates)
   - **Webhook URL**: `https://your-yara-runtime.com/webhooks/github`
   - **Webhook secret**: Generate a strong secret and save securely

4. **Permissions** (Repository permissions):

   | Permission | Access | Rationale |
   |:-----------|:-------|:----------|
   | Contents | **Read** | Fetch spec files at pinned commits |
   | Pull requests | **Write** | Create PRs for spec updates (optional) |
   | Checks | **Write** | Report CI status (optional) |
   | Actions | **Read** | Monitor workflow runs (optional) |
   | Metadata | **Read** | Access repository metadata (required) |

5. **Webhook Events** (Subscribe to):
   - ✓ `pull_request` (opened, synchronize, closed, merged)
   - ✓ `push` (to main branch)
   - ✓ `check_suite` / `check_run`
   - ✓ `workflow_run` (CI status changes)
   - ✓ `repository_dispatch` (manual triggers)

6. **Where can this GitHub App be installed?**
   - Select: **Only on this account**

7. Click **Create GitHub App**

---

## Step 2: Generate Private Key

1. After creation, scroll to **Private keys** section
2. Click **Generate a private key**
3. Save the downloaded `.pem` file securely (this is your App's identity)

**Security:**
- Store in a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- Never commit to version control
- Rotate regularly (every 90 days recommended)

---

## Step 3: Install App on Repository

1. Go to **Install App** (left sidebar)
2. Click **Install** next to your organization/account
3. Select **Only select repositories**
4. Choose: `ourobrancopedro-rgb/alter-agro-yara-logica`
5. Click **Install**

**Note the Installation ID** — you'll need this to authenticate as the installation.

---

## Step 4: Authenticate in Your Runtime

### Python Example (using `PyGithub`)

```python
import jwt
import time
import requests
from github import Github, GithubIntegration

# Load App credentials
APP_ID = 123456  # From GitHub App settings
PRIVATE_KEY_PATH = "/secure/path/to/your-app.pem"
INSTALLATION_ID = 12345678  # From installation page

# Generate JWT for App authentication
def get_jwt_token():
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),  # 10 minutes
        "iss": APP_ID
    }

    return jwt.encode(payload, private_key, algorithm="RS256")

# Get installation access token
def get_installation_token():
    jwt_token = get_jwt_token()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
    response = requests.post(url, headers=headers)
    response.raise_for_status()

    return response.json()["token"]

# Use with PyGithub
token = get_installation_token()
g = Github(token)

# Fetch repository
repo = g.get_repo("ourobrancopedro-rgb/alter-agro-yara-logica")

# Fetch file at pinned commit
commit_sha = "abc123..."
file_content = repo.get_contents("lsa/spec/LSA_PICC.md", ref=commit_sha)

print(file_content.decoded_content.decode("utf-8"))
```

---

## Step 5: Fetch Files at Pinned Commits

### Using REST API Directly

```bash
#!/bin/bash

# Get installation token (JWT dance)
APP_ID="123456"
INSTALLATION_ID="12345678"
PRIVATE_KEY_PATH="/path/to/app.pem"

# Generate JWT (requires openssl/jwt CLI or script)
JWT=$(generate_jwt.sh "$APP_ID" "$PRIVATE_KEY_PATH")

# Get installation token
TOKEN=$(curl -s -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/app/installations/$INSTALLATION_ID/access_tokens" \
  | jq -r '.token')

# Fetch file at pinned commit
curl -H "Authorization: Bearer $TOKEN" \
     -H "Accept: application/vnd.github.raw" \
     "https://api.github.com/repos/ourobrancopedro-rgb/alter-agro-yara-logica/contents/lsa/spec/LSA_PICC.md?ref=abc123..." \
     > LSA_PICC.md
```

---

## Step 6: Handle Webhook Events

Example webhook handler (Flask):

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret"

def verify_signature(payload_body, signature):
    """Verify GitHub webhook signature."""
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.route("/webhooks/github", methods=["POST"])
def github_webhook():
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    event = request.headers.get("X-GitHub-Event")
    payload = request.json

    if event == "pull_request":
        action = payload["action"]
        pr = payload["pull_request"]

        if action == "opened":
            # Run shadow validation on PR specs
            print(f"PR opened: {pr['number']} - {pr['title']}")

        elif action == "closed" and pr["merged"]:
            # Promote pin to production
            new_commit = pr["merge_commit_sha"]
            print(f"PR merged → promote pin to {new_commit}")

    elif event == "push":
        ref = payload["ref"]
        if ref == "refs/heads/main":
            # Main branch updated, consider rotating pin
            print(f"Main updated: {payload['after']}")

    return jsonify({"status": "processed"}), 200
```

---

## Step 7: Rotate Installation Tokens

**Installation tokens expire after 1 hour.** Your runtime should:

1. Cache the token with TTL (55 minutes recommended)
2. Refresh automatically before expiry
3. Handle 401 responses by refreshing token

**Example (Python with caching):**

```python
import time
from functools import lru_cache

@lru_cache(maxsize=1)
def get_cached_token():
    return {
        "token": get_installation_token(),
        "expires_at": time.time() + (55 * 60)  # 55 minutes
    }

def get_valid_token():
    cached = get_cached_token()
    if time.time() >= cached["expires_at"]:
        get_cached_token.cache_clear()
        cached = get_cached_token()
    return cached["token"]
```

---

## Step 8: Security Best Practices

### Private Key Storage

**DO:**
- ✓ Store in secrets manager (AWS Secrets Manager, Vault, etc.)
- ✓ Encrypt at rest
- ✓ Rotate every 90 days
- ✓ Use environment variables, never hardcode

**DON'T:**
- ✗ Commit to Git
- ✗ Store in plain text
- ✗ Share across environments
- ✗ Log or print in plaintext

### Token Security

- Installation tokens are **short-lived** (1 hour)
- Never log tokens in plaintext
- Use HTTPS only
- Implement rate limiting on your webhook endpoint

### Webhook Verification

- **Always verify** webhook signatures
- Use `hmac.compare_digest()` (timing-safe comparison)
- Reject requests with missing/invalid signatures

---

## Step 9: Monitor & Audit

### GitHub Audit Log

- Go to **Settings** → **Audit log**
- Filter by App name to see all actions
- Monitor for unexpected activity

### Rate Limit Monitoring

```python
def check_rate_limit(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.github.com/rate_limit", headers=headers)
    data = response.json()

    core = data["resources"]["core"]
    print(f"Rate limit: {core['remaining']}/{core['limit']}")
    print(f"Resets at: {core['reset']}")
```

---

## Troubleshooting

### "Resource not accessible by integration"

**Cause:** Insufficient permissions

**Fix:**
1. Go to App settings → Permissions
2. Grant required permissions (e.g., Contents: Read)
3. Accept new permissions in installation

### "Bad credentials"

**Cause:** Expired or invalid token

**Fix:**
1. Verify JWT generation (check `iat`, `exp`, `iss`)
2. Ensure private key matches App
3. Refresh installation token

### Webhook not receiving events

**Cause:** Webhook not configured or subscription missing

**Fix:**
1. Verify webhook URL is accessible from GitHub
2. Check webhook secret matches
3. Ensure events are subscribed in App settings

---

## Alternative: Fine-Grained PAT (for testing)

For **local development only**, you can use a Personal Access Token:

**Permissions needed:**
- `repo` → `read:repo` (read repository contents)
- `repo` → `read:org` (if in organization)

**Create PAT:**
1. Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Repository access: Only select repositories → `alter-agro-yara-logica`
3. Permissions: Contents (read-only)
4. Generate and save securely

**Use in code:**

```python
token = "ghp_..."  # Fine-grained PAT
g = Github(token)
```

**⚠️ Security Warning:** PATs have broader scope and longer lifetime. Use GitHub Apps in production.

---

## Next Steps

1. **Integrate with runtime** — Use `infra/github/runtime_integration.py`
2. **Set up webhooks** — Handle PR merge events to rotate pins
3. **Monitor usage** — Track API calls and rate limits
4. **Document rotation** — Schedule key rotation (90 days)

---

**Contact:** [security@alteragro.com.br](mailto:security@alteragro.com.br)
**Docs:** [GitHub Apps Documentation](https://docs.github.com/en/apps)
