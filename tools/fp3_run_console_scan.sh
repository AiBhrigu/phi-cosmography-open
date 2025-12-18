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

# install deps (idempotent)
if [ "$pm" = "pnpm" ]; then
  command -v pnpm >/dev/null 2>&1 || npm i -g pnpm >/dev/null 2>&1 || true
  pnpm i
elif [ "$pm" = "yarn" ]; then
  yarn install
else
  npm ci 2>/dev/null || npm i
fi

# pick preview command
node - <<'NODE'
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync("package.json","utf8"));
const s = pkg.scripts || {};
const has = (k)=>Object.prototype.hasOwnProperty.call(s,k);
let cmd = null;
if (has("preview")) cmd = "preview";
else if (has("dev")) cmd = "dev";
else if (has("start")) cmd = "start";
if (!cmd) {
  console.error("No scripts preview/dev/start in package.json");
  process.exit(3);
}
console.log(cmd);
NODE
script="$(node - <<'NODE'
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync("package.json","utf8"));
const s = pkg.scripts || {};
if (s.preview) process.stdout.write("preview");
else if (s.dev) process.stdout.write("dev");
else if (s.start) process.stdout.write("start");
NODE
)"

# start server
log="${OUT_DIR}/server.log"
pidfile="${OUT_DIR}/server.pid"
rm -f "$pidfile"

if [ "$pm" = "pnpm" ]; then
  (pnpm run "$script" -- --host 127.0.0.1 --port "$PORT" >"$log" 2>&1) & echo $! > "$pidfile"
elif [ "$pm" = "yarn" ]; then
  (yarn "$script" --host 127.0.0.1 --port "$PORT" >"$log" 2>&1) & echo $! > "$pidfile"
else
  (npm run "$script" -- --host 127.0.0.1 --port "$PORT" >"$log" 2>&1) & echo $! > "$pidfile"
fi

pid="$(cat "$pidfile")"

# wait for server
for i in {1..60}; do
  if curl -fsS "$BASE_URL/" >/dev/null 2>&1; then break; fi
  sleep 0.5
done

# run scan
set +e
BASE_URL="$BASE_URL" ROUTES="$ROUTES" OUT_DIR="$OUT_DIR" node tools/fp3_console_scan.mjs
rc=$?
set -e

# stop server
kill "$pid" >/dev/null 2>&1 || true
sleep 0.3
kill -9 "$pid" >/dev/null 2>&1 || true

exit "$rc"
