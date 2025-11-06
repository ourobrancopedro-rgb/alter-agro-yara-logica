# YARA PICC Notarization - Test Suite

**Version:** 1.0
**Last Updated:** 2025-11-06
**Maintainer:** Codex AI + Alter Agro DevOps Team

---

## 📋 Overview

This comprehensive test suite validates the **YARA Lógica PICC Notarization** n8n workflow. It includes:

- ✅ **Valid payload tests** - Happy path scenarios
- ❌ **Invalid payload tests** - Validation error handling
- 🔄 **Idempotency tests** - Duplicate submission handling
- 🔐 **Authentication tests** - HMAC signature verification
- 🧪 **Edge case tests** - Boundary conditions

---

## 🗂️ Test Suite Structure

```
tests/
├── payloads/                    # Test data fixtures (JSON)
│   ├── valid/                   # Valid PICC payloads
│   │   ├── minimal.json
│   │   ├── complete.json
│   │   └── high_confidence.json
│   └── invalid/                 # Invalid payloads for validation tests
│       ├── bad_schema_version.json
│       ├── missing_evidence.json
│       ├── non_https_evidence.json
│       ├── expired_timestamp.json
│       └── short_nonce.json
│
├── scripts/
│   ├── curl/                    # Bash/cURL test scripts
│   │   ├── test_valid.sh
│   │   ├── test_invalid.sh
│   │   └── test_idempotency.sh
│   │
│   ├── python/                  # Python/pytest test suite
│   │   ├── test_picc_notarization.py
│   │   └── requirements.txt
│   │
│   └── javascript/              # JavaScript/Jest test suite
│       ├── test_picc_notarization.test.js
│       ├── package.json
│       └── .npmrc
│
├── postman/                     # Postman collection
│   └── picc_notarization.postman_collection.json
│
└── README.md                    # This file
```

---

## 🚀 Quick Start

### Prerequisites

1. **n8n workflow deployed** and accessible
2. **Webhook URL** from n8n (e.g., `https://your-n8n.com/webhook/yara/picc/notarize`)
3. **HMAC secret** configured in n8n environment

### Environment Setup

```bash
# Export required environment variables
export N8N_WEBHOOK_URL='https://your-n8n.com/webhook/yara/picc/notarize'
export HMAC_SECRET='your-hmac-secret-here'
```

---

## 🧪 Running Tests

### Option 1: cURL Tests (Bash)

**Requirements:** `bash`, `curl`, `jq`, `openssl`

```bash
# Test valid payloads
cd tests/scripts/curl
chmod +x test_valid.sh
./test_valid.sh

# Test invalid payloads (validation errors)
chmod +x test_invalid.sh
./test_invalid.sh

# Test idempotency (duplicate submissions)
chmod +x test_idempotency.sh
./test_idempotency.sh
```

**Features:**
- ✅ Color-coded output
- ✅ Detailed request/response logging
- ✅ Automatic HMAC signature generation
- ✅ Current timestamp injection

---

### Option 2: Python Tests (pytest)

**Requirements:** Python 3.8+, `pytest`, `requests`

```bash
# Install dependencies
cd tests/scripts/python
pip install -r requirements.txt

# Run all tests
pytest test_picc_notarization.py -v

# Run specific test class
pytest test_picc_notarization.py::TestValidPayloads -v

# Run with detailed output
pytest test_picc_notarization.py -v --tb=short

# Generate JUnit XML report
pytest test_picc_notarization.py --junit-xml=pytest-report.xml
```

**Test Classes:**
- `TestValidPayloads` - Valid payload submissions
- `TestInvalidPayloads` - Validation error handling
- `TestIdempotency` - Duplicate submission handling
- `TestEdgeCases` - Boundary conditions

---

### Option 3: JavaScript Tests (Jest)

**Requirements:** Node.js 18+, `jest`

```bash
# Install dependencies
cd tests/scripts/javascript
npm install

# Run all tests
npm test

# Run with verbose output
npm run test:verbose

# Run in watch mode
npm run test:watch

# Generate JUnit XML report
npm test -- --reporters=jest-junit
```

**Test Suites:**
- Valid PICC Payloads
- Invalid PICC Payloads
- Idempotency
- Edge Cases

---

### Option 4: Postman Collection

**Requirements:** Postman Desktop or Newman CLI

#### Using Postman Desktop:

1. **Import Collection:**
   ```
   File → Import → tests/postman/picc_notarization.postman_collection.json
   ```

2. **Create Environment:**
   - Variable: `n8n_webhook_url` → Your webhook URL
   - Variable: `hmac_secret` → Your HMAC secret

3. **Run Collection:**
   - Select collection → Click "Run"
   - Choose environment
   - Click "Run YARA PICC Notarization"

#### Using Newman CLI:

```bash
# Install Newman
npm install -g newman

# Run collection
newman run tests/postman/picc_notarization.postman_collection.json \
  --env-var "n8n_webhook_url=https://your-n8n.com/webhook/yara/picc/notarize" \
  --env-var "hmac_secret=your-hmac-secret-here"

# Generate HTML report
newman run tests/postman/picc_notarization.postman_collection.json \
  --env-var "n8n_webhook_url=..." \
  --env-var "hmac_secret=..." \
  --reporters cli,html \
  --reporter-html-export newman-report.html
```

---

### Option 5: GitHub Actions CI

**Automated testing via GitHub Actions**

#### Manual Trigger:

1. Navigate to **Actions** tab in GitHub
2. Select **"n8n PICC Notarization - Integration Tests"**
3. Click **"Run workflow"**
4. Provide inputs:
   - Webhook URL
   - Test suite (all/valid/invalid/idempotency/python/javascript)

#### Scheduled Runs:

- Automatically runs daily at 06:00 UTC
- Requires `N8N_WEBHOOK_URL` and `HMAC_SECRET` as repository secrets

#### Configuration:

```bash
# Set repository secrets
gh secret set N8N_WEBHOOK_URL --body "https://your-n8n.com/webhook/yara/picc/notarize"
gh secret set HMAC_SECRET --body "your-hmac-secret-here"
```

---

## 📊 Test Coverage

### Valid Payload Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Minimal Valid | Required fields only | HTTP 200, `ok=true`, issue created |
| Complete | All optional fields | HTTP 200, `ok=true`, issue created |
| High Confidence | HIGH confidence decision | HTTP 200, `ok=true` |
| Medium Confidence | MEDIUM confidence decision | HTTP 200, `ok=true` |
| Low Confidence | LOW confidence decision | HTTP 200, `ok=true` |

### Invalid Payload Tests

| Test Case | Description | Expected Error Code |
|-----------|-------------|---------------------|
| Bad HMAC Signature | Wrong HMAC secret | `BAD_SIG` |
| Expired Timestamp | Timestamp > 5 min old | `TS_WINDOW` |
| Bad Schema Version | Invalid schema version | `SCHEMA_VERSION` |
| Short Nonce | Nonce < 8 characters | `NONCE_INVALID` |
| Missing Evidence | FACT without evidence | `FACT_EVIDENCE` |
| Single Evidence | FACT with only 1 evidence | `FACT_EVIDENCE` |
| Non-HTTPS Evidence | HTTP (not HTTPS) URLs | `EVIDENCE_HTTPS` |

### Idempotency Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Duplicate Submission | Submit same payload twice | Second response: `idempotent=true`, same issue number |

### Edge Case Tests

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| Max Nonce Length | Nonce = 128 characters | HTTP 200, `ok=true` |
| Min Nonce Length | Nonce = 8 characters | HTTP 200, `ok=true` |
| Multiple FACT Premises | Multiple FACT premises | HTTP 200, `ok=true` |

---

## 🔍 Test Payloads

### Valid Payload Structure

```json
{
  "schema_version": "PICC-1.0",
  "ts": 1735689600,
  "nonce": "unique-nonce-12345678",
  "decision": {
    "question": "Is this a valid PICC decision?",
    "conclusion": "Yes, this is valid",
    "confidence": "HIGH",
    "premises": [
      {
        "type": "FACT",
        "text": "FACT premise with evidence",
        "evidence": [
          "https://example.com/evidence1",
          "https://example.com/evidence2"
        ]
      }
    ],
    "falsifier": "If validation fails, decision is falsified"
  },
  "metadata": {
    "actor": "test-user",
    "context": "test-context"
  }
}
```

### Expected Response (Success)

```json
{
  "ok": true,
  "created": true,
  "issue_number": 42,
  "issue_url": "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues/42",
  "hash": "e7f4a2b9c8d1..."
}
```

### Expected Response (Idempotent)

```json
{
  "ok": true,
  "idempotent": true,
  "issue_number": 42,
  "issue_url": "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/issues/42",
  "message": "Existing issue returned (idempotency)"
}
```

### Expected Response (Error)

```json
{
  "ok": false,
  "code": "BAD_SIG",
  "msg": "HMAC signature mismatch"
}
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "HMAC signature mismatch" (BAD_SIG)

**Cause:** HMAC secret mismatch between client and n8n

**Solution:**
```bash
# Verify HMAC secret matches n8n environment
echo $HMAC_SECRET

# Regenerate HMAC secret if needed
openssl rand -hex 32

# Update both client environment and n8n environment
```

#### 2. "Timestamp outside 5min window" (TS_WINDOW)

**Cause:** System clock drift or hardcoded timestamp in payload

**Solution:**
```bash
# Check system time
date

# Sync with NTP
sudo ntpdate -s time.nist.gov

# Ensure tests use current timestamp (not hardcoded)
```

#### 3. "Connection refused" or "Network error"

**Cause:** n8n webhook not accessible or URL incorrect

**Solution:**
```bash
# Verify webhook URL
curl -I $N8N_WEBHOOK_URL

# Check n8n workflow is active
# Check firewall/network rules

# Test basic connectivity
curl -X POST $N8N_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

#### 4. Tests hanging or timing out

**Cause:** n8n workflow error or GitHub API rate limit

**Solution:**
```bash
# Check n8n execution logs in n8n UI
# Verify GitHub API quota

# Increase test timeout (pytest)
pytest --timeout=60

# Increase test timeout (jest)
# Edit package.json: "testTimeout": 60000
```

---

## 📈 CI/CD Integration

### GitHub Actions

The test suite includes a comprehensive GitHub Actions workflow:

**File:** `.github/workflows/n8n-integration-tests.yml`

**Features:**
- ✅ Parallel test execution
- ✅ Test result artifacts
- ✅ JUnit XML reports
- ✅ Test summary in PR comments
- ✅ Scheduled daily runs
- ✅ Manual triggers with inputs

**Usage:**
```yaml
# Trigger from another workflow
jobs:
  test:
    uses: ./.github/workflows/n8n-integration-tests.yml
    with:
      webhook_url: ${{ secrets.N8N_WEBHOOK_URL }}
    secrets:
      HMAC_SECRET: ${{ secrets.HMAC_SECRET }}
```

---

## 🔐 Security Considerations

### Secrets Management

⚠️ **NEVER commit secrets to Git!**

**Best Practices:**
1. Use environment variables for local testing
2. Use GitHub Secrets for CI/CD
3. Rotate HMAC secrets every 90 days
4. Use different secrets for dev/staging/prod
5. Audit secret access logs regularly

### Test Data

✅ **Safe:**
- Use `example.com` for test evidence URLs
- Use synthetic test data
- Use unique nonces per test run

❌ **Unsafe:**
- Real customer data in test payloads
- Production secrets in test scripts
- Hardcoded credentials

---

## 📚 References

- **n8n Workflow:** `/spec/workflows/n8n_yara_picc_notarization.json`
- **Setup Guide:** `/docs/N8N_SETUP_GUIDE.md`
- **API Contract:** `/spec/contracts/notarization_api_contract.md`
- **Schema:** `/spec/schemas/picc-1.0.schema.json`
- **Runbook:** `/spec/ops/runbook_notarization.md`

---

## 🤝 Contributing

### Adding New Tests

1. **Create test payload:**
   ```bash
   # Add to tests/payloads/valid/ or tests/payloads/invalid/
   ```

2. **Update test scripts:**
   ```bash
   # Add test case to:
   # - tests/scripts/curl/test_*.sh
   # - tests/scripts/python/test_picc_notarization.py
   # - tests/scripts/javascript/test_picc_notarization.test.js
   ```

3. **Update Postman collection:**
   ```bash
   # Add request to appropriate folder in collection
   ```

4. **Document test:**
   ```bash
   # Update test coverage table in this README
   ```

### Running Full Test Suite

```bash
# Run all test formats
make test-all

# Or manually:
./tests/scripts/curl/test_valid.sh
./tests/scripts/curl/test_invalid.sh
./tests/scripts/curl/test_idempotency.sh
cd tests/scripts/python && pytest test_picc_notarization.py -v
cd tests/scripts/javascript && npm test
```

---

## 📞 Support

- **Documentation Issues:** Open issue in this repository
- **Test Failures:** Check n8n execution logs first
- **Security Questions:** security@alteragro.com.br
- **Technical Support:** devops@alteragro.com.br

---

## 📝 Changelog

### v1.0.0 (2025-11-06)
- ✨ Initial release
- ✅ cURL test scripts
- ✅ Python/pytest test suite
- ✅ JavaScript/Jest test suite
- ✅ Postman collection
- ✅ GitHub Actions CI workflow
- ✅ Comprehensive test coverage

---

**Test Suite Maintained by:** Codex AI (Generator) + Alter Agro DevOps Team
**Last Tested:** 2025-11-06
**Next Review:** 2026-02-01
