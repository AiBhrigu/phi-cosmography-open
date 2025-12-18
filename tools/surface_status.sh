#!/usr/bin/env bash
set -euo pipefail

echo "== COSMOGRAPHY OPEN · SURFACE STATUS =="
echo "repo: $(pwd)"
echo

echo "-- git --"
git rev-parse --abbrev-ref HEAD
git --no-pager log --oneline -n 5
echo

echo "-- dirty? --"
git status --porcelain || true
echo

echo "-- FORBIDDEN MODS (dist/worktrees/_backup)? --"
BAD="$(git status --porcelain | awk '{print $2}' | egrep '^(dist/|.git/worktrees/|.*_backup_.*)' || true)"
if [ -n "${BAD}" ]; then
  echo "BLOCKED: forbidden paths modified:"
  echo "${BAD}"
  exit 2
else
  echo "OK: no forbidden-path modifications"
fi
echo

echo "-- forbidden zones (existence scan; read-only) --"
find . -maxdepth 4 -type d \
  \( -path "*/.git/worktrees*" -o -path "./dist*" -o -iname "_backup_*" \) \
  -not -path "./node_modules/*" 2>/dev/null | head -n 40 || true
echo

echo "-- site entrypoints --"
[ -d site ] && echo "OK: site/" || echo "MISSING: site/"
[ -f package.json ] && echo "OK: package.json" || echo "MISSING: package.json"
echo

echo "-- css hotlist (top 30) --"
find site -maxdepth 3 -type f -name "*.css" 2>/dev/null | head -n 30 || true
