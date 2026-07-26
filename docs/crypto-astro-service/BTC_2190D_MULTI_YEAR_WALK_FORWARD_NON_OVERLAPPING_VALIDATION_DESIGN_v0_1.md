# BTC 2190D Multi-Year Walk-Forward Non-Overlapping Validation Design v0.1

## Decision

This design extends the accepted BTC evidence method without changing any formula,
threshold, label, public page, API, scenario weight, or commercial claim.

The design is intentionally stricter than a normal backtest: the last accepted
365-day OOS block has already been inspected and used to discover four candidate
associations. It is therefore retained only as a **discovery reference** and is
excluded from replication evidence.

## Exact window

- State window: `2020-06-27 → 2026-06-25` — 2,190 daily states
- Warm-up: `2020-06-27 → 2021-06-26` — 365 days
- OOS 1: `2021-06-27 → 2022-06-26`
- OOS 2: `2022-06-27 → 2023-06-26`
- OOS 3: `2023-06-27 → 2024-06-25`
- OOS 4: `2024-06-26 → 2025-06-25`
- OOS 5: `2025-06-26 → 2026-06-25` — discovery reference only
- Maturity tail: through `2026-07-25`
- Archive plan: 73 monthly + 25 daily = 98 checksum-bound archives

## Frozen primary specification

The accepted `btc_730d_price_state_methodology_v0_1` remains unchanged:

1. 1D / 7D / 30D return
2. 30D annualized realized volatility
3. Drawdown from trailing 365D high
4. 30D range position
5. Quote-volume ratio to prior 30D median
6. 30D trend persistence

All six current label families and every current threshold remain frozen.
No result-driven re-optimization is permitted.

## Registered hypotheses

| ID | Metric | Outcome | Expected sign |
|---|---|---|---|
| H1 | quote-volume ratio | forward return 30D | negative |
| H2 | quote-volume ratio | forward max drawdown 7D | negative |
| H3 | quote-volume ratio | forward max drawdown 30D | negative |
| H4 | trend persistence 30D | forward return 30D | negative |

These hypotheses came from OOS 5. OOS 5 cannot confirm them.

## Replication design

OOS 1–4 are four non-overlapping annual retrospective temporal-replication blocks.

A hypothesis passes the retrospective replication gate only when:

- the expected sign appears in at least 3 of 4 blocks;
- random-effects meta-analysis has absolute rho at least 0.10;
- its adjusted interval excludes zero;
- Holm-adjusted alpha is at most 0.05 across H1–H4;
- no single block contributes more than 40% of meta weight;
- horizon-offset non-overlapping checks do not reverse the conclusion.

Even a full PASS is **not prospective confirmation**, because the historical
periods are reconstructed after hypothesis discovery.

## Future untouched gate

Prospective confirmation requires a separately frozen block:

`2026-06-26 → 2027-06-25`

This future block is not part of the 2,190-day corpus and must remain uninspected
until maturity. Public predictive language remains forbidden even after a
retrospective replication PASS.

## Stability and calibration gates

Metric stability uses adjacent annual-block KS D and PSI. Label calibration
requires adequate support across multiple annual blocks and limited threshold
sensitivity.

The six-label composite regime is not calibrated in this design. The previous
730D review produced 99 signatures with no signature reaching 20 observations.
No data-driven label collapse or threshold rewrite is allowed.

## Source integrity

- Binance Public Data, BTCUSDT Spot, 1d UTC
- Adjacent SHA-256 `.CHECKSUM` required for every archive
- Microsecond timestamp transition from 2025-01-01 handled explicitly
- Source replacements create correction events
- Silent overwrite forbidden
- Raw ZIP/CSV archives are not distributed

Binance documents daily/monthly archives, 1d klines, adjacent checksums,
microsecond Spot timestamps from 2025-01-01, and possible archive replacements.

## Decision ladder

1. Data-foundation PASS → internal historical evidence only.
2. Retrospective replication PASS → replicated historical-association language only.
3. Future untouched OOS 6 PASS → candidate for separate public-language review.
4. Rights, correction SLA and machine-contract PASS → candidate AI data product.
5. Trading signal, forecast and price-target language remain forbidden.

`NEXT_SAFE_NODE=BTC_2190D_MULTI_YEAR_WALK_FORWARD_CHECKSUM_BOUND_CORPUS_IMPLEMENTATION_EXACT_SCOPE_v0_1`
