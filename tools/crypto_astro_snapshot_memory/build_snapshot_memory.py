#!/usr/bin/env python3
"""Squash-merge-safe facade over the byte-locked Snapshot Memory v0.2 core."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import types
from pathlib import Path
from typing import Any

LEGACY_BLOB_SHA = "e10641780e88dac648c9bb2daba89aee815cdc69"


def _load_legacy() -> types.ModuleType:
    repo = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "cat-file", "blob", LEGACY_BLOB_SHA],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("PROVENANCE_COMMIT_MISSING: legacy Snapshot Memory core blob")
    module = types.ModuleType("_crypto_astro_snapshot_memory_legacy_v0_2")
    module.__file__ = f"git-blob:{LEGACY_BLOB_SHA}"
    sys.modules[module.__name__] = module
    exec(compile(result.stdout, module.__file__, "exec"), module.__dict__)
    return module


_legacy = _load_legacy()
for _name, _value in vars(_legacy).items():
    if not _name.startswith("__"):
        globals().setdefault(_name, _value)


def _locked_hash_check(bundle: SnapshotBundle, locked: dict[str, Any], code: str) -> None:
    observed = entry(bundle)
    for key in (
        "snapshot_blob_sha", "snapshot_sha256", "proof_blob_sha", "proof_sha256",
        "bindings_blob_sha", "bindings_sha256", "generated_at_utc",
        "proof_generated_at_utc", "source_mode", "schema_version", "acceptance_status",
    ):
        if locked.get(key) != observed.get(key):
            raise ContractError(code, f"{bundle.role} {key}")


def validate_base_materialization(
    repo: Path, role: str, locked: dict[str, Any], materialization_ref: str
) -> SnapshotBundle:
    resolved = resolve_ref(repo, materialization_ref)
    bundle = make_bundle(
        role=role,
        commit_sha=str(locked.get("commit_sha") or resolved),
        data_origin_commit_sha=resolved,
        runner_blob_sha=str(locked.get("runner_blob_sha") or ""),
        snapshot_bytes=git_show(repo, resolved, SNAPSHOT_PATH),
        proof_bytes=git_show(repo, resolved, PROOF_PATH),
        bindings_bytes=git_show(repo, resolved, BINDINGS_PATH),
    )
    _locked_hash_check(bundle, locked, "BASE_MATERIALIZATION_HASH_MISMATCH")
    return bundle


def bundle_from_entry(repo: Path, role: str, locked: dict[str, Any]) -> SnapshotBundle:
    commit_sha = str(locked.get("commit_sha") or "")
    data_origin = str(locked.get("data_origin_commit_sha") or "")
    if len(commit_sha) != 40 or len(data_origin) != 40:
        raise ContractError("PROVENANCE_COMMIT_MISSING", f"{role} commit")
    try:
        snapshot = git_show(repo, commit_sha, SNAPSHOT_PATH)
        proof = git_show(repo, commit_sha, PROOF_PATH)
        bindings = git_show(repo, commit_sha, BINDINGS_PATH)
        runner = git_show(repo, commit_sha, RUNNER_PATH)
    except ContractError as exc:
        raise ContractError("PROVENANCE_COMMIT_MISSING", f"{role} {commit_sha}") from exc
    bundle = make_bundle(
        role=role,
        commit_sha=commit_sha,
        data_origin_commit_sha=data_origin,
        runner_blob_sha=git_blob_sha(runner),
        snapshot_bytes=snapshot,
        proof_bytes=proof,
        bindings_bytes=bindings,
    )
    observed = entry(bundle)
    for key in (
        "snapshot_blob_sha", "snapshot_sha256", "proof_blob_sha", "proof_sha256",
        "bindings_blob_sha", "bindings_sha256", "generated_at_utc",
        "proof_generated_at_utc", "source_mode", "schema_version", "acceptance_status",
    ):
        if locked.get(key) != observed.get(key):
            raise ContractError("PROVENANCE_HASH_MISMATCH", f"{role} {key}")
    if locked.get("runner_blob_sha") != observed.get("runner_blob_sha"):
        raise ContractError("PROVENANCE_HASH_MISMATCH", f"{role} runner_blob_sha")
    if not is_ancestor(repo, data_origin, commit_sha):
        raise ContractError("TRANSACTION_ANCESTRY_INVALID", f"{role} data origin")
    return bundle


def bundle_from_ref(
    repo: Path, role: str, ref: str, *, data_origin_ref: str | None = None
) -> SnapshotBundle:
    commit_sha = resolve_ref(repo, ref)
    data_origin = resolve_ref(repo, data_origin_ref or ref)
    return make_bundle(
        role=role,
        commit_sha=commit_sha,
        data_origin_commit_sha=data_origin,
        runner_blob_sha=git_blob_sha(git_show(repo, commit_sha, RUNNER_PATH)),
        snapshot_bytes=git_show(repo, commit_sha, SNAPSHOT_PATH),
        proof_bytes=git_show(repo, commit_sha, PROOF_PATH),
        bindings_bytes=git_show(repo, commit_sha, BINDINGS_PATH),
    )


def load_pair(repo: Path, *, base_ref: str | None = None, current_ref: str | None = None):
    if bool(base_ref) != bool(current_ref):
        raise ContractError("SCHEMA_MISMATCH", "base-ref and current-ref must be supplied together")
    if base_ref and current_ref:
        base_sha = resolve_ref(repo, base_ref)
        base_registry = load_registry_at_ref(repo, base_sha)
        locked_previous = base_registry.get("current") or {}
        previous = bundle_from_entry(repo, "previous", locked_previous)
        validate_base_materialization(repo, "previous", locked_previous, base_sha)
        current = bundle_from_ref(repo, "current", current_ref, data_origin_ref=base_sha)
        transaction_ok = is_ancestor(repo, base_sha, current.commit_sha)
    else:
        registry = parse_json((repo / REGISTRY_PATH).read_bytes(), "committed registry")
        current_locked = registry.get("current") or {}
        previous_locked = registry.get("previous") or {}
        current = bundle_from_entry(repo, "current", current_locked)
        previous = bundle_from_entry(repo, "previous", previous_locked)
        validate_base_materialization(
            repo, "previous", previous_locked, current.data_origin_commit_sha
        )
        transaction_ok = is_ancestor(
            repo, current.data_origin_commit_sha, current.commit_sha
        )
    return current, previous, transaction_ok


def build_documents(current: SnapshotBundle, previous: SnapshotBundle, *, ancestry_ok: bool):
    if not ancestry_ok:
        raise ContractError(
            "TRANSACTION_ANCESTRY_INVALID",
            "accepted base materialization is not ancestor of current data commit",
        )
    return _legacy.build_documents(current, previous, ancestry_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--base-ref")
    parser.add_argument("--current-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    current, previous, transaction_ok = load_pair(
        repo, base_ref=args.base_ref, current_ref=args.current_ref
    )
    registry, delta = build_documents(current, previous, ancestry_ok=transaction_ok)
    write_documents(args.out_dir.resolve(), registry, delta)
    print(json.dumps({
        "status": "PASS",
        "registry_path": REGISTRY_PATH,
        "delta_path": DELTA_PATH,
        "current_snapshot_id": registry["current"]["snapshot_id"],
        "previous_snapshot_id": registry["previous"]["snapshot_id"],
        "comparison_status": delta["comparison_status"],
        "comparable_metrics": sorted(delta["metrics"]),
        "unavailable_metrics": sorted(delta["unavailable_metrics"]),
        "provenance_hashes": "PASS",
        "base_materialization_hashes": "PASS",
        "transaction_base_ancestry": "PASS",
        "network_requests": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
