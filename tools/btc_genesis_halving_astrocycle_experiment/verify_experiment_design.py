#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

DESIGN = Path(
    "docs/crypto-astro-service/"
    "btc_genesis_next_halving_astrocycle_experiment_design_v0_1.json"
)
READINESS = Path(
    "docs/crypto-astro-service/"
    "btc_astromodule_merriman_gap_and_readiness_v0_1.json"
)


def verify(repo: Path) -> None:
    design = json.loads((repo / DESIGN).read_text(encoding="utf-8"))
    readiness = json.loads((repo / READINESS).read_text(encoding="utf-8"))

    assert (
        design["schema_version"]
        == "btc_genesis_next_halving_astrocycle_experiment_design_v0_1"
    )
    assert design["canonical_protocol_anchors"] == {
        "genesis_height": 0,
        "halving_interval_blocks": 210000,
        "historical_halving_start_heights": [0, 210000, 420000, 630000, 840000],
        "next_halving_start_height": 1050000,
        "height_is_consensus_trigger": True,
        "calendar_date_is_consensus_trigger": False,
    }
    assert design["lane_separation"]["astrocycle_lane"].startswith("RESEARCH_ONLY")
    astro = design["future_astrocycle_input_contract"]
    assert astro["orb_registry_status"] == "MUST_BE_LOCKED_BEFORE_DATA_INSPECTION"
    assert astro["future_halving_anchor"] == "BLOCK_HEIGHT_ONLY_UNTIL_BLOCK_IS_OBSERVED"

    prohibited = set(design["prohibited_claims"])
    for required in {
        "PREDICTION",
        "TRADING_SIGNAL",
        "PRICE_TARGET",
        "ASTRO_CAUSES_PRICE",
        "HALVING_CAUSES_PRICE",
    }:
        assert required in prohibited

    assert readiness["status"] == "PARTIAL_FAIL_CLOSED"
    decision = readiness["readiness_decision"]
    assert decision["protocol_delta_experiment"] == "READY"
    assert decision["a_e_numeric_activation"] == "CLOSED"
    assert decision["product_scoring_effect"] == "NO_CURRENT_EFFECT"
    assert decision["astromodule_deterministic_research_run"].startswith("BLOCKED_")

    missing = readiness["not_yet_accepted"]
    for key in (
        "pinned_ephemeris_files_and_version",
        "locked_aspect_orb_registry",
        "signature_cluster_engine",
        "critical_reversal_date_engine",
        "cycle_phase_engine",
        "no_lookahead_astro_validation",
        "multiple_testing_control",
    ):
        assert missing[key] is True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    args = parser.parse_args()
    verify(args.repo.resolve())
    print("BTC_GENESIS_HALVING_ASTROCYCLE_EXPERIMENT_DESIGN=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
