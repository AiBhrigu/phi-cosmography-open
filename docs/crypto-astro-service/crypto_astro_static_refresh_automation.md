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

---

## v0.6.3 operating state · 2026-07-10

### Verified state

Node: `CRYPTO_ASTRO_STATIC_REFRESH_AUTOMATION_V0_6_3_CLOSURE_SCOPE`

Current verified public surface:

- URL: `https://aibhrigu.github.io/phi-cosmography-open/crypto-astro/index.html`
- Live timestamp: `2026-07-10T10:07:15Z`
- Live boundary text: `No active adapter claim`
- Live adapter label: `No live adapter`

Repository anchor:

- Repo: `AiBhrigu/phi-cosmography-open`
- PR #85: `Crypto-Astro: automated static market snapshot refresh`
- Merge commit: `14c3fda42ba7011d4bd197d34709f6efcac9b33e`
- Manual workflow run: `29085295397`
- Required check run after operator retrigger: `29086075402`

### Current operating procedure

1. Operator manually starts GitHub Action:
   `Crypto-Astro Static Refresh Manual`.

2. Workflow performs the static refresh only:
   - fetch public market sources
   - update static JSON / proof JSON / bindings
   - update Crypto-Astro static HTML values
   - update operator summary/review docs
   - create an automation branch
   - open a review PR

3. Operator reviews the auto-created PR.

4. Expected changed files are limited to:

   - `site/crypto-astro/index.html`
   - `site/crypto-astro/data/crypto_astro_snapshot.public.json`
   - `site/crypto-astro/data/crypto_astro_snapshot_proof.public.json`
   - `site/crypto-astro/data/crypto_astro_module_bindings.public.json`
   - `site/crypto-astro/data/market_field_snapshot.public.v0_1.json`
   - `site/crypto-astro/data/scoring_snapshot.public.json`
   - `docs/crypto-astro-service/crypto_astro_operator_review.md`
   - `docs/crypto-astro-service/crypto_astro_snapshot_summary.md`

5. If required checks do not complete because the PR was created by `github-actions[bot]`, operator may push an empty commit to the same automation branch to retrigger the validator.

6. Merge is manual only.

### Boundary

The workflow does not:

- enable scheduled cron
- auto-merge PRs
- deploy by command
- activate backend/API/payment
- publish trading signals
- publish forecasts
- publish price targets
- provide investment advice

### CoinGecko API posture

Current route remains static public refresh without a paid API key.

Source anchors:

- CoinGecko API docs: `https://docs.coingecko.com/`
- CoinGecko API pricing: `https://www.coingecko.com/en/api/pricing`

Observed future options:

- Demo/keyless public API for prototype/static refresh
- Basic/Analyst/Lite paid plans for higher call credits, rate limits, historical data, REST/WebSocket/Webhook access
- Enterprise only if custom limits/SLA are required

Decision:

- Do not add CoinGecko paid API key in v0.6.3.
- Do not add secrets in v0.6.3.
- Do not open WebSocket/Webhook integration in v0.6.3.
- Open a separate bounded source-and-secret review before any paid/API-key route.

---

## v0.6.5 CoinGecko Demo API key route

Status: prepared for manual workflow testing.

Secret:

- Repository secret: `COINGECKO_DEMO_API_KEY`
- Secret value is not stored in repository files.
- CoinGecko requests use header auth: `x-cg-demo-api-key`.
- Query-string key usage is not used.

Boundary:

- No scheduled cron in v0.6.5.
- No auto-merge.
- No backend/API/payment activation.
- No trading signal, forecast, price target, or investment advice.

Next validation:

1. Run manual workflow dispatch.
2. Confirm source statuses PASS.
3. Confirm auto PR creation.
4. Review PR manually before merge.

