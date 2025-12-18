#!/usr/bin/env bash
set -euo pipefail
echo "== ATOMIC START =="
./tools/preflight.sh
echo
echo "-- surface status --"
./tools/surface_status.sh | head -n 120
