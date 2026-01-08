#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="${FREY_STATE_DIR:-$HOME/.cache/frey_runner}"
PIDFILE="$STATE_DIR/frey.pid"
LOGFILE="$STATE_DIR/frey.log"

mkdir -p "$STATE_DIR"

pid=""
if [ -f "$PIDFILE" ]; then pid="$(cat "$PIDFILE" 2>/dev/null || true)"; fi

if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
  echo "Stopping PID=$pid"
  kill "$pid" 2>/dev/null || true
  for _ in 1 2 3 4 5; do
    sleep 0.3
    ps -p "$pid" >/dev/null 2>&1 || break
  done
  if ps -p "$pid" >/dev/null 2>&1; then
    echo "Force kill PID=$pid"
    kill -9 "$pid" 2>/dev/null || true
  fi
else
  echo "No running PID found"
fi

rm -f "$PIDFILE" 2>/dev/null || true
echo "OK: DOWN"
echo "LOGFILE=$LOGFILE"
