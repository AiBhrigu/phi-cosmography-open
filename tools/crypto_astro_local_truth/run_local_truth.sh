#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
OUT="${2:-${ROOT}/artifacts/crypto-astro-local-truth}"
PORT="${3:-4173}"
URL="http://127.0.0.1:${PORT}/crypto-astro/index.html"
LOG="${OUT}/local-http-server.log"

mkdir -p "${OUT}"

python3 -m http.server "${PORT}" --directory "${ROOT}/site" >"${LOG}" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "${SERVER_PID}" 2>/dev/null || true
  wait "${SERVER_PID}" 2>/dev/null || true
}
trap cleanup EXIT

READY=0
for _ in $(seq 1 60); do
  if curl --fail --silent "${URL}" >/dev/null; then
    READY=1
    break
  fi
  sleep 0.25
done

if [[ "${READY}" != "1" ]]; then
  echo "LOCAL_TRUTH_SERVER_READY=NO" >&2
  exit 1
fi

python3 "${ROOT}/tools/crypto_astro_surface_truth/surface_truth.py" \
  --url "${URL}" \
  --out "${OUT}"

python3 - "${OUT}" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

out = Path(sys.argv[1])
report = json.loads((out / "surface-truth-report.json").read_text(encoding="utf-8"))
assert report["status"] == "PASS", report.get("failures")
assert report.get("failures") == [], report.get("failures")

for row in (out / "sha256_manifest.txt").read_text(encoding="utf-8").splitlines():
    digest, rel = row.split("  ", 1)
    actual = hashlib.sha256((out / rel).read_bytes()).hexdigest()
    assert actual == digest, f"SHA256 mismatch: {rel}"

print("LOCAL_TRUTH_STATUS=PASS")
print(f"LOCAL_TRUTH_DOM_ROWS={report['measurements']['dom_rows']}")
print(f"LOCAL_TRUTH_VISIBLE_TEXT_CHARACTERS={report['measurements']['visible_text_characters']}")
print(f"LOCAL_TRUTH_PUBLIC_VALUE_ROWS={report['measurements']['public_value_rows']}")
print(f"LOCAL_TRUTH_ANCHORS={report['measurements']['anchor_count']}")
print(f"LOCAL_TRUTH_BTC_RUNNING_ANIMATIONS={report['measurements']['btc_running_animations']}")
print(f"LOCAL_TRUTH_DESKTOP_SCROLL_WIDTH={report['measurements']['desktop_scroll_width']}")
print(f"LOCAL_TRUTH_MOBILE_SCROLL_WIDTH={report['measurements']['mobile_scroll_width']}")
PY
