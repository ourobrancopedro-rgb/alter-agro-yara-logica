#!/bin/bash
# Security Gates Test Suite
# Tests all security gates locally before pushing
# Author: Alter Agro Ltda.
# License: BUSL-1.1

set -e  # Exit on first error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔒 SECURITY GATES TEST SUITE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Repository: $REPO_ROOT"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

cd "$REPO_ROOT"

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# Test 1: Hash Verification
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  HASH VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if python infra/github/verify_hashes.py --ledger infra/github/hash_ledger.json 2>&1; then
    echo ""
    echo "✅ Hash verification PASSED"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo ""
    echo "❌ Hash verification FAILED"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Test 2: Allowlist Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  ALLOWLIST CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if python infra/github/check_allowlist.py 2>&1; then
    echo ""
    echo "✅ Allowlist check PASSED"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo ""
    echo "❌ Allowlist check FAILED"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Test 3: Secret Scanning (DLP)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  SECRET SCANNING (DLP)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# DLP scanner may have warnings, so we don't fail on warnings
if python infra/github/scan_secrets.py 2>&1 | grep -q "✅ No violations detected"; then
    echo ""
    echo "✅ DLP scanning PASSED (no critical violations)"
    PASS_COUNT=$((PASS_COUNT + 1))
elif python infra/github/scan_secrets.py 2>&1 | grep -q "WARNING"; then
    echo ""
    echo "⚠️  DLP scanning PASSED with warnings (review manually)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo ""
    echo "❌ DLP scanning FAILED (critical violations detected)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Test 4: KPI Checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  KPI CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -d "lsa/spec" ]; then
    # Generate KPI report
    if python infra/github/kpi_score.py --spec_dir lsa/spec --out /tmp/kpi_report_test.json 2>&1; then
        echo ""
        echo "KPI report generated successfully"

        # Assert thresholds
        if python infra/github/kpi_assert.py \
            --report /tmp/kpi_report_test.json \
            --min_faithfulness 0.95 \
            --min_contradiction 0.90 2>&1; then
            echo ""
            echo "✅ KPI checks PASSED"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            echo ""
            echo "❌ KPI checks FAILED (thresholds not met)"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        echo ""
        echo "❌ KPI checks FAILED (report generation error)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    echo "⚠️  lsa/spec directory not found, skipping KPI checks"
    SKIP_COUNT=$((SKIP_COUNT + 1))
fi
echo ""

# Test 5: GitLeaks (optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  GITLEAKS SCAN (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v gitleaks &> /dev/null; then
    if gitleaks detect --config .gitleaks.toml --no-git --exit-code 1 2>&1; then
        echo ""
        echo "✅ GitLeaks PASSED"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo ""
        echo "❌ GitLeaks FAILED (secrets detected)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    echo "⚠️  GitLeaks not installed"
    echo "   Install: https://github.com/gitleaks/gitleaks#installation"
    SKIP_COUNT=$((SKIP_COUNT + 1))
fi
echo ""

# Test 6: Path/Extension Validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  PATH & EXTENSION VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for forbidden file types
FORBIDDEN_FOUND=false

echo "Checking for forbidden binaries..."
if git ls-files | egrep -i '\.(bin|safetensors|ckpt|pth|pkl|h5|pb|onnx|so|dll|dylib|exe)$' 2>/dev/null; then
    echo "❌ Forbidden binary files detected!"
    FORBIDDEN_FOUND=true
fi

echo "Checking for forbidden code files outside allowed paths..."
if git ls-files | grep -E '\.(py|js|ts|go|java|rb|php|rs)$' | \
    grep -v '^infra/github/' | \
    grep -v '^\.github/' | \
    grep -v '^lsa/spec/examples/' | \
    grep -v '^tools/' | \
    grep -v '^scripts/' | \
    grep -v '^tests/' 2>/dev/null; then
    echo "❌ Code files outside allowed paths detected!"
    FORBIDDEN_FOUND=true
fi

if [ "$FORBIDDEN_FOUND" = true ]; then
    echo ""
    echo "❌ Path/Extension validation FAILED"
    FAIL_COUNT=$((FAIL_COUNT + 1))
else
    echo "✅ No forbidden file types detected"
    echo ""
    echo "✅ Path/Extension validation PASSED"
    PASS_COUNT=$((PASS_COUNT + 1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Passed:  $PASS_COUNT"
echo "❌ Failed:  $FAIL_COUNT"
echo "⏭️  Skipped: $SKIP_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ ALL SECURITY GATES PASSED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎉 Ready to commit and push!"
    echo ""
    exit 0
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ SECURITY GATES FAILED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 Review the failed checks above and fix before committing."
    echo ""
    exit 1
fi
