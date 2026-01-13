# FREY_RUN_LIVE_v0.1 · RUNBOOK (CRYSTAL)

Truth:
- Source repo: ~/phi-cosmography-open
- App: frey_v03.frey_api.main:app
- Host/Port: 127.0.0.1:8811
- Wrapper root: ~/orion_ai/frey_live/FREY_RUN_LIVE_v0.1

Daily ops:
- ping: frey ping
- status (writes log): frey status
- deep status: ~/orion_ai/frey_live/FREY_RUN_LIVE_v0.1/ops/frey_status.sh
- smoke: ~/orion_ai/frey_live/FREY_RUN_LIVE_v0.1/ops/frey_smoke.sh
- watch (noisy): ~/orion_ai/frey_live/FREY_RUN_LIVE_v0.1/ops/frey_watch.sh  (keep OFF unless needed)

Stop conditions (STOP):
- ping != 200 / timeout
- status says STOPPED while guard claims running
- restart loop (many restarts/min) or empty logs
- import/module errors in logs

Crash protocol:
- run: ~/orion_ai/frey_live/FREY_RUN_LIVE_v0.1/ops/term_crash_post.sh
- artifact: ~/orion_ai/artifacts/OPS_TERM_CRASH_POST_<TS>.md + .sha256
