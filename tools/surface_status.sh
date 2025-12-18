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

echo "-- guard scan: forbidden edit zones present? (must be read-only) --"
# Just list; no edits.
find . -maxdepth 4 -type d \( -path "*/.git/worktrees*" -o -path "*/dist*" -o -iname "_backup_*" \) 2>/dev/null | head -n 40 || true
echo

echo "-- site entrypoints --"
[ -d site ] && echo "OK: site/" || echo "MISSING: site/"
[ -f package.json ] && echo "OK: package.json" || echo "MISSING: package.json"
echo

echo "-- css hotlist --"
find site -maxdepth 3 -type f -name "*.css" 2>/dev/null | head -n 30 || true
