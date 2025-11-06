#!/bin/bash
# YARA PICC Notarization - Invalid Test Cases
# Tests that validation properly rejects invalid payloads

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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
echo "🧪 YARA PICC Notarization - Invalid Test Cases"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Webhook URL: $WEBHOOK_URL"
echo "These tests should FAIL validation (HTTP 401 or ok=false)"
echo ""

# Function to test invalid payload (expects failure)
test_invalid_payload() {
  local payload_file="$1"
  local test_name="$2"
  local expected_error_code="$3"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📤 Testing: $test_name"
  echo "   Expected: Validation failure ($expected_error_code)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Read payload
  PAYLOAD=$(cat "$payload_file")

  # Compute HMAC signature (even for invalid payloads)
  SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')

  echo "Payload:"
  echo "$PAYLOAD" | jq .
  echo ""

  # Send request
  HTTP_CODE=$(curl -i -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -H "X-Signature-256: sha256=$SIGNATURE" \
    -d "$PAYLOAD" \
    -o response.txt \
    -w '%{http_code}' \
    -s)

  echo "HTTP Status: $HTTP_CODE"
  echo ""
  echo "Response:"
  cat response.txt
  echo ""

  # Validate that request was rejected
  if [[ "$HTTP_CODE" -eq 401 ]]; then
    # Check error response
    if jq . response.txt > /dev/null 2>&1; then
      OK=$(jq -r '.ok // true' response.txt)
      ERROR_CODE=$(jq -r '.code // "UNKNOWN"' response.txt)

      if [[ "$OK" == "false" ]]; then
        if [[ "$ERROR_CODE" == "$expected_error_code" ]]; then
          echo -e "${GREEN}✅ SUCCESS: Correctly rejected with code $ERROR_CODE${NC}"
        else
          echo -e "${YELLOW}⚠️  WARNING: Rejected but with unexpected code $ERROR_CODE (expected $expected_error_code)${NC}"
        fi
      else
        echo -e "${RED}❌ FAIL: HTTP 401 but ok=true${NC}"
        return 1
      fi
    else
      echo -e "${YELLOW}⚠️  WARNING: HTTP 401 but response is not valid JSON${NC}"
    fi
  elif [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 300 ]]; then
    echo -e "${RED}❌ FAIL: Invalid payload was accepted (HTTP $HTTP_CODE)${NC}"
    return 1
  else
    echo -e "${YELLOW}⚠️  UNEXPECTED: HTTP $HTTP_CODE${NC}"
  fi

  echo ""
}

# Function to test bad HMAC signature
test_bad_hmac() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📤 Testing: Bad HMAC Signature"
  echo "   Expected: BAD_SIG error"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Use a valid payload but wrong signature
  CURRENT_TS=$(date +%s)
  PAYLOAD=$(jq --argjson ts "$CURRENT_TS" '.ts = $ts' "$PAYLOADS_DIR/valid/minimal.json")

  # Use WRONG signature
  WRONG_SIGNATURE="0000000000000000000000000000000000000000000000000000000000000000"

  echo "Payload:"
  echo "$PAYLOAD" | jq .
  echo ""
  echo "HMAC Signature: sha256=$WRONG_SIGNATURE (WRONG)"
  echo ""

  # Send request
  HTTP_CODE=$(curl -i -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -H "X-Signature-256: sha256=$WRONG_SIGNATURE" \
    -d "$PAYLOAD" \
    -o response.txt \
    -w '%{http_code}' \
    -s)

  echo "HTTP Status: $HTTP_CODE"
  echo ""
  echo "Response:"
  cat response.txt
  echo ""

  if [[ "$HTTP_CODE" -eq 401 ]]; then
    if jq . response.txt > /dev/null 2>&1; then
      ERROR_CODE=$(jq -r '.code // "UNKNOWN"' response.txt)
      if [[ "$ERROR_CODE" == "BAD_SIG" ]]; then
        echo -e "${GREEN}✅ SUCCESS: Correctly rejected bad HMAC${NC}"
      else
        echo -e "${YELLOW}⚠️  WARNING: Rejected but with code $ERROR_CODE (expected BAD_SIG)${NC}"
      fi
    fi
  else
    echo -e "${RED}❌ FAIL: Bad HMAC was accepted (HTTP $HTTP_CODE)${NC}"
    return 1
  fi

  echo ""
}

# Run tests
FAILED=0

test_bad_hmac || FAILED=$((FAILED + 1))
test_invalid_payload "$PAYLOADS_DIR/invalid/bad_schema_version.json" "Bad Schema Version" "SCHEMA_VERSION" || FAILED=$((FAILED + 1))
test_invalid_payload "$PAYLOADS_DIR/invalid/missing_evidence.json" "Missing Evidence (FACT)" "FACT_EVIDENCE" || FAILED=$((FAILED + 1))
test_invalid_payload "$PAYLOADS_DIR/invalid/non_https_evidence.json" "Non-HTTPS Evidence" "EVIDENCE_HTTPS" || FAILED=$((FAILED + 1))
test_invalid_payload "$PAYLOADS_DIR/invalid/short_nonce.json" "Short Nonce" "NONCE_INVALID" || FAILED=$((FAILED + 1))
test_invalid_payload "$PAYLOADS_DIR/invalid/expired_timestamp.json" "Expired Timestamp" "TS_WINDOW" || FAILED=$((FAILED + 1))

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✅ All validation tests passed (invalid payloads correctly rejected)!${NC}"
  exit 0
else
  echo -e "${RED}❌ $FAILED test(s) failed${NC}"
  exit 1
fi
