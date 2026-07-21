#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest
from decimal import Decimal
from unittest import mock

from build_snapshot_memory import (
    BOUNDARY, ContractError, TRACKED_METRICS, build_documents, display_delta,
    git_blob_sha, json_bytes, make_bundle,
)


def encoded(document):
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()


def fixture_documents(*, same_defi_method=False):
    base_boundary = {k: v for k, v in BOUNDARY.items() if k not in {
        "crawler_input_forbidden", "html_presentation_input_forbidden",
        "ui_binding_opened", "refresh_pipeline_binding_opened",
    }}
    current_snapshot = {
        "schema_version": "crypto_astro_snapshot_public_v0_1",
        "generated_at_utc": "2026-07-19T18:26:56Z",
        "source_mode": "static_public_snapshot",
        "market_reality": {"btc_dominance_pct": 56.50010249230421, "stablecoin_share_pct": 13.500433230542436},
        "field_output": {"market_field_score": 61.0, "regime_label": "Balanced Expansion"},
        "altcoin_rotation": {"universe": "non-stable top-250 crypto assets", "alt_breadth_24h_pct": 34.5, "alt_breadth_7d_pct": 39.9},
        "liquidity_tvl": {
            "defi_tvl_usd": 75551199898.0, "liquidity_context_state": "context fresh",
            "defi_tvl_methodology_id": "defillama_historical_chain_tvl_ex_double_count_v0_1",
        },
        "boundary": copy.deepcopy(base_boundary),
    }
    previous_snapshot = copy.deepcopy(current_snapshot)
    previous_snapshot["generated_at_utc"] = "2026-07-12T22:05:46Z"
    previous_snapshot["market_reality"].update(btc_dominance_pct=56.21621132126818, stablecoin_share_pct=13.683691685333388)
    previous_snapshot["field_output"]["market_field_score"] = 60.0
    previous_snapshot["altcoin_rotation"].update(alt_breadth_24h_pct=26.5, alt_breadth_7d_pct=41.2)
    previous_snapshot["liquidity_tvl"]["defi_tvl_usd"] = 70000000000.0
    if not same_defi_method:
        previous_snapshot["liquidity_tvl"].pop("defi_tvl_methodology_id")

    common_sources = [
        {"label": "coingecko_global", "url": "https://api.coingecko.com/api/v3/global", "status": "PASS"},
        {"label": "coingecko_top250_markets", "url": "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h%2C24h%2C7d%2C30d&sparkline=false", "status": "PASS"},
        {"label": "defillama_stablecoins", "url": "https://stablecoins.llama.fi/stablecoins?includePrices=true", "status": "PASS"},
    ]
    current_sources = common_sources + [
        {"label": "defillama_protocols", "url": "https://api.llama.fi/v2/historicalChainTvl", "status": "PASS"}
    ]
    previous_sources = copy.deepcopy(common_sources) + [{
        "label": "defillama_protocols",
        "url": "https://api.llama.fi/v2/historicalChainTvl" if same_defi_method else "https://api.llama.fi/protocols",
        "status": "PASS",
    }]
    current_proof = {
        "schema_version": "crypto_astro_snapshot_proof_public_v0_1", "generated_at_utc": "2026-07-19T18:26:49Z",
        "source_mode": "static_public_snapshot", "sources": current_sources, "boundary": copy.deepcopy(base_boundary),
    }
    previous_proof = copy.deepcopy(current_proof)
    previous_proof.update(generated_at_utc="2026-07-12T22:05:45Z", sources=previous_sources)
    modules = {
        "market_reality": {"source": "market_reality"},
        "altcoin_rotation": {"source": "altcoin_rotation"},
        "aem_barometer": {"source": "field_output"},
    }
    current_bindings = {
        "schema_version": "crypto_astro_public_module_bindings_v0_1",
        "generated_at_utc": current_snapshot["generated_at_utc"], "source_mode": "static_public_snapshot",
        "modules": copy.deepcopy(modules), "boundary": copy.deepcopy(base_boundary),
    }
    previous_bindings = copy.deepcopy(current_bindings)
    previous_bindings["generated_at_utc"] = previous_snapshot["generated_at_utc"]
    return current_snapshot, previous_snapshot, current_proof, previous_proof, current_bindings, previous_bindings


def bundles(*, same_defi_method=False):
    cs, ps, cp, pp, cb, pb = fixture_documents(same_defi_method=same_defi_method)
    current = make_bundle(role="current", commit_sha="c"*40, data_origin_commit_sha="c"*40,
                          runner_blob_sha="1"*40, snapshot_bytes=encoded(cs), proof_bytes=encoded(cp), bindings_bytes=encoded(cb))
    previous = make_bundle(role="previous", commit_sha="p"*40, data_origin_commit_sha="p"*40,
                           runner_blob_sha="2"*40, snapshot_bytes=encoded(ps), proof_bytes=encoded(pp), bindings_bytes=encoded(pb))
    return current, previous


class SnapshotMemoryContractTests(unittest.TestCase):
    def test_partial_pair_exact_deltas(self):
        registry, delta = build_documents(*bundles(), ancestry_ok=True)
        self.assertEqual(delta["metrics"]["btc_gravity_pct"]["raw_delta"], "0.28389117103603")
        self.assertEqual(delta["metrics"]["stablecoin_share_pct"]["display_delta"], "-0.18")
        self.assertEqual(delta["comparison_status"], "PARTIAL_COMPARABLE")
        self.assertEqual(registry["schema_version"], "crypto_astro_snapshot_registry_public_v0_2")

    def test_same_method_makes_all_eight_comparable(self):
        _, delta = build_documents(*bundles(same_defi_method=True), ancestry_ok=True)
        self.assertEqual(delta["comparison_status"], "FULL_COMPARABLE")
        self.assertEqual(set(delta["metrics"]), set(TRACKED_METRICS))
        self.assertFalse(delta["unavailable_metrics"])

    def test_methodology_mismatch_is_per_metric_fail_closed(self):
        _, delta = build_documents(*bundles(), ancestry_ok=True)
        self.assertEqual(delta["unavailable_metrics"]["defi_tvl_usd"]["reason_code"], "METHODOLOGY_MISMATCH")
        self.assertEqual(delta["unavailable_metrics"]["liquidity_context_state"]["reason_code"], "DEPENDENCY_METHODOLOGY_MISMATCH")

    def test_proof_hold_only_blocks_affected_metrics(self):
        current, previous = bundles(same_defi_method=True)
        current.proof["sources"][0]["status"] = "HOLD"
        _, delta = build_documents(current, previous, ancestry_ok=True)
        self.assertIn("btc_gravity_pct", delta["unavailable_metrics"])
        self.assertIn("stablecoin_share_pct", delta["unavailable_metrics"])
        self.assertIn("alt_breadth_24h_pct", delta["metrics"])

    def test_universe_mismatch_is_unavailable(self):
        current, previous = bundles()
        previous.snapshot["altcoin_rotation"]["universe"] = "other"
        _, delta = build_documents(current, previous, ancestry_ok=True)
        self.assertEqual(delta["unavailable_metrics"]["alt_breadth_24h_pct"]["reason_code"], "UNIVERSE_MISMATCH")

    def test_missing_field_is_unavailable(self):
        current, previous = bundles()
        previous.snapshot["market_reality"].pop("btc_dominance_pct")
        _, delta = build_documents(current, previous, ancestry_ok=True)
        self.assertEqual(delta["unavailable_metrics"]["btc_gravity_pct"]["reason_code"], "PREVIOUS_MISSING")

    def test_reversed_timestamps_fail_globally(self):
        current, previous = bundles()
        current.snapshot["generated_at_utc"] = "2026-07-01T00:00:00Z"
        current.bindings["generated_at_utc"] = "2026-07-01T00:00:00Z"
        with self.assertRaisesRegex(ContractError, "TIMESTAMP_ORDER_INVALID"):
            build_documents(current, previous, ancestry_ok=True)

    def test_non_ancestor_fails_globally(self):
        with self.assertRaisesRegex(ContractError, "ANCESTRY_INVALID"):
            build_documents(*bundles(), ancestry_ok=False)

    def test_identical_rerun_is_byte_identical(self):
        first = build_documents(*bundles(), ancestry_ok=True)
        second = build_documents(*bundles(), ancestry_ok=True)
        self.assertEqual(json_bytes(first[0]), json_bytes(second[0]))
        self.assertEqual(json_bytes(first[1]), json_bytes(second[1]))

    def test_categorical_unchanged_explicit(self):
        _, delta = build_documents(*bundles(), ancestry_ok=True)
        self.assertEqual(delta["metrics"]["regime_label"]["transition"], "UNCHANGED")

    def test_round_half_up(self):
        self.assertEqual(display_delta(Decimal("0.005"), 2), "+0.01")
        self.assertEqual(display_delta(Decimal("-0.005"), 2), "-0.01")

    def test_modified_bytes_change_blob_hash(self):
        current, _ = bundles()
        self.assertNotEqual(git_blob_sha(current.snapshot_bytes + b" "), current.snapshot_blob_sha)

    def test_no_network_needed(self):
        with mock.patch("socket.socket.connect", side_effect=AssertionError("network forbidden")):
            registry, delta = build_documents(*bundles(), ancestry_ok=True)
        self.assertTrue(registry and delta)


if __name__ == "__main__":
    unittest.main()
