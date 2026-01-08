#!/usr/bin/env bash
set -euo pipefail

HOST="${FREY_HOST:-127.0.0.1}"
PORT="${FREY_PORT:-8811}"
APP="${FREY_APP:-frey_v03.frey_api.main:app}"

STATE_DIR="${FREY_STATE_DIR:-$HOME/.cache/frey_runner}"
PIDFILE="$STATE_DIR/frey.pid"
LOGFILE="$STATE_DIR/frey.log"

echo "APP=$APP"
echo "HOST=$HOST PORT=$PORT"
echo "STATE_DIR=$STATE_DIR"
echo "PIDFILE=$PIDFILE"
echo "LOGFILE=$LOGFILE"
echo

pid=""
if [ -f "$PIDFILE" ]; then
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
fi

# если pidfile пуст/битый — определяем PID по порту
if [ -z "${pid:-}" ]; then
  pid="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
fi

if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
  echo "PROC=RUNNING PID=$pid"
else
  echo "PROC=STOPPED"
fi

echo
echo "PORT CHECK:"
ss -ltnp 2>/dev/null | grep -E ":$PORT\b" || echo "PORT=$PORT not listening"

echo
echo "HTTP CHECK:"
code="$(curl -sS -o /dev/null -w '%{http_code}' "http://$HOST:$PORT/docs" || true)"
echo "HTTP=$code"
[ "$code" = "200" ] || echo "HTTP=FAIL"

echo
echo "LOG TAIL:"
[ -f "$LOGFILE" ] && tail -n 80 "$LOGFILE" || echo "NO LOG"
