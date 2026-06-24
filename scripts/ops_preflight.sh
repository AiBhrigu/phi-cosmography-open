#!/usr/bin/env bash
set -euo pipefail

branch="$(git branch --show-current 2>/dev/null || echo unknown)"
status="$(git status --short 2>/dev/null || true)"

echo "PREFLIGHT_BRANCH=$branch"

if [ "$branch" = "main" ] && [ -n "$status" ]; then
  echo "PREFLIGHT=BLOCKED_MAIN_DIRTY"
  echo "$status"
  exit 1
fi

if [ -n "$status" ]; then
  echo "PREFLIGHT=DIRTY_REVIEW_REQUIRED"
  echo "$status"
else
  echo "PREFLIGHT=CLEAN"
fi
