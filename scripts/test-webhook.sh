#!/bin/bash
#
# YARA Lógica PICC Notarization - Webhook Test Script
#
# Usage:
#   ./scripts/test-webhook.sh <webhook_url> <hmac_secret>
#
# Example:
#   ./scripts/test-webhook.sh \
#     "https://n8n.example.com/webhook/yara/picc/notarize" \
#     "a1b2c3d4e5f6..."
#
# Description:
#   Sends a test PICC decision to the n8n webhook and validates the response.
#   Requires: curl, jq, openssl
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check dependencies
for cmd in curl jq openssl; do
  if ! command -v "$cmd" &> /dev/null; then
    echo -e "${RED}Error: $cmd is not installed${NC}"
    exit 1
  fi
done

# Parse arguments
if [ $# -lt 2 ]; then
  echo -e "${RED}Usage: $0 <webhook_url> <hmac_secret>${NC}"
  echo ""
  echo "Example:"
  echo "  $0 'https://n8n.example.com/webhook/yara/picc/notarize' 'your-secret-here'"
  exit 1
fi

WEBHOOK_URL="$1"
HMAC_SECRET="$2"

# Validate URL format
if [[ ! "$WEBHOOK_URL" =~ ^https?:// ]]; then
  echo -e "${RED}Error: Webhook URL must start with http:// or https://${NC}"
  exit 1
fi

# Generate unique nonce
NONCE=$(openssl rand -hex 16)

# Current Unix timestamp
TS=$(date +%s)

# Build PICC-1.0 decision payload
read -r -d '' PAYLOAD <<EOF || true
{
  "schema_version": "PICC-1.0",
  "ts": ${TS},
  "nonce": "${NONCE}",
  "decision": {
    "question": "Is the n8n YARA PICC notarization workflow operational?",
    "conclusion": "Testing webhook connectivity and validation",
    "confidence": "HIGH",
    "premises": [
      {
        "type": "FACT",
        "text": "Webhook test initiated from setup script",
        "evidence": [
          "https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica",
          "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/"
        ]
      },
      {
        "type": "ASSUMPTION",
        "text": "n8n instance is properly configured with GitHub credentials"
      }
    ],
    "inferences": [
      "Successful response indicates workflow is active",
      "GitHub issue creation confirms end-to-end integration"
    ],
    "contradictions": [
      "Failure would indicate configuration issues"
    ],
    "falsifier": "If no GitHub issue is created or response is error, setup is incomplete"
  },
  "metadata": {
    "actor": "test-webhook-script",
    "context": "n8n-setup-validation"
  }
}
EOF

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  YARA Lógica PICC Notarization - Webhook Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Webhook URL:${NC} $WEBHOOK_URL"
echo -e "${YELLOW}Timestamp:${NC} $TS ($(date -u -d "@$TS" '+%Y-%m-%d %H:%M:%S UTC'))"
echo -e "${YELLOW}Nonce:${NC} $NONCE"
echo ""

# Compute HMAC-SHA256 signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}')
echo -e "${YELLOW}Signature:${NC} sha256=$SIGNATURE"
echo ""

# Send POST request
echo -e "${BLUE}Sending request...${NC}"
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/webhook-response.json \
  -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD")

# Check HTTP status code
echo -e "${YELLOW}HTTP Status:${NC} $HTTP_CODE"
echo ""

# Parse response
if [ -f /tmp/webhook-response.json ]; then
  RESPONSE=$(cat /tmp/webhook-response.json)

  # Pretty print response
  echo -e "${YELLOW}Response:${NC}"
  echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
  echo ""

  # Check if response is valid JSON
  if ! echo "$RESPONSE" | jq '.' >/dev/null 2>&1; then
    echo -e "${RED}❌ Invalid JSON response${NC}"
    rm -f /tmp/webhook-response.json
    exit 1
  fi

  # Extract fields
  OK=$(echo "$RESPONSE" | jq -r '.ok // false')
  CODE=$(echo "$RESPONSE" | jq -r '.code // "UNKNOWN"')
  MSG=$(echo "$RESPONSE" | jq -r '.msg // "No message"')
  ISSUE_URL=$(echo "$RESPONSE" | jq -r '.issue_url // ""')
  ISSUE_NUMBER=$(echo "$RESPONSE" | jq -r '.issue_number // ""')
  HASH=$(echo "$RESPONSE" | jq -r '.hash // ""')

  # Analyze result
  if [ "$HTTP_CODE" = "200" ] && [ "$OK" = "true" ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ SUCCESS${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Code:${NC} $CODE"
    echo -e "${YELLOW}Message:${NC} $MSG"

    if [ "$CODE" = "CREATED" ]; then
      echo ""
      echo -e "${GREEN}New decision notarized!${NC}"
      echo -e "${YELLOW}Issue URL:${NC} $ISSUE_URL"
      echo -e "${YELLOW}Issue Number:${NC} #$ISSUE_NUMBER"
      echo -e "${YELLOW}Hash:${NC} $HASH"
      echo ""
      echo -e "${BLUE}Next steps:${NC}"
      echo "  1. Visit the GitHub issue: $ISSUE_URL"
      echo "  2. Verify the decision record is complete"
      echo "  3. Check labels: yara-logica, picc, hash:${HASH:0:16}"
    elif [ "$CODE" = "IDEMPOTENT" ]; then
      echo ""
      echo -e "${YELLOW}Decision already exists (idempotent response)${NC}"
      echo -e "${YELLOW}Issue URL:${NC} $ISSUE_URL"
      echo -e "${YELLOW}Issue Number:${NC} #$ISSUE_NUMBER"
      echo -e "${YELLOW}Hash:${NC} $HASH"
      echo ""
      echo -e "${BLUE}Note:${NC} This is normal if you've already submitted this exact decision."
    fi
  else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}  ❌ ERROR${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Code:${NC} $CODE"
    echo -e "${YELLOW}Message:${NC} $MSG"
    echo ""

    # Provide troubleshooting hints
    case "$CODE" in
      BAD_SIG)
        echo -e "${BLUE}Troubleshooting:${NC}"
        echo "  • Verify HMAC_SECRET matches between client and n8n"
        echo "  • Check that secret has no extra whitespace or newlines"
        echo "  • Ensure signature is computed on raw JSON body (not canonical)"
        ;;
      TS_WINDOW)
        echo -e "${BLUE}Troubleshooting:${NC}"
        echo "  • Check system time: $(date -u)"
        echo "  • Sync with NTP: sudo ntpdate -s pool.ntp.org"
        echo "  • Verify n8n server time is synchronized"
        ;;
      FACT_EVIDENCE)
        echo -e "${BLUE}Troubleshooting:${NC}"
        echo "  • FACT premises require ≥2 evidence URLs"
        echo "  • Ensure all evidence URLs use HTTPS (not HTTP)"
        ;;
      EVIDENCE_HTTPS)
        echo -e "${BLUE}Troubleshooting:${NC}"
        echo "  • All evidence URLs must use https:// (not http://)"
        echo "  • Check payload for non-HTTPS URLs"
        ;;
      *)
        echo -e "${BLUE}Troubleshooting:${NC}"
        echo "  • Check n8n execution logs for errors"
        echo "  • Verify GitHub credentials are configured"
        echo "  • Ensure environment variables are set (GITHUB_OWNER, GITHUB_REPO)"
        echo "  • Review runbook: spec/ops/runbook_notarization.md"
        ;;
    esac

    rm -f /tmp/webhook-response.json
    exit 1
  fi
else
  echo -e "${RED}❌ No response received${NC}"
  echo ""
  echo -e "${BLUE}Troubleshooting:${NC}"
  echo "  • Verify webhook URL is correct"
  echo "  • Check that n8n workflow is active"
  echo "  • Ensure n8n instance is accessible from this machine"
  echo "  • Review network/firewall settings"
  exit 1
fi

# Cleanup
rm -f /tmp/webhook-response.json

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Test completed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

exit 0
