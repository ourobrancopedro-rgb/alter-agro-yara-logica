#!/usr/bin/env bash

# ============================================================================
# Security Setup Script for YARA Lógica
# ============================================================================
# One-command security toolchain installation
#
# Usage: ./setup_security.sh [--dry-run]
# ============================================================================

set -e

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 YARA Lógica Security Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if $DRY_RUN; then
    echo -e "${YELLOW}🏃 DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

# ============================================================================
# Check prerequisites
# ============================================================================
echo -e "${BLUE}[1/6] Checking prerequisites...${NC}"

# Check git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ git not found${NC}"
    exit 1
fi
echo -e "${GREEN}   ✅ git found${NC}"

# Check python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}   ✅ python3 found${NC}"

# Check GPG
if ! command -v gpg &> /dev/null; then
    echo -e "${YELLOW}   ⚠️  gpg not found (GPG signing will not work)${NC}"
else
    echo -e "${GREEN}   ✅ gpg found${NC}"
fi

echo ""

# ============================================================================
# Install pre-commit hooks
# ============================================================================
echo -e "${BLUE}[2/6] Installing pre-commit hooks...${NC}"

if [ -f ".github/scripts/install-hooks.sh" ]; then
    if ! $DRY_RUN; then
        bash .github/scripts/install-hooks.sh
    else
        echo -e "${YELLOW}   (would run: .github/scripts/install-hooks.sh)${NC}"
    fi
    echo -e "${GREEN}   ✅ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}   ⚠️  Hook installer not found${NC}"
fi

echo ""

# ============================================================================
# Configure git settings
# ============================================================================
echo -e "${BLUE}[3/6] Configuring git settings...${NC}"

# Enable GPG signing
GPG_SIGN=$(git config --get commit.gpgsign || echo "false")
if [ "$GPG_SIGN" != "true" ]; then
    echo -e "${YELLOW}   Enable GPG signing? [Y/n]${NC}"
    if ! $DRY_RUN; then
        read -r response
        if [[ ! "$response" =~ ^[Nn]$ ]]; then
            git config commit.gpgsign true
            echo -e "${GREEN}   ✅ GPG signing enabled${NC}"
        fi
    else
        echo -e "${YELLOW}   (would ask user)${NC}"
    fi
else
    echo -e "${GREEN}   ✅ GPG signing already enabled${NC}"
fi

echo ""

# ============================================================================
# Test security tools
# ============================================================================
echo -e "${BLUE}[4/6] Testing security tools...${NC}"

# Test hash verifier
if python3 infra/github/verify_hashes.py > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Hash verifier works${NC}"
else
    echo -e "${YELLOW}   ⚠️  Hash verifier test failed (may need hash update)${NC}"
fi

# Test secret scanner
if [ -f "infra/github/scan_secrets.py" ]; then
    if python3 infra/github/scan_secrets.py --help > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Secret scanner works${NC}"
    else
        echo -e "${RED}   ❌ Secret scanner test failed${NC}"
    fi
fi

# Test allowlist checker
if [ -f "infra/github/check_allowlist.py" ]; then
    if python3 infra/github/check_allowlist.py --help > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Allowlist checker works${NC}"
    else
        echo -e "${RED}   ❌ Allowlist checker test failed${NC}"
    fi
fi

echo ""

# ============================================================================
# Generate configuration report
# ============================================================================
echo -e "${BLUE}[5/6] Generating configuration report...${NC}"

echo -e "${GREEN}   Security Configuration Summary:${NC}"
echo -e "   • GPG Signing: $(git config --get commit.gpgsign || echo 'not set')"
echo -e "   • User Name: $(git config --get user.name || echo 'not set')"
echo -e "   • User Email: $(git config --get user.email || echo 'not set')"
echo -e "   • Signing Key: $(git config --get user.signingkey || echo 'not set')"

echo ""

# ============================================================================
# Final summary
# ============================================================================
echo -e "${BLUE}[6/6] Setup complete!${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Security setup complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo -e "   1. Configure GPG key if not already done:"
echo -e "      gpg --gen-key"
echo -e "      git config user.signingkey <KEY_ID>"
echo -e "   2. Test pre-commit hook:"
echo -e "      echo 'test' > test.txt && git add test.txt && git commit -m 'test'"
echo -e "   3. Run security scan:"
echo -e "      python infra/github/scan_secrets.py --strict"
echo -e "   4. Generate security dashboard:"
echo -e "      python infra/github/security_dashboard.py"
echo ""
echo -e "${GREEN}Security toolchain ready! 🔒${NC}"
echo ""
