#!/usr/bin/env bash
set -euo pipefail

HOST="${FREY_HOST:-127.0.0.1}"
PORT="${FREY_PORT:-8811}"
APP="${FREY_APP:-frey_v03.frey_api.main:app}"

STATE_DIR="${FREY_STATE_DIR:-$HOME/.cache/frey_runner}"
PIDFILE="$STATE_DIR/frey.pid"
LOGFILE="$STATE_DIR/frey.log"

mkdir -p "$STATE_DIR"

echo "APP=$APP"
echo "HOST=$HOST PORT=$PORT"
echo "STATE_DIR=$STATE_DIR"
echo "PIDFILE=$PIDFILE"
echo "LOGFILE=$LOGFILE"
echo

pid=""
if [ -f "$PIDFILE" ]; then pid="$(cat "$PIDFILE" 2>/dev/null || true)"; fi

if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
  echo "PROC=RUNNING PID=$pid"
else
  echo "PROC=STOPPED"
fi

echo
echo "PORT CHECK:"
if command -v ss >/dev/null 2>&1; then
  ss -ltnp 2>/dev/null | grep -E ":${PORT}\b" || echo "PORT=${PORT} not listening"
elif command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || echo "PORT=${PORT} not listening"
else
  echo "NO ss/lsof available"
fi

echo
echo "HTTP CHECK:"
curl -sS -o /dev/null -w "HTTP=%{http_code}\n" "http://${HOST}:${PORT}/docs" 2>/dev/null || echo "HTTP=FAIL"

echo
echo "LOG TAIL:"
tail -n 40 "$LOGFILE" 2>/dev/null || echo "NO LOG"
