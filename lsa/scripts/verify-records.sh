#!/bin/bash

# LSA Decision Record Verification Script
# Validates decision records against schema and verifies hash integrity
# Usage: ./verify-records.sh [path-to-records-directory]

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECORDS_DIR="${1:-$SCRIPT_DIR/../records}"
SCHEMA_FILE="$SCRIPT_DIR/../schema/decision-record.schema.json"

# Counters
TOTAL=0
VERIFIED=0
HASH_MISMATCHES=0
SCHEMA_VIOLATIONS=0
MISSING_EVIDENCE=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  LSA Decision Record Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Records directory: $RECORDS_DIR"
echo "Schema file: $SCHEMA_FILE"
echo ""

# Check if required tools are installed
command -v jq >/dev/null 2>&1 || {
  echo -e "${RED}Error: jq is not installed. Install with: apt-get install jq${NC}"
  exit 1
}

# Check if schema exists
if [ ! -f "$SCHEMA_FILE" ]; then
  echo -e "${RED}Error: Schema file not found: $SCHEMA_FILE${NC}"
  exit 1
fi

# Check if records directory exists
if [ ! -d "$RECORDS_DIR" ]; then
  echo -e "${YELLOW}Warning: Records directory not found: $RECORDS_DIR${NC}"
  echo -e "${YELLOW}No decision records to verify.${NC}"
  exit 0
fi

# Optional: Check for ajv-cli (for schema validation)
AJV_AVAILABLE=false
if command -v ajv >/dev/null 2>&1; then
  AJV_AVAILABLE=true
else
  echo -e "${YELLOW}Warning: ajv-cli not installed. Schema validation will be skipped.${NC}"
  echo -e "${YELLOW}Install with: npm install -g ajv-cli${NC}"
  echo ""
fi

# Function to verify hash
verify_hash() {
  local record_file=$1
  local record_name=$(basename "$record_file")

  # Extract stored hash
  local stored_hash=$(jq -r '.sha256 // empty' "$record_file")

  if [ -z "$stored_hash" ]; then
    echo -e "${YELLOW}  ⚠️  No hash found in record${NC}"
    return 1
  fi

  # Compute hash (canonical JSON without sha256 field, sorted keys)
  local computed_hash=$(jq -Sc 'del(.sha256)' "$record_file" | jq -S -c | sha256sum | awk '{print $1}')

  # Compare
  if [ "$stored_hash" == "$computed_hash" ]; then
    echo -e "${GREEN}  ✓ Hash verified${NC}"
    return 0
  else
    echo -e "${RED}  ✗ Hash mismatch!${NC}"
    echo -e "${RED}    Expected: $stored_hash${NC}"
    echo -e "${RED}    Computed: $computed_hash${NC}"
    return 1
  fi
}

# Function to validate schema
validate_schema() {
  local record_file=$1

  if [ "$AJV_AVAILABLE" = true ]; then
    if ajv validate -s "$SCHEMA_FILE" -d "$record_file" >/dev/null 2>&1; then
      echo -e "${GREEN}  ✓ Schema valid${NC}"
      return 0
    else
      echo -e "${RED}  ✗ Schema validation failed${NC}"
      ajv validate -s "$SCHEMA_FILE" -d "$record_file" 2>&1 | sed 's/^/    /'
      return 1
    fi
  else
    # Basic manual validation
    local required_fields=("id" "question" "premises" "conclusion" "confidence" "falsifier")
    local valid=true

    for field in "${required_fields[@]}"; do
      if ! jq -e ".$field" "$record_file" >/dev/null 2>&1; then
        echo -e "${RED}  ✗ Missing required field: $field${NC}"
        valid=false
      fi
    done

    if [ "$valid" = true ]; then
      echo -e "${GREEN}  ✓ Basic validation passed${NC}"
      return 0
    else
      return 1
    fi
  fi
}

# Function to check evidence URLs
check_evidence() {
  local record_file=$1

  # Extract FACT premises
  local fact_count=$(jq '[.premises[]? | select(.type == "FACT")] | length' "$record_file")

  if [ "$fact_count" -eq 0 ]; then
    return 0  # No FACT premises to check
  fi

  # Check each FACT premise has ≥2 HTTPS evidence URLs
  local invalid_facts=$(jq -r '[.premises[]? | select(.type == "FACT" and (.evidence | length < 2))] | length' "$record_file")

  if [ "$invalid_facts" -gt 0 ]; then
    echo -e "${YELLOW}  ⚠️  $invalid_facts FACT premise(s) missing required evidence (≥2 URLs)${NC}"
    return 1
  fi

  # Check evidence URLs are HTTPS
  local non_https=$(jq -r '[.premises[]? | select(.type == "FACT") | .evidence[]? | select(startswith("https://") | not)] | length' "$record_file")

  if [ "$non_https" -gt 0 ]; then
    echo -e "${YELLOW}  ⚠️  $non_https evidence URL(s) are not HTTPS${NC}"
    return 1
  fi

  echo -e "${GREEN}  ✓ Evidence validated${NC}"
  return 0
}

# Main verification loop
echo -e "${BLUE}Verifying decision records...${NC}"
echo ""

for record in "$RECORDS_DIR"/*.json; do
  # Skip if no files found
  if [ "$record" = "$RECORDS_DIR/*.json" ]; then
    echo -e "${YELLOW}No JSON files found in $RECORDS_DIR${NC}"
    break
  fi

  TOTAL=$((TOTAL + 1))
  record_name=$(basename "$record")

  echo -e "${BLUE}[$TOTAL] $record_name${NC}"

  # Validate schema
  if validate_schema "$record"; then
    :
  else
    SCHEMA_VIOLATIONS=$((SCHEMA_VIOLATIONS + 1))
  fi

  # Verify hash
  if verify_hash "$record"; then
    :
  else
    HASH_MISMATCHES=$((HASH_MISMATCHES + 1))
  fi

  # Check evidence
  if check_evidence "$record"; then
    :
  else
    MISSING_EVIDENCE=$((MISSING_EVIDENCE + 1))
  fi

  # Count as verified if all checks passed
  if [ $SCHEMA_VIOLATIONS -eq 0 ] && [ $HASH_MISMATCHES -eq 0 ] && [ $MISSING_EVIDENCE -eq 0 ]; then
    VERIFIED=$((VERIFIED))
  fi

  echo ""
done

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Verification Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Total records: $TOTAL"
echo -e "Schema violations: $([ $SCHEMA_VIOLATIONS -eq 0 ] && echo -e "${GREEN}$SCHEMA_VIOLATIONS${NC}" || echo -e "${RED}$SCHEMA_VIOLATIONS${NC}")"
echo -e "Hash mismatches: $([ $HASH_MISMATCHES -eq 0 ] && echo -e "${GREEN}$HASH_MISMATCHES${NC}" || echo -e "${RED}$HASH_MISMATCHES${NC}")"
echo -e "Missing evidence: $([ $MISSING_EVIDENCE -eq 0 ] && echo -e "${GREEN}$MISSING_EVIDENCE${NC}" || echo -e "${YELLOW}$MISSING_EVIDENCE${NC}")"
echo ""

# Exit code
if [ $HASH_MISMATCHES -gt 0 ] || [ $SCHEMA_VIOLATIONS -gt 0 ]; then
  echo -e "${RED}✗ Verification FAILED${NC}"
  exit 1
else
  if [ $TOTAL -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No records found to verify${NC}"
    exit 0
  else
    echo -e "${GREEN}✓ All records verified successfully${NC}"
    exit 0
  fi
fi
