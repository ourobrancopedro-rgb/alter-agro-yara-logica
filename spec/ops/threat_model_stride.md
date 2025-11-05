# YARA Lógica PICC Notarization Threat Model (STRIDE)

**Version:** 1.0
**Last Updated:** 2025-01-05
**Framework:** STRIDE (Microsoft Threat Modeling)
**Scope:** n8n → GitHub notarization workflow

---

## System Overview

**Components:**
1. **Client** (decision submitter: web app, CLI, API consumer)
2. **n8n Webhook** (ingestion endpoint)
3. **n8n Workflow** (validation + orchestration engine)
4. **Redis** (nonce deduplication + rate limiting)
5. **GitHub API** (issue creation + storage)
6. **GitHub Issues** (immutable decision ledger)

**Data Flow:**
```
Client → [HTTPS + HMAC] → n8n Webhook → Validate → Redis (nonce check) →
→ GitHub Search (idempotency) → GitHub Create Issue → Response
```

---

## STRIDE Threat Analysis

### S — Spoofing (Identity)

| Threat | Description | Impact | Likelihood | Mitigation | Residual Risk |
|:-------|:------------|:-------|:-----------|:-----------|:--------------|
| **S1: HMAC Secret Theft** | Attacker steals shared HMAC secret and impersonates legitimate client | HIGH (forged decisions in ledger) | MEDIUM (insider threat, credential leak) | - Store secret in encrypted vault (AWS Secrets Manager, Vault)<br>- Rotate every 90 days<br>- Audit secret access logs<br>- Use separate secrets per client group | LOW |
| **S2: GitHub Token Compromise** | Attacker obtains n8n's GitHub OAuth token and creates malicious issues | HIGH (ledger pollution) | LOW (token scoped to issues, protected by GitHub 2FA) | - Scope token to minimal permissions (issues:write)<br>- Use GitHub App with fine-grained permissions<br>- Enable GitHub organization SSO + 2FA<br>- Rotate tokens every 180 days | LOW |
| **S3: IP/Actor Spoofing** | Attacker forges `metadata.actor` field to frame another user | MEDIUM (misleading audit trail) | HIGH (field not cryptographically bound) | - Document `actor` as self-reported metadata<br>- Use authenticated clients (OAuth) for trusted actor IDs<br>- Cross-reference with IP logs<br>- Label issues with source IP hash (privacy-preserving) | MEDIUM |

**Recommendations:**
- Implement per-client API keys (instead of shared HMAC secret)
- Add `client_id` field to payload, signed with client-specific key
- Require mTLS for high-security clients

---

### T — Tampering (Data Integrity)

| Threat | Description | Impact | Likelihood | Mitigation | Residual Risk |
|:-------|:------------|:-------|:-----------|:-----------|:--------------|
| **T1: MITM Payload Modification** | Attacker intercepts request and alters decision content | HIGH (corrupted ledger) | LOW (HTTPS + HMAC protection) | - Enforce HTTPS only (TLS 1.2+)<br>- HMAC signature covers entire payload<br>- Server validates signature before processing | VERY LOW |
| **T2: GitHub Issue Post-Creation Edit** | Attacker with GitHub write access modifies issue after creation | CRITICAL (ledger immutability broken) | MEDIUM (requires GitHub repo write access) | - Enable GitHub branch protection + audit logs<br>- Use GitHub Issue locks (lock issue after creation)<br>- Monitor issue edit events via webhooks<br>- Hash recorded in issue body (tamper detection) | LOW |
| **T3: Canonical Hash Manipulation** | Attacker finds hash collision to forge idempotency | MEDIUM (duplicate decisions undetected) | VERY LOW (SHA-256 collision resistance) | - Use SHA-256 (collision probability ~2^-128)<br>- Monitor for hash collisions (alert if detected)<br>- Consider upgrading to SHA-3 if quantum threat increases | VERY LOW |
| **T4: Redis Nonce Database Tampering** | Attacker deletes nonce keys to enable replay | MEDIUM (replay attacks succeed) | LOW (requires Redis access) | - Secure Redis with authentication (requirepass)<br>- Network isolation (VPC, no public access)<br>- Enable Redis ACLs with least privilege<br>- Audit Redis commands via slowlog | LOW |

**Recommendations:**
- Implement GitHub Issue immutability webhook (reject edits)
- Use GitHub's audit log API to detect suspicious edits
- Add cryptographic signature to issue body (n8n signs hash + timestamp)

---

### R — Repudiation (Non-Repudiation)

| Threat | Description | Impact | Likelihood | Mitigation | Residual Risk |
|:-------|:------------|:-------|:-----------|:-----------|:--------------|
| **R1: Client Denies Submission** | Client claims they never submitted a decision | MEDIUM (dispute resolution difficulty) | MEDIUM (no client authentication) | - Log client IP, User-Agent, TLS fingerprint<br>- Require authenticated API keys (client identity)<br>- Issue contains hash + timestamp (verifiable by client)<br>- Clients can verify their submissions via GitHub search | MEDIUM |
| **R2: Server Denies Receipt** | n8n claims decision was never received | LOW (client has HTTP response proof) | LOW (logs retained) | - Return GitHub issue URL in response<br>- Client stores issue number as receipt<br>- Enable n8n execution logs (30-day retention)<br>- Use external log aggregation (CloudWatch, Datadog) | VERY LOW |
| **R3: GitHub Edit Unattributed** | Issue edited without clear audit trail of who/when | MEDIUM (accountability lost) | LOW (GitHub tracks all edits) | - GitHub audit log records all changes<br>- Enable GitHub Advanced Security audit logs<br>- Monitor issue timeline events<br>- Use GitHub's signed commit log (Git-level integrity) | LOW |

**Recommendations:**
- Implement digital signatures on client side (client signs decision with private key)
- Add `client_signature` field to payload (optional, for high-assurance clients)
- Archive all n8n execution logs in immutable storage (S3 + Glacier)

---

### I — Information Disclosure (Confidentiality)

| Threat | Description | Impact | Likelihood | Mitigation | Residual Risk |
|:-------|:------------|:-------|:-----------|:-----------|:--------------|
| **I1: Public GitHub Repo Exposure** | Sensitive decision data exposed in public repository | CRITICAL (data breach) | N/A (repo is private) | - Use private GitHub repository<br>- Document public vs. private data policy<br>- Sanitize decisions before submission (PII removal)<br>- Review each issue for sensitive content before publishing (if public) | LOW (private repo) |
| **I2: HMAC Secret Leak in Logs** | Secret accidentally logged in n8n/client logs | HIGH (all clients compromised) | MEDIUM (developer error) | - Sanitize logs (redact secrets)<br>- Use log scrubbing regex (e.g., Datadog patterns)<br>- Environment variable masking in n8n<br>- Pre-commit hooks to detect secrets in code | LOW |
| **I3: Nonce Enumeration** | Attacker lists all nonces in Redis to infer usage patterns | LOW (limited strategic value) | MEDIUM (Redis access required) | - Secure Redis with TLS + authentication<br>- Use hashed nonce keys (e.g., `HMAC(nonce)`)<br>- Network isolation (no public Redis access) | VERY LOW |
| **I4: GitHub API Token Exposure** | Token leaked via logs, error messages, or code | HIGH (repo write access) | MEDIUM (developer error) | - Never log tokens<br>- Use GitHub's secret scanning<br>- Enable GitHub token expiration (180 days)<br>- Use GitHub Apps (auto-expiring installation tokens) | LOW |

**Recommendations:**
- Implement field-level encryption for sensitive decision content
- Use GitHub's `CODEOWNERS` file to require security review before merging
- Deploy secret detection pre-commit hooks (TruffleHog, GitLeaks)

---

### D — Denial of Service (Availability)

| Threat | Description | Impact | Likelihood | Mitigation | Residual Risk |
|:-------|:------------|:-------|:-----------|:-----------|:--------------|
| **D1: Rate Limit Exhaustion** | Attacker floods webhook with requests to DoS legitimate users | MEDIUM (service unavailable) | HIGH (public webhook) | - Rate limiting (100 req/10min per IP)<br>- Token bucket algorithm (Redis)<br>- WAF with IP blocking (Cloudflare, AWS WAF)<br>- CAPTCHA for suspicious traffic | LOW |
| **D2: GitHub API Quota Exhaustion** | Attacker triggers excessive GitHub API calls | HIGH (workflow halted) | MEDIUM (5000/hour limit) | - Rate limit client requests upstream<br>- Idempotency check (avoid duplicate API calls)<br>- Use multiple GitHub tokens (load balancing)<br>- Exponential backoff on quota errors | MEDIUM |
| **D3: Redis Memory Exhaustion** | Attacker submits millions of unique nonces to fill Redis | MEDIUM (Redis crashes) | LOW (rate limiting prevents) | - Redis maxmemory policy (LRU eviction)<br>- Nonce TTL (600s auto-expiration)<br>- Monitor Redis memory usage<br>- Alert if memory > 80% | LOW |
| **D4: Large Payload Attack** | Attacker sends multi-MB JSON payloads | LOW (n8n rejects oversized requests) | MEDIUM (easy to automate) | - n8n payload size limit (1MB default)<br>- JSON schema maxLength constraints<br>- Reverse proxy limits (Nginx `client_max_body_size`) | VERY LOW |
| **D5: Slowloris / Connection Exhaustion** | Attacker opens many slow connections to exhaust n8n workers | MEDIUM (n8n unresponsive) | MEDIUM (common DDoS technique) | - Connection timeout (30s)<br>- Max concurrent connections (n8n config)<br>- Use CDN with DDoS protection (Cloudflare)<br>- Rate limit at load balancer level | LOW |

**Recommendations:**
- Deploy n8n behind AWS ALB with WAF rules
- Use Cloudflare or Fastly for DDoS mitigation
- Implement adaptive rate limiting (increase limits during traffic spikes for known clients)

---

### E — Elevation of Privilege (Authorization)

| Threat | Description | Impact | Likelihood | Mitigation | Residual Risk |
|:-------|:------------|:-------|:-----------|:-----------|:--------------|
| **E1: GitHub Token Over-Privileged** | Token has admin rights instead of issues:write | HIGH (attacker gains repo control) | LOW (token scoped correctly) | - Use GitHub Apps with minimal scopes<br>- Review token permissions quarterly<br>- Principle of least privilege<br>- GitHub organization SAML/SSO enforcement | VERY LOW |
| **E2: n8n Workflow Injection** | Attacker modifies n8n workflow to execute malicious code | CRITICAL (full system compromise) | LOW (requires n8n admin access) | - Restrict n8n UI access (SSO + 2FA)<br>- Audit workflow changes via version control<br>- Deploy workflows via GitOps (IaC)<br>- Monitor workflow execution logs for anomalies | LOW |
| **E3: Redis Command Injection** | Attacker exploits Redis queries to run arbitrary commands | HIGH (Redis takeover) | VERY LOW (parameterized queries) | - Use Redis client libraries (not raw commands)<br>- Disable dangerous commands (FLUSHALL, CONFIG)<br>- Redis ACLs to restrict command access<br>- Network isolation (VPC) | VERY LOW |
| **E4: GitHub Issues as Code Execution** | Attacker injects malicious Markdown/HTML into issue body | MEDIUM (XSS for issue viewers) | LOW (GitHub sanitizes Markdown) | - GitHub's Markdown sanitization (enabled by default)<br>- Avoid rendering untrusted HTML<br>- CSP headers for GitHub Enterprise (if self-hosted)<br>- Sanitize user input in issue body | VERY LOW |

**Recommendations:**
- Implement RBAC for n8n workflows (viewer vs. editor roles)
- Use GitHub's Dependabot to scan workflow dependencies
- Enable GitHub Advanced Security (secret scanning + code scanning)

---

## Additional Threat Considerations

### Quota Exhaustion (Resource Limits)

| Threat | Description | Impact | Likelihood | Mitigation | Residual Risk |
|:-------|:------------|:-------|:-----------|:-----------|:--------------|
| **QE1: GitHub Issue Limit** | Repository exceeds issue count limits | LOW (GitHub supports millions of issues) | VERY LOW | - Monitor issue count<br>- Archive old issues periodically<br>- Consider sharding across multiple repos | VERY LOW |
| **QE2: Redis Storage Limit** | Nonce keys accumulate beyond Redis capacity | LOW (TTL ensures auto-expiration) | VERY LOW | - Nonce TTL (600s)<br>- Redis maxmemory + eviction policy<br>- Monitor Redis memory metrics | VERY LOW |

---

## Risk Summary

| Risk Level | Count | Critical Controls |
|:-----------|:------|:------------------|
| **CRITICAL** | 1 | GitHub repo access control, issue immutability |
| **HIGH** | 5 | HMAC secret rotation, HTTPS enforcement, GitHub token scoping |
| **MEDIUM** | 8 | Rate limiting, Redis security, audit logging |
| **LOW** | 10 | Monitoring, log retention, input validation |

**Overall Risk Posture:** **MEDIUM** (acceptable for production with recommended mitigations)

---

## Security Controls Checklist

### Pre-Deployment

- [ ] HMAC secret stored in encrypted vault (not plaintext env)
- [ ] GitHub token scoped to issues:write only
- [ ] Redis authentication enabled (requirepass)
- [ ] n8n UI protected by SSO + 2FA
- [ ] HTTPS enforced (TLS 1.2+ with valid certificate)
- [ ] Rate limiting configured (100 req/10min)
- [ ] Nonce deduplication enabled (Redis)
- [ ] GitHub repository is private (or content sanitized if public)

### Post-Deployment Monitoring

- [ ] Alert on HMAC failure rate > 5%
- [ ] Alert on DLQ depth > 10
- [ ] Alert on GitHub quota remaining < 500
- [ ] Monitor Redis memory usage (alert > 80%)
- [ ] Track error rate (4xx/5xx) by code
- [ ] Log all requests (IP, actor, hash, outcome)
- [ ] Review GitHub audit logs weekly

### Quarterly Reviews

- [ ] Rotate HMAC secret (90-day cycle)
- [ ] Rotate GitHub token (180-day cycle)
- [ ] Review n8n workflow changes (GitOps audit)
- [ ] Penetration test webhook endpoint
- [ ] Threat model update (review new threats)

---

## Incident Response Plan

**If compromise detected:**

1. **Immediate:** Rotate HMAC secret and GitHub token
2. **Isolate:** Disable n8n workflow (stop processing)
3. **Investigate:** Review logs for malicious activity (IP, actor, payloads)
4. **Notify:** Contact security@alteragro.com.br and affected clients
5. **Remediate:** Apply patches, update configurations
6. **Post-Mortem:** Document incident, update threat model

**Escalation:** Critical incidents escalate to CISO within 1 hour

---

## References

- **STRIDE Framework:** https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
- **OWASP API Security Top 10:** https://owasp.org/www-project-api-security/
- **GitHub Security Best Practices:** https://docs.github.com/en/code-security
- **n8n Security:** https://docs.n8n.io/hosting/security/

---

**Threat Model Maintained by:** Alter Agro Security Team
**Next Review:** 2025-04-01
**Last Penetration Test:** Pending (pre-production)
