#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-COSMO_OPEN}"

command -v tmux >/dev/null 2>&1 || {
  echo "ERROR: tmux not installed."
  echo "Install: sudo apt-get update && sudo apt-get install -y tmux"
  exit 2
}

# If already inside tmux — switch client to target session (no nesting).
if [ -n "${TMUX:-}" ]; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    exec tmux switch-client -t "$SESSION"
  else
    echo "ERROR: session '$SESSION' not found."
    echo "Create: tmux new -d -s '$SESSION'"
    exit 3
  fi
fi

# Outside tmux — attach or create.
if tmux has-session -t "$SESSION" 2>/dev/null; then
  exec tmux attach -t "$SESSION"
else
  exec tmux new -s "$SESSION"
fi
