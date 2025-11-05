# Leak Detection & Monitoring Setup Guide

**YARA Lógica Repository Security**

This guide covers setup and configuration of automated leak detection, fork monitoring, and GitHub Advanced Security features for protecting intellectual property.

---

## Table of Contents

1. [Overview](#overview)
2. [Fork Monitoring](#fork-monitoring)
3. [External Leak Detection](#external-leak-detection)
4. [GitHub Advanced Security](#github-advanced-security)
5. [Monitoring Dashboard](#monitoring-dashboard)
6. [Alerting Configuration](#alerting-configuration)
7. [Response Procedures](#response-procedures)
8. [Advanced Configuration](#advanced-configuration)

---

## Overview

### What This System Monitors

The leak detection system provides continuous monitoring for:

- ✅ **New public forks** of the repository
- ✅ **Fork visibility changes** (private → public)
- ✅ **Unauthorized repository copies** on GitHub (non-forks)
- ✅ **Code leaks on external platforms** (GitLab, Bitbucket)
- ✅ **Paste site leaks** (Gist, Pastebin, etc.)
- ✅ **Web presence** of brand/architecture names + source code keywords
- ✅ **Repository settings changes** (visibility, forking permissions)
- ✅ **Code signature matches** across GitHub

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Actions Workflow                     │
│                (Every 6 hours + manual trigger)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬────────────────┐
        │              │               │                │
        ▼              ▼               ▼                ▼
┌──────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────┐
│  Fork    │  │  External  │  │  GitHub  │  │  Settings   │
│Monitoring│  │   Leak     │  │  Code    │  │  Monitor    │
│          │  │ Detection  │  │  Search  │  │             │
└────┬─────┘  └─────┬──────┘  └─────┬────┘  └──────┬──────┘
     │              │               │               │
     └──────────────┴───────────────┴───────────────┘
                           │
                           ▼
               ┌───────────────────────┐
               │   Reports Generated   │
               │  - JSON (artifact)    │
               │  - Markdown (artifact)│
               │  - GitHub Issues      │
               │  - Email alerts       │
               └───────────────────────┘
```

### Components

| Component | Purpose | Frequency |
|-----------|---------|-----------|
| `leak-detection-monitoring.yml` | GitHub Actions workflow orchestration | Every 6 hours |
| `monitor_forks.py` | Fork detection and visibility analysis | Per workflow run |
| `detect_leaks.py` | External platform leak detection | Per workflow run |
| GitHub Code Search | Signature-based leak detection | Per workflow run |
| Settings Monitor | Repository configuration monitoring | Per workflow run |

---

## Fork Monitoring

### How It Works

The fork monitoring system:

1. **Fetches all forks** of the repository via GitHub API
2. **Analyzes each fork** for security concerns:
   - Public visibility (potential IP exposure)
   - Recent creation (new forks in last 24h/7d)
   - Modifications (potential redistribution)
   - Size increases (unauthorized additions)
   - Different default branch (potential tampering)
3. **Generates alerts** for high-risk forks
4. **Creates GitHub issues** for security team review

### Configuration

**Automated (Default):**

The fork monitor runs automatically every 6 hours via GitHub Actions. No configuration needed.

**Manual Trigger:**

```bash
# Via GitHub Actions UI
# Navigate to: Actions → Leak Detection Monitoring → Run workflow

# Via GitHub CLI
gh workflow run leak-detection-monitoring.yml

# Via API
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/leak-detection-monitoring.yml/dispatches \
  -d '{"ref":"main"}'
```

**Local Testing:**

```bash
# Install dependencies
pip install PyGithub python-dateutil

# Run fork monitor
python infra/github/monitor_forks.py \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica \
  --token YOUR_GITHUB_TOKEN

# Create issue on alerts
python infra/github/monitor_forks.py \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica \
  --token YOUR_GITHUB_TOKEN \
  --create-issue-on-alert
```

### Alert Criteria

| Severity | Criteria | Action |
|----------|----------|--------|
| **High** | New public fork created (24h) | Immediate GitHub issue |
| **High** | Fork size > 1.5x parent size | Immediate GitHub issue |
| **Medium** | New public fork (7d) | Log in report |
| **Medium** | Recent modifications on public fork | Log in report |
| **Low** | Different default branch | Log in report |

### Reports Generated

**JSON Report** (`fork_monitoring_report.json`):
```json
{
  "scan_time": "2025-11-05T12:00:00Z",
  "repository": "ourobrancopedro-rgb/alter-agro-yara-logica",
  "total_forks": 5,
  "public_forks": 3,
  "private_forks": 2,
  "new_forks_24h": 1,
  "new_forks_7d": 2,
  "suspicious_forks": [...],
  "alerts": [...]
}
```

**Markdown Report** (`fork_monitoring_report.md`):

Human-readable summary with:
- Fork statistics
- Alert details
- Suspicious fork list
- Recommended actions

---

## External Leak Detection

### How It Works

The external leak detector searches for unauthorized repository copies across:

1. **GitHub** (non-fork copies using code signatures)
2. **GitLab** (public projects matching brand/architecture)
3. **Bitbucket** (public repositories with matching names)
4. **Gist** (code snippets containing signatures)
5. **Web Search** (deep scan mode - requires API key)

### Search Strategies

**Code Signatures:**

Unique patterns from the codebase used for detection:
- `"LSA/PICC faith premise >= 0.80"`
- `"contradiction coverage >= 0.90"`
- `"infra/github/hash_ledger.json"`
- `"YARA Lógica Public Specifications"`
- `"calculate_contradiction_coverage"`

**Brand + Architecture:**
- `"Alter Agro" + "YARA Lógica"`
- `"YARA Lógica" + "LSA" + "PICC"`
- `"Alter Agro" + "source code"`

### Configuration

**Standard Scan (Default):**

```yaml
# Runs automatically every 6 hours
# Searches: GitHub, GitLab, Bitbucket, Gist
```

**Deep Scan (Manual):**

```bash
# Via GitHub Actions UI
# Navigate to: Actions → Leak Detection Monitoring → Run workflow
# Enable "Perform deep scan"
# Add extra keywords if needed

# Via GitHub CLI
gh workflow run leak-detection-monitoring.yml \
  -f deep_scan=true \
  -f search_keywords="custom,keywords,here"
```

**Local Testing:**

```bash
# Install dependencies
pip install requests beautifulsoup4 python-dateutil

# Run leak detector
python infra/github/detect_leaks.py \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica \
  --token YOUR_GITHUB_TOKEN \
  --brand "Alter Agro" \
  --architecture "YARA Lógica" \
  --keywords "LSA,PICC,RAG Policy" \
  --deep-scan true

# Create issue on leaks
python infra/github/detect_leaks.py \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica \
  --token YOUR_GITHUB_TOKEN \
  --brand "Alter Agro" \
  --architecture "YARA Lógica" \
  --keywords "LSA,PICC,RAG Policy" \
  --create-issue-on-alert
```

### Confidence Levels

| Confidence | Criteria | Action |
|------------|----------|--------|
| **High** | Brand + Architecture + 2+ keywords | Immediate alert |
| **Medium** | Brand OR Architecture + 1 keyword | Review required |
| **Low** | Partial keyword match | Log only |

---

## GitHub Advanced Security

GitHub Advanced Security (GHAS) provides enterprise-grade security features. This section covers setup and best practices.

### Features Available

| Feature | Description | Availability |
|---------|-------------|--------------|
| **Secret Scanning** | Automated detection of committed secrets | Free for public repos |
| **Secret Scanning Push Protection** | Blocks commits with secrets | Requires GHAS license |
| **Dependency Review** | Identifies vulnerable dependencies | Free for public repos |
| **Code Scanning (CodeQL)** | Static analysis for vulnerabilities | Free for public repos |
| **Security Advisories** | Private vulnerability reporting | Free for all repos |

### Setup: Secret Scanning

**Enable for Repository:**

1. Navigate to: **Settings** → **Code security and analysis**
2. Enable **Secret scanning**
3. Enable **Push protection** (if available)

**Configure Alerts:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

**Custom Patterns (Enterprise only):**

For Alter Agro-specific patterns, create custom secret scanning patterns:

```
# Alter Agro API Keys
Pattern: alter[_-]?agro[_-]?api[_-]?key[:\s]*[a-zA-Z0-9]{32,}

# YARA Lógica Credentials
Pattern: yara[_-]?logica[_-]?(password|secret|token)[:\s]*[a-zA-Z0-9]{16,}
```

### Setup: Code Scanning (CodeQL)

**Create Workflow:**

```yaml
# .github/workflows/codeql.yml
name: CodeQL Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: ['python', 'javascript']

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

### Setup: Dependency Review

**Enable in Workflow:**

```yaml
# Add to .github/workflows/ci.yml
- name: Dependency Review
  uses: actions/dependency-review-action@v4
  if: github.event_name == 'pull_request'
```

### Security Advisories

**Enable Private Reporting:**

1. Navigate to: **Settings** → **Code security and analysis**
2. Enable **Private vulnerability reporting**
3. Users can now report vulnerabilities privately via **Security** tab

**Responding to Advisories:**

1. Review report in **Security** → **Advisories**
2. Assess severity and impact
3. Develop fix in private fork
4. Coordinate disclosure with reporter
5. Publish advisory after fix deployed

---

## Monitoring Dashboard

### GitHub Actions Dashboard

View monitoring status:

```
Repository → Actions → Leak Detection Monitoring
```

**Key Metrics:**

- Workflow run status (success/failure)
- Scan duration
- Number of platforms scanned
- Leaks detected by severity

### Artifacts

Each workflow run generates artifacts (retained 90 days):

- `fork-monitoring-report` (JSON + Markdown)
- `leak-detection-report` (JSON + Markdown)

**Download Artifacts:**

```bash
# Via GitHub CLI
gh run download RUN_ID --name fork-monitoring-report

# Via Web UI
# Navigate to workflow run → Artifacts section → Download
```

### Custom Dashboard (Optional)

Create a monitoring dashboard using GitHub Pages:

```bash
# Generate HTML dashboard
python infra/github/security_dashboard.py --output docs/dashboard.html

# Commit and push
git add docs/dashboard.html
git commit -m "docs: update security dashboard"
git push
```

---

## Alerting Configuration

### GitHub Issues

**Automatic Issue Creation:**

Workflows automatically create GitHub issues for:
- High-severity fork alerts (new public forks)
- High-confidence leak detection
- Code signature matches

**Issue Labels:**

- `security` - All security-related issues
- `leak-detection` - External leak detected
- `fork-alert` - Fork monitoring alert
- `urgent` - Requires immediate attention

**De-duplication:**

System checks for existing open issues within last 7 days to avoid duplicate alerts.

### Email Notifications

**Enable via GitHub:**

1. Navigate to: **Profile** → **Settings** → **Notifications**
2. Enable **Issues** notifications
3. Enable **Actions** notifications
4. Set email address

**Filter by Label:**

Create email filter rules for:
- `label:security` → High priority folder
- `label:urgent` → Immediate attention

### Slack/Teams Integration (Optional)

**Webhook Setup:**

1. Create incoming webhook in Slack/Teams
2. Add webhook URL to repository secrets: `SLACK_WEBHOOK_URL`
3. Update workflow to send notifications:

```yaml
- name: Send Slack notification
  if: env.FOUND_LEAKS > 0
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "🚨 Leak Detection Alert: ${{ env.FOUND_LEAKS }} potential leaks found",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Leak Detection Alert*\n${{ env.FOUND_LEAKS }} potential code leaks detected."
            }
          }
        ]
      }
```

---

## Response Procedures

### When Fork Alert is Triggered

**1. Review the Fork**

```bash
# Check fork details
gh repo view FORK_OWNER/FORK_NAME

# Compare with parent
gh repo compare ourobrancopedro-rgb/alter-agro-yara-logica...FORK_OWNER:FORK_NAME
```

**2. Assess Intent**

- ✅ **Legitimate**: Team member, collaborator, authorized partner
- ⚠️ **Uncertain**: Unknown user, no clear purpose
- 🚨 **Suspicious**: Commercial use, redistribution, license violation

**3. Take Action**

**For Legitimate Forks:**
- No action required
- Monitor for future changes

**For Uncertain Forks:**
- Contact fork owner politely via GitHub
- Request clarification of intent
- Monitor closely

**For Suspicious Forks:**
- Document evidence (screenshots, URLs, timestamps)
- Contact fork owner requesting takedown
- If no response within 7 days, escalate to legal team
- File DMCA takedown notice if necessary

### When External Leak is Detected

**1. Verify the Leak**

```bash
# Visit reported URL
# Check if content matches repository
# Assess confidence level from report
```

**2. Document Evidence**

- Take screenshots of infringing content
- Save full URLs and timestamps
- Archive page content (use archive.org)
- Note any license violations

**3. Contact Platform**

**GitLab:**
```
Report via: https://about.gitlab.com/handbook/support/workflows/abuse_response.html
Email: abuse@gitlab.com
```

**Bitbucket:**
```
Report via: https://support.atlassian.com/bitbucket-cloud/docs/report-abuse/
```

**GitHub (non-fork):**
```
DMCA: https://github.com/contact/dmca
Email: copyright@github.com
```

**4. Legal Escalation**

If platform doesn't respond or refuses removal:
- Contact: legal@alteragro.com.br
- Provide all documentation
- Consider cease & desist letter
- Potential legal action for significant violations

### DMCA Takedown Process

**1. Prepare Notice**

Required elements:
- Your contact information
- Identification of copyrighted work
- Identification of infringing material
- Statement of good faith belief
- Statement of accuracy
- Physical or electronic signature

**2. Submit to Platform**

- GitHub: https://github.com/contact/dmca
- GitLab: abuse@gitlab.com
- Bitbucket: Atlassian support system

**3. Follow Up**

- Platforms typically respond within 24-48 hours
- Content removed within 1-10 business days
- Counter-notice possible (rare for clear violations)

---

## Advanced Configuration

### Custom Keywords

Add domain-specific keywords to improve detection:

```bash
# Via workflow manual trigger
gh workflow run leak-detection-monitoring.yml \
  -f search_keywords="custom_function_name,unique_variable,proprietary_algorithm"
```

### Rate Limiting

**GitHub API Limits:**

- Authenticated: 5,000 requests/hour
- Code Search: 10 requests/minute

**Mitigation:**

- Stagger searches with delays (implemented)
- Use GitHub App authentication for higher limits (optional)
- Schedule scans during low-activity periods

### Multi-Repository Monitoring

To monitor multiple repositories:

```yaml
# Create matrix strategy in workflow
strategy:
  matrix:
    repo:
      - ourobrancopedro-rgb/alter-agro-yara-logica
      - ourobrancopedro-rgb/private-repo-name
```

### Integration with SIEM

Export monitoring data to Security Information and Event Management (SIEM) systems:

```bash
# Convert reports to SIEM format (CEF, LEEF, etc.)
python infra/github/export_to_siem.py \
  --format cef \
  --input leak_detection_report.json \
  --output siem_events.log

# Send to SIEM via syslog
logger -t leak-detection -f siem_events.log
```

---

## Troubleshooting

### Workflow Not Running

**Check:**

1. Workflow file syntax: `gh workflow view leak-detection-monitoring.yml`
2. Repository Actions enabled: Settings → Actions → General
3. Schedule triggers enabled (not disabled by repository admin)

### No Alerts Despite Known Forks

**Check:**

1. Fork creation date (alerts only for last 24h/7d)
2. Fork visibility (private forks don't generate high-severity alerts)
3. Alert thresholds in code

### API Rate Limiting

**Symptoms:**

- `403 Forbidden` errors
- `X-RateLimit-Remaining: 0` headers

**Solutions:**

1. Reduce scan frequency
2. Use GitHub App authentication
3. Implement exponential backoff (already implemented)
4. Stagger scans across time

### False Positives

**Common Causes:**

- Generic keywords matching unrelated projects
- Citations or references to YARA Lógica in research
- Legitimate educational use

**Solutions:**

1. Review confidence levels (focus on high-confidence only)
2. Refine keywords to be more specific
3. Maintain allowlist of known legitimate repos
4. Manually review medium-confidence matches

---

## Best Practices

### Security

- ✅ Rotate GitHub tokens every 90 days
- ✅ Use repository secrets for sensitive data
- ✅ Limit workflow permissions (principle of least privilege)
- ✅ Review alerts within 24 hours of generation
- ✅ Document all takedown requests

### Operational

- ✅ Run deep scans weekly (not every 6 hours)
- ✅ Review monitoring reports monthly
- ✅ Update keywords quarterly based on findings
- ✅ Test workflows after any changes
- ✅ Archive reports for compliance (90+ days retention)

### Legal

- ✅ Always attempt friendly contact before DMCA
- ✅ Document all communications
- ✅ Verify license compliance before takedown
- ✅ Escalate significant violations to legal team
- ✅ Maintain evidence archive

---

## Support & Resources

### Documentation

- [Security Policy](../.github/SECURITY.md)
- [Information Barrier Guide](information-barrier.md)
- [Private Repository Guide](PRIVATE_REPOSITORY_GUIDE.md)

### Contacts

- **Security Issues:** security@alteragro.com.br
- **Legal Matters:** legal@alteragro.com.br
- **General Questions:** hello@alteragro.com.br

### External Resources

- [GitHub DMCA Guide](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy)
- [GitHub Advanced Security Docs](https://docs.github.com/en/code-security)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-05
**Next Review:** 2026-02-05

**© 2025 Alter Agro Ltda. All rights reserved.**
