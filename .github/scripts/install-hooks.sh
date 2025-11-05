#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
mkdir -p .git-hooks
git config core.hooksPath .git-hooks
for h in pre-commit commit-msg pre-push; do
  [[ -f ".git-hooks/$h" ]] && chmod +x ".git-hooks/$h"
done
echo "✅ Hooks installed (core.hooksPath=.git-hooks)"
