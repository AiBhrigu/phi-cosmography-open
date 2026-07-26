#!/usr/bin/env python3
"""Verify the BTC 2190D checksum-bound walk-forward evidence artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_btc_2190d_corpus import (
    BLOCK_SCHEMA,
    CORRECTION_SCHEMA,
    MANIFEST_SCHEMA,
    PROOF_SCHEMA,
    PROTOCOL_SCHEMA,
    SCHEMA_VERSION,
    SUMMARY_SCHEMA,
    canonical_json_bytes,
    import_base_builder,
    load_design,
    pretty_json_bytes,
    sha256,
    state_payload,
)


class VerificationError(RuntimeError):
    """Fail-closed verification error."""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(repo: Path, evidence_dir: Path, report_path: Path | None = None) -> dict:
    repo = repo.resolve()
    evidence_dir = evidence_dir.resolve()
    base = import_base_builder(repo)
    design = load_design(repo)

    summary = load_json(evidence_dir / "btc_2190d_summary.json")
    manifest = load_json(evidence_dir / "btc_2190d_source_manifest.json")
    protocol = load_json(evidence_dir / "btc_2190d_validation_protocol.json")
    registry = load_json(evidence_dir / "btc_2190d_block_registry.json")
    corrections = load_json(
        evidence_dir / "btc_2190d_source_correction_ledger.json"
    )
    proof = load_json(evidence_dir / "btc_2190d_no_lookahead_proof.json")
    corpus_path = evidence_dir / "btc_2190d_state_corpus.jsonl"
    rows = [
        json.loads(line)
        for line in corpus_path.read_text(encoding="utf-8").splitlines()
    ]

    if summary["schema_version"] != SUMMARY_SCHEMA or summary["status"] != "PASS":
        raise VerificationError("summary contract failed")
    if manifest["schema_version"] != MANIFEST_SCHEMA:
        raise VerificationError("manifest schema failed")
    if protocol["schema_version"] != PROTOCOL_SCHEMA:
        raise VerificationError("protocol schema failed")
    if registry["schema_version"] != BLOCK_SCHEMA:
        raise VerificationError("block registry schema failed")
    if corrections["schema_version"] != CORRECTION_SCHEMA:
        raise VerificationError("correction schema failed")
    if proof["schema_version"] != PROOF_SCHEMA or proof["status"] != "PASS":
        raise VerificationError("proof contract failed")

    if len(rows) != 2190:
        raise VerificationError("state row count failed")
    if rows[0]["observation_date"] != "2020-06-27":
        raise VerificationError("first observation failed")
    if rows[-1]["observation_date"] != "2026-06-25":
        raise VerificationError("last observation failed")
    if len({row["observation_date"] for row in rows}) != 2190:
        raise VerificationError("observation dates are not unique")
    if len({row["state_sha256"] for row in rows}) != 2190:
        raise VerificationError("state hashes are not unique")
    if any(row["schema_version"] != SCHEMA_VERSION for row in rows):
        raise VerificationError("row schema mismatch")

    warmup = [row for row in rows if row["phase"] == "WARMUP"]
    oos = [row for row in rows if row["phase"] == "OUT_OF_SAMPLE"]
    if len(warmup) != 365 or len(oos) != 1825:
        raise VerificationError("phase counts failed")
    if any(row["outcomes"] is not None for row in warmup):
        raise VerificationError("warmup outcomes must be absent")
    if any(
        row["outcomes"]["maturity_status"] != "COMPLETE" for row in oos
    ):
        raise VerificationError("OOS maturity failed")

    expected_block_counts = {
        "WARMUP": 365,
        "OOS_1": 365,
        "OOS_2": 365,
        "OOS_3": 365,
        "OOS_4": 365,
        "OOS_5": 365,
    }
    actual_block_counts = {}
    for row in rows:
        actual_block_counts[row["block_id"]] = (
            actual_block_counts.get(row["block_id"], 0) + 1
        )
    if actual_block_counts != expected_block_counts:
        raise VerificationError("block counts failed")
    if summary["block_counts"] != expected_block_counts:
        raise VerificationError("summary block counts failed")

    for row in rows:
        if sha256(canonical_json_bytes(state_payload(row))) != row["state_sha256"]:
            raise VerificationError(
                f"state hash mismatch: {row['observation_date']}"
            )
        if row["block_id"] == "OOS_5":
            if row["confirmation_eligible"] is not False:
                raise VerificationError("OOS_5 contamination boundary failed")
            if (
                row["block_role"]
                != "DISCOVERY_REFERENCE_EXCLUDED_FROM_CONFIRMATION"
            ):
                raise VerificationError("OOS_5 role failed")
        elif row["block_id"] in {"OOS_1", "OOS_2", "OOS_3", "OOS_4"}:
            if row["confirmation_eligible"] is not True:
                raise VerificationError("replication block eligibility failed")

    if manifest["archive_count"] != 98:
        raise VerificationError("archive count failed")
    if manifest["monthly_archive_count"] != 73:
        raise VerificationError("monthly archive count failed")
    if manifest["daily_archive_count"] != 25:
        raise VerificationError("daily archive count failed")
    if not all(
        item["expected_sha256"] == item["actual_sha256"]
        for item in manifest["archives"]
    ):
        raise VerificationError("source checksum failed")
    if manifest["source_start_date"] != "2020-06-27":
        raise VerificationError("manifest start failed")
    if manifest["source_end_date"] != "2026-07-25":
        raise VerificationError("manifest end failed")

    if protocol["accepted_methodology_id"] != (
        design["frozen_primary_specification"]["methodology_id"]
    ):
        raise VerificationError("methodology id binding failed")
    accepted_methodology_sha = sha256(base.cbytes(base.method()))
    if protocol["accepted_methodology_sha256"] != accepted_methodology_sha:
        raise VerificationError("methodology SHA binding failed")
    if protocol["accepted_methodology_sha256"] != (
        design["source_binding"]["methodology_sha256"]
    ):
        raise VerificationError("design methodology binding failed")
    if protocol["registered_association_hypotheses"] != (
        design["registered_association_hypotheses"]
    ):
        raise VerificationError("registered hypotheses changed")
    if protocol["distribution_boundary"] != design["distribution_boundary"]:
        raise VerificationError("distribution boundary changed")

    prefix = proof["prefix_invariance"]
    if len(prefix) < 25:
        raise VerificationError("prefix proof count failed")
    if any(item["status"] != "PASS" for item in prefix):
        raise VerificationError("prefix proof failed")
    if proof["forward_fields_excluded_from_state_hash"] != "PASS":
        raise VerificationError("forward-field exclusion failed")
    if proof["formula_selection_after_results"] is not False:
        raise VerificationError("formula contamination failed")
    if proof["threshold_optimization_after_results"] is not False:
        raise VerificationError("threshold contamination failed")

    if corrections["silent_overwrite_allowed"] is not False:
        raise VerificationError("silent source overwrite boundary failed")
    if summary["research_claim"] != "RETROSPECTIVE_TEMPORAL_REPLICATION_ONLY":
        raise VerificationError("research claim failed")
    if summary["discovery_reference_used_for_confirmation"] is not False:
        raise VerificationError("discovery confirmation boundary failed")
    if summary["predictive_power_proven"] is not False:
        raise VerificationError("predictive claim boundary failed")
    if summary["public_binding_allowed"] is not False:
        raise VerificationError("public binding boundary failed")
    if summary["commercial_ai_feed_allowed"] is not False:
        raise VerificationError("commercial AI boundary failed")
    if summary["complete_30d_outcome_count"] != 1825:
        raise VerificationError("complete outcome count failed")
    if summary["prefix_invariance_count"] < 25:
        raise VerificationError("summary prefix count failed")

    corpus_bytes = corpus_path.read_bytes()
    if summary["corpus_sha256"] != hashlib.sha256(corpus_bytes).hexdigest():
        raise VerificationError("corpus digest failed")
    if summary["manifest_sha256"] != sha256(pretty_json_bytes(manifest)):
        raise VerificationError("manifest digest failed")
    if summary["protocol_sha256"] != sha256(pretty_json_bytes(protocol)):
        raise VerificationError("protocol digest failed")
    if summary["block_registry_sha256"] != sha256(
        pretty_json_bytes(registry)
    ):
        raise VerificationError("block registry digest failed")

    if list(evidence_dir.glob("*.zip")) or list(evidence_dir.glob("*.csv")):
        raise VerificationError("raw archives must not be published")

    report = {
        "schema_version": "btc_2190d_walk_forward_verification_v0_1",
        "status": "PASS",
        "state_rows": len(rows),
        "warmup_rows": len(warmup),
        "out_of_sample_rows": len(oos),
        "complete_30d_outcomes": summary["complete_30d_outcome_count"],
        "archive_checksums": "PASS_98_OF_98",
        "monthly_archives": manifest["monthly_archive_count"],
        "daily_archives": manifest["daily_archive_count"],
        "block_counts": actual_block_counts,
        "prefix_invariance_count": len(prefix),
        "discovery_reference_excluded": "PASS",
        "methodology_binding": "PASS",
        "registered_hypotheses_binding": "PASS",
        "correction_memory": "PASS",
        "raw_archive_publication": "NO",
        "predictive_claim": "NO",
        "public_binding": "NO",
        "commercial_ai_feed": "NO",
        "corpus_sha256": summary["corpus_sha256"],
        "manifest_sha256": summary["manifest_sha256"],
        "protocol_sha256": summary["protocol_sha256"],
        "block_registry_sha256": summary["block_registry_sha256"],
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            verify(args.repo, args.evidence_dir, args.report),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
