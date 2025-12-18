#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-COSMO_OPEN}"
DRY="${2:-}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v tmux >/dev/null 2>&1 || {
  echo "ERROR: tmux not installed."
  echo "Install: sudo apt-get update && sudo apt-get install -y tmux"
  exit 2
}

CMD="cd '$ROOT' && ./tools/atomic_start.sh; echo; exec \$SHELL -l"
WIN="ATOMIC_START"

if [ "$DRY" = "--dry-run" ]; then
  echo "DRY-RUN:"
  echo "session=$SESSION"
  echo "window=$WIN"
  echo "cmd=$CMD"
  exit 0
fi

# ensure session exists
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -c "$ROOT" "bash -lc $CMD"
else
  # create a fresh window that runs atomic_start
  tmux new-window -t "$SESSION" -n "$WIN" -c "$ROOT" "bash -lc $CMD" >/dev/null
fi

# switch/attach (no nesting)
if [ -n "${TMUX:-}" ]; then
  exec tmux switch-client -t "$SESSION"
else
  exec tmux attach -t "$SESSION"
fi
