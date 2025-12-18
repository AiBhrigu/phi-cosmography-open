#!/usr/bin/env bash
set -euo pipefail

echo "== PREFLIGHT =="
BR="$(git rev-parse --abbrev-ref HEAD)"
echo "branch: $BR"

DIRTY="$(git status --porcelain || true)"
if [ "$BR" = "main" ] && [ -n "$DIRTY" ]; then
  echo "BLOCKED: main is dirty. Use a branch or commit intentionally."
  echo "$DIRTY"
  exit 2
fi

# forbid edits in these zones (repo-level)
BAD="$(echo "$DIRTY" | awk '{print $2}' | egrep '^(dist/|.git/worktrees/|.*_backup_.*|node_modules/|_wip_quarantine/)' || true)"
if [ -n "$BAD" ]; then
  echo "BLOCKED: forbidden paths modified:"
  echo "$BAD"
  exit 3
fi

echo "OK: clean or allowed changes only"
