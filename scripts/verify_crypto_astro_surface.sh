#!/usr/bin/env bash
set -euo pipefail

PAGE="site/crypto-astro/index.html"

test -f "$PAGE" || { echo "SURFACE_CHECK=FAIL_PAGE_MISSING"; exit 1; }

grep -q "Crypto-Astro" "$PAGE" || { echo "SURFACE_CHECK=FAIL_TITLE_MISSING"; exit 1; }
grep -q "Local Staging Proof" "$PAGE" || { echo "SURFACE_CHECK=FAIL_LOCAL_STAGING_MARKER_MISSING"; exit 1; }
grep -q "Batch Queue Proof" "$PAGE" || { echo "SURFACE_CHECK=FAIL_BATCH_QUEUE_MARKER_MISSING"; exit 1; }
grep -q "No backend/API" "$PAGE" || { echo "SURFACE_CHECK=FAIL_BOUNDARY_COPY_MISSING"; exit 1; }

echo "SURFACE_CHECK=PASS"
