# Crypto-Astro Assistant Dispatch v0.1

## Purpose

Provide one bounded, owner-authenticated route by which the Cosmographer can request the existing manual Crypto-Astro refresh workflow without asking Operator F to use GitHub Actions UI or a terminal.

The bridge does not calculate market data. It validates one public-safe issue request and invokes the existing cadence-locked workflow on `main`.

## Fixed route

```text
explicit chat authorization
→ owner-authenticated GitHub issue
→ strict request validation
→ fixed workflow_dispatch target
→ existing manual refresh workflow
→ callback to the same issue
→ issue close and resolved lock
```

Fixed repository: `AiBhrigu/phi-cosmography-open`  
Fixed workflow: `crypto-astro-static-refresh-manual.yml`  
Fixed ref: `main`

The request cannot choose another repository, workflow, branch, command, secret, or runtime.

## Public-safe request

The issue title must be exactly:

```text
Crypto-Astro assistant dispatch request
```

The body contains exactly six ordered single-line fields:

```text
SCHEMA=crypto_astro_assistant_dispatch_request_v0_1
REQUEST_ID=CA-RP-YYYYMMDD-01
REFRESH_MODE=REPEATABILITY_PROOF
OPERATOR_REF=COSMOGRAPHER-RP-YYYYMMDD-01
REFRESH_REASON=Second bounded repeatability proof from cadence-locked main.
EXPECTED_MAIN_SHA=0000000000000000000000000000000000000000
```

Unknown keys, duplicate keys, multiline values, Markdown payloads, URLs, shell syntax, invalid modes, overlong values, and stale or malformed SHAs are rejected.

## Identity boundary

A dispatch is possible only when all of these are true:

- issue author login is `AiBhrigu`;
- issue author association is `OWNER`;
- event actor is `AiBhrigu`;
- repository owner is `AiBhrigu`;
- issue title is the exact locked title.

Non-owner and wrong-title issues do not receive a workflow mutation. An owner-authored invalid request is closed fail-closed with a public-safe validation result.

## Double main lock

The bridge checks `EXPECTED_MAIN_SHA` against current `main` before dispatch. The manual refresh workflow checks the same SHA again after checkout. A stale request cannot silently run on a newer base.

The bridge also requires:

- exactly one open assistant-dispatch issue: the current request;
- zero open automated refresh PRs;
- the existing manual refresh concurrency lock remains active.

## Permissions

The bridge receives only:

- `contents: read`;
- `actions: write`;
- `issues: write`;
- `pull-requests: read`.

It has no contents write, pull-request write, Pages write, package write, deployment write, identity-token write, or secret-management authority.

## Callback

When the manual workflow finishes, it writes one public-safe callback to the request issue:

```text
SCHEMA=crypto_astro_assistant_dispatch_callback_v0_1
DISPATCH_REQUEST_ID=<request id>
WORKFLOW_RUN_ID=<run id>
WORKFLOW_RUN_URL=<GitHub Actions run URL>
EXPECTED_MAIN_SHA=<requested base>
ACTUAL_BASE_SHA=<checked out base>
JOB_STATUS=<success or failure>
MATERIAL_CHANGE=<true or false>
GENERATED_BRANCH=<review branch or none>
GENERATED_PR_URL=<review PR URL or none>
FINAL_OUTCOME=<bounded outcome code>
```

The issue is then closed and locked as resolved. No callback merges a PR or publishes a deployment.

## Preserved refresh boundary

The invoked manual workflow still requires source, proof, schema, methodology, BHRIGU consumer, file-scope, Snapshot Memory, What Changed, atomic-branch, desktop visual, mobile visual, explicit merge authorization, public Pages verification, and BTC Field Read verification.

This bridge introduces no cron, backend, public API, external webhook, personal access token, new secret, auto-merge, deployment command, payment route, A/E activation, C/T runtime expansion, forecast, trading signal, price target, or ORION core exposure.
