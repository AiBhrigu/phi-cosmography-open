#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-COSMO_OPEN}"

# If already inside tmux — do nothing.
if [ -n "${TMUX:-}" ]; then
  echo "Already inside tmux. Session: ${TMUX}"
  exit 0
fi

command -v tmux >/dev/null 2>&1 || { echo "ERROR: tmux not installed"; exit 2; }

# Attach if exists, else create.
if tmux has-session -t "$SESSION" 2>/dev/null; then
  exec tmux attach -t "$SESSION"
else
  exec tmux new -s "$SESSION"
fi
