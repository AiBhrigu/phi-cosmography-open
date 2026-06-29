# Crypto-Astro Historical Formula Validation Readiness Plan v0.1

STATUS: PLAN_ONLY
PUBLIC_SURFACE: Crypto-Astro
REPO: AiBhrigu/phi-cosmography-open
BOUNDARY: CLEAN

## Purpose

Define the readiness scaffold required before any historical formula validation can be opened.

This artifact does not execute formulas, change scoring, activate A/E numeric fields, change schema/data JSON, open runtime/backend/API, or alter the public UI.

## Current state

Historical Formula Validation is not opened.

A/E numeric activation is blocked.

Runtime, backend/API, live adapters, formula execution, trading signal, forecast, price target, and investment recommendation paths remain closed.

Current public state:

SCORING_V0_2_MARKET_CONTEXT_ACTIVE_UI_LIVE_A_E_SEMANTICS_VISUAL_LIGHT_LOCKED

## Why plan-only

Existing artifacts confirm:

- Historical Formula Validation is later / not opened.
- A/E source classes remain pending and calibration-only.
- A/E has no current scoring effect.
- Formula weights are not activated.
- Public JSON has A=0.0 and E=0.0.
- M is the only active market context layer.
- Public surface remains not a trading signal.

## Plan objective

Prepare a bounded validation architecture for later historical testing of formula logic without activating scoring, runtime, adapters, or public financial claims.

## Required readiness blocks

### 1. Validation objective

Define what historical formula validation is meant to test:

- internal consistency
- separation of A / E / M fields
- behavior of M-only context
- future candidate rules for Φ Balance / Φ Resonance / Sem Phase
- no public prediction claim

### 2. Data source boundary

Define allowed historical sources before any use:

- static historical market snapshots only
- no live adapter
- no private data
- no social/search ingestion
- no runtime daemon
- source license/provenance must be recorded

### 3. Formula candidate inventory

List candidate formulas without executing them:

- M context formula / transform
- possible A source-class placeholder
- possible E source-class placeholder
- Φ Balance candidate
- Φ Resonance candidate
- Sem Phase candidate

Each candidate must be marked:

DRAFT / DOCUMENTED_ONLY / NOT_ACTIVE

### 4. Separation rule

Keep layers separated:

- M-only context can be reviewed first
- A/E numeric activation remains blocked
- A/E cannot be folded into active score before separate authorization
- formula audit must not imply production scoring

### 5. Backtest boundary language

Use safe language only:

- no trading signal
- no forecast
- no price target
- no investment recommendation
- no predictive accuracy public claim
- use historical consistency review instead of signal performance

### 6. Pass/fail criteria

Minimum pass/fail checks:

- data provenance recorded
- formula version recorded
- no hidden live adapter
- no schema drift
- no public UI drift
- no protected ORION exposure
- no A/E activation
- reproducible artifact output exists

### 7. Output artifact format

Any future validation report must include:

- formula version
- dataset reference
- date range
- asset scope
- boundary object
- pass/fail table
- notes
- SHA256
- no recommendation language

### 8. Stop gate

Before any execution:

STOP_REQUIRED_BEFORE_FORMULA_EXECUTION=YES
STOP_REQUIRED_BEFORE_DATA_CHANGE=YES
STOP_REQUIRED_BEFORE_SCHEMA_CHANGE=YES
STOP_REQUIRED_BEFORE_PUBLIC_UI_CHANGE=YES
STOP_REQUIRED_BEFORE_A_E_NUMERIC_ACTIVATION=YES
STOP_REQUIRED_BEFORE_RUNTIME=YES

## Do not open from this plan

- formula execution
- backtest runner
- runtime
- backend/API
- live adapters
- A/E numeric activation
- public UI patch
- trading signal
- forecast
- investment recommendation

## Boundary

PLAN_ONLY=YES
PUBLIC_HTML_CHANGE=NO
CARD_CHANGE=NO
SCHEMA_CHANGE=NO
DATA_CHANGE=NO
FORMULA_EXECUTION=NO
A_E_NUMERIC_ACTIVATION=NO
RUNTIME=NO
BACKEND_API=NO
LIVE_ADAPTERS=NO
TRADING_SIGNAL=NO
FORECAST=NO
PRICE_TARGET=NO
INVESTMENT_RECOMMENDATION=NO
BOUNDARY=CLEAN
