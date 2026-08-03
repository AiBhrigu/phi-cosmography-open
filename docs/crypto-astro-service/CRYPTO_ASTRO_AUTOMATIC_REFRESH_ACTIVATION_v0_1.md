# Crypto-Astro Automatic Snapshot Refresh Activation v0.1

Status: **REVIEW CANDIDATE · ACTIVATES ONLY AFTER EXPLICIT MERGE**

Activation node: `BTC_COSMOGRAPHER_MARKET_SNAPSHOT_AUTOMATIC_REFRESH_SOURCE_TRUTH_REPAIR_v0_1`.

Machine-readable contract: `crypto_astro_automatic_refresh_activation_v0_1.json`.

## Proven root cause

The accepted 24-hour automatic refresh existed only as `DESIGN_ONLY_DRY_RUN`. The locked operational cadence intentionally prohibited `schedule` and `cron` inside the source-producing manual workflow. No scheduled static Snapshot run existed after the accepted refresh of 2026-08-01. Therefore the stale state was caused by `SCHEDULE_DID_NOT_START`, not by a failed source fetch, validation, artifact build, commit, deployment, cache, or freshness classifier.

## Architecture

The producer and publication chain remains:

1. `AiBhrigu/phi-cosmography-open` owns source fetch, methodology, generated Snapshot, Proof, module bindings, derived market field, Registry, Delta, Snapshot Memory and GitHub Pages publication.
2. `AiBhrigu/bhrigu-portal` consumes the three accepted public producer artifacts with `cache: no-store` and classifies freshness from `generated_at_utc`.
3. The existing `crypto-astro-static-refresh-manual.yml` remains the only source-producing workflow and the direct `workflow_dispatch` fallback.
4. The new `crypto-astro-automatic-refresh.yml` is a thin control plane. It does not implement a second market model and does not merge or deploy.

## Schedule and eligibility

- Scheduler: hourly at minute 17 UTC.
- Existing 18-hour hard minimum remains unchanged.
- Automatic eligibility opens at 20 hours.
- Public `FRESH` remains through exactly 24 hours.
- Operational breach remains after 48 hours.
- Fail-closed `UNAVAILABLE` remains after 168 hours.

The scheduler locks current `main`, rejects a future Snapshot, blocks when a refresh PR is open, blocks when the manual refresh workflow is queued or running, and runs the accepted source implementation in an ephemeral probe workspace.

## Source truth and material change

The probe invokes the accepted BHRIGU-compatible static refresh implementation and the accepted DeFi TVL methodology test. It preserves the authorized source identities, source hashes and provenance rules. No synthetic fallback is allowed.

If the source probe is healthy but produces no material file change, the scheduler records `NO_MATERIAL_CHANGE_RECHECK` and does not refresh the timestamp. The next hourly evaluation remains available.

If material change is proven, the scheduler dispatches the existing manual workflow in `DAILY_CADENCE` mode. The manual workflow remains responsible for complete source fetch, schema validation, Proof, consumer compatibility, deterministic Snapshot Memory, exact branch scope and review-PR creation.

## Failure diagnostics

Every run writes a machine-readable decision artifact and a GitHub Step Summary. Source or methodology failure fails the scheduled workflow visibly. Dispatch is accepted only when a new manual workflow run is observable after the dispatch request.

## Publication boundary

The scheduler may request one review PR. It may not merge a PR and may not issue a deployment command. Public mutation remains impossible until explicit merge authorization. GitHub Pages publishes accepted `main` through the existing publication workflow after an authorized merge.

## Current proof refresh in this candidate

The same review candidate contains one current generated refresh from the accepted source workflow. It advances the canonical Snapshot timestamp beyond `2026-08-01T18:24:00Z` and atomically rebuilds Proof, bindings, derived fields, Registry, Delta, Snapshot Memory and the static What Changed surface.

## Preserved boundaries

No question-protocol change, PR #114 runtime change, Astro routing, protocol bridge, BHRIGU Home change, payment, account, backend-provider activation, ORION exposure, new asset or redesign is included.
