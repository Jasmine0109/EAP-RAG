#!/usr/bin/env bash
# Install the repository's git hooks (currently: pre-commit validation + tests).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cp "$ROOT/scripts/pre-commit" "$ROOT/.git/hooks/pre-commit"
chmod +x "$ROOT/.git/hooks/pre-commit"
echo "installed pre-commit hook: $ROOT/.git/hooks/pre-commit"
