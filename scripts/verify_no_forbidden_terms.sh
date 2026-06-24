#!/usr/bin/env bash
set -euo pipefail

TARGETS=("site" "OPS_F_AGENT_BOUNDARY.md" ".github/copilot-instructions.md")
PATTERN='guaranteed profit|investment advice|financial advice|trading signal|price target|auto-delivery|live market data|ORION core exposure'

status=0
for target in "${TARGETS[@]}"; do
  if [ -e "$target" ]; then
    if grep -RInE "$PATTERN" "$target" >/tmp/forbidden_terms_hits.txt 2>/dev/null; then
      echo "FORBIDDEN_TERMS_CHECK=REVIEW_REQUIRED"
      cat /tmp/forbidden_terms_hits.txt
      status=1
    fi
  fi
done

if [ "$status" -eq 0 ]; then
  echo "FORBIDDEN_TERMS_CHECK=PASS"
fi

exit "$status"
