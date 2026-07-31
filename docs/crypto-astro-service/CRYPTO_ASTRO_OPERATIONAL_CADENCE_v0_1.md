# Crypto-Astro Operational Cadence v0.1

Status: **LOCKED FOR MANUAL CONTROLLED REFRESH**

Machine-readable source of truth: `crypto_astro_operational_cadence_v0_1.json`.

Freshness contract: `btc_market_snapshot_freshness_24h_168h_v0_1`.

## Operating model

Crypto-Astro uses a static, source-bound market snapshot. A refresh is prepared by a manually dispatched GitHub Actions workflow. The workflow may create one fully validated branch and one review pull request. It may not merge the pull request or issue a deployment command.

Publication occurs only after explicit merge authorization. The existing Pages workflow then publishes accepted `main` automatically, followed by public Pages and BHRIGU BTC Field Read verification.

## Normal cadence

- Target: one accepted snapshot per rolling 24 hours.
- `DAILY_CADENCE` may not run less than 18 hours after the latest accepted snapshot.
- Target maximum operational gap: 48 hours.
- BHRIGU public freshness boundary: `FRESH` through exactly 24 hours.
- After 24 hours and through 168 hours the public state is `STALE_LIMITED`.
- Crossing 48 hours is an operational breach and escalation boundary; it is not a second public freshness state.
- The 72-hour point is a regression probe inside `STALE_LIMITED`, never a `FRESH` boundary.
- After 168 hours the BTC Field Read fails closed as unavailable.
- A refresh is not accepted merely to change a timestamp. If no material file change is generated, no review PR is opened.

## Authorized modes

| Mode | Purpose | 18-hour minimum |
|---|---|---:|
| `DAILY_CADENCE` | Normal accepted daily snapshot | Enforced |
| `PRE_REPORT` | Snapshot before an important operator or public report | Bypassed with recorded reason |
| `MATERIAL_MARKET_EVENT` | Bounded refresh after a material market-state change | Bypassed with recorded reason |
| `REPEATABILITY_PROOF` | Gate 3 second end-to-end proof | Bypassed with recorded reason |
| `SOURCE_OR_SCHEMA_REPAIR` | Restore availability after a proven contract defect | Bypassed with recorded reason |

Every dispatch requires `refresh_mode`, `operator_ref`, and `refresh_reason`.

## Single-flight policy

A dispatch fails closed when:

- the checkout is not the current `origin/main`;
- another automated refresh pull request is open;
- the dispatch mode or operator reference is missing;
- `DAILY_CADENCE` is attempted before 18 hours have elapsed;
- source, proof, schema, methodology, consumer, scope, memory, or atomicity validation fails.

GitHub Actions concurrency prevents simultaneous workflow runs. The open-PR preflight prevents multiple review contours from existing at once.

## Acceptance sequence

1. Lock the exact current `main` SHA.
2. Prove that no refresh PR is already open.
3. Validate dispatch mode, operator reference, reason, and cadence.
4. Fetch source data and bind source hashes.
5. Validate schema and methodology.
6. Validate the generated packet with the current BHRIGU consumer.
7. Prove the exact atomic branch scope.
8. Open one generated review PR.
9. Review source, proof, bindings, memory, delta, scope, and methodology.
10. Review desktop and mobile rendering.
11. Obtain explicit Operator F merge authorization.
12. Merge to `main`.
13. Allow the existing Pages workflow to publish the accepted `main`.
14. Verify the public Pages snapshot.
15. Verify BHRIGU BTC Field Read.
16. Close the contour with source anchors.

## Prohibited automation

The refresh workflow must not contain:

- a `schedule` or `push` trigger;
- cron;
- an automatic merge command;
- a deployment command;
- automatic replacement or closure of a prior refresh PR;
- backend, public API, payment, or live-adapter activation;
- forecast, trading signal, or price-target publication;
- A/E activation, C/T runtime expansion, or ORION core exposure.

## Deployment distinction

`NO_DEPLOY_COMMAND` applies to the refresh workflow. It does not disable the repository's established Pages workflow. Pages publication after an explicitly authorized merge to `main` is part of the accepted operating contour.

## Operator review language

The generated review record must state:

> Workflow may push one fully validated review branch and open one review PR. It may not merge or issue a deployment command. Publication follows only after explicit merge authorization.

This replaces the obsolete local-only statement `No push, no PR, no deploy.`

## Automatic 24-hour refresh design — dry-run only

Design ID: `crypto_astro_automatic_24h_refresh_fail_closed_design_v0_1`.

Status: **DESIGN_ONLY_DRY_RUN**.

This design does not activate a GitHub `schedule`, does not change production, and does not turn the current manual workflow into an auto-merge or deployment workflow. Activation requires a separate exact node and authorization.

The proposed checker evaluates the accepted Snapshot once per hour. It preserves the 18-hour hard minimum and opens its automatic eligibility window at 20 hours, leaving a four-hour buffer before the public `FRESH` boundary at 24 hours.

When eligible, the checker may only request the existing `crypto-astro-static-refresh-manual.yml` workflow in `DAILY_CADENCE` mode with an exact `main` SHA lock. The existing workflow remains the sole source-fetch, methodology, consumer, memory, scope, branch, and review-PR implementation.

The design fails closed when:

- the accepted Snapshot is in the future;
- the exact `main` lock has moved;
- another refresh PR is open;
- a refresh workflow is already running;
- a required source is unhealthy or unavailable;
- material change cannot be established;
- any existing source, proof, schema, methodology, consumer, scope, memory, or atomicity gate fails.

If sources are healthy but there is no material change, the checker does not refresh the timestamp and does not create a PR. It records `NO_MATERIAL_CHANGE_RECHECK` and evaluates again after 60 minutes. This may allow the public state to become `STALE_LIMITED`; the system must not claim freshness without new accepted evidence.

### Dry-run decision matrix

| Scenario | Expected decision | Public state | Side effects |
|---|---|---|---|
| 17h | `HOLD_MINIMUM_INTERVAL` | `FRESH` | none |
| 19h | `HOLD_BEFORE_AUTOMATIC_WINDOW` | `FRESH` | none |
| 20h, healthy, material change | `WOULD_DISPATCH_REVIEW_PR` | `FRESH` | simulated review PR only |
| exact-main drift | `BLOCK_MAIN_DRIFT` | age-derived | none |
| open refresh PR | `BLOCK_OPEN_REFRESH_PR` | age-derived | none |
| workflow in progress | `BLOCK_SINGLE_FLIGHT` | age-derived | none |
| source failure | `SOURCE_FAILURE_RECHECK` | age-derived | none |
| no material change | `NO_MATERIAL_CHANGE_RECHECK` | age-derived | none |
| 24h exact | `WOULD_DISPATCH_REVIEW_PR` | `FRESH` | simulated review PR only |
| 25h | `WOULD_DISPATCH_REVIEW_PR` | `STALE_LIMITED` | simulated review PR only |
| 49h | `WOULD_DISPATCH_REVIEW_PR` | `STALE_LIMITED` + operational breach | simulated review PR only |
| 72h | `WOULD_DISPATCH_REVIEW_PR` | `STALE_LIMITED` | simulated review PR only |
| 168h exact | `WOULD_DISPATCH_REVIEW_PR` | `STALE_LIMITED` | simulated review PR only |
| 169h | `WOULD_DISPATCH_REVIEW_PR` | `UNAVAILABLE` | simulated review PR only |
| future timestamp | `BLOCK_FUTURE_SNAPSHOT` | `UNAVAILABLE` | none |

Every dry-run result hard-codes:

- `schedule_active=false`;
- `production_active=false`;
- `would_merge=false`;
- `would_deploy=false`;
- `would_modify_public_data=false`;
- explicit merge authorization remains required.

A future activation node must independently prove scheduler permissions, owner-authenticated dispatch, replay resistance, alerting, rollback, quota behavior, and public exact-SHA verification before any schedule is added.
