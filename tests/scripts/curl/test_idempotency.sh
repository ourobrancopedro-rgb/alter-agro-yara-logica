#!/bin/bash
# YARA PICC Notarization - Idempotency Test
# Tests that duplicate submissions return the existing issue

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WEBHOOK_URL="${N8N_WEBHOOK_URL:-}"
HMAC_SECRET="${HMAC_SECRET:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOADS_DIR="$(cd "$SCRIPT_DIR/../../payloads" && pwd)"

# Usage check
if [[ -z "$WEBHOOK_URL" || -z "$HMAC_SECRET" ]]; then
  echo -e "${RED}Error: Required environment variables not set${NC}"
  echo ""
  echo "Usage:"
  echo "  export N8N_WEBHOOK_URL='https://your-n8n.com/webhook/yara/picc/notarize'"
  echo "  export HMAC_SECRET='your-hmac-secret-here'"
  echo "  $0"
  echo ""
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 YARA PICC Notarization - Idempotency Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Webhook URL: $WEBHOOK_URL"
echo "Test: Submit same payload twice, expect same issue returned"
echo ""

# Generate a unique test payload with current timestamp
CURRENT_TS=$(date +%s)
NONCE="idempotency-test-$CURRENT_TS"

PAYLOAD=$(cat <<EOF
{
  "schema_version": "PICC-1.0",
  "ts": $CURRENT_TS,
  "nonce": "$NONCE",
  "decision": {
    "question": "Idempotency test: Will duplicate submissions return the same issue?",
    "conclusion": "Yes, search-before-create ensures idempotency",
    "confidence": "HIGH",
    "premises": [
      {
        "type": "FACT",
        "text": "The workflow uses canonical hash labels to detect duplicates",
        "evidence": [
          "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica/blob/main/spec/workflows/n8n_yara_picc_notarization.json",
          "https://example.com/idempotency/canonical-hash"
        ]
      }
    ],
    "falsifier": "If duplicate issues are created, idempotency is broken"
  },
  "metadata": {
    "actor": "test-codex-agent",
    "context": "test-idempotency"
  }
}
EOF
)

# Compute HMAC signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')

echo "Test Payload:"
echo "$PAYLOAD" | jq .
echo ""
echo "HMAC Signature: sha256=$SIGNATURE"
echo ""

# First submission
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📤 First Submission (should create new issue)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

HTTP_CODE_1=$(curl -i -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD" \
  -o response1.txt \
  -w '%{http_code}' \
  -s)

echo "HTTP Status: $HTTP_CODE_1"
echo ""
echo "Response:"
cat response1.txt
echo ""

# Validate first response
if [[ "$HTTP_CODE_1" -ge 200 && "$HTTP_CODE_1" -lt 300 ]]; then
  if jq . response1.txt > /dev/null 2>&1; then
    OK_1=$(jq -r '.ok // false' response1.txt)
    CREATED_1=$(jq -r '.created // false' response1.txt)
    ISSUE_NUMBER_1=$(jq -r '.issue_number // "N/A"' response1.txt)
    ISSUE_URL_1=$(jq -r '.issue_url // "N/A"' response1.txt)
    HASH_1=$(jq -r '.hash // "N/A"' response1.txt)

    if [[ "$OK_1" == "true" ]]; then
      echo -e "${GREEN}✅ First submission successful${NC}"
      echo "   Created: $CREATED_1"
      echo "   Issue #: $ISSUE_NUMBER_1"
      echo "   Issue URL: $ISSUE_URL_1"
      echo "   Hash: ${HASH_1:0:32}..."
    else
      echo -e "${RED}❌ FAIL: First submission returned ok=false${NC}"
      exit 1
    fi
  else
    echo -e "${RED}❌ FAIL: Response is not valid JSON${NC}"
    exit 1
  fi
else
  echo -e "${RED}❌ FAIL: First submission failed with HTTP $HTTP_CODE_1${NC}"
  exit 1
fi

echo ""
echo "Waiting 2 seconds before second submission..."
sleep 2
echo ""

# Second submission (identical payload)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📤 Second Submission (should return existing issue)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

HTTP_CODE_2=$(curl -i -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD" \
  -o response2.txt \
  -w '%{http_code}' \
  -s)

echo "HTTP Status: $HTTP_CODE_2"
echo ""
echo "Response:"
cat response2.txt
echo ""

# Validate second response
if [[ "$HTTP_CODE_2" -ge 200 && "$HTTP_CODE_2" -lt 300 ]]; then
  if jq . response2.txt > /dev/null 2>&1; then
    OK_2=$(jq -r '.ok // false' response2.txt)
    CREATED_2=$(jq -r '.created // false' response2.txt)
    IDEMPOTENT_2=$(jq -r '.idempotent // false' response2.txt)
    ISSUE_NUMBER_2=$(jq -r '.issue_number // "N/A"' response2.txt)
    ISSUE_URL_2=$(jq -r '.issue_url // "N/A"' response2.txt)

    if [[ "$OK_2" == "true" ]]; then
      echo -e "${GREEN}✅ Second submission successful${NC}"
      echo "   Idempotent: $IDEMPOTENT_2"
      echo "   Issue #: $ISSUE_NUMBER_2"
      echo "   Issue URL: $ISSUE_URL_2"
    else
      echo -e "${RED}❌ FAIL: Second submission returned ok=false${NC}"
      exit 1
    fi
  else
    echo -e "${RED}❌ FAIL: Response is not valid JSON${NC}"
    exit 1
  fi
else
  echo -e "${RED}❌ FAIL: Second submission failed with HTTP $HTTP_CODE_2${NC}"
  exit 1
fi

echo ""

# Compare responses
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Idempotency Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

FAILED=0

# Check that second response has idempotent flag
if [[ "$IDEMPOTENT_2" == "true" ]]; then
  echo -e "${GREEN}✅ Second response correctly marked as idempotent${NC}"
else
  echo -e "${RED}❌ FAIL: Second response missing idempotent flag${NC}"
  FAILED=$((FAILED + 1))
fi

# Check that issue numbers match
if [[ "$ISSUE_NUMBER_1" == "$ISSUE_NUMBER_2" ]]; then
  echo -e "${GREEN}✅ Same issue number returned ($ISSUE_NUMBER_1)${NC}"
else
  echo -e "${RED}❌ FAIL: Different issue numbers (first: $ISSUE_NUMBER_1, second: $ISSUE_NUMBER_2)${NC}"
  FAILED=$((FAILED + 1))
fi

# Check that URLs match
if [[ "$ISSUE_URL_1" == "$ISSUE_URL_2" ]]; then
  echo -e "${GREEN}✅ Same issue URL returned${NC}"
else
  echo -e "${RED}❌ FAIL: Different issue URLs${NC}"
  FAILED=$((FAILED + 1))
fi

# Check that second submission did NOT create a new issue
if [[ "$CREATED_2" == "false" ]]; then
  echo -e "${GREEN}✅ Second submission did not create new issue${NC}"
else
  echo -e "${RED}❌ FAIL: Second submission incorrectly created new issue${NC}"
  FAILED=$((FAILED + 1))
fi

echo ""

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Final Result"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✅ IDEMPOTENCY TEST PASSED${NC}"
  echo ""
  echo "Summary:"
  echo "  • First submission created issue #$ISSUE_NUMBER_1"
  echo "  • Second submission returned same issue (idempotent)"
  echo "  • No duplicate issues were created"
  echo ""
  echo "Verify in GitHub:"
  echo "  $ISSUE_URL_1"
  exit 0
else
  echo -e "${RED}❌ IDEMPOTENCY TEST FAILED ($FAILED checks failed)${NC}"
  exit 1
fi
