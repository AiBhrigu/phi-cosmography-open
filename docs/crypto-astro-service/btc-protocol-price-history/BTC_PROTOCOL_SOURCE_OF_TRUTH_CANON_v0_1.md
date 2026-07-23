# BTC Protocol Source of Truth Canon v0.1

NODE=`BTC_PROTOCOL_CANON_AND_HALVING_ARCHIVE_BUILD_SCOPE_v0_1`  
STATUS=`PASS`  
GENERATED_AT_UTC=`2026-07-23T21:56:55Z`  
SOURCE_REPO_BASE_SHA=`040df096d569d0f0b5e885068042d450e987bcb2`  
BITCOIN_CORE_RELEASE=`31.1`  
BITCOIN_CORE_RELEASE_COMMIT=`9be056a8a72b624dae9623b2f7bded92c2a21c91`

## Scope and boundary

This canon separates three layers:

1. **Original design:** Satoshi Nakamoto's 2008 white paper.
2. **Consensus implementation:** Bitcoin Core 31.1, pinned to an exact release commit.
3. **Derived research method:** transparent calculations that do not modify or replace consensus truth.

This document is descriptive. It is not a price forecast, trading signal, target price, investment recommendation, or claim that a halving causes a particular market outcome.

## 1. Transaction and UTXO model

A Bitcoin transaction consumes previously created, unspent transaction outputs and creates new outputs. Each input identifies a previous output and supplies the unlocking data required by that output's script. Each output contains an amount and locking script.

The canonical state is therefore not an account-balance table. It is the set of currently unspent outputs accepted by the active chain. A full-validating node verifies that referenced inputs exist, are unspent, satisfy value and script rules, and are not spent twice in the same accepted history.

**Implementation anchors**

- `src/primitives/transaction.h`
- `src/coins.h`
- `src/validation.cpp`
- `src/consensus/tx_verify.cpp`

## 2. Blocks, proof of work and chain selection

A block header commits to the previous block hash and the Merkle root of its transactions, and carries a timestamp, compact target (`nBits`) and nonce. A valid proof of work requires the numeric block hash to be less than or equal to the target derived from `nBits`.

Bitcoin Core tracks cumulative chain work. The active chain is selected by the valid branch with the most accumulated proof of work, not by the largest block count alone. The white paper's “longest chain” wording is interpreted operationally as the chain carrying the greatest cumulative proof-of-work effort.

## 3. Difficulty adjustment

Mainnet parameters in Bitcoin Core 31.1 are:

- target block spacing: `600` seconds;
- target timespan: `1,209,600` seconds, or 14 days;
- adjustment interval: `2,016` blocks;
- minimum-difficulty exception: disabled on mainnet;
- retargeting: enabled.

At an adjustment boundary, Core compares the elapsed header time over the prior interval with the target timespan. The effective elapsed timespan is bounded to one quarter through four times the target before calculating the new target. Outside an adjustment boundary, mainnet retains the previous target.

Block timestamps are consensus fields supplied by miners and constrained by protocol rules; they are not exact wall-clock attestations. Halving epoch identity therefore comes from height, never from calendar time.

## 4. Block subsidy implementation

Mainnet sets:

```text
nSubsidyHalvingInterval = 210000
```

For block height `h`:

```text
epoch = floor(h / 210000)
subsidy_satoshis = (50 * 100000000) >> epoch, when epoch < 64
subsidy_satoshis = 0, when epoch >= 64
```

The right shift is integer arithmetic in satoshis. The subsidy changes at exact start heights:

```text
0, 210000, 420000, 630000, 840000, 1050000, ...
```

The target estimate of four years is a consequence of `210000 × 600 seconds`; it is not the consensus trigger.

The exact nominal subsidy sum over all 64 nonzero/defined shift epochs is:

```text
20,999,999.9769 BTC
```

This is distinct from spendable supply, circulating supply, lost coins, provably unspendable outputs, and transaction fees.

## 5. Incentive and fee transition

A valid coinbase transaction may claim no more than:

```text
block subsidy + transaction fees in the block
```

The subsidy is newly issued value. Fees are transfers of already existing value, calculated from transaction inputs minus outputs. As subsidy approaches zero, the protocol's direct miner compensation shifts toward fees; this is an incentive architecture, not a guarantee about future hash rate, fee levels, or security budget.

## 6. Chain selection and finality assumptions

Bitcoin has **probabilistic settlement**, not instant deterministic finality. A block can be displaced by a valid competing branch with more accumulated work. Each additional block built on top increases the work an attacker would need to replace the history, but no fixed confirmation count creates mathematical irreversibility.

Operational conclusions must therefore state a confirmation depth and threat model rather than claiming absolute finality.

## 7. Full-node verification boundary

A full-validating node independently applies consensus rules to blocks and transactions and maintains a verified UTXO state. Peer agreement does not make an invalid block valid.

`defaultAssumeValid` and AssumeUTXO are synchronization optimizations with explicit pinned anchors. They must not be described as authority replacing consensus. A canon consumer that requires independent historical validation should use a fully validated chainstate and record the node version, chain tip and validation mode.

## 8. SPV boundary

Simplified Payment Verification retains the proof-of-work header chain and obtains a Merkle branch showing that a transaction is committed to a block. It does **not** independently execute every transaction and script rule for the block.

Therefore:

- SPV can verify inclusion under a proof-of-work-chain assumption;
- SPV cannot provide the same invalid-transaction detection boundary as a full node;
- an SPV result must not be represented as full consensus validation.

## 9. Consensus versus policy

Consensus rules determine whether blocks and transactions can belong to the valid chain. Relay and mempool policy determine what an individual node will normally accept into its mempool or relay before confirmation. A policy-rejected transaction can still be consensus-valid if mined into a valid block.

Research artifacts must not promote current policy defaults into permanent consensus rules.

## 10. Halving archive method

For epoch `e`:

```text
start_block = e × 210000
end_block = ((e + 1) × 210000) − 1
subsidy = 50 BTC / 2^e, executed as an integer satoshi right shift
target_blocks_per_day = 86400 / 600 = 144
estimated_daily_issuance = subsidy × 144
```

Actual boundary timestamps are read from the exact epoch-start block. Protocol-target timestamp estimates are calculated only as:

```text
previous actual boundary timestamp + 210000 × 600 seconds
```

They are labelled estimates and never replace block height or the actual header timestamp.

## Source index

| Source | Pin |
|---|---|
| Bitcoin white paper | https://bitcoin.org/bitcoin.pdf |
| Bitcoin Core 31.1 release commit | https://github.com/bitcoin/bitcoin/commit/9be056a8a72b624dae9623b2f7bded92c2a21c91 |
| Mainnet parameters | https://github.com/bitcoin/bitcoin/blob/9be056a8a72b624dae9623b2f7bded92c2a21c91/src/kernel/chainparams.cpp |
| Subsidy and validation | https://github.com/bitcoin/bitcoin/blob/9be056a8a72b624dae9623b2f7bded92c2a21c91/src/validation.cpp |
| Proof-of-work and retargeting | https://github.com/bitcoin/bitcoin/blob/9be056a8a72b624dae9623b2f7bded92c2a21c91/src/pow.cpp |
| Block-index chain work and header time | https://github.com/bitcoin/bitcoin/blob/9be056a8a72b624dae9623b2f7bded92c2a21c91/src/chain.h |
| Transaction primitives | https://github.com/bitcoin/bitcoin/blob/9be056a8a72b624dae9623b2f7bded92c2a21c91/src/primitives/transaction.h |
| UTXO views | https://github.com/bitcoin/bitcoin/blob/9be056a8a72b624dae9623b2f7bded92c2a21c91/src/coins.h |
| Block-template incentive construction | https://github.com/bitcoin/bitcoin/blob/9be056a8a72b624dae9623b2f7bded92c2a21c91/src/node/miner.cpp |
| Halving archive | `BTC_HALVING_EPOCH_ARCHIVE_v0_1.csv` |
| Halving proof | `BTC_HALVING_SOURCE_PROOF_v0_1.json` |

## Closure

```text
PROTOCOL_CANON_STATUS=PASS
WHITEPAPER_AS_IMPLEMENTATION_SOURCE=NO
CURRENT_CORE_PINNED=YES
HALVING_BY_HEIGHT=YES
CALENDAR_TRIGGER=NO
UNSUPPORTED_CAUSALITY=NO
PRICE_PREDICTION=NO
TRADING_SIGNAL=NO
```
