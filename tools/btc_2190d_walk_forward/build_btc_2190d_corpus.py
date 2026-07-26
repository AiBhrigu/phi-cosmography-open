#!/usr/bin/env python3
"""Build the frozen-methodology BTC 2190D walk-forward research corpus."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType

BASE_BUILDER_REL = Path("tools/btc_730d_longitudinal_evidence/build_btc_730d_corpus.py")
DESIGN_REL = Path("docs/crypto-astro-service/btc_2190d_walk_forward_validation_design_v0_1.json")
EXPECTED_BASE_BLOB_SHA1 = "8a82aaeac13d59ad4a82a0af60c7d96b7172bbc3"
EXPECTED_DESIGN_BLOB_SHA1 = "60dbebd6db6e0877967ebde5a762488b2a45fe10"
SCHEMA_VERSION = "btc_2190d_walk_forward_evidence_v0_1"
SUMMARY_SCHEMA = "btc_2190d_walk_forward_summary_v0_1"
MANIFEST_SCHEMA = "btc_2190d_source_manifest_v0_1"
PROOF_SCHEMA = "btc_2190d_no_lookahead_proof_v0_1"
BLOCK_SCHEMA = "btc_2190d_block_registry_v0_1"
PROTOCOL_SCHEMA = "btc_2190d_validation_protocol_v0_1"
CORRECTION_SCHEMA = "btc_2190d_source_correction_ledger_v0_1"


class WalkForwardError(RuntimeError):
    """Fail-closed implementation error."""


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(value) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def pretty_json_bytes(value) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def import_base_builder(repo: Path) -> ModuleType:
    path = repo / BASE_BUILDER_REL
    if git_blob_sha1(path) != EXPECTED_BASE_BLOB_SHA1:
        raise WalkForwardError("accepted 730D builder binding changed")
    spec = importlib.util.spec_from_file_location("btc_730d_frozen_builder", path)
    if spec is None or spec.loader is None:
        raise WalkForwardError("cannot load accepted 730D builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_design(repo: Path) -> dict:
    path = repo / DESIGN_REL
    if git_blob_sha1(path) != EXPECTED_DESIGN_BLOB_SHA1:
        raise WalkForwardError("accepted 2190D design binding changed")
    design = load_json(path)
    if design.get("status") != "DESIGN_LOCKED":
        raise WalkForwardError("design is not locked")
    if design["window"] != {
        "archive_plan": {
            "daily_archives": 25,
            "monthly_archives": 73,
            "total_archives": 98,
        },
        "maturity_tail_days": 30,
        "oos_blocks": design["window"]["oos_blocks"],
        "oos_days": 1825,
        "source_tail_end_date": "2026-07-25",
        "state_days": 2190,
        "state_end_date": "2026-06-25",
        "state_start_date": "2020-06-27",
        "warmup": {
            "days": 365,
            "end_date": "2021-06-26",
            "start_date": "2020-06-27",
        },
    }:
        raise WalkForwardError("design window contract changed")
    if len(design["window"]["oos_blocks"]) != 5:
        raise WalkForwardError("expected five OOS blocks")
    if design["contamination_control"] != {
        "discovery_reference_block": "OOS_5",
        "discovery_reference_used_for_confirmation": False,
        "future_untouched_block_required": "OOS_6_2026-06-26_TO_2027-06-25",
        "retrospective_replication_blocks": ["OOS_1", "OOS_2", "OOS_3", "OOS_4"],
        "retrospective_replication_is_prospective_confirmation": False,
    }:
        raise WalkForwardError("contamination control changed")
    return design


def parse_date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise WalkForwardError(f"noncanonical date: {value}")
    return parsed


def block_registry(design: dict) -> dict:
    warmup = design["window"]["warmup"]
    blocks = [
        {
            "block_id": "WARMUP",
            "phase": "WARMUP",
            "role": "WARMUP_ONLY",
            "start_date": warmup["start_date"],
            "end_date": warmup["end_date"],
            "days": warmup["days"],
            "confirmation_eligible": False,
        }
    ]
    for block in design["window"]["oos_blocks"]:
        blocks.append(
            {
                **block,
                "phase": "OUT_OF_SAMPLE",
                "confirmation_eligible": block["block_id"]
                in design["contamination_control"]["retrospective_replication_blocks"],
            }
        )
    return {
        "schema_version": BLOCK_SCHEMA,
        "status": "PASS",
        "blocks": blocks,
        "retrospective_confirmation_blocks": design["contamination_control"][
            "retrospective_replication_blocks"
        ],
        "discovery_reference_block": design["contamination_control"][
            "discovery_reference_block"
        ],
        "discovery_reference_used_for_confirmation": False,
        "future_untouched_block_required": design["contamination_control"][
            "future_untouched_block_required"
        ],
    }


def classify_day(observation_day: date, registry: dict) -> dict:
    matches = []
    for block in registry["blocks"]:
        start = parse_date(block["start_date"])
        end = parse_date(block["end_date"])
        if start <= observation_day <= end:
            matches.append(block)
    if len(matches) != 1:
        raise WalkForwardError(
            f"day must map to exactly one registered block: {observation_day}"
        )
    return matches[0]


def state_payload(item: dict) -> dict:
    return {
        key: item[key]
        for key in (
            "observation_date",
            "phase",
            "block_id",
            "block_role",
            "confirmation_eligible",
            "source",
            "input_max_timestamp_utc",
            "methodology_id",
            "methodology_sha256",
            "metrics",
        )
    }


def prefix_indices(state_count: int, minimum: int) -> list[int]:
    if minimum < 2 or state_count < minimum:
        raise WalkForwardError("invalid prefix-invariance request")
    last = state_count - 1
    values = {round(index * last / (minimum - 1)) for index in range(minimum)}
    values.add(365)
    values.add(last)
    ordered = sorted(value for value in values if 0 <= value < state_count)
    if len(ordered) < minimum:
        raise WalkForwardError("insufficient unique prefix points")
    return ordered


def validation_protocol(design: dict, base) -> dict:
    accepted_methodology = base.method()
    accepted_methodology_sha = sha256(base.cbytes(accepted_methodology))
    expected_methodology_sha = design["source_binding"]["methodology_sha256"]
    if accepted_methodology_sha != expected_methodology_sha:
        raise WalkForwardError("accepted methodology SHA-256 changed")
    if accepted_methodology["methodology_id"] != design[
        "frozen_primary_specification"
    ]["methodology_id"]:
        raise WalkForwardError("accepted methodology id changed")
    return {
        "schema_version": PROTOCOL_SCHEMA,
        "status": "PASS",
        "purpose": design["purpose"],
        "design_schema_version": design["schema_version"],
        "design_blob_sha1": EXPECTED_DESIGN_BLOB_SHA1,
        "base_builder_blob_sha1": EXPECTED_BASE_BLOB_SHA1,
        "accepted_methodology_id": accepted_methodology["methodology_id"],
        "accepted_methodology_sha256": accepted_methodology_sha,
        "frozen_metrics": design["frozen_primary_specification"]["metrics"],
        "frozen_label_families": design["frozen_primary_specification"][
            "label_families"
        ],
        "registered_association_hypotheses": design[
            "registered_association_hypotheses"
        ],
        "distribution_boundary": design["distribution_boundary"],
        "decision_ladder": design["decision_ladder"],
        "no_lookahead": design["no_lookahead"],
    }


def build_corpus(source_rows: list[dict], design: dict, base):
    start = parse_date(design["window"]["state_start_date"])
    end = parse_date(design["window"]["state_end_date"])
    state_rows = [row for row in source_rows if start <= row["day"] <= end]
    if len(state_rows) != design["window"]["state_days"]:
        raise WalkForwardError("state row count mismatch")
    expected_days = list(base.days(start, end))
    if [row["day"] for row in state_rows] != expected_days:
        raise WalkForwardError("state window is not contiguous")

    registry = block_registry(design)
    protocol = validation_protocol(design, base)
    methodology_id = protocol["accepted_methodology_id"]
    methodology_sha = protocol["accepted_methodology_sha256"]
    source_index = {row["day"]: index for index, row in enumerate(source_rows)}
    output = []

    for row in state_rows:
        index = source_index[row["day"]]
        block = classify_day(row["day"], registry)
        item = {
            "schema_version": SCHEMA_VERSION,
            "observation_date": row["day"].isoformat(),
            "phase": block["phase"],
            "block_id": block["block_id"],
            "block_role": block["role"],
            "confirmation_eligible": block["confirmation_eligible"],
            "source": {
                "provider": "BINANCE_PUBLIC_DATA",
                "market": "BTCUSDT_SPOT",
                "interval": "1d",
                "archive_id": row["archive_id"],
                "archive_sha256": row["archive_sha256"],
            },
            "input_max_timestamp_utc": row["close_time"],
            "methodology_id": methodology_id,
            "methodology_sha256": methodology_sha,
            "metrics": base.metrics(source_rows, index),
            "outcomes": None
            if block["phase"] == "WARMUP"
            else base.forward(source_rows, index),
        }
        item["state_sha256"] = sha256(canonical_json_bytes(state_payload(item)))
        output.append(item)

    prefix_checks = []
    for position in prefix_indices(
        len(state_rows), design["no_lookahead"]["prefix_invariance_points_minimum"]
    ):
        source_position = source_index[state_rows[position]["day"]]
        full_metrics = base.metrics(source_rows, source_position)
        prefix_metrics = base.metrics(
            source_rows[: source_position + 1], source_position
        )
        status = (
            "PASS"
            if canonical_json_bytes(full_metrics)
            == canonical_json_bytes(prefix_metrics)
            else "FAIL"
        )
        prefix_checks.append(
            {
                "observation_date": state_rows[position]["day"].isoformat(),
                "state_position": position,
                "status": status,
            }
        )
        if status != "PASS":
            raise WalkForwardError("prefix invariance failed")

    proof = {
        "schema_version": PROOF_SCHEMA,
        "status": "PASS",
        "state_rows": len(output),
        "warmup_rows": sum(item["phase"] == "WARMUP" for item in output),
        "out_of_sample_rows": sum(
            item["phase"] == "OUT_OF_SAMPLE" for item in output
        ),
        "forward_fields_excluded_from_state_hash": "PASS",
        "prefix_invariance_minimum": design["no_lookahead"][
            "prefix_invariance_points_minimum"
        ],
        "prefix_invariance": prefix_checks,
        "formula_selection_after_results": False,
        "threshold_optimization_after_results": False,
        "full_sample_normalization": False,
    }
    return output, registry, protocol, proof


def correction_ledger(current_manifest: dict, previous_manifest: dict | None) -> dict:
    events = []
    if previous_manifest:
        previous = {
            item["archive_id"]: item for item in previous_manifest.get("archives", [])
        }
        current = {
            item["archive_id"]: item for item in current_manifest.get("archives", [])
        }
        for archive_id in sorted(previous.keys() & current.keys()):
            previous_sha = previous[archive_id].get("actual_sha256")
            current_sha = current[archive_id].get("actual_sha256")
            if previous_sha != current_sha:
                events.append(
                    {
                        "archive_id": archive_id,
                        "status": "SOURCE_ARCHIVE_REPLACED",
                        "previous_sha256": previous_sha,
                        "current_sha256": current_sha,
                    }
                )
    return {
        "schema_version": CORRECTION_SCHEMA,
        "status": "CORRECTIONS_FOUND" if events else "NO_CORRECTIONS",
        "event_count": len(events),
        "events": events,
        "silent_overwrite_allowed": False,
    }


def write_outputs(
    output_dir: Path,
    corpus_rows: list[dict],
    manifest: dict,
    registry: dict,
    protocol: dict,
    corrections: dict,
    proof: dict,
    design: dict,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_bytes = b"".join(canonical_json_bytes(row) for row in corpus_rows)
    warmup_rows = [row for row in corpus_rows if row["phase"] == "WARMUP"]
    oos_rows = [row for row in corpus_rows if row["phase"] == "OUT_OF_SAMPLE"]
    block_counts = {}
    for row in corpus_rows:
        block_counts[row["block_id"]] = block_counts.get(row["block_id"], 0) + 1

    summary = {
        "schema_version": SUMMARY_SCHEMA,
        "status": "PASS",
        "research_claim": "RETROSPECTIVE_TEMPORAL_REPLICATION_ONLY",
        "provider": "BINANCE_PUBLIC_DATA",
        "market": "BTCUSDT_SPOT",
        "state_start_date": design["window"]["state_start_date"],
        "state_end_date": design["window"]["state_end_date"],
        "source_tail_end_date": design["window"]["source_tail_end_date"],
        "state_row_count": len(corpus_rows),
        "warmup_row_count": len(warmup_rows),
        "out_of_sample_row_count": len(oos_rows),
        "complete_30d_outcome_count": sum(
            row["outcomes"]["maturity_status"] == "COMPLETE" for row in oos_rows
        ),
        "block_counts": block_counts,
        "retrospective_replication_blocks": registry[
            "retrospective_confirmation_blocks"
        ],
        "discovery_reference_block": registry["discovery_reference_block"],
        "discovery_reference_used_for_confirmation": False,
        "future_untouched_block_required": registry[
            "future_untouched_block_required"
        ],
        "correction_event_count": corrections["event_count"],
        "no_lookahead_status": proof["status"],
        "prefix_invariance_count": len(proof["prefix_invariance"]),
        "corpus_sha256": sha256(corpus_bytes),
        "manifest_sha256": sha256(pretty_json_bytes(manifest)),
        "protocol_sha256": sha256(pretty_json_bytes(protocol)),
        "block_registry_sha256": sha256(pretty_json_bytes(registry)),
        "methodology_id": protocol["accepted_methodology_id"],
        "methodology_sha256": protocol["accepted_methodology_sha256"],
        "predictive_power_proven": False,
        "public_binding_allowed": False,
        "commercial_ai_feed_allowed": False,
    }

    files = {
        "btc_2190d_state_corpus.jsonl": corpus_bytes,
        "btc_2190d_source_manifest.json": pretty_json_bytes(manifest),
        "btc_2190d_validation_protocol.json": pretty_json_bytes(protocol),
        "btc_2190d_block_registry.json": pretty_json_bytes(registry),
        "btc_2190d_source_correction_ledger.json": pretty_json_bytes(corrections),
        "btc_2190d_no_lookahead_proof.json": pretty_json_bytes(proof),
        "btc_2190d_summary.json": pretty_json_bytes(summary),
    }
    for filename, data in files.items():
        (output_dir / filename).write_bytes(data)
    return summary


def build(
    repo: Path,
    cache_dir: Path,
    output_dir: Path,
    previous_manifest_path: Path | None = None,
) -> dict:
    repo = repo.resolve()
    base = import_base_builder(repo)
    design = load_design(repo)
    start = parse_date(design["window"]["state_start_date"])
    end = parse_date(design["window"]["state_end_date"])
    tail = parse_date(design["window"]["source_tail_end_date"])

    if end != start + timedelta(days=design["window"]["state_days"] - 1):
        raise WalkForwardError("state window length mismatch")
    if tail != end + timedelta(days=design["window"]["maturity_tail_days"]):
        raise WalkForwardError("maturity tail mismatch")

    source_rows, archives = base.sources(start, tail, cache_dir)
    monthly_count = sum(item["frequency"] == "monthly" for item in archives)
    daily_count = sum(item["frequency"] == "daily" for item in archives)
    planned = design["window"]["archive_plan"]
    if {
        "monthly_archives": monthly_count,
        "daily_archives": daily_count,
        "total_archives": len(archives),
    } != planned:
        raise WalkForwardError("source archive plan mismatch")

    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "provider": "BINANCE_PUBLIC_DATA",
        "market": "BTCUSDT_SPOT",
        "interval": "1d",
        "source_start_date": start.isoformat(),
        "source_end_date": tail.isoformat(),
        "archive_count": len(archives),
        "monthly_archive_count": monthly_count,
        "daily_archive_count": daily_count,
        "archives": archives,
    }
    previous_manifest = (
        load_json(previous_manifest_path) if previous_manifest_path else None
    )
    corpus_rows, registry, protocol, proof = build_corpus(
        source_rows, design, base
    )
    corrections = correction_ledger(manifest, previous_manifest)
    return write_outputs(
        output_dir,
        corpus_rows,
        manifest,
        registry,
        protocol,
        corrections,
        proof,
        design,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--previous-manifest", type=Path)
    args = parser.parse_args()
    summary = build(
        args.repo,
        args.cache_dir,
        args.output_dir,
        args.previous_manifest,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
