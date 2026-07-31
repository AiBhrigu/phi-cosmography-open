#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_BLOBS = {
    ".github/workflows/crypto-astro-snapshot-memory-pr.yml": "d4cdae9a33edeec8b59d037f0b356d90b50d090e",
    ".github/workflows/crypto-astro-assistant-dispatch-pr.yml": "5403a527dd477f089a64eacb64d2d0a1872817c9",
    ".github/workflows/crypto-astro-operational-cadence-pr.yml": "db8761d88290639e27381cd773e2e112c4776157",
}
FRESHNESS_POLICY_FILES = (
    "docs/crypto-astro-service/CRYPTO_ASTRO_OPERATIONAL_CADENCE_v0_1.md",
    "docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json",
    "tools/crypto_astro_operations/test_verify_operational_cadence.py",
    "tools/crypto_astro_operations/verify_operational_cadence.py",
)


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return value.replace(old, new, 1)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def verify_source(path: Path, expected_blob: str) -> str:
    text = path.read_text(encoding="utf-8")
    actual = git_blob_sha(text.encode())
    if actual != expected_blob:
        raise RuntimeError(f"source blob drift for {path}: {actual}")
    return text


def freshness_set(indent: str, quote: str) -> str:
    lines = [f"{indent}freshness_policy_scope = {{"]
    lines.extend(f"{indent}    {quote}{path}{quote}," for path in FRESHNESS_POLICY_FILES)
    lines.append(f"{indent}}}")
    return "\n".join(lines) + "\n"


def patch_snapshot(text: str) -> str:
    sets = freshness_set("          ", "'") + (
        "          freshness_policy_scope_applicability_repair = {\n"
        "            '.github/workflows/crypto-astro-snapshot-memory-pr.yml',\n"
        "          }\n"
    )
    text = replace_once(text, "          generated = {\n", sets + "          generated = {\n", "snapshot sets")
    text = replace_once(
        text,
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
        "snapshot classifier",
    )
    text = replace_once(
        text,
        "              'consumer_repair_missing':sorted(consumer_repair-changed),\n"
        "              'generated_missing':sorted(generated-changed),\n",
        "              'consumer_repair_missing':sorted(consumer_repair-changed),\n"
        "              'freshness_policy_scope_missing':sorted(freshness_policy_scope-changed),\n"
        "              'freshness_policy_scope_applicability_repair_missing':sorted(freshness_policy_scope_applicability_repair-changed),\n"
        "              'generated_missing':sorted(generated-changed),\n",
        "snapshot diagnostics",
    )
    text = replace_once(
        text,
        "              'unexpected':sorted(changed-implementation-squash_merge_ancestry_repair-runtime_registry_test_repair-workflow_applicability_repair-btc_phi_semantic_geometry-public_service_truth_alignment-producer_public_identity-timestamp_consistency_repair-maintenance-cadence_maintenance-assistant_dispatch_maintenance-consumer_repair-generated-optional),\n",
        "              'unexpected':sorted(changed-implementation-squash_merge_ancestry_repair-runtime_registry_test_repair-workflow_applicability_repair-btc_phi_semantic_geometry-public_service_truth_alignment-producer_public_identity-timestamp_consistency_repair-maintenance-cadence_maintenance-assistant_dispatch_maintenance-consumer_repair-freshness_policy_scope-freshness_policy_scope_applicability_repair-generated-optional),\n",
        "snapshot unexpected",
    )
    return text


def patch_assistant(text: str) -> str:
    text = replace_once(
        text,
        "          btc_phi_semantic_geometry_scope = {\n",
        freshness_set("          ", '"') + "          btc_phi_semantic_geometry_scope = {\n",
        "assistant set",
    )
    text = replace_once(
        text,
        "          elif changed == btc_phi_semantic_geometry_scope:\n"
        "              mode = \"btc_phi_semantic_geometry\"\n",
        "          elif changed == freshness_policy_scope:\n"
        "              mode = \"freshness_policy_scope\"\n"
        "              print(\"ASSISTANT_DISPATCH_FRESHNESS_POLICY_SCOPE=PASS\")\n"
        "          elif changed == btc_phi_semantic_geometry_scope:\n"
        "              mode = \"btc_phi_semantic_geometry\"\n",
        "assistant classifier",
    )
    text = replace_once(
        text,
        "                  \"workflow_applicability_repair_missing\": sorted(\n"
        "                      workflow_applicability_repair_scope - changed\n"
        "                  ),\n"
        "                  \"btc_phi_semantic_geometry_missing\": sorted(\n",
        "                  \"workflow_applicability_repair_missing\": sorted(\n"
        "                      workflow_applicability_repair_scope - changed\n"
        "                  ),\n"
        "                  \"freshness_policy_scope_missing\": sorted(\n"
        "                      freshness_policy_scope - changed\n"
        "                  ),\n"
        "                  \"btc_phi_semantic_geometry_missing\": sorted(\n",
        "assistant diagnostics",
    )
    text = replace_once(
        text,
        "                      - workflow_applicability_repair_scope\n"
        "                      - btc_phi_semantic_geometry_scope\n",
        "                      - workflow_applicability_repair_scope\n"
        "                      - freshness_policy_scope\n"
        "                      - btc_phi_semantic_geometry_scope\n",
        "assistant unexpected",
    )
    return text


def patch_cadence(text: str) -> str:
    text = replace_once(
        text,
        "          btc_phi_semantic_geometry_scope = {\n",
        freshness_set("          ", '"') + "          btc_phi_semantic_geometry_scope = {\n",
        "cadence set",
    )
    text = replace_once(
        text,
        "          elif changed == btc_phi_semantic_geometry_scope:\n"
        "              print(\"BTC_PHI_SEMANTIC_GEOMETRY_FILE_SCOPE=PASS\")\n",
        "          elif changed == freshness_policy_scope:\n"
        "              print(\"OPERATIONAL_CADENCE_FRESHNESS_POLICY_SCOPE=PASS\")\n"
        "          elif changed == btc_phi_semantic_geometry_scope:\n"
        "              print(\"BTC_PHI_SEMANTIC_GEOMETRY_FILE_SCOPE=PASS\")\n",
        "cadence classifier",
    )
    text = replace_once(
        text,
        "              print(\"PRODUCER_IDENTITY_BTC_ROUTE_SOVEREIGNTY_PREREQUISITE=PASS\")\n",
        "              print(\"PRODUCER_IDENTITY_BTC_ROUTE_SOVEREIGNTY_PREREQUISITE=PASS\")\n"
        "              print(\"SNAPSHOT_MEMORY_FRESHNESS_POLICY_CROSS_WORKFLOW_APPLICABILITY=PASS\")\n",
        "cadence cross-workflow receipt",
    )
    return text


def write_output(repo: Path, out_dir: Path, report_path: Path) -> None:
    patchers = {
        ".github/workflows/crypto-astro-snapshot-memory-pr.yml": patch_snapshot,
        ".github/workflows/crypto-astro-assistant-dispatch-pr.yml": patch_assistant,
        ".github/workflows/crypto-astro-operational-cadence-pr.yml": patch_cadence,
    }
    records: dict[str, dict[str, str]] = {}
    for rel_path, patcher in patchers.items():
        source = repo / rel_path
        original = verify_source(source, SOURCE_BLOBS[rel_path])
        patched = patcher(original)
        if patched == original:
            raise RuntimeError(f"patch produced no change: {rel_path}")
        output = out_dir / rel_path
        output.parent.mkdir(parents=True, exist_ok=True)
        data = patched.encode()
        output.write_bytes(data)
        records[rel_path] = {
            "source_blob_sha": SOURCE_BLOBS[rel_path],
            "patched_git_blob_sha": git_blob_sha(data),
            "patched_sha256": hashlib.sha256(data).hexdigest(),
        }

    required = {
        ".github/workflows/crypto-astro-snapshot-memory-pr.yml": (
            "SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE=PASS",
            "SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE_APPLICABILITY_REPAIR=PASS",
        ),
        ".github/workflows/crypto-astro-assistant-dispatch-pr.yml": (
            "ASSISTANT_DISPATCH_FRESHNESS_POLICY_SCOPE=PASS",
        ),
        ".github/workflows/crypto-astro-operational-cadence-pr.yml": (
            "OPERATIONAL_CADENCE_FRESHNESS_POLICY_SCOPE=PASS",
            "SNAPSHOT_MEMORY_FRESHNESS_POLICY_CROSS_WORKFLOW_APPLICABILITY=PASS",
        ),
    }
    for rel_path, tokens in required.items():
        value = (out_dir / rel_path).read_text(encoding="utf-8")
        for token in tokens:
            if value.count(token) != 1:
                raise RuntimeError(f"token drift in {rel_path}: {token}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PASS",
        "node": "CRYPTO_ASTRO_SNAPSHOT_MEMORY_FRESHNESS_POLICY_SCOPE_APPLICABILITY_REPAIR_v0_1",
        "repair_scope": sorted(patchers),
        "freshness_policy_scope_files": list(FRESHNESS_POLICY_FILES),
        "files": records,
        "snapshot_data_changed": False,
        "memory_artifacts_changed": False,
        "runtime_changed": False,
        "target_pr_merge_authorized": False,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    write_output(args.repo, args.out_dir, args.report)
    print("SNAPSHOT_MEMORY_FRESHNESS_CROSS_WORKFLOW_STAGE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
