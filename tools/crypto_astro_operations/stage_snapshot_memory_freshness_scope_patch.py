#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_BLOB_SHA = "d4cdae9a33edeec8b59d037f0b356d90b50d090e"
PATCHED_GIT_BLOB_SHA = "ecfeb9d8df18d316f5fc4f72beeb3d442bd2d296"
PATCHED_SHA256 = "407b37d48d17a26af2f21a93b6a33ede077a94656835acaea75c8fb472a0d7b4"


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return value.replace(old, new, 1)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def build_patch(source: Path, output: Path, report_path: Path) -> None:
    original = source.read_text(encoding="utf-8")
    source_bytes = original.encode()
    actual_source_blob = git_blob_sha(source_bytes)
    if actual_source_blob != SOURCE_BLOB_SHA:
        raise RuntimeError(f"source blob drift: {actual_source_blob}")

    scope_sets = (
        "          freshness_policy_scope = {\n"
        "            'docs/crypto-astro-service/CRYPTO_ASTRO_OPERATIONAL_CADENCE_v0_1.md',\n"
        "            'docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json',\n"
        "            'tools/crypto_astro_operations/test_verify_operational_cadence.py',\n"
        "            'tools/crypto_astro_operations/verify_operational_cadence.py',\n"
        "          }\n"
        "          freshness_policy_scope_applicability_repair = {\n"
        "            '.github/workflows/crypto-astro-snapshot-memory-pr.yml',\n"
        "          }\n"
    )

    patched = replace_once(
        original,
        "          generated = {\n",
        scope_sets + "          generated = {\n",
        "scope set insertion",
    )
    patched = replace_once(
        patched,
        "          elif changed == consumer_repair:\n"
        "            mode='bhrigu_consumer_contract_repair'\n"
        "          elif changed in (generated, generated | optional):\n",
        "          elif changed == consumer_repair:\n"
        "            mode='bhrigu_consumer_contract_repair'\n"
        "          elif changed == freshness_policy_scope:\n"
        "            mode='freshness_policy_scope'\n"
        "            print('SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE=PASS')\n"
        "          elif changed == freshness_policy_scope_applicability_repair:\n"
        "            mode='freshness_policy_scope_applicability_repair'\n"
        "            print('SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE_APPLICABILITY_REPAIR=PASS')\n"
        "          elif changed in (generated, generated | optional):\n",
        "classification insertion",
    )
    patched = replace_once(
        patched,
        "              'consumer_repair_missing':sorted(consumer_repair-changed),\n"
        "              'generated_missing':sorted(generated-changed),\n",
        "              'consumer_repair_missing':sorted(consumer_repair-changed),\n"
        "              'freshness_policy_scope_missing':sorted(freshness_policy_scope-changed),\n"
        "              'freshness_policy_scope_applicability_repair_missing':sorted(freshness_policy_scope_applicability_repair-changed),\n"
        "              'generated_missing':sorted(generated-changed),\n",
        "missing diagnostics insertion",
    )
    patched = replace_once(
        patched,
        "              'unexpected':sorted(changed-implementation-squash_merge_ancestry_repair-runtime_registry_test_repair-workflow_applicability_repair-btc_phi_semantic_geometry-public_service_truth_alignment-producer_public_identity-timestamp_consistency_repair-maintenance-cadence_maintenance-assistant_dispatch_maintenance-consumer_repair-generated-optional),\n",
        "              'unexpected':sorted(changed-implementation-squash_merge_ancestry_repair-runtime_registry_test_repair-workflow_applicability_repair-btc_phi_semantic_geometry-public_service_truth_alignment-producer_public_identity-timestamp_consistency_repair-maintenance-cadence_maintenance-assistant_dispatch_maintenance-consumer_repair-freshness_policy_scope-freshness_policy_scope_applicability_repair-generated-optional),\n",
        "unexpected diagnostics alignment",
    )

    required_tokens = (
        "mode='freshness_policy_scope'",
        "SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE=PASS",
        "mode='freshness_policy_scope_applicability_repair'",
        "SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE_APPLICABILITY_REPAIR=PASS",
    )
    for token in required_tokens:
        if patched.count(token) != 1:
            raise RuntimeError(f"required token count drift: {token!r} -> {patched.count(token)}")
    if patched == original:
        raise RuntimeError("patch produced no change")

    patched_bytes = patched.encode()
    actual_blob = git_blob_sha(patched_bytes)
    actual_sha256 = hashlib.sha256(patched_bytes).hexdigest()
    if actual_blob != PATCHED_GIT_BLOB_SHA:
        raise RuntimeError(f"patched git blob drift: {actual_blob}")
    if actual_sha256 != PATCHED_SHA256:
        raise RuntimeError(f"patched sha256 drift: {actual_sha256}")

    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(patched_bytes)
    report = {
        "status": "PASS",
        "node": "CRYPTO_ASTRO_SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE_APPLICABILITY_REPAIR_v0_1",
        "source_blob_sha": SOURCE_BLOB_SHA,
        "patched_git_blob_sha": PATCHED_GIT_BLOB_SHA,
        "patched_sha256": PATCHED_SHA256,
        "changed_repository_files_after_apply": [
            ".github/workflows/crypto-astro-snapshot-memory-pr.yml"
        ],
        "freshness_policy_scope_files": [
            "docs/crypto-astro-service/CRYPTO_ASTRO_OPERATIONAL_CADENCE_v0_1.md",
            "docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json",
            "tools/crypto_astro_operations/test_verify_operational_cadence.py",
            "tools/crypto_astro_operations/verify_operational_cadence.py",
        ],
        "snapshot_data_changed": False,
        "memory_artifacts_changed": False,
        "target_pr_merge_authorized": False,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    build_patch(args.source, args.output, args.report)
    print("SNAPSHOT_MEMORY_FRESHNESS_SCOPE_PATCH_STAGE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
