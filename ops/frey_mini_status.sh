#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/orion_ai/frey_live/FREY_RUN_LIVE_v0.1"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$HOME/orion_ai/artifacts/FREY_MINI_STATUS_${TS}.md"

{
  echo "# FREY_MINI_STATUS"
  echo "DATE: $(date -Is)"
  echo
  echo "ping => $(frey ping 2>/dev/null || echo fail)"
  echo
  echo "tmux =>"
  tmux ls 2>/dev/null | grep -E 'frey_guard|frey_watch|frey_local' || echo "no frey tmux sessions"
  echo
  echo "ops status (head) =>"
  "$ROOT/ops/frey_status.sh" 2>/dev/null | head -n 45 || echo "ops status: fail/missing"
  echo
  echo "guard tail =>"
  tail -n 40 "$ROOT/logs/frey_guard.log" 2>/dev/null || echo "no guard log"
} | tee "$OUT" >/dev/null

sha256sum "$OUT" | tee "$OUT.sha256" >/dev/null
echo "OK: $OUT"
