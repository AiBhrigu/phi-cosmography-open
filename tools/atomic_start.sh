#!/usr/bin/env bash
set -euo pipefail
echo "== ATOMIC START =="
echo "-- hooks --"
echo "Install hooks once: ./tools/install_git_hooks.sh"
echo
./tools/preflight.sh
echo
echo "-- surface status --"
./tools/surface_status.sh | head -n 120
