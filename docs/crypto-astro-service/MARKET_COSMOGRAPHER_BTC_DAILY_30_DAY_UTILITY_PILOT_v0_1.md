# Market Cosmographer · BTC Daily 30-Day Utility Pilot v0.1

## Purpose

Move the accepted evidence-tiered BTC consumer from one frozen historical example to a bounded daily utility pilot without opening a public, predictive, trading, backend, payment, or commercial-AI surface.

## Daily acceptance path

```text
latest completed UTC day
→ 32 Binance daily archives
→ provider SHA-256 checksums
→ contiguous UTC rows
→ current and previous Tier 2 state
→ no-lookahead proof
→ Market Cosmographer packet validator
→ deterministic RU/EN reads
→ immutable workflow artifact
→ one utility-pilot entry
```

## Pilot window

- Pilot ID: `market_cosmographer_btc_30_day_utility_pilot_v0_1`
- First observation: `2026-07-25`
- Last planned observation: `2026-08-23`
- Planned accepted observations: `30`
- Scheduled run: daily after the completed UTC archive is expected to be available.

The workflow exits successfully without generation outside the locked pilot window. A missed or stale day is not silently backfilled as fresh.

## Source boundary

Each accepted day is recomputed from 32 checksum-bound Binance Public Data daily archives. Raw archives are temporary workflow inputs and are not committed or redistributed. The packet and proof package remain `INTERNAL_RESEARCH_ONLY`; data-rights and commercial-feed gates remain pending.

The existing public CoinGecko Snapshot is not an input because its rolling `24h/7d` semantics are not equivalent to the accepted completed-UTC methodology.

## Accepted output

Only these Tier 2 metrics may enter the packet:

- `return_1d`
- `return_7d`
- `range_position_30d`
- `quote_volume_ratio_to_prior_30d_median`

Only `range_state` may enter as a Tier 3 label. Tier 1 metrics, blocked labels, forward outcomes, historical-association fields, predictive fields, trading signals, targets and recommendations remain explicit exclusions.

## Daily artifact

Each accepted run contains:

1. `btc_daily_descriptive_packet.json`
2. `btc_daily_descriptive_read.en.md`
3. `btc_daily_descriptive_read.ru.md`
4. `btc_daily_source_manifest.json`
5. `btc_daily_correction_ledger.json`
6. `btc_daily_no_lookahead_proof.json`
7. `btc_daily_build_report.json`
8. `btc_daily_utility_entry.json`

The workflow performs two byte-identical builds before finalizing the utility entry.

## Utility evaluation

Automated acceptance requires every daily gate to pass. Human utility remains separately reviewable through three questions:

- Is the read clear?
- Is the evidence understandable?
- Is it useful without a prediction?

Thirty entries do not automatically authorize public or commercial release. The aggregate tool returns `IN_PROGRESS`, `COMPLETE_PENDING_HUMAN_REVIEW`, `PASS`, or `FAIL` according to the locked policy.

## Boundary

No public page or public Snapshot change. No live backend/API. No payment or subscription change. No ORION change. No prediction, trading signal, scenario probability, target, or investment recommendation. Operator manual action is not required for daily generation.
