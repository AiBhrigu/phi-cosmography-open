# Crypto-Astro TVL / Liquidity Context Layer Plan v0.1

STATUS: PLAN_ONLY
PUBLIC_SURFACE: Crypto-Astro
REPO: AiBhrigu/phi-cosmography-open
BOUNDARY: CLEAN

## Purpose

Define TVL / liquidity as a context-only environment layer for Crypto-Astro without opening implementation, live adapters, runtime, backend/API, forecast logic, investment language, or trading signals.

## Current state

TVL / liquidity context is not implemented.

It is a future context layer for liquidity and capital environment review only.

## Governance route

Any future public-surface or production change must follow:

branch -> patch -> verify diff -> draft PR -> validation -> merge -> public verify -> closure report -> memory fixation

## Semantics lock

Allowed language:

- liquidity context
- capital environment
- market structure context
- static public artifact
- calibration pending
- not a trading signal

Blocked language:

- liquidity signal
- TVL score
- buy pressure
- sell pressure
- predictive liquidity model
- investment opportunity
- forecast window

## Layer role

The TVL / liquidity layer may describe background capital conditions.

It must not decide direction, recommend action, rank assets for investment, or imply predictive financial output.

## Source mode

Initial source mode must remain static public artifact.

Live adapter claims are closed until a separate adapter authorization, schema review, and boundary review are completed.

## Separation from scoring

TVL / liquidity context must remain separate from:

- M market context
- A/E source classes
- Φ Balance
- Φ Resonance
- Sem Phase
- public-safe output language

It may be shown as context only after review.

It must not be folded into active scoring without a later formula validation node.

## Schema separation plan

Future schema fields should use context naming, for example:

- liquidity_context_state
- tvl_context_state
- liquidity_source_mode
- liquidity_calibration_state
- liquidity_boundary

Field values should preserve neutral states, for example:

- pending
- static_public_artifact
- calibration_pending
- context_only
- inactive

## Boundary object

Any future JSON or schema artifact must preserve explicit closed flags:

- no_trading_signal
- no_forecast
- no_price_target
- no_investment_recommendation
- backend_api_closed
- runtime_closed
- no_live_adapter_claim
- orion_core_protected

## Allowed next connections

- semantics plan
- schema separation plan
- boundary review
- static artifact design

## Blocked next connections

- implementation
- live adapter
- runtime daemon
- backend/API
- trading signal
- forecast
- price target
- investment recommendation
- A/E numeric activation
- public prediction claim

## PR validation checklist

Before merging any TVL / liquidity context artifact, confirm:

- changed files match authorized scope
- public HTML is untouched unless explicitly authorized
- schema/data files are untouched unless explicitly authorized
- runtime/backend/API remain closed
- no live adapter language is added
- no forecast or investment language is added
- no scoring formula is changed
- boundary remains clean

## Current decision

This plan does not connect TVL / liquidity to public scoring.

This plan does not activate any data feed.

This plan does not publish any financial interpretation.

## Boundary

PUBLIC_HTML_CHANGE=NO
SCHEMA_CHANGE=NO
DATA_CHANGE=NO
RUNTIME=NO
BACKEND_API=NO
TVL_IMPLEMENTATION=NO
LIVE_ADAPTER=NO
A_E_ACTIVATION=NO
TRADING_SIGNAL=NO
FORECAST=NO
INVESTMENT_RECOMMENDATION=NO
BOUNDARY=CLEAN
