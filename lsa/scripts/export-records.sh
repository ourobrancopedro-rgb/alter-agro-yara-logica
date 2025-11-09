#!/bin/bash

# LSA Decision Record Export Script
# Exports decision records to various formats (CSV, HTML, Markdown)
# Usage: ./export-records.sh --format [csv|html|markdown] [--output file]

set -e

# Color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECORDS_DIR="$SCRIPT_DIR/../records"
FORMAT="csv"
OUTPUT=""
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --format)
      FORMAT="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 --format [csv|html|markdown] [--output file]"
      echo ""
      echo "Options:"
      echo "  --format   Export format (csv, html, markdown) [default: csv]"
      echo "  --output   Output file path [default: auto-generated]"
      echo "  --help     Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate format
if [[ ! "$FORMAT" =~ ^(csv|html|markdown)$ ]]; then
  echo "Error: Invalid format '$FORMAT'. Use csv, html, or markdown."
  exit 1
fi

# Set default output file
if [ -z "$OUTPUT" ]; then
  OUTPUT="$SCRIPT_DIR/../exports/decision-records-$TIMESTAMP.$FORMAT"
  mkdir -p "$SCRIPT_DIR/../exports"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  LSA Decision Record Export${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Records directory: $RECORDS_DIR"
echo "Format: $FORMAT"
echo "Output: $OUTPUT"
echo ""

# Check dependencies
command -v jq >/dev/null 2>&1 || {
  echo "Error: jq is not installed. Install with: apt-get install jq"
  exit 1
}

# Export to CSV
export_csv() {
  echo "ID,Question,Conclusion,Confidence,Author,Created,Premises_Count,Contradictions_Count,Hash" > "$OUTPUT"

  for record in "$RECORDS_DIR"/*.json; do
    [ -f "$record" ] || continue

    local id=$(jq -r '.id // "N/A"' "$record")
    local question=$(jq -r '.question // "N/A"' "$record" | tr ',' ';' | tr '\n' ' ')
    local conclusion=$(jq -r '.conclusion // "N/A"' "$record" | tr ',' ';' | tr '\n' ' ')
    local confidence=$(jq -r '.confidence // "N/A"' "$record")
    local author=$(jq -r '.author // "N/A"' "$record")
    local created=$(jq -r '.created_at // "N/A"' "$record")
    local premises_count=$(jq '[.premises[]?] | length' "$record")
    local contradictions_count=$(jq '[.contradictions[]?] | length' "$record")
    local hash=$(jq -r '.sha256 // "N/A"' "$record")

    echo "$id,\"$question\",\"$conclusion\",$confidence,\"$author\",$created,$premises_count,$contradictions_count,$hash" >> "$OUTPUT"
  done

  echo -e "${GREEN}✓ CSV export complete${NC}"
}

# Export to HTML
export_html() {
  cat > "$OUTPUT" <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LSA Decision Records</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
    h1 { color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }
    .record { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .record h2 { margin-top: 0; color: #667eea; }
    .metadata { color: #666; font-size: 0.9em; margin-bottom: 15px; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold; margin-right: 8px; }
    .badge.high { background: #28a745; color: white; }
    .badge.medium { background: #ffc107; color: black; }
    .badge.low { background: #dc3545; color: white; }
    .section { margin: 15px 0; }
    .section h3 { font-size: 1.1em; color: #555; margin-bottom: 8px; }
    .premise, .inference, .contradiction { padding: 8px; margin: 8px 0; border-left: 3px solid #ddd; background: #f9f9f9; }
    .hash { font-family: monospace; font-size: 0.85em; background: #f0f0f0; padding: 8px; border-radius: 4px; overflow-wrap: break-word; }
  </style>
</head>
<body>
  <h1>📊 LSA Decision Records</h1>
  <p>Generated: <strong>TIMESTAMP_PLACEHOLDER</strong></p>
EOF

  # Replace timestamp
  sed -i "s/TIMESTAMP_PLACEHOLDER/$(date '+%Y-%m-%d %H:%M:%S UTC')/" "$OUTPUT"

  for record in "$RECORDS_DIR"/*.json; do
    [ -f "$record" ] || continue

    local id=$(jq -r '.id // "N/A"' "$record")
    local question=$(jq -r '.question // "N/A"' "$record")
    local conclusion=$(jq -r '.conclusion // "N/A"' "$record")
    local confidence=$(jq -r '.confidence // "N/A"' "$record")
    local author=$(jq -r '.author // "N/A"' "$record")
    local created=$(jq -r '.created_at // "N/A"' "$record")
    local hash=$(jq -r '.sha256 // "N/A"' "$record")

    # Confidence badge class
    local badge_class="medium"
    case "$confidence" in
      HIGH|VERY_HIGH) badge_class="high" ;;
      LOW) badge_class="low" ;;
    esac

    cat >> "$OUTPUT" <<EOF
  <div class="record">
    <h2>$question</h2>
    <div class="metadata">
      <span class="badge $badge_class">$confidence</span>
      <strong>ID:</strong> $id | <strong>Author:</strong> $author | <strong>Created:</strong> $created
    </div>

    <div class="section">
      <h3>Conclusion</h3>
      <p>$conclusion</p>
    </div>

    <div class="section">
      <h3>Premises</h3>
EOF

    # Add premises
    jq -r '.premises[]? | "      <div class=\"premise\"><strong>\(.id // "P?"):</strong> \(.text // "N/A")</div>"' "$record" >> "$OUTPUT" || echo "      <p>No premises</p>" >> "$OUTPUT"

    cat >> "$OUTPUT" <<EOF
    </div>

    <div class="section">
      <h3>Hash</h3>
      <div class="hash">$hash</div>
    </div>
  </div>
EOF
  done

  cat >> "$OUTPUT" <<'EOF'
</body>
</html>
EOF

  echo -e "${GREEN}✓ HTML export complete${NC}"
}

# Export to Markdown
export_markdown() {
  cat > "$OUTPUT" <<EOF
# LSA Decision Records

**Generated:** $(date '+%Y-%m-%d %H:%M:%S UTC')

---

EOF

  for record in "$RECORDS_DIR"/*.json; do
    [ -f "$record" ] || continue

    local id=$(jq -r '.id // "N/A"' "$record")
    local question=$(jq -r '.question // "N/A"' "$record")
    local conclusion=$(jq -r '.conclusion // "N/A"' "$record")
    local confidence=$(jq -r '.confidence // "N/A"' "$record")
    local author=$(jq -r '.author // "N/A"' "$record")
    local created=$(jq -r '.created_at // "N/A"' "$record")
    local hash=$(jq -r '.sha256 // "N/A"' "$record")

    cat >> "$OUTPUT" <<EOF
## $question

**ID:** $id | **Confidence:** $confidence | **Author:** $author | **Created:** $created

### Conclusion
$conclusion

### Premises
EOF

    jq -r '.premises[]? | "- **\(.id // "P?"):** \(.text // "N/A")"' "$record" >> "$OUTPUT" || echo "No premises" >> "$OUTPUT"

    cat >> "$OUTPUT" <<EOF

### Contradictions
EOF

    jq -r '.contradictions[]? | "- **\(.id // "C?"):** \(.text // "N/A")"' "$record" >> "$OUTPUT" || echo "None" >> "$OUTPUT"

    cat >> "$OUTPUT" <<EOF

### Hash
\`\`\`
$hash
\`\`\`

---

EOF
  done

  echo -e "${GREEN}✓ Markdown export complete${NC}"
}

# Execute export based on format
case "$FORMAT" in
  csv)
    export_csv
    ;;
  html)
    export_html
    ;;
  markdown)
    export_markdown
    ;;
esac

echo ""
echo "Export saved to: $OUTPUT"
echo -e "${GREEN}✓ Export complete${NC}"
