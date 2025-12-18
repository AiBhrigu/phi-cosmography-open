#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-COSMO_OPEN}"

# If already inside tmux — do nothing (no nesting).
if [ -n "${TMUX:-}" ]; then
  echo "Already inside tmux: ${TMUX}"
  echo "Keep working, or switch client manually if needed."
  exit 0
fi

command -v tmux >/dev/null 2>&1 || {
  echo "ERROR: tmux not installed."
  echo "Install: sudo apt-get update && sudo apt-get install -y tmux"
  exit 2
}

if tmux has-session -t "$SESSION" 2>/dev/null; then
  exec tmux attach -t "$SESSION"
else
  exec tmux new -s "$SESSION"
fi
