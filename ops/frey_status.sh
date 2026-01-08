#!/usr/bin/env bash
set -euo pipefail

HOST="${FREY_HOST:-127.0.0.1}"
PORT="${FREY_PORT:-8811}"
APP="${FREY_APP:-frey_v03.frey_api.main:app}"

STATE_DIR="${FREY_STATE_DIR:-$HOME/.cache/frey_runner}"
PIDFILE="$STATE_DIR/frey.pid"
LOGFILE="$STATE_DIR/frey.log"
BASE="http://$HOST:$PORT"

mkdir -p "$STATE_DIR"

echo "== OPS STATUS =="
echo "APP=$APP"
echo "HOST=$HOST PORT=$PORT"
echo "STATE_DIR=$STATE_DIR"
echo "PIDFILE=$PIDFILE"
echo "LOGFILE=$LOGFILE"
echo

pidfile_pid=""
if [ -f "$PIDFILE" ]; then pidfile_pid="$(cat "$PIDFILE" 2>/dev/null || true)"; fi
alive="NO"
if [ -n "${pidfile_pid:-}" ] && ps -p "$pidfile_pid" >/dev/null 2>&1; then alive="YES"; fi

listen_pid="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"

echo "PROC CHECK:"
echo "PIDFILE_PID=${pidfile_pid:-} (alive=$alive)"
echo "LISTEN_PID=${listen_pid:-}"
echo

echo "PORT CHECK:"
if [ -n "${listen_pid:-}" ]; then
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || true
else
  echo "PORT=$PORT not listening"
fi
echo

echo "HTTP CHECK:"
code="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE/ping" 2>/dev/null || true)"
echo "HTTP=$code"
if [ "$code" = "200" ]; then
  echo "HTTP=OK"
else
  echo "HTTP=FAIL"
fi
echo

# FINAL truth: if port listens + http 200 => RUNNING
final="STOPPED"
final_pid="${pidfile_pid:-}"
if [ -n "${listen_pid:-}" ] && [ "$code" = "200" ]; then
  final="RUNNING"
  final_pid="$listen_pid"
fi

echo "FINAL:"
echo "PROC=$final PID=${final_pid:-}"
echo

echo "LOG TAIL:"
if [ -f "$LOGFILE" ]; then
  tail -n 60 "$LOGFILE" || true
else
  echo "NO LOG"
fi
