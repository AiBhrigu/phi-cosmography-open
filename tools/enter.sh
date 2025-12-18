#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-COSMO_OPEN}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIN="ATOMIC_START"

command -v tmux >/dev/null 2>&1 || {
  echo "ERROR: tmux not installed."
  echo "Install: sudo apt-get update && sudo apt-get install -y tmux"
  exit 2
}

CMD="cd \"$ROOT\" && ./tools/atomic_start.sh | head -n 120; echo; exec ${SHELL:-bash} -l"
QCMD="$(printf %q "$CMD")"

# ensure session exists
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -c "$ROOT" -n "$WIN" "bash -lc $QCMD"
else
  # ensure window exists; if exists — refresh pane
  if tmux list-windows -t "$SESSION" -F '#{window_name}' | grep -qx "$WIN"; then
    tmux respawn-pane -k -t "$SESSION:$WIN" "bash -lc $QCMD"
  else
    tmux new-window -t "$SESSION" -n "$WIN" -c "$ROOT" "bash -lc $QCMD"
  fi
fi

# attach/switch
if [ -n "${TMUX:-}" ]; then
  tmux select-window -t "$SESSION:$WIN" >/dev/null 2>&1 || true
  exec tmux switch-client -t "$SESSION"
else
  exec tmux attach -t "$SESSION"
fi
