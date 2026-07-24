# BTC Protocol Source of Truth Canon v0.1

NODE=`BTC_PROTOCOL_HALVING_PR_186_EXACT_SOURCE_PROOF_REPAIR_SCOPE_v0_1`  
STATUS=`PASS`  
GENERATED_AT_UTC=`2026-07-23T23:09:08Z`  
SOURCE_REPO_BASE_SHA=`040df096d569d0f0b5e885068042d450e987bcb2`  
BITCOIN_CORE_RELEASE=`31.1`  
BITCOIN_CORE_RELEASE_COMMIT=`9be056a8a72b624dae9623b2f7bded92c2a21c91`

## Scope and truth layers

This canon separates:

1. **Original design:** Satoshi Nakamoto's 2008 white paper.
2. **Consensus implementation:** Bitcoin Core 31.1, pinned to an exact release commit.
3. **Header evidence:** immutable 80-byte mainnet headers pinned by Git commit and independently verified by proof of work.
4. **Derived research method:** transparent calculations that do not modify consensus truth.

This document is descriptive. It is not a price forecast, trading signal, price target, investment recommendation, or claim that a halving causes a specific market outcome.

## 1. Transaction and UTXO model

A Bitcoin transaction consumes previously created unspent transaction outputs and creates new outputs. Each input identifies a previous output and supplies unlocking data. Each output contains an amount and locking script.

The validated state is therefore not an account-balance table. It is the set of unspent outputs accepted by the active chain. A full-validating node verifies that referenced inputs exist, remain unspent, satisfy value and script rules, and are not spent twice in the accepted history.

Implementation anchors:

- `src/primitives/transaction.h`
- `src/coins.h`
- `src/validation.cpp`
- `src/consensus/tx_verify.cpp`

## 2. Blocks, proof of work and chain selection

A block header commits to the previous block hash and transaction Merkle root and carries a timestamp, compact target (`nBits`) and nonce. A valid proof of work requires the numeric double-SHA-256 header hash to be less than or equal to the target derived from `nBits`.

Bitcoin Core tracks cumulative chainwork. The active chain is selected from valid candidates by accumulated proof of work, not raw block count alone. The white paper's “longest chain” wording is therefore interpreted operationally as the valid chain carrying the most accumulated work.

## 3. Difficulty adjustment

Bitcoin Core 31.1 mainnet parameters are:

- target block spacing: `600` seconds;
- target timespan: `1,209,600` seconds;
- adjustment interval: `2,016` blocks;
- minimum-difficulty exception: disabled;
- retargeting: enabled.

At an adjustment boundary, Core compares elapsed header time over the prior interval with the target timespan. The effective elapsed timespan is bounded to one quarter through four times the target before the new target is calculated. Outside an adjustment boundary, mainnet retains the prior target.

Block timestamps are miner-supplied consensus fields constrained by protocol rules, not exact wall-clock attestations. Halving epoch identity therefore comes from block height, never calendar time.

## 4. Block subsidy implementation

Mainnet sets:

```text
nSubsidyHalvingInterval = 210000
```

For height `h`:

```text
epoch = floor(h / 210000)
subsidy_satoshis = (50 * 100000000) >> epoch, when epoch < 64
subsidy_satoshis = 0, when epoch >= 64
```

The right shift uses integer satoshis. Subsidy changes at exact start heights:

```text
0, 210000, 420000, 630000, 840000, 1050000, ...
```

The approximate four-year cadence follows from `210000 × 600 seconds`; it is not the consensus trigger.

The exact nominal subsidy sum across all positive-subsidy epochs, under Bitcoin Core's 64-halving shift guard, is:

```text
20,999,999.9769 BTC
```

This nominal amount is distinct from spendable supply, circulating supply, lost coins, provably unspendable outputs, and fees.

## 5. Miner incentive and fees

A valid coinbase transaction may claim no more than:

```text
block subsidy + transaction fees in the block
```

Subsidy is newly issued value. Fees transfer existing value and are calculated from transaction inputs minus outputs. As subsidy approaches zero, direct protocol compensation shifts toward fees. This is an incentive structure, not a guarantee of future hash rate, fees, or security budget.

## 6. Probabilistic settlement

Bitcoin does not provide instant deterministic finality. A block can be displaced by a valid competing branch with more accumulated work. Additional confirmations increase the work required to replace history, but no fixed confirmation count creates mathematical irreversibility.

Operational statements must specify confirmation depth and threat model rather than claim absolute finality.

## 7. Full-node boundary

A full-validating node independently applies consensus rules to blocks and transactions and maintains verified UTXO state. Peer agreement cannot make an invalid block valid.

`defaultAssumeValid` and AssumeUTXO are synchronization optimizations with explicit anchors. They are not consensus authorities. Independent historical validation should record node version, chain tip, chainstate mode and whether background validation is complete.

## 8. SPV boundary

Simplified Payment Verification retains a proof-of-work header chain and obtains a Merkle branch showing transaction inclusion in a block. It does not independently execute every block transaction and script rule.

Therefore:

- SPV can verify inclusion under a header-chain proof-of-work assumption;
- SPV cannot provide the same invalid-transaction detection boundary as a full node;
- SPV evidence must not be represented as full consensus validation.

## 9. Consensus versus policy

Consensus rules determine whether a block and its transactions can belong to the valid chain. Relay and mempool policy determine what a particular node normally accepts before confirmation. A transaction rejected by current policy can still be consensus-valid if included in a valid block.

Research artifacts must not promote current policy defaults into permanent consensus rules.

## 10. Halving archive method

For epoch `e`:

```text
start_block = e × 210000
end_block = ((e + 1) × 210000) − 1
subsidy = integer-satoshi right shift of 50 BTC
target_blocks_per_day = 86400 / 600 = 144
estimated_daily_issuance = subsidy × 144
```

Actual boundary timestamps and Median Time Past are attached to exact boundary blocks. Protocol-target timestamp estimates are calculated only as:

```text
previous actual boundary timestamp + 210000 × 600 seconds
```

They remain labelled estimates and never replace height or header time.

Every archived boundary records:

- exact 80-byte serialized header;
- single-SHA-256 digest of those 80 bytes;
- double-SHA-256 recomputed block hash;
- Median Time Past;
- cumulative chainwork;
- pinned header repository commit, path and Git blob SHA;
- normalized canonical-record SHA-256.

## 11. Dynamic current-state exclusion

A mutable “current tip” does not belong in this static archival canon. PR #186 therefore contains no current height, current hash, blocks-to-next-halving or current-supply observation.

Those fields may be introduced only through a separately timestamped dynamic snapshot that captures an exact block hash, header, source digest and applicability interval.

## Source index

| Source | Exact pin |
|---|---|
| Bitcoin white paper | `bitcoin.org/bitcoin.pdf` |
| Bitcoin Core release | `9be056a8a72b624dae9623b2f7bded92c2a21c91` |
| Mainnet parameters | Bitcoin Core `9be056a8a72b624dae9623b2f7bded92c2a21c91` · `src/kernel/chainparams.cpp` |
| Subsidy and validation | Bitcoin Core `9be056a8a72b624dae9623b2f7bded92c2a21c91` · `src/validation.cpp` |
| Proof of work | Bitcoin Core `9be056a8a72b624dae9623b2f7bded92c2a21c91` · `src/pow.cpp` |
| Chainwork and MTP semantics | Bitcoin Core `9be056a8a72b624dae9623b2f7bded92c2a21c91` · `src/chain.h` |
| Transaction primitives | Bitcoin Core `9be056a8a72b624dae9623b2f7bded92c2a21c91` · `src/primitives/transaction.h` |
| Immutable header archive | `bitcoincc/headers` · commit `b53315ec4991e0ca06eabae0d17774afea7bf4b5` |
| Height 210000 RPC capture | `blockchain-for/Learning-Bitcoin` · commit `cebd5d502e9df4f20e4bfbd47c472901ba4ff370` |
| Height 420000 RPC capture | `datacabinet/datacabinet-pixyll` · commit `78f58fe41c7c659ad5d931e8b0be36099829d51a` |
| Boundary archive | `BTC_HALVING_EPOCH_ARCHIVE_v0_1.csv` |
| Source proof | `BTC_HALVING_SOURCE_PROOF_v0_1.json` |

## Closure

```text
PROTOCOL_CANON_STATUS=PASS
BITCOIN_CORE_PINNED=YES
RAW_HEADERS_RECOMPUTED=YES
HALVING_BY_HEIGHT=YES
CALENDAR_TRIGGER=NO
MUTABLE_CURRENT_REFERENCE=REMOVED
UNSUPPORTED_CAUSALITY=NO
PRICE_PREDICTION=NO
TRADING_SIGNAL=NO
```
