#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp)"
cat > "$tmp"
bash "$tmp"
rm -f "$tmp"
