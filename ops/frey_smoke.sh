#!/usr/bin/env bash
set -euo pipefail

BASE="${FREY_BASE:-http://127.0.0.1:8811}"

echo "== FREY SMOKE @ $(date +%H:%M) =="
echo "BASE=$BASE"
echo

echo "== PING =="
curl -sS -w '\nHTTP=%{http_code}\n' "$BASE/ping"
echo

echo "== PHI-PASSPORT =="
curl -sS -H 'Content-Type: application/json' \
  -d '{"user_id":"demo","birth_date":19860324}' \
  -w '\nHTTP=%{http_code}\n' \
  "$BASE/phi-passport"
echo

echo "== MATCH-USER-ASSET =="
curl -sS -H 'Content-Type: application/json' \
  -d '{"user_birth":19860324,"asset_code":"BTC"}' \
  -w '\nHTTP=%{http_code}\n' \
  "$BASE/match-user-asset"
echo

echo "== EVENT-LOG =="
curl -sS -H 'Content-Type: application/json' \
  -d '{"user_id":"demo","event":"local_smoke_003"}' \
  -w '\nHTTP=%{http_code}\n' \
  "$BASE/event-log"
echo
