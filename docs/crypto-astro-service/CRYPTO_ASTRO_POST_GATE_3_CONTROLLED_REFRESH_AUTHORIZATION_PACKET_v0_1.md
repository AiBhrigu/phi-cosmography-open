# Crypto-Astro Post-Gate-3 Controlled Refresh Authorization Packet v0.1

## Purpose

Define the complete fail-closed contract for **one** future controlled Crypto-Astro static market refresh after Gate 3 closure.

This packet does not refresh data, dispatch a workflow, open a generated refresh PR, merge, deploy, or publish. It makes the next execution reviewable before any source request is sent.

## Locked starting state

- Repository: `AiBhrigu/phi-cosmography-open`
- Packet authoring base: `ac86447a89daf4b71333cb133e978a98b82b4abf`
- Gate 3 operational closure: `PASS`
- Gate 3 memory closure: `PASS`
- Gate 3 finalization PR: `#169`
- Sole Gate 3 production proof: issue `#167`, run `29914563042`
- Gate 3 production-proof main SHA: `4f00ec234b1bb3db43c5687cf678b77ff5d98eaa`
- Gate 3 finalization main SHA: `ac86447a89daf4b71333cb133e978a98b82b4abf`
- Current accepted snapshot timestamp: `2026-07-22T08:02:05Z`
- Packet status: `READY_FOR_REVIEW`
- Refresh execution authorized by this packet: `NO`

After this packet is merged, the future refresh authorization must bind `EXPECTED_MAIN_SHA` to the then-current repository `main`. The authoring SHA above is a source anchor, not permission to dispatch from a stale base.

## One-refresh identity lock

Exactly one controlled refresh is allowed after a separate execution authorization.

Required future execution fields:

```text
REFRESH_ID=CA-REFRESH-YYYYMMDD-01
OPERATOR_REF=COSMOGRAPHER-REFRESH-YYYYMMDD-01
REFRESH_MODE=REPEATABILITY_PROOF
REFRESH_REASON=<bounded reason>
EXPECTED_MAIN_SHA=<exact main after this packet merge>
DISPATCH_REQUEST_ISSUE=<owner-authenticated issue number>
```

Rules:

1. Issue opener and workflow actor must be repository owner `AiBhrigu`.
2. `EXPECTED_MAIN_SHA` must be 40 lowercase hex and equal current `main`.
3. Exactly zero other open refresh requests, generated refresh PRs, or active refresh runs may exist.
4. One request may produce at most one workflow run and one generated review PR.
5. Operator F performs no manual terminal or code action.

## Source and timestamp lock

All seven sources are required for this first post-Gate-3 refresh. A partial source bundle is not publishable.

| Proof label | Fixed URL | Role |
|---|---|---|
| `coingecko_global` | `https://api.coingecko.com/api/v3/global` | Market cap, volume, BTC/ETH dominance |
| `coingecko_asset_markets_btc_eth_sol_ton_icp` | fixed five-asset markets query | Public asset samples |
| `coingecko_top250_markets` | fixed top-250 markets query | Altcoin breadth and concentration |
| `coingecko_stablecoin_sample` | fixed stablecoin sample query | Stablecoin fallback sample |
| `defillama_protocols` | `https://api.llama.fi/v2/historicalChainTvl` | Global DeFi TVL excluding double counting |
| `defillama_dex_overview` | fixed DEX overview query | DEX volume context |
| `defillama_stablecoins` | `https://stablecoins.llama.fi/stablecoins?includePrices=true` | Stablecoin cap primary source |

For every source, proof must contain:

- exact label and URL;
- `status=PASS`;
- `fetched_at_utc`;
- SHA-256 of raw payload;
- raw byte count.

Timestamp gates:

- maximum spread between first and last source fetch: `600 seconds`;
- snapshot generation must occur after all source fetches;
- snapshot generation may lag the final fetch by at most `120 seconds`;
- snapshot/proof timestamp skew may not exceed `120 seconds`;
- the new snapshot must be later than the accepted snapshot at `2026-07-22T08:02:05Z`;
- future timestamps, cached-payload substitution, and unlisted-source substitution fail closed.

## DeFi TVL methodology lock

The only accepted value path is:

```text
METHODOLOGY_ID=defillama_historical_chain_tvl_ex_double_count_v0_1
CANONICAL_SOURCE_ID=defillama_global_tvl_ex_double_count
PROOF_LABEL=defillama_protocols
SOURCE_URL=https://api.llama.fi/v2/historicalChainTvl
```

`defillama_protocols` remains the legacy proof label for compatibility. It must point to `/v2/historicalChainTvl`; it must never be interpreted as permission to sum `/protocols`.

Selection rule:

1. Parse the response as the historical global TVL series.
2. Select exactly one latest valid point containing a finite positive `tvl`.
3. Use that point's date as `defi_tvl_source_timestamp_utc`.
4. Do not sum protocols, chains, categories, liquid-staking totals, or multiple historical points.
5. Do not add liquid-staking or double-counted values back into the selected point.
6. Reject `https://api.llama.fi/protocols` as a value source.
7. Require source age `<=48 hours`.
8. Require the methodology ID to match the previous accepted snapshot.
9. If absolute TVL change exceeds `25%` from the previous accepted value, stop with `FAIL_DEFI_TVL_ANOMALY` and require a separate methodology review. Do not silently publish.

Required snapshot fields:

```text
defi_tvl_source_label=defillama_protocols
defi_tvl_canonical_source_id=defillama_global_tvl_ex_double_count
defi_tvl_source_url=https://api.llama.fi/v2/historicalChainTvl
defi_tvl_methodology_id=defillama_historical_chain_tvl_ex_double_count_v0_1
defi_tvl_excludes_liquid_staking=true
defi_tvl_excludes_double_counted=true
```

The `liquidity_tvl` module binding must preserve the same methodology, proof label, and canonical source ID.

## Exact generated review-PR scope

The generated refresh PR must change exactly the following ten files:

```text
site/crypto-astro/index.html
site/crypto-astro/data/crypto_astro_snapshot.public.json
site/crypto-astro/data/crypto_astro_snapshot_proof.public.json
site/crypto-astro/data/crypto_astro_module_bindings.public.json
site/crypto-astro/data/market_field_snapshot.public.v0_1.json
site/crypto-astro/data/scoring_snapshot.public.json
site/crypto-astro/data/crypto_astro_snapshot_registry.public.json
site/crypto-astro/data/crypto_astro_snapshot_delta.public.json
docs/crypto-astro-service/crypto_astro_snapshot_summary.md
docs/crypto-astro-service/crypto_astro_operator_review.md
```

The following file may additionally change only when deterministic generation produces different schema bytes:

```text
site/crypto-astro/data/crypto_astro_module_bindings.public.schema.json
```

No runner, operational workflow, production proof workflow, schema migration, theme, backend, API, payment, Temporal, A/E, ORION, or unrelated documentation change is allowed.

## Snapshot, proof, derived and memory bindings

The generated branch must atomically contain:

- public snapshot;
- raw-source proof with hashes and byte counts;
- module bindings;
- market-field and scoring derived JSON;
- rendered public HTML;
- snapshot summary and operator review;
- accepted-pair registry;
- current-versus-previous delta;
- rendered and verified What Changed section.

Required invariants:

1. Snapshot, bindings, derived JSON, registry current entry, delta current entry, and visible HTML anchors refer to the same generated snapshot.
2. Snapshot/proof timestamp skew is at most `120 seconds`.
3. Registry selection policy remains `EXPLICIT_ACCEPTED_PAIR`.
4. Registry current and previous entries remain `ACCEPTED`.
5. Current transaction ancestry descends from the previous accepted materialization.
6. Snapshot, proof, bindings, and runner blob/SHA-256 bindings are present and exact.
7. Snapshot memory is built twice and both outputs are byte-identical.
8. What Changed is rendered and verified from the accepted pair.
9. BHRIGU producer/consumer compatibility passes before branch push.
10. The final branch is clean and contains only the accepted generated file set.

## Fail-closed gates

The refresh must stop without publication on any of these classes:

```text
FAIL_EXPECTED_MAIN_SHA
FAIL_IDENTITY_OR_OWNER_AUTH
FAIL_SINGLE_FLIGHT
FAIL_CADENCE
FAIL_SOURCE_MISSING
FAIL_SOURCE_URL
FAIL_SOURCE_STATUS
FAIL_SOURCE_HASH
FAIL_SOURCE_TIMESTAMP
FAIL_DEFI_TVL_METHODOLOGY
FAIL_DEFI_TVL_STALE
FAIL_DEFI_TVL_ANOMALY
FAIL_SCHEMA
FAIL_TIMESTAMP_ORDER
FAIL_BINDINGS
FAIL_MEMORY
FAIL_ATOMIC_SCOPE
FAIL_BHRIGU_CONSUMER
FAIL_VISUAL_REVIEW
FAIL_CI
FAIL_MERGE_SHA_LOCK
FAIL_PUBLIC_HTTP_PROOF
```

No failed step may be converted into a partial PASS.

## PR, merge, visual review and public proof sequence

1. Merge this packet only through a separately authorized SHA-locked squash merge.
2. Open one owner-authenticated refresh-dispatch issue bound to current `main`.
3. Dispatch the existing `Crypto-Astro Static Refresh Manual` workflow once.
4. Require `PASS_REVIEW_PR_OPENED` and exactly one generated review PR.
5. Require exact generated scope, source proof, methodology, memory, consumer, and CI PASS.
6. Review desktop and mobile render before merge.
7. Squash merge the generated refresh PR using its reviewed head SHA.
8. Verify `main` equals the refresh merge SHA and no duplicate run/PR exists.
9. Open exactly one owner-authenticated public HTTP proof request for that merge SHA.
10. Require one resolved proof run with `PUBLIC_HTTP_PROOF_PASS`, six HTTP 200 targets, zero redirects, and issue auto-close/lock.
11. Return a closure report containing refresh PR/head/merge, dispatch issue/run, proof issue/run/artifact/digest, snapshot timestamp, and methodology ID.
12. Return to `HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH`.

Visual review must verify both public surfaces:

- `https://aibhrigu.github.io/phi-cosmography-open/crypto-astro/index.html`
- `https://www.bhrigu.io/crypto-astro/btc`

The review must reject mismatched metric cards/rails, unsynchronized BTC bindings, duplicated or missing TVL methodology copy, broken What Changed rendering, clipping, overflow, overlap, empty slots, or prohibited live/forecast/trading language.

## Rollback and hold rules

- No branch push before atomic PASS.
- No automatic merge.
- No deploy command.
- Pre-merge failure: keep the generated PR unmerged or close it; preserve evidence and return the exact failure code.
- Post-merge HTTP-proof failure: do not claim refresh PASS; open a separately authorized minimal repair or rollback decision node.
- Automatic rollback is forbidden.
- Rollback requires separate authorization.
- A successful cycle returns to `HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH`.
- A second dispatch requires a new authorization.

## Boundary

```text
DATA_REFRESH_IN_THIS_PACKET=NO
DISPATCH_IN_THIS_PACKET=NO
DEPLOY_IN_THIS_PACKET=NO
PUBLIC_HTML_CHANGE_IN_THIS_PACKET=NO
PUBLIC_JSON_CHANGE_IN_THIS_PACKET=NO
RUNNER_CHANGE_IN_THIS_PACKET=NO
PRODUCTION_WORKFLOW_CHANGE_IN_THIS_PACKET=NO
CRON=NO
BACKEND=NO
API_ACTIVATION=NO
PAYMENT=NO
A_E=NO
TEMPORAL=NO
FORECAST=NO
TRADING_SIGNAL=NO
PRICE_TARGET=NO
INVESTMENT_RECOMMENDATION=NO
ORION_EXPOSURE=NO
OPERATOR_F_MANUAL_ACTIONS=NONE
```

## Next gate

After this packet is merged:

```text
NEXT_SAFE_NODE=CRYPTO_ASTRO_POST_GATE_3_CONTROLLED_REFRESH_OWNER_AUTHENTICATED_DISPATCH_AUTHORIZATION_v0_1
```
