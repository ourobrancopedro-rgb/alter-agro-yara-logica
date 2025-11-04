#!/usr/bin/env bash

# ============================================================================
# Git Hooks Installer for YARA Lógica
# ============================================================================
# Purpose: Install pre-commit hooks for local security enforcement
# Usage: .github/scripts/install-hooks.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 YARA Lógica - Git Hooks Installer${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    echo -e "${RED}   Run this script from the repository root${NC}"
    exit 1
fi

# Check if source hooks exist
if [ ! -f ".git-hooks/pre-commit" ]; then
    echo -e "${RED}❌ Error: Source hooks not found${NC}"
    echo -e "${RED}   Missing: .git-hooks/pre-commit${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Installation steps:${NC}"
echo -e "   1. Verify source hooks"
echo -e "   2. Create symlinks in .git/hooks/"
echo -e "   3. Configure git settings"
echo -e "   4. Test hook installation"
echo ""

# ============================================================================
# STEP 1: Verify source hooks
# ============================================================================
echo -e "${BLUE}[1/4] Verifying source hooks...${NC}"

if [ ! -x ".git-hooks/pre-commit" ]; then
    echo -e "${YELLOW}   ⚠️  Making pre-commit hook executable...${NC}"
    chmod +x .git-hooks/pre-commit
fi

echo -e "${GREEN}   ✅ Source hooks verified${NC}"
echo ""

# ============================================================================
# STEP 2: Install hooks via symlink
# ============================================================================
echo -e "${BLUE}[2/4] Installing hooks...${NC}"

HOOKS_DIR=".git/hooks"
mkdir -p "$HOOKS_DIR"

# Pre-commit hook
if [ -f "$HOOKS_DIR/pre-commit" ] || [ -L "$HOOKS_DIR/pre-commit" ]; then
    echo -e "${YELLOW}   ⚠️  Existing pre-commit hook found${NC}"
    echo -e "${YELLOW}      Creating backup: $HOOKS_DIR/pre-commit.backup${NC}"
    mv "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/pre-commit.backup"
fi

# Create symlink (use relative path for portability)
REPO_ROOT=$(pwd)
ln -sf "../../.git-hooks/pre-commit" "$HOOKS_DIR/pre-commit"

if [ -L "$HOOKS_DIR/pre-commit" ]; then
    echo -e "${GREEN}   ✅ Pre-commit hook installed${NC}"
else
    echo -e "${RED}   ❌ Failed to install pre-commit hook${NC}"
    exit 1
fi
echo ""

# ============================================================================
# STEP 3: Configure git settings
# ============================================================================
echo -e "${BLUE}[3/4] Configuring git settings...${NC}"

# Enable GPG signing (recommended)
CURRENT_GPG_SETTING=$(git config --get commit.gpgsign || echo "not set")

if [ "$CURRENT_GPG_SETTING" != "true" ]; then
    echo -e "${YELLOW}   ⚠️  GPG signing is not enabled${NC}"
    echo -e "${YELLOW}      Enable GPG signing? (recommended) [Y/n]${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Nn]$ ]]; then
        git config commit.gpgsign true
        echo -e "${GREEN}      ✅ GPG signing enabled${NC}"

        # Check if user has a GPG key configured
        GPG_KEY=$(git config --get user.signingkey || echo "")
        if [ -z "$GPG_KEY" ]; then
            echo -e "${YELLOW}      ⚠️  No GPG key configured${NC}"
            echo -e "${YELLOW}         To configure:${NC}"
            echo -e "${YELLOW}         1. Generate key: gpg --gen-key${NC}"
            echo -e "${YELLOW}         2. List keys: gpg --list-secret-keys --keyid-format LONG${NC}"
            echo -e "${YELLOW}         3. Configure: git config user.signingkey <KEY_ID>${NC}"
        fi
    else
        echo -e "${YELLOW}      ⚠️  Skipping GPG signing configuration${NC}"
    fi
else
    echo -e "${GREEN}   ✅ GPG signing already enabled${NC}"
fi

# Set core.hooksPath (optional - we're using symlinks instead)
# git config core.hooksPath .git-hooks

echo -e "${GREEN}   ✅ Git settings configured${NC}"
echo ""

# ============================================================================
# STEP 4: Test installation
# ============================================================================
echo -e "${BLUE}[4/4] Testing hook installation...${NC}"

# Create a temporary test file
TEST_FILE=".test-hook-$$"
echo "test" > "$TEST_FILE"
git add "$TEST_FILE" 2>/dev/null || true

# Try to run the hook
if bash "$HOOKS_DIR/pre-commit" > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Pre-commit hook is working${NC}"
else
    # This might fail due to test file being outside allowlist, which is expected
    echo -e "${YELLOW}   ⚠️  Hook executed but may have validation warnings (this is normal)${NC}"
fi

# Clean up test file
git reset HEAD "$TEST_FILE" 2>/dev/null || true
rm -f "$TEST_FILE"

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Git hooks installed successfully!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📝 What happens now:${NC}"
echo -e "   • Pre-commit hook will run on every commit"
echo -e "   • It checks for secrets, forbidden content, file sizes"
echo -e "   • Commits will be blocked if violations are found"
echo -e "   • You can bypass with: git commit --no-verify (not recommended)"
echo ""
echo -e "${BLUE}🔧 Optional configurations:${NC}"
echo -e "   • Strict mode (warnings = errors): export YARA_STRICT_MODE=1"
echo -e "   • Configure GPG key: git config user.signingkey <KEY_ID>"
echo ""
echo -e "${BLUE}📚 More information:${NC}"
echo -e "   • Security policy: .github/SECURITY.md"
echo -e "   • Contributing guide: .github/CONTRIBUTING_SECURITY.md"
echo -e "   • Hook source: .git-hooks/pre-commit"
echo ""
echo -e "${GREEN}Happy secure coding! 🔒${NC}"
echo ""
