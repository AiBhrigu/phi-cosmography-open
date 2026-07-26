# BTC 730D Longitudinal Evidence Methodology v0.1

## Purpose

This is a bounded research corpus for testing whether transparent BTC price-state metrics remain stable and interpretable across time. It does not claim prediction, trading utility, or investment performance.

## Source identity

- Provider: Binance Public Data
- Market: BTCUSDT Spot
- Interval: 1d UTC
- State window: 2024-06-26 through 2026-06-25, inclusive
- Warm-up: first 365 state days
- Out-of-sample: next 365 state days
- Maturity tail: 2026-06-26 through 2026-07-25

Every source ZIP must pass its adjacent SHA-256 `.CHECKSUM`. Monthly archives are used for closed months; daily archives are used for the final partial month. Raw ZIP and CSV files remain in the ephemeral CI cache and are not published as evidence artifacts.

## Timestamp contract

Binance Spot archive timestamps before 2025 are normalized from milliseconds. Spot archive timestamps from 2025 onward are normalized from microseconds. Every 1d row must open at 00:00 UTC and close on the same UTC calendar day.

## State metrics

All formulas are fixed before outcome review.

1. Return state: 1D, 7D and 30D close-to-close returns.
2. Realized volatility: population standard deviation of 30 daily log returns, annualized by `sqrt(365)`.
3. Rolling drawdown: close relative to the maximum high in the trailing 365 observations.
4. Range position: close inside the trailing 30-day high-low range.
5. Volume state: current quote volume divided by the median quote volume of the previous 30 observations.
6. Trend persistence: fraction of positive close-to-close changes in the trailing 30 observations.

Labels use fixed numeric thresholds recorded in the machine contract. They are descriptive states, not forecasts.

## No-lookahead contract

For observation day `t`, state construction may use only source rows whose timestamp is no later than the close of day `t`.

Forward outcomes at 1D, 7D and 30D are added only after those observations exist. They are stored outside the state payload and excluded from `state_sha256`.

The verifier proves prefix invariance on representative out-of-sample dates: computing a state from the complete source sequence must produce byte-identical metrics to computing it from a source prefix ending on that date.

Forbidden:

- full-sample normalization;
- thresholds calculated from future observations;
- formula selection after outcome inspection;
- silent replacement of an archive checksum;
- missing-date interpolation;
- predictive, trading, price-target, or investment claims.

## Correction memory

Each archive is identified by URL, archive ID, expected SHA-256 and actual SHA-256. A later run may compare its source manifest with a previous manifest. Any changed checksum creates a `SOURCE_ARCHIVE_REPLACED` event. Silent overwrite is forbidden.

## Outputs

The CI evidence artifact contains only:

- 730 state rows in JSONL;
- source archive manifest;
- methodology document;
- correction ledger;
- no-lookahead proof;
- summary and deterministic hashes.

It does not contain downloaded ZIP or CSV files.

## Interpretation boundary

The first allowed analytical phrase is **historical association**. Predictive power, probability calibration, public API, commercial AI feed, subscription, and public-page integration remain closed until separate review.
