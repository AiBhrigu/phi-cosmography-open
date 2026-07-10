# Crypto-Astro Static Refresh Automation v0.5

STATUS=MANUAL_DISPATCH_ONLY

## Purpose

This automation promotes the proven local hardened refresh runner into the repository as a manual GitHub Action workflow.

## Boundary

- No scheduled cron in v0.5.
- No auto-merge.
- No deploy command.
- No backend/API activation.
- No payment activation.
- No live adapter claim.
- No trading signal.
- No forecast.
- No price target.
- No investment advice.

## Manual workflow

Workflow file:

`.github/workflows/crypto-astro-static-refresh-manual.yml`

The workflow:

1. runs only by `workflow_dispatch`;
2. fetches public source data through the hardened runner;
3. updates static JSON, HTML, and docs only if validation passes;
4. pushes an automation branch;
5. opens a review PR;
6. does not merge the PR.

## Promotion rule

Cron remains closed until at least two manual dispatch runs complete successfully and their PRs are reviewed/merged without repair.
