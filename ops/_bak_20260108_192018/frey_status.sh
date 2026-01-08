#!/usr/bin/env bash
set -euo pipefail

HOST="${FREY_HOST:-127.0.0.1}"
PORT="${FREY_PORT:-8811}"
APP="${FREY_APP:-frey_v03.frey_api.main:app}"

STATE_DIR="${FREY_STATE_DIR:-$HOME/.cache/frey_runner}"
PIDFILE="$STATE_DIR/frey.pid"
LOGFILE="$STATE_DIR/frey.log"

pid=""
if [ -f "$PIDFILE" ]; then pid="$(cat "$PIDFILE" 2>/dev/null || true)"; fi

proc="STOPPED"
if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
  proc="RUNNING PID=$pid"
fi

# PORT: authoritative check
port_listen="NO"
port_pids="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [ -n "${port_pids:-}" ]; then
  port_listen="YES (pids: $port_pids)"
fi

# HTTP: authoritative check
http_code="$(curl -sS -o /dev/null -w '%{http_code}' "http://$HOST:$PORT/docs" 2>/dev/null || echo 000)"
http_ok="FAIL"
[ "$http_code" = "200" ] && http_ok="OK"

echo "== OPS STATUS =="
echo "APP=$APP"
echo "HOST=$HOST PORT=$PORT"
echo "STATE_DIR=$STATE_DIR"
echo "PIDFILE=$PIDFILE"
echo "LOGFILE=$LOGFILE"
echo
echo "PROC=$proc"
echo
echo "PORT CHECK:"
if [ "$port_listen" = "NO" ]; then
  echo "PORT=$PORT not listening"
else
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || true
fi
echo
echo "HTTP CHECK:"
echo "HTTP=$http_code"
echo "HTTP=$http_ok"
echo
echo "LOG TAIL:"
tail -n 40 "$LOGFILE" 2>/dev/null || echo "NO LOG"
echo

# warn on inconsistencies
if [ "$http_code" = "200" ] && [ "$port_listen" = "NO" ]; then
  echo "WARN: HTTP=200 but port-check says NO. Show ss/lsof details:"
  ss -ltnp 2>/dev/null | grep -F ":$PORT" || true
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || true
fi
