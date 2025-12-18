#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-4173}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT}}"
ROUTES="${ROUTES:-/ /start /cosmography /map /orion /frey /dao}"
OUT_DIR="${OUT_DIR:-/tmp/fp3}"

pm=""
if [ -f pnpm-lock.yaml ]; then pm="pnpm"
elif [ -f yarn.lock ]; then pm="yarn"
else pm="npm"
fi

if [ "$pm" = "pnpm" ]; then
  command -v pnpm >/dev/null 2>&1 || npm i -g pnpm >/dev/null 2>&1 || true
  pnpm i
elif [ "$pm" = "yarn" ]; then
  yarn install
else
  npm ci 2>/dev/null || npm i
fi

if node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  npx playwright install >/dev/null 2>&1 || true
fi

script="$(node - <<'NODE'
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync("package.json","utf8"));
const s = pkg.scripts || {};
if (s.preview) process.stdout.write("preview");
else if (s.dev) process.stdout.write("dev");
else if (s.start) process.stdout.write("start");
else process.exit(3);
NODE
)"

log="${OUT_DIR}/server.log"
pidfile="${OUT_DIR}/server.pid"
rm -f "$pidfile"
mkdir -p "$OUT_DIR"

if [ "$pm" = "pnpm" ]; then
  (pnpm run "$script" -- --host 127.0.0.1 --port "$PORT" >"$log" 2>&1) & echo $! > "$pidfile"
elif [ "$pm" = "yarn" ]; then
  (yarn "$script" --host 127.0.0.1 --port "$PORT" >"$log" 2>&1) & echo $! > "$pidfile"
else
  (npm run "$script" -- --host 127.0.0.1 --port "$PORT" >"$log" 2>&1) & echo $! > "$pidfile"
fi

pid="$(cat "$pidfile")"

for i in {1..60}; do
  if curl -fsS "$BASE_URL/" >/dev/null 2>&1; then break; fi
  sleep 0.5
done

set +e
BASE_URL="$BASE_URL" ROUTES="$ROUTES" OUT_DIR="$OUT_DIR" node tools/fp3_console_scan.mjs
rc=$?
set -e

kill "$pid" >/dev/null 2>&1 || true
sleep 0.3
kill -9 "$pid" >/dev/null 2>&1 || true

exit "$rc"
