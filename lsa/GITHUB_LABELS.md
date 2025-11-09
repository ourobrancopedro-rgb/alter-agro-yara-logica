# GitHub Labels for LSA Decision Records

## Required Labels

The LSA workflow uses the following GitHub labels for categorization and audit tracking. These labels should be created in the repository before using the automated n8n workflow.

### Core LSA Labels

| Label | Color | Description |
|:------|:------|:------------|
| `lsa` | `#667eea` | Logic Sorting Architecture decision record |
| `decision-record` | `#764ba2` | Audit-grade decision documentation |

### Confidence Level Labels

| Label | Color | Description |
|:------|:------|:------------|
| `high-confidence` | `#28a745` | HIGH confidence level |
| `medium-confidence` | `#ffc107` | MEDIUM confidence level |
| `low-confidence` | `#dc3545` | LOW confidence level |

### Workflow Labels

| Label | Color | Description |
|:------|:------|:------------|
| `needs-review` | `#6c757d` | Decision requires human validation |

### Dynamic Labels (Auto-Generated)

These labels are created automatically by the n8n workflow:

- `hash:<hex16>` — First 16 characters of SHA-256 hash (for idempotency)
- `schema:PICC-1.0` — Schema version identifier
- `actor:<name>` — Decision author/submitter
- `context:<env>` — Execution context (e.g., production, staging)

## Manual Creation via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Authenticate
gh auth login

# Create LSA labels
gh label create "lsa" \
  --color "667eea" \
  --description "Logic Sorting Architecture decision record" \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica

gh label create "decision-record" \
  --color "764ba2" \
  --description "Audit-grade decision documentation" \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica

gh label create "high-confidence" \
  --color "28a745" \
  --description "HIGH confidence level" \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica

gh label create "medium-confidence" \
  --color "ffc107" \
  --description "MEDIUM confidence level" \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica

gh label create "low-confidence" \
  --color "dc3545" \
  --description "LOW confidence level" \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica

gh label create "needs-review" \
  --color "6c757d" \
  --description "Decision requires human validation" \
  --repo ourobrancopedro-rgb/alter-agro-yara-logica
```

## Manual Creation via GitHub Web UI

1. Navigate to repository: https://github.com/ourobrancopedro-rgb/alter-agro-yara-logica
2. Click **Issues** tab
3. Click **Labels** (next to Milestones)
4. Click **New label**
5. Enter label details from table above
6. Click **Create label**
7. Repeat for all required labels

## Automated Creation via Script

Save this as `create-labels.sh` and run:

```bash
#!/bin/bash

REPO="ourobrancopedro-rgb/alter-agro-yara-logica"

declare -A LABELS=(
  ["lsa"]="667eea|Logic Sorting Architecture decision record"
  ["decision-record"]="764ba2|Audit-grade decision documentation"
  ["high-confidence"]="28a745|HIGH confidence level"
  ["medium-confidence"]="ffc107|MEDIUM confidence level"
  ["low-confidence"]="dc3545|LOW confidence level"
  ["needs-review"]="6c757d|Decision requires human validation"
)

for label in "${!LABELS[@]}"; do
  IFS='|' read -r color description <<< "${LABELS[$label]}"
  gh label create "$label" \
    --color "$color" \
    --description "$description" \
    --repo "$REPO" || echo "Label '$label' may already exist"
done

echo "✅ Label creation complete"
```

## Verification

Verify labels were created:

```bash
gh label list --repo ourobrancopedro-rgb/alter-agro-yara-logica | grep -E "(lsa|decision-record|confidence|needs-review)"
```

Expected output:
```
lsa                  Logic Sorting Architecture decision record
decision-record      Audit-grade decision documentation
high-confidence      HIGH confidence level
medium-confidence    MEDIUM confidence level
low-confidence       LOW confidence level
needs-review         Decision requires human validation
```

## Notes

- Labels are case-sensitive
- Hash labels (e.g., `hash:a3b5c7d9e1f3a5b7`) are created automatically by the workflow
- Existing labels with the same name will not be overwritten
- Label colors are hex codes without the `#` prefix

---

**© 2025 Alter Agro Ltda.**
_LSA Decision Record System — GitHub Label Configuration_
