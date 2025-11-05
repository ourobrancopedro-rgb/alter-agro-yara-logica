# Leak Detection & Monitoring Quick Start

**YARA Lógica — Repository Security Monitoring**

Quick reference for repository leak detection and fork monitoring.

---

## 🚀 Quick Start

### Automated Monitoring (No Setup Required)

The system runs automatically **every 6 hours** via GitHub Actions:

✅ Monitors new public forks
✅ Detects unauthorized code copies
✅ Searches external platforms (GitLab, Bitbucket)
✅ Generates security reports
✅ Creates alerts for security team

**View Status:** [Actions → Leak Detection Monitoring](../../actions/workflows/leak-detection-monitoring.yml)

---

## 🔍 Manual Scan

### Via GitHub Actions UI

1. Go to **Actions** tab
2. Select **Leak Detection & Fork Monitoring** workflow
3. Click **Run workflow** dropdown
4. (Optional) Enable **deep scan** for comprehensive search
5. (Optional) Add **extra keywords** for custom searches
6. Click **Run workflow**

### Via GitHub CLI

```bash
# Standard scan
gh workflow run leak-detection-monitoring.yml

# Deep scan with custom keywords
gh workflow run leak-detection-monitoring.yml \
  -f deep_scan=true \
  -f search_keywords="custom,keywords,here"
```

### Local Testing

```bash
# Install dependencies
pip install PyGithub requests beautifulsoup4 python-dateutil

# Test fork monitoring
python infra/github/monitor_forks.py \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica \
  --token YOUR_GITHUB_TOKEN

# Test leak detection
python infra/github/detect_leaks.py \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica \
  --token YOUR_GITHUB_TOKEN \
  --brand "Alter Agro" \
  --architecture "YARA Lógica" \
  --keywords "LSA,PICC,RAG"
```

---

## 📊 View Reports

### Workflow Artifacts

Each scan generates downloadable reports:

1. Navigate to **Actions** → Select workflow run
2. Scroll to **Artifacts** section
3. Download:
   - `fork-monitoring-report` (JSON + Markdown)
   - `leak-detection-report` (JSON + Markdown)

### Via GitHub CLI

```bash
# List recent runs
gh run list --workflow=leak-detection-monitoring.yml

# Download artifacts from latest run
gh run download --name fork-monitoring-report
gh run download --name leak-detection-report
```

---

## 🚨 Alerts & Notifications

### When You'll Be Alerted

**Automatic GitHub Issues Created For:**

- 🚨 **New public forks** (last 24 hours)
- 🚨 **High-confidence code leaks** on external platforms
- 🚨 **Code signature matches** across GitHub
- ⚠️ **Fork size increases** (>150% of parent)

**Issue Labels:**
- `security` - Security-related
- `leak-detection` - External leak
- `fork-alert` - Fork monitoring
- `urgent` - Immediate attention required

### Enable Email Notifications

1. **Settings** → **Notifications**
2. Enable **Issues** and **Actions** notifications
3. Set email address
4. (Optional) Create filter for `label:security`

---

## 📋 What to Do When Alerted

### For Fork Alerts

**1. Review the Fork**

```bash
gh repo view FORK_OWNER/FORK_REPO
```

**2. Determine Intent**

- ✅ **Legitimate**: Team member, collaborator → No action
- ⚠️ **Unclear**: Unknown user → Contact owner
- 🚨 **Suspicious**: Commercial use, redistribution → Escalate

**3. Take Action**

| Type | Action |
|------|--------|
| Legitimate | Monitor for changes |
| Unclear | Contact fork owner politely |
| Suspicious | Document + escalate to legal@alteragro.com.br |

### For Leak Alerts

**1. Verify the Leak**

- Visit reported URL
- Confirm content matches repository
- Check confidence level from report

**2. Document Evidence**

- Screenshots
- Full URLs and timestamps
- License violations noted

**3. Initiate Takedown**

- **Friendly contact** first (if owner contact available)
- **Platform report** if no response (7 days)
- **DMCA takedown** if platform ignores
- **Legal escalation** for significant violations

---

## 🔧 Configuration

### Adjust Scan Frequency

Edit `.github/workflows/leak-detection-monitoring.yml`:

```yaml
on:
  schedule:
    # Every 6 hours (default)
    - cron: '0 */6 * * *'

    # Or choose your own:
    # - cron: '0 */12 * * *'  # Every 12 hours
    # - cron: '0 0 * * *'     # Daily at midnight
    # - cron: '0 0 * * 1'     # Weekly on Monday
```

### Add Custom Keywords

For better detection of your specific code:

```bash
# Via manual workflow trigger
gh workflow run leak-detection-monitoring.yml \
  -f search_keywords="your_unique_function,custom_class,proprietary_algo"
```

### Disable Monitoring (Not Recommended)

To temporarily disable:

```bash
# Disable workflow
gh workflow disable leak-detection-monitoring.yml

# Re-enable later
gh workflow enable leak-detection-monitoring.yml
```

---

## 📖 Full Documentation

For detailed setup, configuration, and advanced features:

→ **[Complete Setup Guide](LEAK_DETECTION_SETUP.md)**

Topics covered:
- GitHub Advanced Security setup
- Custom dashboards
- SIEM integration
- DMCA takedown procedures
- Response workflows
- Troubleshooting

---

## 🛡️ Security Best Practices

### ✅ DO

- Review alerts within 24 hours
- Rotate GitHub tokens every 90 days
- Document all takedown requests
- Run deep scans weekly
- Update keywords quarterly

### ❌ DON'T

- Ignore high-severity alerts
- File DMCA without attempting contact first
- Share monitoring tokens
- Disable monitoring without approval
- Delete evidence before documenting

---

## 📞 Support

### Contacts

| Issue Type | Contact |
|------------|---------|
| Security incidents | security@alteragro.com.br |
| Legal matters | legal@alteragro.com.br |
| General questions | hello@alteragro.com.br |

### Resources

- [Security Policy](../.github/SECURITY.md)
- [Leak Detection Setup Guide](LEAK_DETECTION_SETUP.md)
- [GitHub DMCA Guide](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy)

---

## 🔬 System Health Check

Run this to verify monitoring is working:

```bash
# Check workflow status
gh workflow view leak-detection-monitoring.yml

# List recent runs
gh run list --workflow=leak-detection-monitoring.yml --limit 5

# View latest run
gh run view --log

# Verify scripts are executable
ls -la infra/github/monitor_forks.py infra/github/detect_leaks.py

# Test fork monitoring (local)
python infra/github/monitor_forks.py \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica \
  --token $GITHUB_TOKEN
```

**Expected Output:**

```
✅ Loaded repository: ourobrancopedro-rgb/alter-agro-yara-logica
🔍 Analyzing forks...
Total forks: X

======================================================================
FORK MONITORING SUMMARY
======================================================================
Repository: ourobrancopedro-rgb/alter-agro-yara-logica
Total Forks: X
  - Public: X
  - Private: X
Suspicious Forks: X
Alerts Generated: X
======================================================================

✅ Monitoring complete
```

---

**Quick Reference Version:** 1.0.0
**Last Updated:** 2025-11-05

For detailed documentation, see [LEAK_DETECTION_SETUP.md](LEAK_DETECTION_SETUP.md)
