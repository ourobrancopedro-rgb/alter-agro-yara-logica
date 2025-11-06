#!/bin/bash
# YARA PICC Notarization - Valid Test Cases
# Tests successful payload submissions with proper HMAC authentication

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
echo "🧪 YARA PICC Notarization - Valid Test Cases"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Webhook URL: $WEBHOOK_URL"
echo "HMAC Secret: ${HMAC_SECRET:0:16}... (truncated)"
echo ""

# Function to test a payload
test_payload() {
  local payload_file="$1"
  local test_name="$2"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📤 Testing: $test_name"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Update timestamp to current time (to avoid TS_WINDOW errors)
  CURRENT_TS=$(date +%s)
  PAYLOAD=$(jq --argjson ts "$CURRENT_TS" '.ts = $ts' "$payload_file")

  # Compute HMAC signature
  SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')

  echo "Payload:"
  echo "$PAYLOAD" | jq .
  echo ""
  echo "HMAC Signature: sha256=$SIGNATURE"
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

  # Validate response
  if [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 300 ]]; then
    # Check if response is valid JSON
    if jq . response.txt > /dev/null 2>&1; then
      OK=$(jq -r '.ok // false' response.txt)
      if [[ "$OK" == "true" ]]; then
        ISSUE_URL=$(jq -r '.issue_url // "N/A"' response.txt)
        CREATED=$(jq -r '.created // false' response.txt)
        IDEMPOTENT=$(jq -r '.idempotent // false' response.txt)

        echo -e "${GREEN}✅ SUCCESS${NC}"
        echo "   Issue URL: $ISSUE_URL"
        if [[ "$CREATED" == "true" ]]; then
          echo "   Status: New issue created"
        elif [[ "$IDEMPOTENT" == "true" ]]; then
          echo "   Status: Existing issue returned (idempotent)"
        fi
      else
        echo -e "${RED}❌ FAIL: Response ok=false${NC}"
        return 1
      fi
    else
      echo -e "${YELLOW}⚠️  WARNING: Response is not valid JSON${NC}"
    fi
  else
    echo -e "${RED}❌ FAIL: HTTP $HTTP_CODE${NC}"
    return 1
  fi

  echo ""
}

# Run tests
FAILED=0

test_payload "$PAYLOADS_DIR/valid/minimal.json" "Minimal Valid Payload" || FAILED=$((FAILED + 1))
test_payload "$PAYLOADS_DIR/valid/complete.json" "Complete Payload (All Fields)" || FAILED=$((FAILED + 1))
test_payload "$PAYLOADS_DIR/valid/high_confidence.json" "High Confidence Decision" || FAILED=$((FAILED + 1))

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✅ All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}❌ $FAILED test(s) failed${NC}"
  exit 1
fi
