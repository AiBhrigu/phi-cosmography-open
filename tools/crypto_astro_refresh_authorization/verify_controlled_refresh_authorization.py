#!/usr/bin/env python3
"""Fail-closed verifier for the post-Gate-3 controlled refresh authorization packet."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "crypto_astro_post_gate_3_controlled_refresh_authorization_packet_v0_1"
NODE = "CRYPTO_ASTRO_POST_GATE_3_CONTROLLED_REFRESH_AUTHORIZATION_PACKET_SCOPE_v0_1"
REPOSITORY = "AiBhrigu/phi-cosmography-open"
AUTHORING_BASE_SHA = "ac86447a89daf4b71333cb133e978a98b82b4abf"
PROOF_MAIN_SHA = "4f00ec234b1bb3db43c5687cf678b77ff5d98eaa"
HANDOFF_MERGE_SHA = "f46002db6864a069b1340c20fb2c4113e2fef080"
FINALIZATION_SHA = AUTHORING_BASE_SHA

PACKET_PATH = Path("docs/crypto-astro-service/crypto_astro_post_gate_3_controlled_refresh_authorization_packet_v0_1.json")
INDEX_PATH = Path("docs/crypto-astro-service/CRYPTO_ASTRO_POST_GATE_3_CONTROLLED_REFRESH_AUTHORIZATION_PACKET_v0_1.md")

REQUIRED_FILES = {
    "site/crypto-astro/index.html",
    "site/crypto-astro/data/crypto_astro_snapshot.public.json",
    "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json",
    "site/crypto-astro/data/crypto_astro_module_bindings.public.json",
    "site/crypto-astro/data/market_field_snapshot.public.v0_1.json",
    "site/crypto-astro/data/scoring_snapshot.public.json",
    "site/crypto-astro/data/crypto_astro_snapshot_registry.public.json",
    "site/crypto-astro/data/crypto_astro_snapshot_delta.public.json",
    "docs/crypto-astro-service/crypto_astro_snapshot_summary.md",
    "docs/crypto-astro-service/crypto_astro_operator_review.md",
}
OPTIONAL_FILES = {"site/crypto-astro/data/crypto_astro_module_bindings.public.schema.json"}
REQUIRED_SOURCE_LABELS = [
    "coingecko_global",
    "coingecko_asset_markets_btc_eth_sol_ton_icp",
    "coingecko_top250_markets",
    "coingecko_stablecoin_sample",
    "defillama_protocols",
    "defillama_dex_overview",
    "defillama_stablecoins",
]
REQUIRED_FAIL_CODES = [
    "FAIL_EXPECTED_MAIN_SHA",
    "FAIL_IDENTITY_OR_OWNER_AUTH",
    "FAIL_SINGLE_FLIGHT",
    "FAIL_CADENCE",
    "FAIL_SOURCE_MISSING",
    "FAIL_SOURCE_URL",
    "FAIL_SOURCE_STATUS",
    "FAIL_SOURCE_HASH",
    "FAIL_SOURCE_TIMESTAMP",
    "FAIL_DEFI_TVL_METHODOLOGY",
    "FAIL_DEFI_TVL_STALE",
    "FAIL_DEFI_TVL_ANOMALY",
    "FAIL_SCHEMA",
    "FAIL_TIMESTAMP_ORDER",
    "FAIL_BINDINGS",
    "FAIL_MEMORY",
    "FAIL_ATOMIC_SCOPE",
    "FAIL_BHRIGU_CONSUMER",
    "FAIL_VISUAL_REVIEW",
    "FAIL_CI",
    "FAIL_MERGE_SHA_LOCK",
    "FAIL_PUBLIC_HTTP_PROOF",
]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def check(ok: bool, code: str, failures: list[str]) -> None:
    if not ok:
        failures.append(code)


def load_packet(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("PACKET_NOT_OBJECT")
    return value


def validate_packet(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    check(value.get("schema_version") == SCHEMA, "packet:schema", failures)
    check(value.get("node") == NODE, "packet:node", failures)
    check(value.get("packet_status") == "READY_FOR_REVIEW", "packet:status", failures)
    check(value.get("execution_authorized") is False, "packet:execution_authorized", failures)
    check(value.get("repository") == REPOSITORY, "packet:repository", failures)
    check(value.get("packet_authoring_base_sha") == AUTHORING_BASE_SHA, "packet:authoring_base", failures)
    check(SHA_RE.fullmatch(str(value.get("packet_authoring_base_sha", ""))) is not None, "packet:authoring_sha_format", failures)

    closure = value.get("gate_3_closure") if isinstance(value.get("gate_3_closure"), dict) else {}
    check(closure.get("operational_status") == "PASS", "closure:operational", failures)
    check(closure.get("memory_status") == "PASS", "closure:memory", failures)
    check(closure.get("finalization_pr") == 169, "closure:pr", failures)
    check(closure.get("finalization_merge_sha") == FINALIZATION_SHA, "closure:finalization_sha", failures)
    check(closure.get("production_proof_issue") == 167, "closure:proof_issue", failures)
    check(closure.get("production_proof_run_id") == 29914563042, "closure:proof_run", failures)
    check(closure.get("production_proof_main_sha") == PROOF_MAIN_SHA, "closure:proof_sha", failures)
    check(closure.get("handoff_merge_sha") == HANDOFF_MERGE_SHA, "closure:handoff_sha", failures)
    check(closure.get("production_proof_artifact_id") == 8527304778, "closure:artifact", failures)
    check(DIGEST_RE.fullmatch(str(closure.get("production_proof_artifact_digest", ""))) is not None, "closure:digest", failures)

    identity = value.get("execution_identity") if isinstance(value.get("execution_identity"), dict) else {}
    check(identity.get("refresh_count") == 1, "identity:refresh_count", failures)
    check(identity.get("refresh_mode") == "REPEATABILITY_PROOF", "identity:mode", failures)
    check(identity.get("owner_authenticated_issue_required") is True, "identity:owner_issue", failures)
    check(identity.get("single_flight_required") is True, "identity:single_flight", failures)
    check(identity.get("operator_f_manual_actions") == "NONE", "identity:operator_f", failures)
    future_fields = identity.get("required_future_fields")
    check(future_fields == ["REFRESH_ID", "OPERATOR_REF", "REFRESH_REASON", "EXPECTED_MAIN_SHA", "DISPATCH_REQUEST_ISSUE"], "identity:future_fields", failures)

    source = value.get("source_lock") if isinstance(value.get("source_lock"), dict) else {}
    items = source.get("required_sources") if isinstance(source.get("required_sources"), list) else []
    labels = [item.get("label") for item in items if isinstance(item, dict)]
    check(labels == REQUIRED_SOURCE_LABELS, "source:labels", failures)
    check(all(item.get("required_status") == "PASS" for item in items if isinstance(item, dict)), "source:status", failures)
    check(source.get("all_required_sources_must_pass") is True, "source:all_pass", failures)
    check(source.get("source_payload_sha256_required") is True, "source:hash", failures)
    check(source.get("source_payload_byte_count_required") is True, "source:bytes", failures)
    check(source.get("maximum_fetch_spread_seconds") == 600, "source:fetch_spread", failures)
    check(source.get("maximum_snapshot_after_latest_fetch_seconds") == 120, "source:snapshot_lag", failures)
    check(source.get("no_cached_payload_substitution") is True, "source:no_cache_substitution", failures)
    check(source.get("no_unlisted_source_substitution") is True, "source:no_unlisted_substitution", failures)

    defi = value.get("defi_tvl_methodology_lock") if isinstance(value.get("defi_tvl_methodology_lock"), dict) else {}
    check(defi.get("methodology_id") == "defillama_historical_chain_tvl_ex_double_count_v0_1", "defi:methodology", failures)
    check(defi.get("canonical_source_id") == "defillama_global_tvl_ex_double_count", "defi:canonical_source", failures)
    check(defi.get("proof_label") == "defillama_protocols", "defi:proof_label", failures)
    check(defi.get("source_url") == "https://api.llama.fi/v2/historicalChainTvl", "defi:url", failures)
    check(defi.get("legacy_protocols_url_for_value_forbidden") == "https://api.llama.fi/protocols", "defi:legacy_forbidden", failures)
    for key in (
        "protocol_sum_forbidden",
        "multi_chain_sum_forbidden",
        "liquid_staking_addback_forbidden",
        "double_count_addback_forbidden",
        "finite_positive_value_required",
        "previous_accepted_methodology_must_match",
        "excludes_liquid_staking",
        "excludes_double_counted",
    ):
        check(defi.get(key) is True, f"defi:{key}", failures)
    check(defi.get("maximum_source_age_hours") == 48, "defi:max_age", failures)
    check(defi.get("absolute_change_manual_review_threshold_pct") == 25.0, "defi:threshold", failures)
    check(defi.get("threshold_action") == "FAIL_CLOSED_REQUIRE_SEPARATE_METHODOLOGY_REVIEW", "defi:threshold_action", failures)

    scope = value.get("exact_generated_pr_scope") if isinstance(value.get("exact_generated_pr_scope"), dict) else {}
    required = set(scope.get("required_changed_files") or [])
    optional = set(scope.get("optional_changed_files") or [])
    accepted = [set(item) for item in scope.get("accepted_changed_file_sets") or [] if isinstance(item, list)]
    check(required == REQUIRED_FILES, "scope:required", failures)
    check(optional == OPTIONAL_FILES, "scope:optional", failures)
    check(accepted == [REQUIRED_FILES, REQUIRED_FILES | OPTIONAL_FILES], "scope:accepted_sets", failures)
    check(scope.get("runner_or_workflow_changes_forbidden") is True, "scope:no_runner_workflow", failures)
    check(scope.get("schema_migration_forbidden") is True, "scope:no_schema_migration", failures)
    check(scope.get("unlisted_file_change_forbidden") is True, "scope:no_unlisted", failures)

    bindings = value.get("binding_lock") if isinstance(value.get("binding_lock"), dict) else {}
    expected_paths = {
        bindings.get("snapshot_path"),
        bindings.get("proof_path"),
        bindings.get("bindings_path"),
        bindings.get("registry_path"),
        bindings.get("delta_path"),
    }
    check(expected_paths == {
        "site/crypto-astro/data/crypto_astro_snapshot.public.json",
        "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json",
        "site/crypto-astro/data/crypto_astro_module_bindings.public.json",
        "site/crypto-astro/data/crypto_astro_snapshot_registry.public.json",
        "site/crypto-astro/data/crypto_astro_snapshot_delta.public.json",
    }, "bindings:paths", failures)
    check(bindings.get("registry_selection_policy") == "EXPLICIT_ACCEPTED_PAIR", "bindings:selection_policy", failures)
    check(bindings.get("registry_acceptance_status") == "ACCEPTED", "bindings:acceptance", failures)
    check(bindings.get("current_must_descend_from_previous") is True, "bindings:ancestry", failures)
    check(bindings.get("memory_build_twice_byte_identical") is True, "bindings:determinism", failures)
    check(bindings.get("what_changed_render_and_verify_required") is True, "bindings:what_changed", failures)
    check(bindings.get("bhrigu_consumer_contract_required") is True, "bindings:consumer", failures)

    check(value.get("fail_closed_gates") == REQUIRED_FAIL_CODES, "fail_codes:exact", failures)
    sequence = value.get("review_merge_proof_sequence")
    check(isinstance(sequence, list) and len(sequence) == 12, "sequence:length", failures)
    if isinstance(sequence, list):
        joined = "\n".join(sequence)
        for marker in (
            "owner-authenticated refresh dispatch issue",
            "Crypto-Astro Static Refresh Manual",
            "desktop and mobile visual review",
            "Squash merge",
            "owner-authenticated public HTTP proof request",
            "PUBLIC_HTTP_PROOF_PASS",
            "HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH",
        ):
            check(marker in joined, f"sequence:missing:{marker}", failures)

    visual = value.get("visual_review_lock") if isinstance(value.get("visual_review_lock"), dict) else {}
    check(visual.get("desktop_required") is True, "visual:desktop", failures)
    check(visual.get("mobile_required") is True, "visual:mobile", failures)
    check(visual.get("visual_failure_blocks_merge") is True, "visual:block", failures)
    check(visual.get("surfaces") == [
        "https://aibhrigu.github.io/phi-cosmography-open/crypto-astro/index.html",
        "https://www.bhrigu.io/crypto-astro/btc",
    ], "visual:surfaces", failures)

    rollback = value.get("rollback_and_hold") if isinstance(value.get("rollback_and_hold"), dict) else {}
    check(rollback.get("no_push_before_atomic_pass") is True, "rollback:no_push", failures)
    check(rollback.get("no_auto_merge") is True, "rollback:no_auto_merge", failures)
    check(rollback.get("no_deploy_command") is True, "rollback:no_deploy", failures)
    check(rollback.get("automatic_rollback") is False, "rollback:no_automatic", failures)
    check(rollback.get("rollback_requires_separate_authorization") is True, "rollback:separate_auth", failures)
    check(rollback.get("success_hold_state") == "HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH", "rollback:hold", failures)
    check(rollback.get("no_repeat_dispatch_without_new_authorization") is True, "rollback:no_repeat", failures)

    boundary = value.get("boundary") if isinstance(value.get("boundary"), dict) else {}
    check(bool(boundary), "boundary:missing", failures)
    check(all(item is False for item in boundary.values()), "boundary:opened", failures)
    check(value.get("next_safe_node_after_packet_merge") == "CRYPTO_ASTRO_POST_GATE_3_CONTROLLED_REFRESH_OWNER_AUTHENTICATED_DISPATCH_AUTHORIZATION_v0_1", "next_node", failures)
    return failures


def validate_index(text: str) -> list[str]:
    failures: list[str] = []
    markers = [
        "# Crypto-Astro Post-Gate-3 Controlled Refresh Authorization Packet v0.1",
        AUTHORING_BASE_SHA,
        "Refresh execution authorized by this packet: `NO`",
        "defillama_historical_chain_tvl_ex_double_count_v0_1",
        "Do not sum protocols, chains, categories",
        "FAIL_DEFI_TVL_ANOMALY",
        "exactly the following ten files",
        "PUBLIC_HTTP_PROOF_PASS",
        "HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH",
        "DATA_REFRESH_IN_THIS_PACKET=NO",
        "NEXT_SAFE_NODE=CRYPTO_ASTRO_POST_GATE_3_CONTROLLED_REFRESH_OWNER_AUTHENTICATED_DISPATCH_AUTHORIZATION_v0_1",
    ]
    for marker in markers:
        check(marker in text, f"index:missing:{marker}", failures)
    for path in REQUIRED_FILES | OPTIONAL_FILES:
        check(path in text, f"index:missing_path:{path}", failures)
    return failures


def verify_repository(repo: Path) -> dict[str, Any]:
    failures: list[str] = []
    packet_path = repo / PACKET_PATH
    index_path = repo / INDEX_PATH
    if not packet_path.is_file():
        failures.append(f"missing:{PACKET_PATH}")
    else:
        failures.extend(validate_packet(load_packet(packet_path)))
    if not index_path.is_file():
        failures.append(f"missing:{INDEX_PATH}")
    else:
        failures.extend(validate_index(index_path.read_text(encoding="utf-8")))
    return {
        "schema_version": "crypto_astro_post_gate_3_controlled_refresh_authorization_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "repository": REPOSITORY,
        "packet_authoring_base_sha": AUTHORING_BASE_SHA,
        "execution_authorized": False,
        "required_generated_files": sorted(REQUIRED_FILES),
        "optional_generated_files": sorted(OPTIONAL_FILES),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = verify_repository(args.repo.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
