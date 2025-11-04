# Private Repository Guide
**YARA Lógica — Working with Public & Private Repos**

---

## Overview

Alter Agro maintains a **dual-repository strategy** for YARA Lógica:

1. **Public Repository** (`alter-agro-yara-logica`) — Specifications, audit artifacts (P0)
2. **Private Repositories** — Runtime code, prompts, models, customer integrations (P2/P3)

This guide explains when to use each repository and how to work across them safely.

---

## Repository Strategy

### Public Repository

**URL:** `github.com/ourobrancopedro-rgb/alter-agro-yara-logica`
**Visibility:** Public
**License:** BUSL-1.1 (source-available, non-commercial until 2029)
**Purpose:** Specifications and methodological transparency

**What goes here:**
- ✅ LSA/PICC specifications
- ✅ RAG policy documents
- ✅ Audit trails and validation schemas
- ✅ Architecture documentation (high-level)
- ✅ CI/CD enforcement tools
- ✅ Legal artifacts (LICENSE, TRADEMARKS)

**What does NOT go here:**
- ❌ Runtime code (FastAPI, LangChain, etc.)
- ❌ Prompts or prompt templates
- ❌ Model weights or training data
- ❌ Customer data or integrations
- ❌ Secrets, credentials, API keys
- ❌ Infrastructure configurations

### Private Repositories

**Location:** GitHub Enterprise (or private GitHub)
**Visibility:** Private (authorized personnel only)
**License:** Proprietary
**Purpose:** Operational systems and competitive IP

**Structure:**
```
yara-logica-runtime/          # Main runtime code
├─ backend/                   # FastAPI, LangChain
├─ frontend/                  # UI (if applicable)
├─ infra/                     # IaC, deployment
└─ prompts/                   # Prompt engineering (P3!)

yara-logica-models/           # ML models
├─ weights/                   # Fine-tuned models
├─ training/                  # Training scripts
└─ evaluation/                # Metrics, benchmarks

yara-logica-customers/        # Customer integrations
├─ <customer-name>/           # Per-customer code
└─ configs/                   # Customer-specific configs
```

---

## When to Use Which Repository

| Task | Repository | Classification |
|:-----|:-----------|:---------------|
| Document LSA methodology | **Public** | P0 |
| Implement LSA logic in Python | **Private** | P2 |
| Explain RAG policy | **Public** | P0 |
| Build RAG retrieval system | **Private** | P2-P3 |
| Publish audit schema | **Public** | P0 |
| Store audit logs (customer data) | **Private** | P3 |
| Create CI/CD for specs | **Public** | P0 |
| Deploy production infrastructure | **Private** | P2-P3 |
| Write security policy | **Public** | P0 |
| Configure actual secrets | **Private** | P3 |

**Rule of thumb:** If it runs in production or contains secrets/customer data → **Private**

---

## Access Management

### Public Repository Access

- **Read:** Anyone (public)
- **Write:** Authorized contributors with approved PRs
- **Admin:** Alter Agro security & engineering leads

### Private Repository Access

**Access Levels:**

| Role | Access | Approver |
|:-----|:-------|:---------|
| **Core Team** | Read/Write to most repos | Manager |
| **Contractor** | Read-only or limited write | CTO + Legal (NDA required) |
| **Customer Success** | Read-only to customer-specific dirs | Manager |
| **External Auditor** | Read-only to specific files | CTO + Legal (NDA required) |

**Access Request Process:**

1. Submit request via [Internal Access Portal]
2. Provide business justification
3. Manager approval
4. CTO approval (for P3 repos)
5. Sign NDA if external
6. Access granted with MFA requirement
7. Access reviewed quarterly

---

## Git Workflow Between Repos

### Scenario 1: Specification Change

**Example:** Update LSA/PICC schema

```bash
# Work in PUBLIC repo
cd alter-agro-yara-logica
git checkout -b spec/update-lsa-schema

# Edit specification
vim lsa/spec/LSA_PICC.md

# Update hash ledger
python infra/github/verify_hashes.py --update

# Commit & push
git commit -S -m "spec(lsa): update premise validation schema"
git push origin spec/update-lsa-schema

# Create PR → Review → Merge
```

**Then, update implementation in PRIVATE repo:**

```bash
# Work in PRIVATE repo
cd yara-logica-runtime
git checkout -b impl/update-lsa-schema

# Update implementation to match new spec
vim backend/lsa/premise_validator.py

# Reference the public spec commit
git commit -S -m "impl(lsa): update validator per spec@abc123

See: github.com/ourobrancopedro-rgb/alter-agro-yara-logica/commit/abc123"
```

### Scenario 2: Bug Fix in Private Code

**Example:** Fix bug in RAG retrieval

```bash
# Work in PRIVATE repo
cd yara-logica-runtime
git checkout -b fix/rag-retrieval-bug

# Fix the bug
vim backend/rag/retriever.py
pytest tests/test_retriever.py

# Commit
git commit -S -m "fix(rag): correct similarity scoring bug"
git push origin fix/rag-retrieval-bug

# Create PR → Review → Merge
```

**Do NOT mention in public repo** (implementation details are P2)

### Scenario 3: Security Vulnerability

**Example:** Discovered vulnerability in hash verification

```bash
# 1. Email security@alteragro.com.br privately

# 2. Fix in PRIVATE repo first
cd yara-logica-runtime
git checkout -b security/fix-hash-verify
# ... fix ...
git commit -S -m "security: fix hash verification bypass"

# 3. After fix is deployed, update PUBLIC spec if needed
cd alter-agro-yara-logica
git checkout -b spec/update-hash-verification
# ... update spec ...

# 4. Coordinate public disclosure per SECURITY.md
```

---

## .gitignore Best Practices

### Public Repository

**File:** `alter-agro-yara-logica/.gitignore`

```gitignore
# Secrets
.env
.env.*
*.key
*.pem
*.p12
secrets/
credentials/

# Runtime code (should not be here anyway)
*.pyc
__pycache__/
venv/
node_modules/

# Build artifacts
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
*.tmp
```

### Private Repository

**File:** `yara-logica-runtime/.gitignore`

```gitignore
# NEVER COMMIT THESE
.env
.env.*
*.env
config/production.yml
config/secrets.yml

# API Keys & Tokens
*.key
*.pem
*.p12
*.keystore
credentials/
secrets/

# Customer Data
data/customers/
backups/
dumps/

# Models (use Git LFS or separate storage)
models/weights/*.bin
models/weights/*.safetensors
models/weights/*.ckpt
*.h5
*.pb

# Build
*.pyc
__pycache__/
dist/
build/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

**IMPORTANT:** Even with .gitignore, NEVER create files with real secrets in the repo. Use environment variables or secrets managers.

---

## Secrets Management

### ❌ NEVER Do This

```python
# ❌ Hardcoded API key
API_KEY = "sk-1234567890abcdef"

# ❌ In .env committed to repo
# .env file:
OPENAI_API_KEY=sk-1234567890abcdef

# ❌ In config file
# config.yml:
openai:
  api_key: sk-1234567890abcdef
```

### ✅ DO This Instead

**Option 1: Environment Variables (for development)**

```python
# ✅ Load from environment
import os
API_KEY = os.getenv("OPENAI_API_KEY")

# .env file (NOT committed):
OPENAI_API_KEY=sk-1234567890abcdef

# .gitignore:
.env
```

**Option 2: Secrets Manager (for production)**

```python
# ✅ AWS Secrets Manager
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='prod/openai/api_key')
API_KEY = response['SecretString']
```

**Option 3: GitHub Secrets (for CI/CD)**

```yaml
# ✅ .github/workflows/deploy.yml
- name: Deploy
  env:
    API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: ./deploy.sh
```

---

## Referencing Private Code from Public Specs

### ✅ Good Examples

**In public spec:**
```markdown
## Implementation Requirements

The LSA premise validator MUST implement the following checks:
1. Non-empty premise text
2. Valid source citation format
3. Faithfulness score ≥ 0.80

**Note:** Reference implementation available in private runtime repository
(access restricted to authorized personnel).
```

**In public README:**
```markdown
## Repository Structure

- **Public Specifications:** github.com/ourobrancopedro-rgb/alter-agro-yara-logica
- **Private Runtime:** Contact security@alteragro.com.br for access (authorized personnel only)
```

### ❌ Bad Examples

**In public spec:**
```markdown
# ❌ TOO SPECIFIC
Implementation: See yara-logica-runtime/backend/lsa/premise.py:45-67

# ❌ LEAKS STRUCTURE
The FastAPI endpoint at POST /api/v2/lsa/validate uses the PremiseValidator class...

# ❌ EXPOSES DETAILS
We use GPT-4 with custom fine-tuning and the prompt template from prompts/lsa_v3.txt...
```

---

## Migration Checklist

### Moving from Public to Private

If content was mistakenly published publicly:

1. **Immediately email security@alteragro.com.br**
2. **Do NOT attempt to fix yourself** (leaves traces in Git history)
3. Security team will:
   - Assess exposure
   - Scrub Git history if needed
   - Rotate any exposed secrets
   - Notify affected parties

### Moving from Private to Public

If spec is ready to publish:

1. **Sanitize content** — Remove all P2/P3 information
2. **Security review** — Scan with DLP tools
3. **Legal review** — Verify BUSL-1.1 compatibility
4. **CTO approval** — Sign off on public release
5. **Move to public repo** — PR with full review process

---

## Troubleshooting

### Problem: Accidentally Committed Secret

**Solution:**

```bash
# DON'T just delete the file and commit
# Secret is still in Git history!

# INSTEAD:
# 1. Email security@alteragro.com.br IMMEDIATELY
# 2. Rotate the secret (new API key, etc.)
# 3. Security team will scrub history with:
git filter-branch --tree-filter 'rm -f path/to/secret.key' HEAD
# or
bfg --delete-files secret.key
```

### Problem: Not Sure If Content is P0 or P2

**Solution:**

1. Review [Information Classification Guide](INFORMATION_CLASSIFICATION_GUIDE.md)
2. Use decision tree
3. If still unsure, email security@alteragro.com.br
4. Default to higher protection (P2) while awaiting answer

### Problem: Need to Share Private Code with External Auditor

**Solution:**

1. Submit access request to CTO
2. Auditor signs NDA (minimum 5-year term)
3. Create time-limited read-only access
4. Provide specific file/directory access only
5. Monitor access logs
6. Revoke access after audit completes

---

## Best Practices Summary

### ✅ DO

- **Classify before committing** — Know if content is P0/P1/P2/P3
- **Use private repo for anything uncertain** — Can always downgrade later
- **Sanitize before publicizing** — Run security scans
- **Reference public specs from private code** — Link to commit hashes
- **Use secrets managers** — Never hardcode credentials
- **Enable MFA** — On all GitHub accounts
- **Sign commits with GPG** — Both public and private repos
- **Review .gitignore** — Before first commit

### ❌ DON'T

- **Assume public repo contributors see private code** — They don't
- **Copy-paste from private to public** — Always sanitize
- **Commit .env files** — Even to private repos
- **Hardcode secrets** — Use environment variables or secrets managers
- **Share private repo URLs publicly** — Keep links internal
- **Grant broad access** — Principle of least privilege
- **Forget to rotate secrets** — Quarterly rotation for P3

---

## Contact & Support

**For Access Requests:**
[Internal Access Portal] or email manager

**For Security Questions:**
[security@alteragro.com.br](mailto:security@alteragro.com.br)

**For Technical Issues:**
[Internal IT Support] or Slack #devops

---

**Last Updated:** 2025-11-04
**Next Review:** 2026-01-01

**© 2025 Alter Agro Ltda.**
**Classification: P1-Internal**
