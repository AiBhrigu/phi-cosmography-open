#!/usr/bin/env bash
set -euo pipefail
while true; do
  echo
  echo "===== $(date +%H:%M) ====="
  ./ops/frey_status.sh || true
  sleep 5
done
