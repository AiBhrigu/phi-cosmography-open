#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

HOST="${FREY_HOST:-127.0.0.1}"
PORT="${FREY_PORT:-8811}"
APP="${FREY_APP:-frey_v03.frey_api.main:app}"

STATE_DIR="${FREY_STATE_DIR:-$HOME/.cache/frey_runner}"
PIDFILE="$STATE_DIR/frey.pid"
LOGFILE="$STATE_DIR/frey.log"

mkdir -p "$STATE_DIR"

# 0) if already running, exit green
if [ -f "$PIDFILE" ]; then
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "${pid:-}" ] && ps -p "$pid" >/dev/null 2>&1; then
    echo "OK: already running PID=$pid"
    echo "LOGFILE=$LOGFILE"
    exit 0
  fi
fi

# 1) port lock
if command -v ss >/dev/null 2>&1; then
  if ss -ltn 2>/dev/null | grep -qE ":${PORT}\b"; then
    echo "BLOCKED: port ${PORT} already listening"
    ss -ltnp 2>/dev/null | grep -E ":${PORT}\b" || true
    exit 2
  fi
elif command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "BLOCKED: port ${PORT} already listening"
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN || true
    exit 2
  fi
fi

# 2) install editable package (safe, quiet-ish)
python3 -m pip install -e ./frey_v03 >/dev/null

# 3) start
: > "$LOGFILE"
nohup python3 -m uvicorn "$APP" --host "$HOST" --port "$PORT" >>"$LOGFILE" 2>&1 &
pid=$!
echo "$pid" > "$PIDFILE"

# 4) probe
sleep 0.6
if curl -sS -o /dev/null "http://${HOST}:${PORT}/docs" 2>/dev/null; then
  echo "OK: UP PID=$pid http://${HOST}:${PORT}/docs"
  echo "LOGFILE=$LOGFILE"
  exit 0
fi

echo "ERR: not reachable yet (PID=$pid)"
tail -n 80 "$LOGFILE" || true
exit 1
