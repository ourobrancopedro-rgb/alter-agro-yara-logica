# Security Policy — YARA Lógica

**Alter Agro Ltda. — Security & Responsible Disclosure**

---

## 📋 Overview

This repository (`alter-agro-yara-logica`) publishes **specifications and audit artifacts only** under the BUSL-1.1 license. Operational systems, runtime code, prompts, models, and private infrastructure are maintained separately in private repositories and are **not** in scope for this public repository.

This security policy covers:

1. **Vulnerability Reporting** — How to report security issues responsibly
2. **Supported Versions** — What versions receive security updates
3. **Response Process** — Our commitment to security researchers
4. **Security Guarantees** — What protections are in place
5. **Out of Scope** — What is not covered by this policy
6. **Recognition Program** — Hall of Fame for contributors

---

## 🔒 Supported Versions

Security updates are provided for the following versions of YARA Lógica specifications:

| Version | Supported | Notes |
| :------ | :-------- | :---- |
| 1.x (current) | ✅ Yes | Active development and security updates |
| 0.x (legacy) | ⚠️ Limited | Critical security fixes only |
| < 0.1 (pre-release) | ❌ No | Unsupported - upgrade required |

**Note:** Since this is a specification-only repository, "versions" refer to major revisions of the LSA/PICC and RAG methodologies documented here. Runtime implementations may have separate versioning.

---

## 📬 Reporting a Vulnerability

### Security Contact

**Email:** [security@alteragro.com.br](mailto:security@alteragro.com.br)
**Subject Line:** `[SECURITY] YARA Lógica - <brief description>`

**For encrypted communication:**
- PGP Public Key: [Available on request or at keybase.io/alteragro]
- Signal: [Contact security@ for secure messaging number]

### What to Include in Your Report

Please provide as much detail as possible:

1. **Vulnerability Description**
   - Type of issue (information disclosure, injection, logic flaw, etc.)
   - Potential impact (confidentiality, integrity, availability)

2. **Affected Component**
   - Specific file(s) or specification section(s)
   - Version or commit hash affected

3. **Steps to Reproduce**
   - Clear, numbered steps
   - Include any necessary prerequisites
   - Provide proof-of-concept if possible (code, screenshots)

4. **Impact Assessment**
   - Your assessment of severity (Low/Medium/High/Critical)
   - Potential attack scenarios
   - Who could be affected

5. **Recommended Mitigation** (optional)
   - Your suggestions for fixing the issue
   - Workarounds if available

6. **Your Contact Information**
   - Name or handle (pseudonyms accepted)
   - Email for follow-up
   - Preferred method of contact

### Example Report

```
Subject: [SECURITY] YARA Lógica - Information Disclosure in CI Workflow

Description:
The information-barrier.yml workflow may expose sensitive patterns in error
messages when violations are detected, potentially leaking information about
internal naming conventions.

Affected Component:
- File: .github/workflows/information-barrier.yml
- Lines: 156-162
- Commit: abc123def456

Steps to Reproduce:
1. Create a commit with forbidden pattern "internal-api-endpoint"
2. Push to trigger CI
3. Review GitHub Actions logs (publicly accessible)
4. Observe pattern revealed in error message

Impact: Medium
- Public disclosure of internal naming conventions
- Could aid reconnaissance for more targeted attacks
- Limited direct security impact

Recommendation:
Sanitize error messages to show only generic violation type, not matched content.

Researcher: Jane Doe (jane@example.com)
```

---

## ⏱️ Response Timeline

We are committed to timely responses:

| Stage | Timeline | Description |
| :---- | :------- | :---------- |
| **Initial Acknowledgment** | 24 hours | We confirm receipt of your report |
| **Initial Assessment** | 3 business days | We assess severity and validity |
| **Detailed Response** | 10 business days | We provide our analysis and planned actions |
| **Fix Development** | Varies by severity | See table below |
| **Disclosure** | Coordinated | We coordinate public disclosure with you |

### Fix Timelines by Severity

| Severity | Target Fix Time | Description |
| :------- | :-------------- | :---------- |
| **Critical** | 24-48 hours | Active exploitation or severe data exposure risk |
| **High** | 7 days | Significant security impact, no known exploitation |
| **Medium** | 30 days | Moderate impact, requires attack complexity |
| **Low** | 90 days | Minimal impact, theoretical or edge case |

**Note:** These are target timelines for specification updates. Runtime fixes (in private repositories) follow separate, often faster, timelines.

---

## 🛡️ Security Guarantees & Protections

### What We Protect

This repository implements multiple security layers:

#### 1. Information Barrier System
- **Automated secret scanning** (TruffleHog, GitLeaks) on every commit
- **Custom DLP scanner** for Alter Agro-specific patterns
- **Pre-commit hooks** for client-side validation
- **Continuous monitoring** for forbidden content

#### 2. Integrity Verification
- **GPG-signed commits** required for all changes
- **Hash ledger** (`infra/github/hash_ledger.json`) for cryptographic binding
- **Diff-based scope guard** enforcing allowlist compliance
- **KPI scoring** for logical consistency

#### 3. Access Control
- **Branch protection** on main branch
- **Required reviews** (Security + Engineering signoff)
- **Status checks** must pass before merge
- **No force pushes** allowed

#### 4. Content Restrictions
- **Spec-only enforcement** — no runtime code allowed
- **File type validation** by directory
- **File size limits** to prevent binary uploads
- **Symlink detection** (security risk mitigation)

### What We Monitor

Continuous monitoring includes:

- Commits for secrets, API keys, credentials
- Pull requests for policy violations
- Repository settings changes
- Collaborator additions
- Webhook modifications
- Deploy key additions
- File integrity (hash mismatches)

---

## 🚫 Out of Scope

The following are **outside the scope** of this security policy:

### Not Applicable to This Repository

- **Runtime vulnerabilities** (SQL injection, XSS, etc.) — This is a spec-only repo with no executable code
- **DoS attacks** on GitHub infrastructure — Report to GitHub directly
- **Social engineering** or phishing attempts
- **Physical security** of Alter Agro facilities
- **Vulnerabilities in third-party dependencies** — Report to the respective project

### Issues We Cannot Accept

- **Issues requiring violation of law or ToS**
- **Issues in forked repositories** (not maintained by us)
- **Spam or low-quality reports**
- **Publicly disclosed issues** (0-day disclosure) — Please follow responsible disclosure
- **Attacks requiring user interaction** (e.g., "user must click malicious link in issue comment")

### Private Systems (Separate Scope)

Security issues in Alter Agro's **private runtime systems** are handled separately:

- Contact [security@alteragro.com.br](mailto:security@alteragro.com.br) with details
- Include "PRIVATE SYSTEM" in subject line
- Expect separate process and potentially different terms
- Bug bounty may apply (inquire)

---

## 🎯 In Scope Security Research

We **encourage** research on:

✅ **Information Disclosure**
- Secrets or credentials leaked in commits
- Sensitive patterns in specifications
- Internal infrastructure details exposed

✅ **Integrity Violations**
- Bypassing hash ledger verification
- Circumventing allowlist enforcement
- GPG signature forging or verification bypass

✅ **Policy Bypass**
- Smuggling prohibited content past CI/CD
- Evading secret scanners
- Allowlist or scope guard circumvention

✅ **Supply Chain Security**
- Dependency confusion or substitution
- Malicious workflow injection
- Compromised CI/CD pipeline

✅ **Access Control Issues**
- Unauthorized repository access
- Branch protection bypass
- Permission escalation

---

## 🏆 Hall of Fame

We recognize and thank security researchers who help protect YARA Lógica:

| Researcher | Date | Issue | Severity |
| :--------- | :--- | :---- | :------- |
| *No reports yet* | — | — | — |

**Recognition Criteria:**
- Responsible disclosure followed
- Valid security issue confirmed
- Researcher consents to public acknowledgment

**Opt-Out:** If you prefer to remain anonymous, please indicate this in your report.

---

## 💰 Bug Bounty Program

**Status:** 🚧 Under Development

Alter Agro is evaluating a formal bug bounty program for YARA Lógica. Until then:

- **Monetary rewards** are considered on a case-by-case basis for exceptional findings
- **Swag and recognition** for all valid reports
- **Early access** to new features for contributing researchers

Interested in beta testing our bug bounty program? Email [security@alteragro.com.br](mailto:security@alteragro.com.br) with subject "Bug Bounty Beta Interest".

---

## 🔐 Safe Harbor Policy

Alter Agro commits to **safe harbor** for security researchers:

We will **not** pursue legal action against researchers who:

1. **Act in good faith** — Make reasonable efforts to avoid privacy violations, data destruction, and service disruption
2. **Follow responsible disclosure** — Give us reasonable time to address issues before public disclosure (90 days standard)
3. **Do not exploit** — Do not access more data than necessary to demonstrate the vulnerability
4. **Respect scope** — Focus on systems and issues within scope
5. **Report responsibly** — Use designated channels and provide detailed, actionable information

**If you follow these guidelines, we will:**

- Not initiate legal action against you
- Work with you to understand and resolve the issue
- Recognize your contribution publicly (with your consent)
- Consider you for rewards/bounty (when available)

**Note:** This safe harbor applies to Alter Agro's actions only. We cannot authorize actions against third-party services or infrastructure.

---

## 📜 Disclosure Policy

### Coordinated Disclosure

We prefer **coordinated disclosure**:

1. You report the issue privately to us
2. We work together to understand and fix it
3. We coordinate a public disclosure date
4. We publish details after fix is deployed and users have time to update

**Standard Timeline:** 90 days from initial report (negotiable based on complexity)

### Public Disclosure by Researcher

If you plan to publicly disclose:

- **Give us at least 90 days** to address the issue
- **Coordinate disclosure date** with us
- **Credit our response** if we've been responsive and collaborative
- **Redact sensitive details** that could enable exploitation of unpatched systems

### Public Disclosure by Alter Agro

We may publicly disclose:

- After fix is deployed and verified
- After coordinated disclosure date
- If issue is independently discovered and disclosed publicly
- If required by law or regulation

We will:

- Credit the researcher (with consent)
- Provide technical details and impact assessment
- Link to patches and remediation guidance

---

## 🔍 Security Audit & Verification

### Internal Audits

Alter Agro conducts:

- **Quarterly security reviews** of this repository
- **Annual penetration testing** of infrastructure
- **Continuous monitoring** via automated tools
- **Code reviews** with security focus

### External Audits

We welcome:

- **Independent security audits** of public specifications
- **Academic research** on YARA Lógica security properties
- **Third-party verification** of cryptographic implementations

If you're conducting research on YARA Lógica, we'd love to hear about it: [hello@alteragro.com.br](mailto:hello@alteragro.com.br)

---

## 🔧 Integrity & Compliance Tools

### Verification Commands

Verify repository integrity:

```bash
# Verify hash ledger
python infra/github/verify_hashes.py

# Run KPI compliance check
python infra/github/kpi_score.py --min-faith-premise 0.80 --min-contradiction-coverage 0.90

# Scan for secrets
python infra/github/scan_secrets.py --strict

# Check allowlist compliance
python infra/github/check_allowlist.py

# Verify GPG signatures
git log --show-signature -1
```

### Security Tools (for developers)

```bash
# Install pre-commit hooks
.github/scripts/install-hooks.sh

# Run information barrier checks locally
python infra/github/scan_secrets.py --staged

# Generate security dashboard
python infra/github/security_dashboard.py
```

---

## 📚 Additional Resources

### Security Documentation

- [Trade Secret Protection Policy](../legal/TRADE_SECRET_POLICY.md) — Classification and handling procedures
- [Information Classification Guide](../docs/INFORMATION_CLASSIFICATION_GUIDE.md) — How to classify information
- [Security Contributing Guide](CONTRIBUTING_SECURITY.md) — Security-focused contribution guidelines
- [Private Repository Guide](../docs/PRIVATE_REPOSITORY_GUIDE.md) — Working with private repos

### External References

- **OWASP Top 10:** [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/)
- **GitHub Security Best Practices:** [https://docs.github.com/en/code-security](https://docs.github.com/en/code-security)
- **Brazilian Data Protection Law (LGPD):** [https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

---

## 📞 Contact Information

### For Security Issues

**Primary:** [security@alteragro.com.br](mailto:security@alteragro.com.br)
**Response Time:** 24 hours (weekdays), 48 hours (weekends)

### For General Inquiries

**General:** [hello@alteragro.com.br](mailto:hello@alteragro.com.br)
**Business Development:** [business@alteragro.com.br](mailto:business@alteragro.com.br)

### For Legal/Compliance

**Legal Team:** [legal@alteragro.com.br](mailto:legal@alteragro.com.br)

---

## 📄 Policy Updates

| Version | Date | Changes |
| :------ | :--- | :------ |
| 2.0.0 | 2025-11-04 | Comprehensive security policy update with disclosure procedures, safe harbor, and hall of fame |
| 1.0.0 | 2025-01-01 | Initial security policy |

**Last Reviewed:** 2025-11-04
**Next Review:** 2026-01-01 (annual)

---

**Thank you for helping protect YARA Lógica and Alter Agro's intellectual property while maintaining transparent public specifications.**

**© 2025 Alter Agro Ltda. All rights reserved.**
