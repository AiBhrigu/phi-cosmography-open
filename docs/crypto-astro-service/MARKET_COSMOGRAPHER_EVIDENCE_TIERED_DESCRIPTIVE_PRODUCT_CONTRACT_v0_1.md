# Market Cosmographer Evidence-Tiered Descriptive Product Contract v0.1

## Status

`IMPLEMENTATION_CONTRACT`

This contract converts the accepted BTC 2190D retrospective replication result into one fail-closed human and internal-AI descriptive product boundary.

## Source of truth

- Repository: `AiBhrigu/phi-cosmography-open`
- Source PR: `#238`
- Source head: `6c1bceadc360d5baa624ab0866a82dc1597a070a`
- Source merge / accepted main: `464ca98a630af809870a4780072044bb66b59110`
- Source workflow run: `30224683777`
- Source artifact digest: `sha256:28503c54a30e21002d240a47ee7a27f3d2b39f199a5d67f03571778863f59667`
- Retrospective review closure comment: `5085918674`
- Retrospective review package: `cd54909a6ef429a231e5fa3a51cd4092435e83df36f64a43dc77f136d009261c`
- Accepted result: `REGISTERED_ASSOCIATIONS_NOT_REPLICATED`

## Product core

`STATE → CHANGE → EVIDENCE → STABILITY → UNCERTAINTY`

Every human read and internal AI packet must answer:

1. What is happening?
2. What changed?
3. What supports this?
4. What remains uncertain?

The product describes observed state and historical change. Predictive edge, future probability, trading utility, price targets and investment recommendations remain unproven and prohibited.

## Evidence tiers

### Tier 0 — raw source fact

Directly observed source values. Product use is allowed only with provider identity, observation and retrieval timestamps, source locator, checksum or payload hash, unit, correction status and freshness policy.

### Tier 1 — derived descriptive metric

Deterministic metrics that did not pass accepted multi-block stability review. They may appear only in an explicitly experimental support appendix or internal research context. They cannot become headline state, calibrated labels, confidence elevation or decision inputs.

Current Tier 1 metrics:

- `return_30d`
- `realized_volatility_30d_annualized`
- `drawdown_from_365d_high`
- `trend_persistence_30d`

### Tier 2 — stable descriptive metric

Metrics that passed the accepted four-block stability review:

- `return_1d`
- `return_7d`
- `range_position_30d`
- `quote_volume_ratio_to_prior_30d_median`

They may describe current observed values and methodologically comparable historical change. They may not be transformed into future probability, expected return, trading signals or targets.

### Tier 3 — calibrated state label

A label is product-eligible only when both its label family and exact input metric pass.

`range_state` is allowed because its family passed and `range_position_30d` is Tier 2.

`return_state` is blocked even though its family passed because the implementation derives it from `return_30d`, which is Tier 1.

`volatility_state`, `drawdown_state`, `volume_state` and `trend_state` remain blocked because their label families failed calibration.

### Tier 4 — historical association research only

`H1` through `H4`, forward returns, forward drawdowns and association statistics remain research archive material. They cannot enter human product output or AI product packets.

### Tier 5 — predictive claim prohibited

Any future direction, probability, edge, signal, expected return, target or recommendation is prohibited.

## Human contract

Required order:

1. Observation
2. Change
3. Evidence
4. Uncertainty
5. Boundary

A change statement requires matching metric definitions, methodology IDs and hashes, units, comparable status, clear correction status and an explicit historical interval.

Allowed examples:

- “As of 2026-07-25, the observed 7-day return was …”
- “Range position increased since the previous comparable Snapshot.”
- “Quote volume was 1.2 times its prior 30-day median.”
- “This metric passed the accepted four-block stability review.”
- “Predictive power has not been demonstrated.”

Forbidden examples:

- “BTC is likely to rise.”
- “Bullish regime.”
- “Expansion probability is 61%.”
- “Confirmed edge.”
- “Buy, sell or hold.”
- “Target price.”

## Internal AI packet

The packet schema is:

`docs/crypto-astro-service/market_cosmographer_ai_descriptive_packet_schema_v0_1.json`

Distribution is `INTERNAL_RESEARCH_ONLY`. Every packet exposes source, methodology, evidence tier, stability, freshness, correction, exclusions and uncertainty. Silent omission of blocked content is forbidden.

Historical `UP`, `DOWN` and `UNCHANGED` values refer only to an explicit past comparison interval.

## Legacy field isolation

The current public Snapshot may still contain legacy fields. This contract does not mutate that surface, but the following fields cannot be copied, mapped or inferred into the new descriptive product:

- `market_field_score` — unassessed and not eligible;
- `regime_label` — legacy unvalidated and not eligible;
- `direction_bias` — prohibited;
- `probability_continuation` — prohibited;
- `continuation_label` — prohibited;
- scenario percentages — prohibited.

## Freshness

Every source class must use an explicit freshness policy. There is no universal implicit threshold.

Statuses:

- `FRESH`
- `AGING`
- `STALE`
- `HISTORICAL`
- `UNKNOWN`

Words meaning “current” or “now” are allowed only for `FRESH` observations. Older observations must retain exact timestamps and historical language.

## Corrections

Accepted packets are immutable. A source replacement creates a new generation, an explicit correction event, supersession links and downstream invalidation:

`SOURCE_FACT → DERIVED_METRIC → CALIBRATED_LABEL → HUMAN_RESPONSE → AI_PACKET`

Silent overwrite is forbidden.

## Commercial AI readiness

Commercial AI feed readiness remains `NO`. All gates are conjunctive:

1. Data rights
2. Machine schema implementation
3. Correction SLA
4. AI consumer utility test
5. Independent review

This PR implements only the documentary contract, machine schema and fail-closed validator. It does not open distribution or commercial use.

## Boundary

No public page, public Snapshot, proof, registry, market score, provider, refresh, BHRIGU consumer, API, backend, payment, subscription, prediction, trading or ORION change is included.
