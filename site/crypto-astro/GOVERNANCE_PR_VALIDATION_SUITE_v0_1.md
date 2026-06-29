# Crypto-Astro Governance PR Validation Suite v0.1

STATUS: GOVERNANCE_ARTIFACT
PUBLIC_SURFACE: Crypto-Astro
REPO: AiBhrigu/phi-cosmography-open
BOUNDARY: CLEAN

## Purpose

Define the minimum governance contour for public-surface changes.

## Required route

branch -> patch -> verify diff -> draft PR -> validation -> merge -> public verify -> closure report -> memory fixation

## Main branch rule

Do not push directly to main except emergency rollback.

## PR minimum packet

Every production/public-surface PR must include:

- target branch
- target files
- purpose
- boundary statement
- validation checklist
- changed-files proof
- post-merge public verify plan

## Changed-files check

Verify the PR changed files match the authorized scope.

Fail if unexpected files appear.

## Boundary checks

The PR must not introduce:

- backend/API opening
- runtime daemon opening
- payment route opening
- live adapter claim
- trading signal
- forecast
- price target
- investment recommendation
- protected ORION core exposure

## Crypto-Astro scoring checks

If scoring surface is touched:

- M formula must remain documented if unchanged
- A/E pending state must remain explicit unless separately authorized
- no A/E numeric activation without formula-review node
- public copy must state not a trading signal when scoring context is visible

## Schema/data checks

If JSON or schema files are touched:

- validate schema compatibility
- confirm public values match schema guards
- confirm boundary object remains closed
- confirm static-public artifact mode unless live adapter scope is separately authorized

## Visual/public page checks

Before merge:

- page loads
- anchor section renders
- copy is readable on mobile
- long hashes wrap safely
- boundary copy remains visible

## Post-merge checks

After merge:

- verify public URL
- verify cache-busted URL when needed
- record commit SHA
- record changed files
- create closure report
- store memory fixation

## Current public-surface note

A/E source semantics is closed / production verified.

Current public state:

SCORING_V0_2_MARKET_CONTEXT_ACTIVE_UI_LIVE_A_E_SEMANTICS_VISUAL_LIGHT_LOCKED

Public HTML changes still require the full PR route.

No A/E numeric activation without a separate formula-review node.

No public UI additions without a visual architecture plan.

Do not create micro-PRs by default; batch small related UI/copy fixes when possible.
