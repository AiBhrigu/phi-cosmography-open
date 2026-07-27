# Market Cosmographer BTC Descriptive Consumer v0.1

## Status

`IMPLEMENTED_INTERNAL_RESEARCH_PILOT`

This component is the first real consumer of the accepted Market Cosmographer evidence-tiered descriptive contract. It converts one checksum-bound BTC state pair into:

1. one machine-readable descriptive packet;
2. one English human read;
3. one Russian human read;
4. one deterministic build report.

## Accepted source of truth

- Repository: `AiBhrigu/phi-cosmography-open`
- Retrospective evidence PR: `#238`
- Source head: `6c1bceadc360d5baa624ab0866a82dc1597a070a`
- Source merge: `464ca98a630af809870a4780072044bb66b59110`
- Source workflow run: `30224683777`
- Source artifact: `btc-2190d-walk-forward-evidence-238`
- Source artifact digest: `sha256:28503c54a30e21002d240a47ee7a27f3d2b39f199a5d67f03571778863f59667`
- Contract merge: `3d2f396afbf06c04e6f375cddaa9745b39fb6699`

The pilot binds the accepted state pair:

- previous observation: `2026-06-24`, state SHA-256 `46aeb1f3d4d0a632728d616d1cbdf3ffe1340b921a0a11970b12ccb817d214b2`;
- current observation: `2026-06-25`, state SHA-256 `7b5b91af760ad50dee48c8267bd30238b58bf5249996aadbc68534d52b0f11da`.

Both observations belong to `OOS_5`, whose role is `DISCOVERY_REFERENCE_EXCLUDED_FROM_CONFIRMATION`. The consumer may use the accepted Tier 2 metrics descriptively. It must not reinterpret this block as prospective confirmation or predictive evidence.

## Frozen archive inputs

The integration gate downloads only two immutable Binance Data Vision archives:

- `BTCUSDT-1d-2026-05.zip` — SHA-256 `978936e8f1f80b570248f8d4478d6fe08d94b98bc1c7d372feb27573ff466cde`;
- `BTCUSDT-1d-2026-06.zip` — SHA-256 `7020d4d850a875b93f0b0fa6df4a4c36ab615273e2ab03f9e896852330dad77e`.

The archives are not redistributed. They are read only to reproduce the accepted observations and validate source facts.

## Product output

Only these Tier 2 metrics enter the packet:

- `return_1d`;
- `return_7d`;
- `range_position_30d`;
- `quote_volume_ratio_to_prior_30d_median`.

Only one calibrated label enters the packet:

- `range_state`.

The output order is fixed:

`OBSERVATION → CHANGE → EVIDENCE → UNCERTAINTY → BOUNDARY`

The English packet is validated by:

`tools/market_cosmographer_descriptive_contract/verify_descriptive_contract.py`

The RU and EN Markdown reads are deterministic renderings of that validated packet. They are not independent narrative generations.

## Fail-closed controls

The generator rejects:

- a changed artifact digest or corpus hash;
- a changed state date or state SHA-256;
- injected forward outcomes;
- a changed methodology or stability-review binding;
- an unexpected archive, archive checksum or archive member;
- a non-contiguous raw observation window;
- a mismatch between raw recomputation and accepted Tier 2 metrics;
- a generation timestamp earlier than the accepted observation;
- any packet rejected by the evidence-tiered descriptive validator.

The integration workflow generates the output twice and requires byte-identical results.

## Output boundary

- Distribution: `INTERNAL_RESEARCH_ONLY`
- Commercial AI feed: `CLOSED`
- Public page change: `NO`
- Public Snapshot change: `NO`
- Backend/API change: `NO`
- Payment/subscription change: `NO`
- Forecast: `PROHIBITED`
- Trading signal: `PROHIBITED`
- Price target: `PROHIBITED`
- Investment recommendation: `PROHIBITED`

This pilot is historical. It proves the consumer path but does not claim a current BTC read. A current read requires a separately accepted fresh source Snapshot and freshness/correction gates.
