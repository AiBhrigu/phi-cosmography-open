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

# if already listening: don't start another
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "BLOCKED: port $PORT already listening"
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || true
  exit 2
fi

# if pidfile alive but port not listening — cleanup stale pidfile
pid=""
if [ -f "$PIDFILE" ]; then pid="$(cat "$PIDFILE" 2>/dev/null || true)"; fi
if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
  echo "WARN: PIDFILE says alive (PID=$pid) but port is free; continuing anyway"
fi
rm -f "$PIDFILE" 2>/dev/null || true

# start
: > "$LOGFILE" 2>/dev/null || true
nohup python3 -m uvicorn "$APP" --host "$HOST" --port "$PORT" >"$LOGFILE" 2>&1 &
newpid=$!
echo "$newpid" > "$PIDFILE"
echo "OK: START PID=$newpid"
echo "LOGFILE=$LOGFILE"

# wait until reachable (max ~12s)
for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 1
  code="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE/ping" 2>/dev/null || true)"
  if [ "$code" = "200" ]; then
    echo "OK: HTTP=200"
    exit 0
  fi
done

echo "ERR: not reachable yet (PID=$newpid)"
tail -n 80 "$LOGFILE" || true
exit 1
