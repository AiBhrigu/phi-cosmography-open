# Crypto-Astro Public HTTP Proof Dispatch v0.1

## Purpose

Provide one owner-authenticated route by which the Cosmographer can run the merged `Crypto-Astro Public HTTP Proof` workflow without Operator F opening GitHub Actions or using a terminal.

The bridge does not fetch or calculate market data itself. It validates one strict issue request, locks the current `main` SHA, dispatches the already merged read-only verifier, resolves the single new workflow run, records the result, and closes the request.

## Fixed route

```text
explicit chat authorization
→ owner-authenticated GitHub issue
→ strict request validation
→ exact current-main SHA lock
→ fixed workflow_dispatch target
→ single new run resolution
→ proof run completion
→ callback to the same issue
→ issue close and resolved lock
```

Fixed repository: `AiBhrigu/phi-cosmography-open`  
Fixed workflow: `crypto-astro-public-http-proof.yml`  
Fixed ref: `main`

The request cannot choose another repository, workflow, ref, command, URL, secret, or runtime.

## Public-safe request

The issue title must be exactly:

```text
Crypto-Astro public HTTP proof dispatch request
```

The body contains exactly four ordered single-line fields:

```text
SCHEMA=crypto_astro_public_http_proof_dispatch_request_v0_1
REQUEST_ID=CA-HTTP-YYYYMMDD-01
OPERATOR_REF=COSMOGRAPHER-HTTP-YYYYMMDD-01
EXPECTED_MAIN_SHA=0000000000000000000000000000000000000000
```

Unknown keys, duplicate keys, multiline values, Markdown payloads, URLs, shell syntax, invalid identifiers, and stale or malformed SHAs are rejected.

## Identity boundary

Dispatch is possible only when all of these are true:

- issue author login is `AiBhrigu`;
- issue author association is `OWNER`;
- event actor is `AiBhrigu`;
- repository owner is `AiBhrigu`;
- issue title is the exact locked title.

Non-owner and wrong-title issues do not enter the job. An owner-authored invalid request is closed fail-closed with a public-safe reason code.

## Double execution lock

Before dispatch, the bridge requires:

- requested `EXPECTED_MAIN_SHA` equals current remote `main`;
- exactly one open issue with the fixed title: the current request;
- zero queued, waiting, pending, requested, or in-progress runs of the target workflow;
- the target workflow exists on `main`.

After dispatch, the bridge accepts only one new workflow run that:

- uses event `workflow_dispatch`;
- runs on branch `main`;
- has `headSha` equal to the locked `EXPECTED_MAIN_SHA`;
- was created after the recorded dispatch timestamp.

No pre-existing or ambiguous run can be accepted as proof.

## Permissions

The bridge receives only:

- `contents: read`;
- `actions: write`;
- `issues: write`.

It has no contents write, pull-request write, Pages write, package write, deployment write, identity-token write, or secret-management authority.

The target proof workflow remains `contents: read` only.

## Callback

When the target workflow finishes, the bridge writes one callback to the request issue:

```text
SCHEMA=crypto_astro_public_http_proof_dispatch_callback_v0_1
REQUEST_ID=<request id>
WORKFLOW_RUN_ID=<run id>
WORKFLOW_RUN_URL=<GitHub Actions run URL>
EXPECTED_MAIN_SHA=<requested main>
ACTUAL_HEAD_SHA=<run head sha>
JOB_STATUS=<success or failure>
FINAL_OUTCOME=<bounded outcome code>
```

The issue is then closed and locked as resolved. A failed proof returns a failed bridge run after the safe callback and closure.

## Preserved boundary

- no cron;
- no repository mutation;
- no contents write;
- no pull-request or Pages write;
- no deployment command;
- no backend, public API, webhook, payment route, or new secret;
- no A/E activation;
- no Temporal runtime expansion;
- no forecast, trading signal, price target, or investment recommendation;
- no ORION core exposure.
