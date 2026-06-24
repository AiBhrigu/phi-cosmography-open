# OPS/F Agent Boundary

This file is the repo-native anti-drift boundary for Crypto-Astro automation work.

## Accepted working mode

- Restore accepted state first.
- Work only inside the named node/scope.
- Keep changes small and reviewable.
- Use pull requests as truth artifacts.
- Do not claim production state without source or visual proof.
- Do not put long terminal logs into master chat.

## Strict stops

Do not add or activate these without explicit operator authorization:

- backend/API runtime
- payment automation
- public feed
- client auto-delivery
- live market data route
- trading-signal language
- price-target language
- financial-advice language
- ORION core exposure

## Required output for AI/worker tasks

Every task must return:

- node
- status
- changed files
- verification performed
- boundary status
- next safe node

## Public-safe rule

Crypto-Astro is a research-context surface. It must not be presented as a trading product, prediction system, investment advisor, or live automated client service unless a later explicit authorization changes that boundary.
