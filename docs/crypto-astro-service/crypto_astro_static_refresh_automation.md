# Crypto-Astro Static Refresh Automation

NODE=CRYPTO_ASTRO_STATIC_REFRESH_AUTOMATION_DOC_v0_6_1
STATUS=ACTIVE_MANUAL_DISPATCH_ONLY

## Purpose

This workflow provides a controlled static refresh path for the public Crypto-Astro surface.
It is not a live adapter, backend service, API, payment system, trading signal, forecast, or investment tool.

## Current mode

- Manual GitHub Actions dispatch only.
- No scheduled cron in v0.6.
- No auto-merge.
- No deploy command.
- No backend/API/payment activation.
- The workflow may create a refresh branch and review PR.
- A human/operator review gate remains required before merge.

## Workflow behavior

1. Operator manually runs `crypto-astro-static-refresh-manual.yml` from GitHub Actions.
2. The workflow runs the hardened static refresh runner.
3. Refresh reports are written to `${{ runner.temp }}/crypto_astro_static_refresh_output`, outside the repository workspace.
4. If static surface files changed, the workflow commits those allowed files to a generated automation branch.
5. The workflow opens a review PR.
6. The workflow does not merge or deploy.

## v0.6.1 repair note

The v0.5 manual dispatch test failed because the report output directory was created inside the repository workspace and then appeared as an unexpected changed file. v0.6 moves the report output directory to GitHub runner temp storage and keeps it available through the `crypto-astro-static-refresh-report` artifact.

## Boundary

- No scheduled cron.
- No auto-merge.
- No deploy.
- No backend/API activation.
- No payment activation.
- No live adapter claim.
- No trading signal.
- No forecast.
- No price target.
- No investment advice.

## v0.6.1 apply-script note

v0.6.1 repairs the local atompack apply script packaging error from v0.6. The repository payload remains the workflow outdir fix.
