# Crypto-Astro Operational Cadence v0.1

Status: **AUTOMATIC CONTROL PLANE REVIEW CANDIDATE · SOURCE PRODUCER REMAINS REVIEW-ONLY**

Machine-readable source of truth: `crypto_astro_operational_cadence_v0_1.json`.

Activation contract: `crypto_astro_automatic_refresh_activation_v0_1.json`.

Freshness contract: `btc_market_snapshot_freshness_24h_168h_v0_1`.

## Operating model

Crypto-Astro uses a static, source-bound market Snapshot produced in `AiBhrigu/phi-cosmography-open` and consumed by BHRIGU. Source fetch, validation, generated artifacts, Snapshot Memory, branch creation and review-PR creation remain owned exclusively by `crypto-astro-static-refresh-manual.yml`.

The manual producer remains `workflow_dispatch` only. It may create one fully validated branch and one review PR. It may not merge or issue a deployment command.

The separate `crypto-astro-automatic-refresh.yml` control plane activates only after explicit merge authorization. It checks eligibility once per hour and may dispatch the existing manual producer. It does not fetch into `main`, commit, push, create a PR directly, merge or deploy.

Publication occurs only after explicit merge authorization of a generated refresh PR. The established Pages workflow then publishes accepted `main`, followed by public Pages and BHRIGU verification.

## Locked thresholds

- Target accepted refresh interval: 24 hours.
- Hard minimum for `DAILY_CADENCE`: 18 hours.
- Automatic eligibility: 20 hours.
- Automatic check interval: 60 minutes.
- Public `FRESH`: through exactly 24 hours.
- Public `STALE_LIMITED`: after 24 hours through 168 hours.
- Operational breach: after 48 hours; this is not a second public freshness state.
- Public `UNAVAILABLE`: after 168 hours.
- Timestamp-only refresh is forbidden. No material change means `NO_MATERIAL_CHANGE_RECHECK`.

No threshold is changed by the automatic-control activation.

## Authorized modes

| Mode | Purpose | 18-hour minimum |
|---|---|---:|
| `DAILY_CADENCE` | Normal accepted daily Snapshot | Enforced |
| `PRE_REPORT` | Snapshot before an important report | Bypassed with recorded reason |
| `MATERIAL_MARKET_EVENT` | Bounded refresh after a material market-state change | Bypassed with recorded reason |
| `REPEATABILITY_PROOF` | End-to-end proof | Bypassed with recorded reason |
| `SOURCE_OR_SCHEMA_REPAIR` | Restore availability after a proven contract defect | Bypassed with recorded reason |

Every manual dispatch requires `refresh_mode`, `operator_ref`, and `refresh_reason`.

## Automatic eligibility and single flight

The scheduler fails closed when:

- the checkout is not exact current `origin/main`;
- the accepted Snapshot timestamp is in the future;
- the 18-hour minimum or 20-hour automatic window has not been reached;
- another generated refresh PR is open;
- the manual refresh workflow is queued or running;
- source or methodology verification fails;
- material change cannot be established.

If sources are healthy but no material file change exists, no timestamp is advanced and no PR is requested. The scheduler records `NO_MATERIAL_CHANGE_RECHECK` and evaluates again at the next hourly check.

## Source-truth sequence

1. Lock exact current `main`.
2. Read the accepted Snapshot timestamp and existing freshness contract.
3. Prove no open refresh PR and no active manual refresh run.
4. Run the accepted DeFi TVL methodology test.
5. Run the accepted source implementation in an ephemeral probe workspace.
6. Prove authorized source identities, provenance, no double counting and no synthetic fallback.
7. Prove a material generated-file change.
8. Dispatch `crypto-astro-static-refresh-manual.yml` in `DAILY_CADENCE` mode.
9. Prove the new workflow run is observable.
10. Allow the manual producer to validate the full generated packet and open one review PR.
11. Require desktop/mobile review and explicit merge authorization.
12. Publish only after authorized merge to `main`.

## Prohibited behavior

The source-producing manual workflow must not contain `schedule`, `push` or cron triggers. Neither the manual producer nor the scheduler may:

- merge a PR;
- issue a deployment command;
- replace or close a prior refresh PR automatically;
- write directly to `main`;
- activate backend, public API, payment or live adapters;
- publish forecasts, trading signals or price targets;
- expand A/E, C/T runtime or expose ORION.

The separate scheduler is the only permitted cron control plane. Its permissions are limited to `contents: read`, `pull-requests: read` and `actions: write` for dispatching the existing producer.

## Failure diagnostics

Every scheduled evaluation writes a machine-readable decision artifact and GitHub Step Summary. Source or methodology failure fails the workflow visibly. A dispatch is accepted only when a new manual workflow run on the locked `main` SHA is observable.

## Operator boundary

> Workflow may push one fully validated review branch and open one review PR. It may not merge or issue a deployment command. Publication follows only after explicit merge authorization.

## Activation boundary

This document and the scheduler are a review candidate. The schedule is not active while the repair PR remains unmerged. Explicit merge authorization is the activation event. `workflow_dispatch` remains available on both the scheduler and the existing manual producer after activation.
