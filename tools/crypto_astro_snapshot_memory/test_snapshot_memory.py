#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest
from decimal import Decimal
from unittest import mock

from build_snapshot_memory import (
    BOUNDARY,
    ContractError,
    build_documents,
    display_delta,
    git_blob_sha,
    json_bytes,
    make_bundle,
)


def encoded(document, newline=True):
    value = json.dumps(document, ensure_ascii=False, indent=2)
    return (value + ("\n" if newline else "")).encode("utf-8")


def fixture_documents():
    boundary = {key: value for key, value in BOUNDARY.items() if key in {
        "read_only", "static_public_snapshot", "no_live_adapter_claim",
        "no_true_live_feed_claim", "no_trading_signal", "no_forecast",
        "no_price_target", "no_investment_recommendation", "backend_api_closed",
        "runtime_closed", "payment_closed", "orion_core_protected",
        "formula_weights_exposed",
    }}
    current_snapshot = {
        "schema_version": "crypto_astro_snapshot_public_v0_1",
        "generated_at_utc": "2026-07-19T18:26:56Z",
        "source_mode": "static_public_snapshot",
        "market_reality": {"btc_dominance_pct": 56.50010249230421, "stablecoin_share_pct": 13.500433230542436},
        "field_output": {"market_field_score": 61.0, "regime_label": "Balanced Expansion"},
        "altcoin_rotation": {
            "universe": "non-stable top-250 crypto assets",
            "alt_breadth_24h_pct": 34.5,
            "alt_breadth_7d_pct": 39.9,
        },
        "liquidity_tvl": {"defi_tvl_usd": 75551199898.0, "liquidity_context_state": "context fresh"},
        "boundary": copy.deepcopy(boundary),
    }
    previous_snapshot = copy.deepcopy(current_snapshot)
    previous_snapshot["generated_at_utc"] = "2026-07-12T22:05:46Z"
    previous_snapshot["market_reality"]["btc_dominance_pct"] = 56.21621132126818
    previous_snapshot["market_reality"]["stablecoin_share_pct"] = 13.683691685333388
    previous_snapshot["field_output"]["market_field_score"] = 60.0
    previous_snapshot["altcoin_rotation"]["alt_breadth_24h_pct"] = 26.5
    previous_snapshot["altcoin_rotation"]["alt_breadth_7d_pct"] = 41.2
    previous_snapshot["liquidity_tvl"]["defi_tvl_usd"] = 483272549277.112

    source_entries_current = [
        {"label": "coingecko_global", "url": "https://api.coingecko.com/api/v3/global", "status": "PASS"},
        {"label": "coingecko_top250_markets", "url": "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h%2C24h%2C7d%2C30d&sparkline=false", "status": "PASS"},
        {"label": "defillama_stablecoins", "url": "https://stablecoins.llama.fi/stablecoins?includePrices=true", "status": "PASS"},
    ]
    source_entries_previous = copy.deepcopy(source_entries_current)
    current_proof = {
        "schema_version": "crypto_astro_snapshot_proof_public_v0_1",
        "generated_at_utc": "2026-07-19T18:26:49Z",
        "source_mode": "static_public_snapshot",
        "sources": source_entries_current,
        "boundary": copy.deepcopy(boundary),
    }
    previous_proof = copy.deepcopy(current_proof)
    previous_proof["generated_at_utc"] = "2026-07-12T22:05:45Z"
    previous_proof["sources"] = source_entries_previous

    modules = {
        "market_reality": {"source": "market_reality"},
        "altcoin_rotation": {"source": "altcoin_rotation"},
        "aem_barometer": {"source": "field_output"},
    }
    current_bindings = {
        "schema_version": "crypto_astro_public_module_bindings_v0_1",
        "generated_at_utc": current_snapshot["generated_at_utc"],
        "source_mode": "static_public_snapshot",
        "modules": copy.deepcopy(modules),
        "boundary": copy.deepcopy(boundary),
    }
    previous_bindings = copy.deepcopy(current_bindings)
    previous_bindings["generated_at_utc"] = previous_snapshot["generated_at_utc"]
    return current_snapshot, previous_snapshot, current_proof, previous_proof, current_bindings, previous_bindings


def bundles():
    cs, ps, cp, pp, cb, pb = fixture_documents()
    current = make_bundle(
        role="current", commit_sha="c" * 40, data_origin_commit_sha="d" * 40,
        runner_blob_sha="1" * 40, snapshot_bytes=encoded(cs), proof_bytes=encoded(cp),
        bindings_bytes=encoded(cb),
    )
    previous = make_bundle(
        role="previous", commit_sha="p" * 40, data_origin_commit_sha="p" * 40,
        runner_blob_sha="2" * 40, snapshot_bytes=encoded(ps), proof_bytes=encoded(pp),
        bindings_bytes=encoded(pb),
    )
    return current, previous


class SnapshotMemoryContractTests(unittest.TestCase):
    def test_valid_pair_exact_deltas(self):
        registry, delta = build_documents(*bundles(), ancestry_ok=True, strict_locks=False)
        self.assertEqual(delta["metrics"]["btc_gravity_pct"]["raw_delta"], "0.28389117103603")
        self.assertEqual(delta["metrics"]["stablecoin_share_pct"]["display_delta"], "-0.18")
        self.assertEqual(registry["selection_policy"], "EXPLICIT_ACCEPTED_PAIR")

    def test_identical_rerun_is_byte_identical(self):
        first = build_documents(*bundles(), ancestry_ok=True, strict_locks=False)
        second = build_documents(*bundles(), ancestry_ok=True, strict_locks=False)
        self.assertEqual(json_bytes(first[0]), json_bytes(second[0]))
        self.assertEqual(json_bytes(first[1]), json_bytes(second[1]))

    def test_missing_previous_field_fails_closed(self):
        current, previous = bundles()
        previous.snapshot["market_reality"].pop("btc_dominance_pct")
        with self.assertRaisesRegex(ContractError, "CURRENT_MISSING"):
            build_documents(current, previous, ancestry_ok=True, strict_locks=False)

    def test_reversed_timestamps_fail_closed(self):
        current, previous = bundles()
        current.snapshot["generated_at_utc"] = "2026-07-01T00:00:00Z"
        current.bindings["generated_at_utc"] = "2026-07-01T00:00:00Z"
        with self.assertRaisesRegex(ContractError, "TIMESTAMP_ORDER_INVALID"):
            build_documents(current, previous, ancestry_ok=True, strict_locks=False)

    def test_non_ancestor_fails_closed(self):
        with self.assertRaisesRegex(ContractError, "ANCESTRY_INVALID"):
            build_documents(*bundles(), ancestry_ok=False, strict_locks=False)

    def test_proof_hold_blocks_affected_metric(self):
        current, previous = bundles()
        current.proof["sources"][0]["status"] = "HOLD"
        with self.assertRaisesRegex(ContractError, "PROOF_NOT_PASS"):
            build_documents(current, previous, ancestry_ok=True, strict_locks=False)

    def test_source_url_mismatch_fails_closed(self):
        current, previous = bundles()
        current.proof["sources"][0]["url"] = "https://example.invalid"
        with self.assertRaisesRegex(ContractError, "SOURCE_URL_MISMATCH"):
            build_documents(current, previous, ancestry_ok=True, strict_locks=False)

    def test_universe_mismatch_fails_closed(self):
        current, previous = bundles()
        previous.snapshot["altcoin_rotation"]["universe"] = "other"
        with self.assertRaisesRegex(ContractError, "UNIVERSE_MISMATCH"):
            build_documents(current, previous, ancestry_ok=True, strict_locks=False)

    def test_modified_bytes_change_blob_hash(self):
        current, _ = bundles()
        self.assertNotEqual(git_blob_sha(current.snapshot_bytes + b" "), current.snapshot_blob_sha)

    def test_categorical_unchanged_explicit(self):
        _, delta = build_documents(*bundles(), ancestry_ok=True, strict_locks=False)
        self.assertEqual(delta["metrics"]["regime_label"]["transition"], "UNCHANGED")

    def test_defi_tvl_unavailable(self):
        _, delta = build_documents(*bundles(), ancestry_ok=True, strict_locks=False)
        item = delta["unavailable_metrics"]["defi_tvl_usd"]
        self.assertEqual(item["reason_code"], "METHODOLOGY_MISMATCH")
        self.assertIsNone(item["delta_value"])

    def test_liquidity_dependency_unavailable(self):
        _, delta = build_documents(*bundles(), ancestry_ok=True, strict_locks=False)
        item = delta["unavailable_metrics"]["liquidity_context_state"]
        self.assertEqual(item["dependency"], "defi_tvl_usd")

    def test_round_half_up(self):
        self.assertEqual(display_delta(Decimal("0.005"), 2), "+0.01")
        self.assertEqual(display_delta(Decimal("-0.005"), 2), "-0.01")

    def test_no_network_needed(self):
        with mock.patch("socket.socket.connect", side_effect=AssertionError("network forbidden")):
            registry, delta = build_documents(*bundles(), ancestry_ok=True, strict_locks=False)
        self.assertTrue(registry)
        self.assertTrue(delta)


if __name__ == "__main__":
    unittest.main()
