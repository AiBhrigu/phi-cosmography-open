# Crypto-Astro Operational Cadence v0.1

Status: **LOCKED FOR MANUAL CONTROLLED REFRESH**

Machine-readable source of truth: `crypto_astro_operational_cadence_v0_1.json`.

## Operating model

Crypto-Astro uses a static, source-bound market snapshot. A refresh is prepared by a manually dispatched GitHub Actions workflow. The workflow may create one fully validated branch and one review pull request. It may not merge the pull request or issue a deployment command.

Publication occurs only after explicit merge authorization. The existing Pages workflow then publishes accepted `main` automatically, followed by public Pages and BHRIGU BTC Field Read verification.

## Normal cadence

- Target: one accepted snapshot per rolling 24 hours.
- `DAILY_CADENCE` may not run less than 18 hours after the latest accepted snapshot.
- Target maximum operational gap: 48 hours.
- BHRIGU freshness boundary: `FRESH` through 72 hours.
- BHRIGU limited stale boundary: through 168 hours.
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
