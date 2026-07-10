# Crypto-Astro Static Refresh Automation

NODE=CRYPTO_ASTRO_STATIC_REFRESH_AUTOMATION_DOC_v0_6_2
STATUS=ACTIVE_MANUAL_DISPATCH_ONLY

## Purpose

This workflow provides a controlled static refresh path for the public Crypto-Astro surface.
It is not a live adapter, backend service, API, payment system, trading signal, forecast, or investment tool.

## Current mode

- Manual GitHub Actions dispatch only.
- No scheduled cron in v0.6.2.
- No auto-merge.
- No deploy command.
- No backend/API/payment activation.
- The workflow may create a refresh branch and review PR.
- A human/operator review gate remains required before merge.

## Workflow behavior

1. Operator manually runs `crypto-astro-static-refresh-manual.yml` from GitHub Actions.
2. The workflow runs the hardened static refresh runner.
3. Refresh reports are written to `/tmp/crypto_astro_static_refresh_output`, outside the repository workspace.
4. If static surface files changed, the workflow commits those allowed files to a generated automation branch.
5. The workflow opens a review PR.
6. The workflow does not merge or deploy.

## Repair notes

- v0.5 manual dispatch failed because `.crypto_astro_static_refresh_output/` was created inside the repository workspace and was treated as an unexpected changed file.
- v0.6.1 moved output to `${{ runner.temp }}`, but GitHub rejected that expression during workflow dispatch parsing.
- v0.6.2 uses the fixed Ubuntu runner path `/tmp/crypto_astro_static_refresh_output`, which is outside the repository workspace and does not require the `runner` expression context.

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
