# Security-Focused Contributing Guide
**YARA Lógica — Spec-Only Repository**

---

## Overview

This guide complements the general [CONTRIBUTING.md](CONTRIBUTING.md) with **security-specific requirements** for contributing to the YARA Lógica public specifications repository.

**Key Principle:** This is a **spec-only repository**. Runtime code, prompts, models, and secrets are **strictly prohibited**.

---

## 🔒 Security Checklist for Contributors

Before submitting ANY pull request, verify:

- [ ] **No secrets or credentials** (API keys, tokens, passwords)
- [ ] **No runtime code** (FastAPI, LangChain, database code)
- [ ] **No prompt templates** or instruction sets
- [ ] **No customer data** (names, emails, phone numbers, PII)
- [ ] **No pricing information** (specific amounts, contracts)
- [ ] **No internal infrastructure details** (IP addresses, internal domains)
- [ ] **No model weights** or binary files (except approved: PDF, PNG, JPG)
- [ ] **Files within allowlist paths only** (lsa/spec/, rag/spec/, docs/, etc.)
- [ ] **Hash ledger updated** (`python infra/github/verify_hashes.py --update`)
- [ ] **Commits GPG-signed** (`git config commit.gpgsign true`)
- [ ] **Evidence citations included** for factual claims
- [ ] **Pre-commit hooks installed** (`.github/scripts/install-hooks.sh`)

---

## ✅ What CAN Be Contributed

**Allowed contributions:**

1. **Specifications** (P0-Public)
   - LSA/PICC methodology improvements
   - RAG policy refinements
   - Audit trail schema enhancements

2. **Documentation** (P0-Public)
   - Architecture explanations
   - Usage examples (with sanitized data)
   - Audit guides and validation procedures

3. **Tooling** (P0-Public)
   - CI/CD scripts for integrity enforcement
   - Hash verification tools
   - Allowlist checkers

4. **Legal** (P0-Public)
   - License clarifications
   - Trademark usage guidelines

---

## 🚫 What CANNOT Be Contributed

**Prohibited contributions:**

1. **Runtime Code**
   - FastAPI endpoints, routes, middleware
   - LangChain chains, agents, retrievers
   - Database models, ORMs, queries
   - Docker files, docker-compose

2. **AI/ML Components**
   - Prompt engineering templates
   - Model weights (.bin, .safetensors, .ckpt)
   - Training scripts or data
   - Fine-tuning configurations

3. **Secrets & Credentials**
   - API keys, tokens, passwords
   - Private keys, certificates
   - Environment variables with sensitive values
   - Connection strings

4. **Business Information**
   - Customer names, contacts, or data
   - Pricing, contracts, revenue details
   - Internal roadmaps or unreleased features
   - Partnership terms

5. **Infrastructure**
   - Internal IP addresses or domains
   - Cloud configurations (AWS, Azure, GCP)
   - Security configurations
   - Backup/DR procedures

---

## 🔐 Security Requirements

### 1. GPG-Signed Commits

**All commits must be GPG-signed.**

Setup:
```bash
# Generate GPG key
gpg --gen-key

# List keys
gpg --list-secret-keys --keyid-format LONG

# Configure git
git config user.signingkey <KEY_ID>
git config commit.gpgsign true

# Verify
git log --show-signature -1
```

### 2. Pre-Commit Hooks

Install security hooks before first commit:

```bash
# Install hooks
.github/scripts/install-hooks.sh

# Test
git add <file>
git commit -m "test"  # Should trigger security checks
```

### 3. Hash Ledger Updates

Update hash ledger after every file change:

```bash
# Update ledger
python infra/github/verify_hashes.py --update

# Verify
python infra/github/verify_hashes.py

# Commit the updated ledger
git add infra/github/hash_ledger.json
git commit -S -m "chore: update hash ledger"
```

### 4. Secret Scanning

Run local scans before pushing:

```bash
# Scan staged files
python infra/github/scan_secrets.py --staged

# Scan all files (thorough)
python infra/github/scan_secrets.py --strict

# Check allowlist compliance
python infra/github/check_allowlist.py --staged
```

---

## 📝 Contribution Workflow

### Step 1: Fork & Clone

```bash
# Fork repository on GitHub
# Then clone
git clone git@github.com:<your-username>/alter-agro-yara-logica.git
cd alter-agro-yara-logica

# Add upstream
git remote add upstream git@github.com:ourobrancopedro-rgb/alter-agro-yara-logica.git
```

### Step 2: Install Security Tools

```bash
# Install pre-commit hooks
.github/scripts/install-hooks.sh

# Enable GPG signing
git config commit.gpgsign true
```

### Step 3: Create Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create branch (use descriptive name)
git checkout -b docs/improve-lsa-spec
```

### Step 4: Make Changes

```bash
# Edit files (only in allowed directories)
vim lsa/spec/LSA_PICC.md

# Run security checks
python infra/github/scan_secrets.py --staged
python infra/github/check_allowlist.py --staged

# Update hash ledger
python infra/github/verify_hashes.py --update
```

### Step 5: Commit Changes

```bash
# Stage changes
git add lsa/spec/LSA_PICC.md
git add infra/github/hash_ledger.json

# Commit with GPG signature (automatic if configured)
git commit -S -m "docs(lsa): clarify premise validation requirements

Evidence: [LSA_PICC.md@lines:45-67]
Impact: Improves auditor guidance for premise evaluation"

# Pre-commit hooks will run automatically
```

### Step 6: Push & Create PR

```bash
# Push to your fork
git push origin docs/improve-lsa-spec

# Create PR on GitHub
# Use PR template and fill all sections
```

---

## 🧪 PR Review Process

### Automatic Checks (CI/CD)

Your PR will be automatically checked for:

1. ✅ **Information Barrier** - Secret scanning (TruffleHog, GitLeaks, custom DLP)
2. ✅ **Scope Guard** - Allowlist enforcement
3. ✅ **Hash Verification** - Ledger integrity
4. ✅ **KPI Scoring** - Logical consistency
5. ✅ **GPG Signatures** - Commit signing verification

**All checks must pass** before human review.

### Manual Review

Requires **2 approvals**:

1. **Security Review** - Verifies no sensitive content, correct classification
2. **Engineering Review** - Verifies technical accuracy, evidence quality

Reviewers will check:

- Classification correctness (all content is P0-Public)
- Evidence citations complete
- Specification clarity
- No prohibited content
- Compliance with BUSL-1.1 license

---

## 🚨 Handling Sensitive Information in Issues

### Creating Issues

**NEVER include sensitive information in GitHub issues.**

If you discover:

- **Security vulnerability** → Use [SECURITY.md](SECURITY.md) disclosure process
- **Confidential data leak** → Email [security@alteragro.com.br](mailto:security@alteragro.com.br) immediately
- **General bug** → Create public issue (sanitize all data)

### Sanitizing Data for Issues

**BAD:**
```
Customer "Fazenda ABC" has pricing issue with $5,000/month contract.
API endpoint api.alteragro.internal/v2/pricing is failing.
```

**GOOD:**
```
Example customer has issue with pricing calculation.
Public API endpoint (details available to maintainers) returns unexpected result.
```

### Security Issue Template

Use `.github/ISSUE_TEMPLATE/security-issue.md` for security-related issues.
Auto-marks as confidential and assigns to security team.

---

## ⚖️ Legal & Licensing

### Contributor License Agreement (CLA)

By contributing, you agree:

1. **You own the rights** to your contribution
2. **You grant Alter Agro** a perpetual, worldwide, royalty-free license
3. **Your contribution is accurate** to the best of your knowledge
4. **You will not contribute confidential information** of third parties

### BUSL-1.1 Implications

This repository is licensed under **BUSL-1.1**:

- ✅ **Research and evaluation use** is permitted
- ✅ **Non-commercial use** is permitted
- ❌ **Commercial use restricted** until 2029-01-01
- ❌ **No production use** without Alter Agro license

Your contributions become part of the BUSL-1.1 licensed codebase.

### Trademark Usage

"YARA Lógica" and "Alter Agro" are trademarks. See [TRADEMARKS.md](../legal/TRADEMARKS.md) for usage guidelines.

Permitted: Nominative use (referring to the system)
Not permitted: Using marks for your own products/services

---

## 📞 Questions & Support

### For Security Questions

**Email:** [security@alteragro.com.br](mailto:security@alteragro.com.br)
**Subject:** `[CONTRIB] <your question>`

### For Contribution Help

**Email:** [hello@alteragro.com.br](mailto:hello@alteragro.com.br)
**GitHub Discussions:** Use repository discussions for public questions

### For Legal/Licensing

**Email:** [legal@alteragro.com.br](mailto:legal@alteragro.com.br)

---

## 📚 Additional Resources

- [Trade Secret Protection Policy](../legal/TRADE_SECRET_POLICY.md) — Understanding classification
- [Information Classification Guide](../docs/INFORMATION_CLASSIFICATION_GUIDE.md) — How to classify content
- [SECURITY.md](SECURITY.md) — Vulnerability disclosure
- [Private Repository Guide](../docs/PRIVATE_REPOSITORY_GUIDE.md) — Working with private repos (for team)

---

**Thank you for contributing securely to YARA Lógica!**

**© 2025 Alter Agro Ltda.**
