#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-COSMO_OPEN}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v tmux >/dev/null 2>&1 || {
  echo "ERROR: tmux not installed."
  echo "Install: sudo apt-get update && sudo apt-get install -y tmux"
  exit 2
}

# inside tmux: switch client to session (no nesting)
if [ -n "${TMUX:-}" ]; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    exec tmux switch-client -t "$SESSION"
  else
    echo "ERROR: session '$SESSION' not found."
    echo "Create: tmux new-session -d -s '$SESSION' -c '$ROOT'"
    exit 3
  fi
fi

# outside tmux: attach/create with correct cwd
exec tmux new-session -As "$SESSION" -c "$ROOT"
