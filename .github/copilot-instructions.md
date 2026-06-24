# Copilot instructions for Crypto-Astro

Follow `OPS_F_AGENT_BOUNDARY.md` before changing files.

## Work style

- Prefer small diffs.
- Prefer static/public-safe surface changes before runtime work.
- Keep public copy restrained and factual.
- Preserve existing visual style and layout rhythm.
- Add verification notes in PR descriptions.

## Crypto-Astro boundaries

Do not create or imply:

- backend/API activation
- payment automation
- public feed
- client auto-delivery
- live market data route
- trading-signal output
- price-target output
- financial-advice output
- ORION internal mechanism exposure

## Required PR notes

Every PR should state:

- scope
- files changed
- verification performed
- strict stops preserved
- next safe node

## Module 7 direction

For Service Entry Shell tasks, build a public-safe static request shell first:

- asset / ticker
- UTC snapshot time
- observation window
- research focus
- output language
- prepare request route
- operator-gated delivery copy

No backend submission, payment, or client auto-delivery in Module 7 unless explicitly authorized.
