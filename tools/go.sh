#!/usr/bin/env bash
set -euo pipefail

# ONE COMMAND ENTRYPOINT
if [ ! -x .git/hooks/pre-commit ] || [ ! -x .git/hooks/pre-push ]; then
  echo "== hooks missing: installing =="
  ./tools/install_git_hooks.sh
fi

./tools/atomic_start.sh
