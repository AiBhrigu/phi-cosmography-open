#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from build_snapshot_memory import (
    BINDINGS_PATH,
    BOUNDARY,
    PROOF_PATH,
    REGISTRY_PATH,
    RUNNER_PATH,
    SNAPSHOT_PATH,
    ContractError,
    TRACKED_METRICS,
    build_documents,
    bundle_from_entry,
    bundle_from_ref,
    display_delta,
    entry,
    git_blob_sha,
    json_bytes,
    load_pair,
    make_bundle,
)


def encoded(document):
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()


def fixture_documents(*, same_defi_method=False):
    base_boundary = {
        key: value
        for key, value in BOUNDARY.items()
        if key not in {
            "crawler_input_forbidden",
            "html_presentation_input_forbidden",
            "ui_binding_opened",
            "refresh_pipeline_binding_opened",
        }
    }
    current_snapshot = {
        "schema_version": "crypto_astro_snapshot_public_v0_1",
        "generated_at_utc": "2026-07-19T18:26:56Z",
        "source_mode": "static_public_snapshot",
        "market_reality": {
            "btc_dominance_pct": 56.50010249230421,
            "stablecoin_share_pct": 13.500433230542436,
        },
        "field_output": {
            "market_field_score": 61.0,
            "regime_label": "Balanced Expansion",
        },
        "altcoin_rotation": {
            "universe": "non-stable top-250 crypto assets",
            "alt_breadth_24h_pct": 34.5,
            "alt_breadth_7d_pct": 39.9,
        },
        "liquidity_tvl": {
            "defi_tvl_usd": 75551199898.0,
            "liquidity_context_state": "context fresh",
            "defi_tvl_methodology_id": "defillama_historical_chain_tvl_ex_double_count_v0_1",
        },
        "boundary": copy.deepcopy(base_boundary),
    }
    previous_snapshot = copy.deepcopy(current_snapshot)
    previous_snapshot["generated_at_utc"] = "2026-07-12T22:05:46Z"
    previous_snapshot["market_reality"].update(
        btc_dominance_pct=56.21621132126818,
        stablecoin_share_pct=13.683691685333388,
    )
    previous_snapshot["field_output"]["market_field_score"] = 60.0
    previous_snapshot["altcoin_rotation"].update(
        alt_breadth_24h_pct=26.5,
        alt_breadth_7d_pct=41.2,
    )
    previous_snapshot["liquidity_tvl"]["defi_tvl_usd"] = 70000000000.0
    if not same_defi_method:
        previous_snapshot["liquidity_tvl"].pop("defi_tvl_methodology_id")

    common_sources = [
        {
            "label": "coingecko_global",
            "url": "https://api.coingecko.com/api/v3/global",
            "status": "PASS",
        },
        {
            "label": "coingecko_top250_markets",
            "url": "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h%2C24h%2C7d%2C30d&sparkline=false",
            "status": "PASS",
        },
        {
            "label": "defillama_stablecoins",
            "url": "https://stablecoins.llama.fi/stablecoins?includePrices=true",
            "status": "PASS",
        },
    ]
    current_sources = common_sources + [
        {
            "label": "defillama_protocols",
            "url": "https://api.llama.fi/v2/historicalChainTvl",
            "status": "PASS",
        }
    ]
    previous_sources = copy.deepcopy(common_sources) + [
        {
            "label": "defillama_protocols",
            "url": (
                "https://api.llama.fi/v2/historicalChainTvl"
                if same_defi_method
                else "https://api.llama.fi/protocols"
            ),
            "status": "PASS",
        }
    ]
    current_proof = {
        "schema_version": "crypto_astro_snapshot_proof_public_v0_1",
        "generated_at_utc": "2026-07-19T18:26:49Z",
        "source_mode": "static_public_snapshot",
        "sources": current_sources,
        "boundary": copy.deepcopy(base_boundary),
    }
    previous_proof = copy.deepcopy(current_proof)
    previous_proof.update(
        generated_at_utc="2026-07-12T22:05:45Z",
        sources=previous_sources,
    )
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
        "boundary": copy.deepcopy(base_boundary),
    }
    previous_bindings = copy.deepcopy(current_bindings)
    previous_bindings["generated_at_utc"] = previous_snapshot["generated_at_utc"]
    return (
        current_snapshot,
        previous_snapshot,
        current_proof,
        previous_proof,
        current_bindings,
        previous_bindings,
    )


def bundles(*, same_defi_method=False):
    cs, ps, cp, pp, cb, pb = fixture_documents(same_defi_method=same_defi_method)
    current = make_bundle(
        role="current",
        commit_sha="c" * 40,
        data_origin_commit_sha="b" * 40,
        runner_blob_sha="1" * 40,
        snapshot_bytes=encoded(cs),
        proof_bytes=encoded(cp),
        bindings_bytes=encoded(cb),
    )
    previous = make_bundle(
        role="previous",
        commit_sha="p" * 40,
        data_origin_commit_sha="o" * 40,
        runner_blob_sha="2" * 40,
        snapshot_bytes=encoded(ps),
        proof_bytes=encoded(pp),
        bindings_bytes=encoded(pb),
    )
    return current, previous


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def write_json(repo: Path, relative: str, document: dict) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def topology_documents(timestamp_value: str, score: float) -> tuple[dict, dict, dict]:
    boundary = {
        key: value
        for key, value in BOUNDARY.items()
        if key not in {
            "crawler_input_forbidden",
            "html_presentation_input_forbidden",
            "ui_binding_opened",
            "refresh_pipeline_binding_opened",
        }
    }
    snapshot = {
        "schema_version": "crypto_astro_snapshot_public_v0_1",
        "generated_at_utc": timestamp_value,
        "source_mode": "static_public_snapshot",
        "market_reality": {
            "btc_dominance_pct": 56.0 + score,
            "stablecoin_share_pct": 13.0,
        },
        "field_output": {
            "market_field_score": score,
            "regime_label": "Balanced Expansion",
        },
        "altcoin_rotation": {
            "universe": "non-stable top-250 crypto assets",
            "alt_breadth_24h_pct": 50.0,
            "alt_breadth_7d_pct": 50.0,
        },
        "liquidity_tvl": {
            "defi_tvl_usd": 70000000000.0 + score,
            "liquidity_context_state": "context fresh",
            "defi_tvl_methodology_id": "defillama_historical_chain_tvl_ex_double_count_v0_1",
        },
        "boundary": copy.deepcopy(boundary),
    }
    proof = {
        "schema_version": "crypto_astro_snapshot_proof_public_v0_1",
        "generated_at_utc": timestamp_value,
        "source_mode": "static_public_snapshot",
        "sources": [
            {
                "label": "coingecko_global",
                "url": "https://api.coingecko.com/api/v3/global",
                "status": "PASS",
            },
            {
                "label": "coingecko_top250_markets",
                "url": "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h%2C24h%2C7d%2C30d&sparkline=false",
                "status": "PASS",
            },
            {
                "label": "defillama_stablecoins",
                "url": "https://stablecoins.llama.fi/stablecoins?includePrices=true",
                "status": "PASS",
            },
            {
                "label": "defillama_protocols",
                "url": "https://api.llama.fi/v2/historicalChainTvl",
                "status": "PASS",
            },
        ],
        "boundary": copy.deepcopy(boundary),
    }
    bindings = {
        "schema_version": "crypto_astro_public_module_bindings_v0_1",
        "generated_at_utc": timestamp_value,
        "source_mode": "static_public_snapshot",
        "modules": {
            "market_reality": {"source": "market_reality"},
            "altcoin_rotation": {"source": "altcoin_rotation"},
            "aem_barometer": {"source": "field_output"},
        },
        "boundary": copy.deepcopy(boundary),
    }
    return snapshot, proof, bindings


class GitTopologyFixture:
    def __init__(self, squash: bool):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "snapshot-memory@example.invalid")
        git(self.repo, "config", "user.name", "Snapshot Memory Test")
        runner = self.repo / RUNNER_PATH
        runner.parent.mkdir(parents=True, exist_ok=True)
        runner.write_text("#!/usr/bin/env python3\nprint('locked runner')\n", encoding="utf-8")

        self._write_bundle("2026-07-19T00:00:00Z", 60.0)
        self.old_base = self._commit("old accepted materialization")

        self._write_bundle("2026-07-21T00:00:00Z", 70.0)
        self.provenance_current = self._commit("generated current data")
        self.locked_current = entry(
            bundle_from_ref(
                self.repo,
                "current",
                self.provenance_current,
                data_origin_ref=self.old_base,
            )
        )

        if squash:
            git(self.repo, "checkout", "--detach", self.old_base)
            self._write_bundle("2026-07-21T00:00:00Z", 70.0)
        write_json(self.repo, REGISTRY_PATH, {"current": self.locked_current})
        self.accepted_base = self._commit(
            "squash accepted current" if squash else "linear accepted current"
        )

        self._write_bundle("2026-07-22T00:00:00Z", 80.0)
        self.current_data = self._commit("next generated data")

    def _write_bundle(self, timestamp_value: str, score: float) -> None:
        snapshot, proof, bindings = topology_documents(timestamp_value, score)
        write_json(self.repo, SNAPSHOT_PATH, snapshot)
        write_json(self.repo, PROOF_PATH, proof)
        write_json(self.repo, BINDINGS_PATH, bindings)

    def _commit(self, message: str) -> str:
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")

    def tampered_base_and_current(self, path: str) -> tuple[str, str]:
        git(self.repo, "checkout", "--detach", self.accepted_base)
        target = self.repo / path
        target.write_bytes(target.read_bytes() + b" ")
        tampered_base = self._commit(f"tamper {path}")
        self._write_bundle("2026-07-23T00:00:00Z", 90.0)
        current = self._commit("new data after tampered base")
        return tampered_base, current

    def unrelated_commit(self) -> str:
        git(self.repo, "checkout", "--orphan", "unrelated")
        for child in list(self.repo.iterdir()):
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        (self.repo / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        return self._commit("unrelated root")

    def close(self) -> None:
        self.temp.cleanup()


class SnapshotMemoryMetricTests(unittest.TestCase):
    def test_partial_pair_exact_deltas(self):
        registry, delta = build_documents(*bundles())
        self.assertEqual(delta["metrics"]["btc_gravity_pct"]["raw_delta"], "0.28389117103603")
        self.assertEqual(delta["metrics"]["stablecoin_share_pct"]["display_delta"], "-0.18")
        self.assertEqual(delta["comparison_status"], "PARTIAL_COMPARABLE")
        self.assertEqual(registry["schema_version"], "crypto_astro_snapshot_registry_public_v0_2")

    def test_same_method_makes_all_eight_comparable(self):
        _, delta = build_documents(*bundles(same_defi_method=True))
        self.assertEqual(delta["comparison_status"], "FULL_COMPARABLE")
        self.assertEqual(set(delta["metrics"]), set(TRACKED_METRICS))
        self.assertFalse(delta["unavailable_metrics"])

    def test_methodology_mismatch_is_per_metric_fail_closed(self):
        _, delta = build_documents(*bundles())
        self.assertEqual(delta["unavailable_metrics"]["defi_tvl_usd"]["reason_code"], "METHODOLOGY_MISMATCH")
        self.assertEqual(delta["unavailable_metrics"]["liquidity_context_state"]["reason_code"], "DEPENDENCY_METHODOLOGY_MISMATCH")

    def test_proof_hold_only_blocks_affected_metrics(self):
        current, previous = bundles(same_defi_method=True)
        current.proof["sources"][0]["status"] = "HOLD"
        _, delta = build_documents(current, previous)
        self.assertIn("btc_gravity_pct", delta["unavailable_metrics"])
        self.assertIn("stablecoin_share_pct", delta["unavailable_metrics"])
        self.assertIn("alt_breadth_24h_pct", delta["metrics"])

    def test_universe_mismatch_is_unavailable(self):
        current, previous = bundles()
        previous.snapshot["altcoin_rotation"]["universe"] = "other"
        _, delta = build_documents(current, previous)
        self.assertEqual(delta["unavailable_metrics"]["alt_breadth_24h_pct"]["reason_code"], "UNIVERSE_MISMATCH")

    def test_missing_field_is_unavailable(self):
        current, previous = bundles()
        previous.snapshot["market_reality"].pop("btc_dominance_pct")
        _, delta = build_documents(current, previous)
        self.assertEqual(delta["unavailable_metrics"]["btc_gravity_pct"]["reason_code"], "PREVIOUS_MISSING")

    def test_reversed_timestamps_fail_globally(self):
        current, previous = bundles()
        current.snapshot["generated_at_utc"] = "2026-07-01T00:00:00Z"
        current.bindings["generated_at_utc"] = "2026-07-01T00:00:00Z"
        with self.assertRaisesRegex(ContractError, "TIMESTAMP_ORDER_INVALID"):
            build_documents(current, previous)

    def test_identical_rerun_is_byte_identical(self):
        first = build_documents(*bundles())
        second = build_documents(*bundles())
        self.assertEqual(json_bytes(first[0]), json_bytes(second[0]))
        self.assertEqual(json_bytes(first[1]), json_bytes(second[1]))

    def test_categorical_unchanged_explicit(self):
        _, delta = build_documents(*bundles())
        self.assertEqual(delta["metrics"]["regime_label"]["transition"], "UNCHANGED")

    def test_round_half_up(self):
        self.assertEqual(display_delta(Decimal("0.005"), 2), "+0.01")
        self.assertEqual(display_delta(Decimal("-0.005"), 2), "-0.01")

    def test_modified_bytes_change_blob_hash(self):
        current, _ = bundles()
        self.assertNotEqual(git_blob_sha(current.snapshot_bytes + b" "), current.snapshot_blob_sha)

    def test_no_network_needed(self):
        with mock.patch("socket.socket.connect", side_effect=AssertionError("network forbidden")):
            registry, delta = build_documents(*bundles())
        self.assertTrue(registry and delta)


class SnapshotMemoryTopologyTests(unittest.TestCase):
    def test_linear_branch_to_branch_topology(self):
        fixture = GitTopologyFixture(squash=False)
        self.addCleanup(fixture.close)
        current, previous, evidence = load_pair(
            fixture.repo,
            base_ref=fixture.accepted_base,
            current_ref=fixture.current_data,
        )
        self.assertEqual(previous.commit_sha, fixture.provenance_current)
        self.assertEqual(current.data_origin_commit_sha, fixture.accepted_base)
        self.assertEqual(evidence["transaction_base_ancestry"], "PASS")

    def test_squash_merge_topology(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        self.assertNotEqual(
            git(fixture.repo, "merge-base", fixture.provenance_current, fixture.accepted_base),
            fixture.provenance_current,
        )
        current, previous, evidence = load_pair(
            fixture.repo,
            base_ref=fixture.accepted_base,
            current_ref=fixture.current_data,
        )
        self.assertEqual(previous.commit_sha, fixture.provenance_current)
        self.assertEqual(current.data_origin_commit_sha, fixture.accepted_base)
        self.assertEqual(evidence["base_materialization_hashes"], "PASS")

    def test_tampered_base_snapshot_fails(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        base, current = fixture.tampered_base_and_current(SNAPSHOT_PATH)
        with self.assertRaisesRegex(ContractError, "BASE_MATERIALIZATION_HASH_MISMATCH"):
            load_pair(fixture.repo, base_ref=base, current_ref=current)

    def test_tampered_base_proof_fails(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        base, current = fixture.tampered_base_and_current(PROOF_PATH)
        with self.assertRaisesRegex(ContractError, "BASE_MATERIALIZATION_HASH_MISMATCH"):
            load_pair(fixture.repo, base_ref=base, current_ref=current)

    def test_tampered_base_bindings_fails(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        base, current = fixture.tampered_base_and_current(BINDINGS_PATH)
        with self.assertRaisesRegex(ContractError, "BASE_MATERIALIZATION_HASH_MISMATCH"):
            load_pair(fixture.repo, base_ref=base, current_ref=current)

    def test_data_origin_not_ancestor_fails(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        unrelated = fixture.unrelated_commit()
        locked = copy.deepcopy(fixture.locked_current)
        locked["data_origin_commit_sha"] = unrelated
        with self.assertRaisesRegex(ContractError, "TRANSACTION_ANCESTRY_INVALID"):
            bundle_from_entry(fixture.repo, "previous", locked)

    def test_missing_provenance_commit_fails(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        locked = copy.deepcopy(fixture.locked_current)
        locked["commit_sha"] = "f" * 40
        with self.assertRaisesRegex(ContractError, "PROVENANCE_COMMIT_MISSING"):
            bundle_from_entry(fixture.repo, "previous", locked)

    def test_provenance_runner_hash_drift_fails(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        locked = copy.deepcopy(fixture.locked_current)
        locked["runner_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(ContractError, "PROVENANCE_HASH_MISMATCH"):
            bundle_from_entry(fixture.repo, "previous", locked)

    def test_new_registry_preserves_previous_provenance_and_uses_base_origin(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        current, previous, _ = load_pair(
            fixture.repo,
            base_ref=fixture.accepted_base,
            current_ref=fixture.current_data,
        )
        registry, _ = build_documents(current, previous)
        self.assertEqual(registry["previous"]["commit_sha"], fixture.provenance_current)
        self.assertEqual(registry["current"]["data_origin_commit_sha"], fixture.accepted_base)

    def test_runtime_generated_registry_uses_dynamic_accepted_base(self):
        fixture = GitTopologyFixture(squash=True)
        self.addCleanup(fixture.close)
        current, previous, evidence = load_pair(
            fixture.repo,
            base_ref=fixture.accepted_base,
            current_ref=fixture.current_data,
        )
        registry, delta = build_documents(current, previous)
        write_json(fixture.repo, REGISTRY_PATH, registry)
        committed_current, committed_previous, committed_evidence = load_pair(fixture.repo)

        self.assertNotEqual(fixture.accepted_base, fixture.old_base)
        self.assertEqual(registry["current"]["data_origin_commit_sha"], fixture.accepted_base)
        self.assertEqual(registry["current"]["commit_sha"], fixture.current_data)
        self.assertEqual(registry["previous"]["commit_sha"], fixture.provenance_current)
        self.assertEqual(committed_current.data_origin_commit_sha, fixture.accepted_base)
        self.assertEqual(committed_previous.commit_sha, fixture.provenance_current)
        self.assertEqual(evidence["provenance_hashes"], "PASS")
        self.assertEqual(evidence["base_materialization_hashes"], "PASS")
        self.assertEqual(committed_evidence["transaction_base_ancestry"], "PASS")
        self.assertEqual(
            set(delta["metrics"]) | set(delta["unavailable_metrics"]),
            set(TRACKED_METRICS),
        )


if __name__ == "__main__":
    unittest.main()
