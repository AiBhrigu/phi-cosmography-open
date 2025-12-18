#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION="${1:-COSMO_OPEN}"

if [ -n "${TMUX:-}" ]; then
  echo "Already inside tmux. Session: ${TMUX}"
  exit 0
fi

# attach or create session at repo root
tmux new-session -As "$SESSION" -c "$ROOT" \; \
  rename-window -t "$SESSION:0" "lane" \; \
  set-option -t "$SESSION" history-limit 20000 \; \
  display-message "COSMO lane ready. Run: ./tools/atomic_start.sh"
