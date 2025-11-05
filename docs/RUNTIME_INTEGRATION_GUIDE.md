# YARA Runtime Integration Guide — Spec Pinning Architecture

This guide provides a complete walkthrough for integrating YARA runtime with the public specification repository using commit pinning and hash verification.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Read Path: Fetching Pinned Specs](#read-path-fetching-pinned-specs)
4. [Write Path: Proposing Updates](#write-path-proposing-updates)
5. [Webhook Integration](#webhook-integration)
6. [Provenance Tracking](#provenance-tracking)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Key Principles

1. **Pinned by Commit SHA** — Runtime always fetches specs at an exact commit (never "latest")
2. **Hash Verification** — Every file verified against SHA-256 in hash ledger
3. **PR-Only Updates** — Changes to specs go through PRs with CI gates
4. **Provenance First-Class** — Every inference logs which specs (repo@commit + file@sha256) were used
5. **Auditable & Reversible** — Full history, instant rollback

### Data Contracts

```
SpecBundle      → What runtime consumes (pinned commit + files + hashes)
HashLedger      → Single source of truth for file integrity
DecisionRecord  → Governance records with falsifiers
```

### Flow Diagram

```
┌─────────────────┐
│  YARA Runtime   │
│  (Private)      │
└────────┬────────┘
         │
         │ 1. Fetch specs @ commit SHA
         │    (REST API: GET contents?ref=<sha>)
         │
         ▼
┌─────────────────┐
│  GitHub API     │
│  (Public Repo)  │
└────────┬────────┘
         │
         │ 2. Return file content
         │    + verify SHA-256
         │
         ▼
┌─────────────────┐
│  Runtime Cache  │
│  (Local)        │
└─────────────────┘

Write Path (via PR):
─────────────────────
Runtime → Git Data API → Create blob/tree/commit → Open PR → CI Gates → Merge → Webhook → Rotate Pin
```

---

## Quick Start

### Prerequisites

- **Python 3.9+**
- **GitHub Token** (fine-grained PAT or GitHub App)
- **Specs repo cloned** (optional, for local testing)

### Installation

```bash
# Install dependencies
pip install requests PyGithub flask

# Clone repository (optional, for local testing)
git clone https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica.git
cd alter-agro-yara-logica
```

### Environment Setup

```bash
# Set GitHub token
export GITHUB_TOKEN="ghp_..." # or use GitHub App

# (Optional) Set webhook secret
export WEBHOOK_SECRET="your-webhook-secret"

# (Optional) Set YARA callback URL
export YARA_CALLBACK_URL="https://your-yara-runtime.com/api/webhooks/spec-update"
```

---

## Read Path: Fetching Pinned Specs

### Option 1: Using CLI (Simplest)

```bash
# Fetch specs at pinned commit
python infra/github/yara_specs_cli.py pull \\
  --pin abc123def456... \\
  --files lsa/spec/LSA_PICC.md rag/spec/RAG_POLICY.md \\
  --output ./specs

# Outputs:
# specs/LSA_PICC.md
# specs/RAG_POLICY.md
```

### Option 2: Using SpecBundle (Recommended for Production)

**Step 1: Generate SpecBundle**

```bash
python infra/github/generate_spec_bundle.py \\
  --id "lsa-spec-v2.1" \\
  --commit abc123def456... \\
  --auto \\
  --output spec_bundle.json
```

**Step 2: Load Bundle in Runtime**

```python
from infra.github.runtime_integration import load_spec_bundle

bundle = load_spec_bundle(
    bundle_path="spec_bundle.json",
    token=GITHUB_TOKEN,
    verify_ledger=True,
    cache_dir=".spec_cache"
)

# Access specs
lsa_content = bundle["files"]["lsa/spec/LSA_PICC.md"]["content"]
rag_content = bundle["files"]["rag/spec/RAG_POLICY.md"]["content"]

# Generate provenance stamp (for logging)
from infra.github.runtime_integration import generate_provenance_stamp

stamp = generate_provenance_stamp(bundle)
print(stamp)
```

**Provenance Stamp Output:**

```json
{
  "timestamp": "2025-11-05T10:15:00Z",
  "spec_repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
  "commit_sha": "abc123def456...",
  "bundle_id": "lsa-spec-v2.1",
  "files": {
    "lsa/spec/LSA_PICC.md": "sha256:7b41...",
    "rag/spec/RAG_POLICY.md": "sha256:1f0c..."
  }
}
```

### Option 3: Direct API Call

```python
from infra.github.runtime_integration import fetch_file

content, sha256 = fetch_file(
    owner="ourobrancopedro-rgb",
    repo="alter-agro-yara-logica",
    path="lsa/spec/LSA_PICC.md",
    commit_sha="abc123def456...",
    token=GITHUB_TOKEN
)

# Verify against ledger
from infra.github.runtime_integration import verify_against_ledger

verify_against_ledger("lsa/spec/LSA_PICC.md", sha256)
# Raises SpecIntegrityError if mismatch
```

---

## Write Path: Proposing Updates

### Workflow

```
1. Runtime detects need for spec update (e.g., new regulation)
2. Edit spec file locally
3. Use GitWriter to create branch + commit + PR
4. CI validates (path allowlist, hash ledger, KPI gates)
5. Human review + approval
6. Merge (squash + GPG sign)
7. Webhook triggers pin rotation in runtime
```

### Example: Propose LSA Spec Update

```python
from infra.github.git_write_api import GitWriter, update_hash_ledger
from pathlib import Path

# Initialize writer
writer = GitWriter(
    owner="ourobrancopedro-rgb",
    repo="alter-agro-yara-logica",
    token=GITHUB_TOKEN
)

# Read edited spec
new_lsa_content = Path("lsa/spec/LSA_PICC.md").read_text()

# Update hash ledger
ledger_content = update_hash_ledger(
    ledger_path="infra/github/hash_ledger.json",
    updated_files={"lsa/spec/LSA_PICC.md": new_lsa_content}
)

# Create PR
pr_url = writer.propose_spec_update(
    branch_name="yara/update-lsa-spec-2025-11-05",
    files={
        "lsa/spec/LSA_PICC.md": new_lsa_content,
        "infra/github/hash_ledger.json": ledger_content
    },
    commit_message="feat(lsa): tighten PCB gate for FACT/HIGH",
    pr_title="YARA: Update LSA spec + ledger",
    pr_body="""
## Summary
Tightens PCB gate requirement for FACT/HIGH confidence outputs.

## Rationale
Based on Q4-2024 audit findings, PCB reduces false positives by 87%.

## KPI Impact
- Faithfulness @ Premise: 0.82 → 0.89 (projected)
- Contradiction Coverage: 0.92 (unchanged)

## Decision Record
See: DEC-2025-11-04-01
"""
)

print(f"✓ PR created: {pr_url}")
```

### Using CLI

```bash
# Edit file locally
vim lsa/spec/LSA_PICC.md

# Propose via CLI
python infra/github/yara_specs_cli.py propose \\
  --branch yara/update-lsa-spec-2025-11-05 \\
  --edit lsa/spec/LSA_PICC.md \\
  --message "feat(lsa): tighten PCB gate for FACT/HIGH"
```

---

## Webhook Integration

### Setup Webhook Handler

**Run webhook server:**

```bash
export WEBHOOK_SECRET="your-secret"
export YARA_CALLBACK_URL="https://your-runtime.com/api/webhooks/spec-update"

python infra/github/webhook_handler.py
# Listening on http://0.0.0.0:8080/webhooks/github
```

**Configure in GitHub:**

1. Go to repo **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL**: `https://your-domain.com/webhooks/github`
3. **Content type**: `application/json`
4. **Secret**: (same as `WEBHOOK_SECRET`)
5. **Events**: Select:
   - `pull_request` (opened, synchronize, closed)
   - `push` (to main)
   - `check_suite` (completed)
   - `workflow_run` (completed)

### Handle Events in YARA Runtime

Your YARA runtime should expose an endpoint that receives notifications:

```python
# In your YARA runtime API
@app.post("/api/webhooks/spec-update")
async def handle_spec_update(request: Request):
    data = await request.json()

    event = data["event"]

    if event == "pr_opened":
        # Run shadow validation on changed specs
        pr_number = data["data"]["pr_number"]
        head_sha = data["data"]["head_sha"]
        await run_shadow_validation(head_sha)

    elif event == "pr_merged":
        # Queue staging pin rotation
        merge_sha = data["data"]["merge_commit_sha"]
        await queue_pin_rotation(merge_sha, environment="staging")

    elif event == "ci_passed_main":
        # Promote to production after CI passes
        commit_sha = data["data"]["commit_sha"]
        await promote_pin(commit_sha, environment="production")

    return {"status": "processed"}
```

### Manual Pin Rotation

```bash
# Trigger manual rotation via webhook endpoint
curl -X POST http://localhost:8080/trigger/rotate-pin \\
  -H "Content-Type: application/json" \\
  -d '{"commit_sha": "abc123...", "environment": "production"}'
```

**Or via CLI:**

```bash
python infra/github/yara_specs_cli.py promote \\
  --commit abc123... \\
  --environment production
```

---

## Provenance Tracking

### Log Provenance in Every Inference

**Example YARA output with provenance:**

```json
{
  "inference_id": "INF-2025-11-05-001",
  "timestamp": "2025-11-05T14:30:00Z",
  "conclusion": "PCB obrigatório para FACT/HIGH",
  "confidence": "HIGH",
  "premises": ["P1", "P2", "P3"],
  "inferences": ["I1", "I2"],
  "contradictions": [],
  "specs_provenance": {
    "repo": "ourobrancopedro-rgb/alter-agro-yara-logica",
    "commit": "abc123def456789...",
    "files": {
      "lsa/spec/LSA_PICC.md": "sha256:7b41c9f8...",
      "rag/spec/RAG_POLICY.md": "sha256:1f0c3e82..."
    },
    "bundle_id": "lsa-spec-v2.1",
    "sealed_at": "2025-11-04T21:10:00-03:00"
  }
}
```

### Query Provenance Retroactively

```python
# Given an inference ID, retrieve exact specs used
def get_inference_specs(inference_id: str):
    inference = db.get_inference(inference_id)
    provenance = inference["specs_provenance"]

    # Fetch exact specs from GitHub
    commit_sha = provenance["commit"]

    for path, sha256_with_prefix in provenance["files"].items():
        sha256 = sha256_with_prefix.split(":")[1]

        content, fetched_sha = fetch_file(
            owner="ourobrancopedro-rgb",
            repo="alter-agro-yara-logica",
            path=path,
            commit_sha=commit_sha,
            token=GITHUB_TOKEN
        )

        assert fetched_sha == sha256, f"Provenance mismatch for {path}"

        print(f"✓ Verified {path} @ {commit_sha[:7]}")
```

---

## Security Best Practices

### 1. GitHub Token Management

**DO:**
- ✓ Use GitHub App with least privilege (read-only for contents)
- ✓ Store tokens in secrets manager (AWS Secrets Manager, Vault, etc.)
- ✓ Rotate tokens every 90 days
- ✓ Use environment variables, never hardcode

**DON'T:**
- ✗ Commit tokens to Git
- ✗ Share tokens across environments
- ✗ Use tokens with write access unless necessary

### 2. Webhook Security

- **Always verify** webhook signatures (`X-Hub-Signature-256`)
- Use `hmac.compare_digest()` (timing-safe comparison)
- Reject requests with missing/invalid signatures

### 3. Hash Ledger Integrity

- **Never bypass** hash verification
- If hash mismatch detected → **abort** and alert
- Log all hash mismatches for forensics

### 4. Pin Rotation Policy

- **Staging first** → shadow validate → **then production**
- Automated rotation requires CI green + human approval
- Keep last 3 pins for rollback

---

## Troubleshooting

### Error: "Hash mismatch detected"

**Cause:** File content doesn't match hash ledger

**Fix:**
1. Check if ledger is up-to-date: `python infra/github/verify_hashes.py`
2. If ledger is wrong, update it: `python infra/github/verify_hashes.py --update`
3. If file is wrong, revert to correct version

### Error: "GitHub API rate limit exceeded"

**Cause:** Too many API calls

**Fix:**
1. Use authenticated requests (increases limit from 60 to 5,000/hour)
2. Implement caching (use `cache_dir` in `load_spec_bundle`)
3. Monitor rate limit: `GET https://api.github.com/rate_limit`

### Error: "Resource not accessible by integration"

**Cause:** GitHub App lacks required permissions

**Fix:**
1. Go to App settings → Permissions
2. Grant **Contents: Read** permission
3. Accept new permissions in installation

### Webhook not receiving events

**Cause:** Webhook not configured or URL inaccessible

**Fix:**
1. Verify webhook URL is publicly accessible
2. Check webhook secret matches
3. Test with: `curl -X POST <webhook_url> -d '{}'` (should return 401 without signature)

### Commit not GPG-signed

**Cause:** Commits created via API aren't automatically signed

**Fix:**
- GitHub App commits are signed by GitHub (using noreply commit email)
- For manual commits, ensure GPG key is configured: `git config --global user.signingkey <key>`
- Verify: `git log --show-signature -1`

---

## Advanced Topics

### Shadow Validation on PRs

Run YARA runtime against PR specs **before** merging:

```python
async def run_shadow_validation(pr_number: int, head_sha: str):
    # Generate SpecBundle for PR branch
    bundle = generate_spec_bundle(
        bundle_id=f"shadow-pr-{pr_number}",
        commit_sha=head_sha,
        files=auto_discover_spec_files()
    )

    # Load in isolated environment
    test_runtime = YARARuntimeIsolated()
    test_runtime.load_specs(bundle)

    # Run test cases
    results = test_runtime.run_test_suite()

    # Report back to PR
    if results["all_passed"]:
        post_pr_comment(pr_number, "✓ Shadow validation passed")
    else:
        post_pr_comment(pr_number, f"✗ Shadow validation failed: {results['errors']}")
```

### Rollback to Previous Pin

```bash
# Get commit from 7 days ago
OLD_COMMIT=$(git log --since="7 days ago" --format="%H" | tail -1)

# Rotate pin back
python infra/github/yara_specs_cli.py promote \\
  --commit $OLD_COMMIT \\
  --environment production

# Verify
python infra/github/yara_specs_cli.py verify \\
  --bundle spec_bundle_backup.json
```

### Multi-Environment Pins

```
Development   → HEAD (latest)
Staging       → Last merged PR commit
Production    → Last CI-green commit on main (+ 24h soak time)
```

Store in runtime config:

```json
{
  "pins": {
    "development": "abc123...",
    "staging": "def456...",
    "production": "789abc..."
  }
}
```

---

## Next Steps

1. **Set up GitHub App** — See [GITHUB_APP_SETUP.md](GITHUB_APP_SETUP.md)
2. **Configure webhooks** — Point to your YARA runtime
3. **Integrate runtime** — Use `runtime_integration.py` in your codebase
4. **Test end-to-end** — Propose a test PR and verify pin rotation
5. **Monitor** — Set up alerts for hash mismatches, rate limits, webhook failures

---

## Support

**Questions?** Contact [security@alteragro.com.br](mailto:security@alteragro.com.br)

**Issues?** Open an issue: https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues

**Documentation:** See `docs/` for more guides:
- [Architecture Overview](README_ARCH.md)
- [GitHub App Setup](GITHUB_APP_SETUP.md)
- [Decision Records](DECISION_RECORDS.md)
- [Auditor Guide](AUDITOR_GUIDE.md)

---

**© 2025 Alter Agro Ltda. — "No Hash, No Commit"**
