#!/usr/bin/env python3
"""Verify committed Snapshot Memory against provenance and accepted materialization truth."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

from build_snapshot_memory import (
    DELTA_PATH, REGISTRY_PATH, TRACKED_METRICS, build_documents, json_bytes,
    load_pair, write_documents,
)

FORBIDDEN_IMPORT_ROOTS = {"urllib", "requests", "http", "socket", "aiohttp"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_no_network_imports(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".", 1)[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            names = {(node.module or "").split(".", 1)[0]}
        else:
            continue
        overlap = names & FORBIDDEN_IMPORT_ROOTS
        if overlap:
            raise AssertionError(f"network import forbidden in {path}: {sorted(overlap)}")


def verify(repo: Path, report_path: Path | None = None) -> dict:
    current, previous, transaction_ok = load_pair(repo)
    registry, delta = build_documents(current, previous, ancestry_ok=transaction_ok)

    registry_schema = load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot_registry.public.schema.json")
    delta_schema = load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot_delta.public.schema.json")
    Draft202012Validator.check_schema(registry_schema)
    Draft202012Validator.check_schema(delta_schema)
    Draft202012Validator(registry_schema).validate(registry)
    Draft202012Validator(delta_schema).validate(delta)

    committed_registry = (repo / REGISTRY_PATH).read_bytes()
    committed_delta = (repo / DELTA_PATH).read_bytes()
    if committed_registry != json_bytes(registry):
        raise AssertionError("committed registry differs from deterministic build")
    if committed_delta != json_bytes(delta):
        raise AssertionError("committed delta differs from deterministic build")

    with tempfile.TemporaryDirectory() as temp_a, tempfile.TemporaryDirectory() as temp_b:
        out_a, out_b = Path(temp_a), Path(temp_b)
        write_documents(out_a, registry, delta)
        registry2, delta2 = build_documents(current, previous, ancestry_ok=transaction_ok)
        write_documents(out_b, registry2, delta2)
        for relative in (REGISTRY_PATH, DELTA_PATH):
            if (out_a / relative).read_bytes() != (out_b / relative).read_bytes():
                raise AssertionError(f"non-deterministic output: {relative}")

    metrics = set(delta["metrics"])
    unavailable = set(delta["unavailable_metrics"])
    assert metrics | unavailable == set(TRACKED_METRICS)
    assert not (metrics & unavailable)
    expected_status = "FULL_COMPARABLE" if len(metrics) == len(TRACKED_METRICS) else \
                      "PARTIAL_COMPARABLE" if metrics else "UNAVAILABLE"
    assert delta["comparison_status"] == expected_status

    for relative in (
        "tools/crypto_astro_snapshot_memory/build_snapshot_memory.py",
        "tools/crypto_astro_snapshot_memory/verify_snapshot_memory.py",
    ):
        validate_no_network_imports(repo / relative)

    report = {
        "schema_version": "crypto_astro_snapshot_memory_verification_v0_2",
        "status": "PASS",
        "registry_schema": "PASS",
        "delta_schema": "PASS",
        "locked_source_hashes": "PASS",
        "provenance_hashes": "PASS",
        "base_materialization_hashes": "PASS",
        "transaction_base_ancestry": "PASS",
        "deterministic_double_build": "PASS",
        "metric_partition": "PASS",
        "per_metric_fail_closed": "PASS",
        "zero_network_imports": "PASS",
        "comparison_status": delta["comparison_status"],
        "comparable_metric_count": len(metrics),
        "unavailable_metric_count": len(unavailable),
        "registry_sha256": hashlib.sha256(committed_registry).hexdigest(),
        "delta_sha256": hashlib.sha256(committed_delta).hexdigest(),
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo.resolve(), args.report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
