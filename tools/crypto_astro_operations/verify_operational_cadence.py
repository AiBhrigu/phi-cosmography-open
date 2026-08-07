#!/usr/bin/env python3
"""Fail-closed verifier for the Crypto-Astro producer and automatic control plane."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "crypto_astro_operational_cadence_v0_1"
FRESHNESS_CONTRACT_ID = "btc_market_snapshot_freshness_24h_168h_v0_1"
AUTOMATIC_REFRESH_DESIGN_ID = "crypto_astro_automatic_24h_refresh_fail_closed_design_v0_1"
AUTOMATIC_REFRESH_DESIGN_STATUS = "ACTIVATION_REVIEW_CANDIDATE"
EXPECTED_MODES = [
    "DAILY_CADENCE",
    "PRE_REPORT",
    "MATERIAL_MARKET_EVENT",
    "REPEATABILITY_PROOF",
    "SOURCE_OR_SCHEMA_REPAIR",
]
EXPECTED_EXCEPTION_MODES = EXPECTED_MODES[1:]
EXPECTED_INPUTS = ["refresh_mode", "operator_ref", "refresh_reason"]
OPERATOR_BOUNDARY = (
    "Workflow may push one fully validated review branch and open one review PR. "
    "It may not merge or issue a deployment command. Publication follows only "
    "after explicit merge authorization."
)


class CadenceVerificationError(RuntimeError):
    pass


def require(condition: bool, code: str, failures: list[str]) -> None:
    if not condition:
        failures.append(code)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CadenceVerificationError(f"{path}: expected JSON object")
    return value


def verify_automatic_refresh_design(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    design = policy.get("automatic_refresh_design") if isinstance(policy.get("automatic_refresh_design"), dict) else {}
    expected = {
        "design_id": AUTOMATIC_REFRESH_DESIGN_ID,
        "activation_contract_id": "crypto_astro_automatic_refresh_activation_v0_1",
        "status": AUTOMATIC_REFRESH_DESIGN_STATUS,
        "activation_requires_explicit_merge_authorization": True,
        "activation_on_default_branch_merge": True,
        "schedule_activation_allowed": True,
        "check_interval_minutes": 60,
        "eligibility_age_hours": 20,
        "daily_minimum_interval_hours": 18,
        "freshness_boundary_hours": 24,
        "operational_breach_hours": 48,
        "unavailable_after_hours": 168,
        "scheduler_workflow": "crypto-astro-automatic-refresh.yml",
        "dispatch_target": "crypto-astro-static-refresh-manual.yml",
        "dispatch_mode": "DAILY_CADENCE",
        "exact_main_lock_required": True,
        "single_flight_required": True,
        "source_health_required": True,
        "material_change_required_for_review_pr": True,
        "review_pr_only": True,
        "manual_workflow_dispatch_fallback_preserved": True,
        "auto_merge_allowed": False,
        "deploy_command_allowed": False,
        "timestamp_only_refresh_allowed": False,
        "recheck_after_no_material_change_minutes": 60,
    }
    for key, value in expected.items():
        require(design.get(key) == value, f"automatic:{key}", failures)
    return failures


def evaluate_automatic_refresh_dry_run(policy: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    design = policy["automatic_refresh_design"]
    age_hours = float(scenario["snapshot_age_hours"])
    if age_hours < 0:
        freshness_state = "UNAVAILABLE"
        decision = "BLOCK_FUTURE_SNAPSHOT"
    elif age_hours <= design["freshness_boundary_hours"]:
        freshness_state = "FRESH"
        decision = ""
    elif age_hours <= design["unavailable_after_hours"]:
        freshness_state = "STALE_LIMITED"
        decision = ""
    else:
        freshness_state = "UNAVAILABLE"
        decision = ""

    if not decision:
        if age_hours < design["daily_minimum_interval_hours"]:
            decision = "HOLD_MINIMUM_INTERVAL"
        elif age_hours < design["eligibility_age_hours"]:
            decision = "HOLD_BEFORE_AUTOMATIC_WINDOW"
        elif scenario.get("exact_main_match") is not True:
            decision = "BLOCK_MAIN_DRIFT"
        elif int(scenario.get("open_refresh_pr_count", 0)) != 0:
            decision = "BLOCK_OPEN_REFRESH_PR"
        elif scenario.get("workflow_in_progress") is True:
            decision = "BLOCK_SINGLE_FLIGHT"
        elif scenario.get("source_status") != "HEALTHY":
            decision = "SOURCE_FAILURE_RECHECK"
        elif scenario.get("material_change") == "NO":
            decision = "NO_MATERIAL_CHANGE_RECHECK"
        elif scenario.get("material_change") != "YES":
            decision = "BLOCK_MATERIAL_CHANGE_UNKNOWN"
        else:
            decision = "WOULD_DISPATCH_REVIEW_PR"

    dispatch = decision == "WOULD_DISPATCH_REVIEW_PR"
    return {
        "schema_version": "crypto_astro_automatic_24h_refresh_dry_run_result_v0_1",
        "design_id": design["design_id"],
        "design_status": design["status"],
        "scenario_id": str(scenario.get("scenario_id", "unnamed")),
        "snapshot_age_hours": age_hours,
        "freshness_state": freshness_state,
        "operational_breach": age_hours > design["operational_breach_hours"],
        "decision": decision,
        "would_dispatch_existing_manual_workflow": dispatch,
        "dispatch_mode": design["dispatch_mode"] if dispatch else None,
        "would_create_review_pr_only": dispatch,
        "would_merge": False,
        "would_deploy": False,
        "would_modify_public_data": False,
        "schedule_configured": True,
        "schedule_active_before_merge": False,
        "requires_explicit_merge_authorization": True,
    }


def automatic_refresh_dry_run_matrix(policy: dict[str, Any]) -> list[dict[str, Any]]:
    base = {
        "exact_main_match": True,
        "open_refresh_pr_count": 0,
        "workflow_in_progress": False,
        "source_status": "HEALTHY",
        "material_change": "YES",
    }
    scenarios = [
        {**base, "scenario_id": "minimum_hold_17h", "snapshot_age_hours": 17},
        {**base, "scenario_id": "pre_window_hold_19h", "snapshot_age_hours": 19},
        {**base, "scenario_id": "eligible_20h", "snapshot_age_hours": 20},
        {**base, "scenario_id": "main_drift_22h", "snapshot_age_hours": 22, "exact_main_match": False},
        {**base, "scenario_id": "open_pr_block_22h", "snapshot_age_hours": 22, "open_refresh_pr_count": 1},
        {**base, "scenario_id": "single_flight_block_22h", "snapshot_age_hours": 22, "workflow_in_progress": True},
        {**base, "scenario_id": "source_failure_22h", "snapshot_age_hours": 22, "source_status": "FAILED"},
        {**base, "scenario_id": "no_material_change_22h", "snapshot_age_hours": 22, "material_change": "NO"},
        {**base, "scenario_id": "fresh_boundary_24h", "snapshot_age_hours": 24},
        {**base, "scenario_id": "stale_limited_25h", "snapshot_age_hours": 25},
        {**base, "scenario_id": "operational_breach_49h", "snapshot_age_hours": 49},
        {**base, "scenario_id": "legacy_probe_72h", "snapshot_age_hours": 72},
        {**base, "scenario_id": "stale_boundary_168h", "snapshot_age_hours": 168},
        {**base, "scenario_id": "unavailable_169h", "snapshot_age_hours": 169},
        {**base, "scenario_id": "future_snapshot", "snapshot_age_hours": -0.1},
    ]
    return [evaluate_automatic_refresh_dry_run(policy, scenario) for scenario in scenarios]


def verify_automatic_refresh_dry_run(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    results = {item["scenario_id"]: item for item in automatic_refresh_dry_run_matrix(policy)}
    expected = {
        "minimum_hold_17h": ("HOLD_MINIMUM_INTERVAL", "FRESH", False),
        "pre_window_hold_19h": ("HOLD_BEFORE_AUTOMATIC_WINDOW", "FRESH", False),
        "eligible_20h": ("WOULD_DISPATCH_REVIEW_PR", "FRESH", False),
        "main_drift_22h": ("BLOCK_MAIN_DRIFT", "FRESH", False),
        "open_pr_block_22h": ("BLOCK_OPEN_REFRESH_PR", "FRESH", False),
        "single_flight_block_22h": ("BLOCK_SINGLE_FLIGHT", "FRESH", False),
        "source_failure_22h": ("SOURCE_FAILURE_RECHECK", "FRESH", False),
        "no_material_change_22h": ("NO_MATERIAL_CHANGE_RECHECK", "FRESH", False),
        "fresh_boundary_24h": ("WOULD_DISPATCH_REVIEW_PR", "FRESH", False),
        "stale_limited_25h": ("WOULD_DISPATCH_REVIEW_PR", "STALE_LIMITED", False),
        "operational_breach_49h": ("WOULD_DISPATCH_REVIEW_PR", "STALE_LIMITED", True),
        "legacy_probe_72h": ("WOULD_DISPATCH_REVIEW_PR", "STALE_LIMITED", True),
        "stale_boundary_168h": ("WOULD_DISPATCH_REVIEW_PR", "STALE_LIMITED", True),
        "unavailable_169h": ("WOULD_DISPATCH_REVIEW_PR", "UNAVAILABLE", True),
        "future_snapshot": ("BLOCK_FUTURE_SNAPSHOT", "UNAVAILABLE", False),
    }
    for scenario_id, (decision, freshness, breach) in expected.items():
        result = results.get(scenario_id, {})
        require(result.get("decision") == decision, f"dry_run:{scenario_id}:decision", failures)
        require(result.get("freshness_state") == freshness, f"dry_run:{scenario_id}:freshness", failures)
        require(result.get("operational_breach") is breach, f"dry_run:{scenario_id}:breach", failures)
        require(result.get("would_merge") is False, f"dry_run:{scenario_id}:would_merge", failures)
        require(result.get("would_deploy") is False, f"dry_run:{scenario_id}:would_deploy", failures)
        require(result.get("would_modify_public_data") is False, f"dry_run:{scenario_id}:public_mutation", failures)
        require(result.get("schedule_configured") is True, f"dry_run:{scenario_id}:schedule_configured", failures)
        require(result.get("schedule_active_before_merge") is False, f"dry_run:{scenario_id}:premerge_activation", failures)
    return failures


def verify_policy(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    require(policy.get("schema_version") == SCHEMA_VERSION, "policy:schema_version", failures)
    require(policy.get("freshness_contract_id") == FRESHNESS_CONTRACT_ID, "policy:freshness_contract_id", failures)
    require(policy.get("source_producer_trigger") == "workflow_dispatch", "policy:source_producer_trigger", failures)
    require(policy.get("automatic_control_trigger") == "schedule_and_workflow_dispatch", "policy:automatic_control_trigger", failures)
    require(policy.get("default_mode") == "DAILY_CADENCE", "policy:default_mode", failures)
    require(policy.get("allowed_modes") == EXPECTED_MODES, "policy:allowed_modes", failures)
    require(policy.get("exception_modes") == EXPECTED_EXCEPTION_MODES, "policy:exception_modes", failures)
    require(policy.get("required_dispatch_inputs") == EXPECTED_INPUTS, "policy:required_dispatch_inputs", failures)

    cadence = policy.get("cadence") if isinstance(policy.get("cadence"), dict) else {}
    expected_cadence = {
        "target_accepted_refresh_interval_hours": 24,
        "daily_minimum_interval_hours": 18,
        "automatic_eligibility_age_hours": 20,
        "automatic_check_interval_minutes": 60,
        "target_max_operational_gap_hours": 48,
    }
    for key, value in expected_cadence.items():
        require(cadence.get(key) == value, f"policy:cadence:{key}", failures)

    freshness = policy.get("freshness") if isinstance(policy.get("freshness"), dict) else {}
    require(freshness.get("fresh_hours") == 24, "policy:fresh_hours", failures)
    require(freshness.get("stale_limited_hours") == 168, "policy:stale_limited_hours", failures)
    require(freshness.get("unavailable_after_hours") == 168, "policy:unavailable_after_hours", failures)

    single_flight = policy.get("single_flight") if isinstance(policy.get("single_flight"), dict) else {}
    require(single_flight.get("concurrent_workflow_runs_forbidden") is True, "policy:concurrency", failures)
    require(single_flight.get("second_open_refresh_pr_forbidden") is True, "policy:open_pr", failures)
    require(single_flight.get("non_current_main_dispatch_forbidden") is True, "policy:current_main", failures)
    require(single_flight.get("auto_close_previous_refresh_pr") is False, "policy:no_auto_close", failures)

    acceptance = policy.get("acceptance") if isinstance(policy.get("acceptance"), dict) else {}
    for key in (
        "bhrigu_consumer_preflight_required",
        "atomic_branch_proof_required",
        "review_pr_required",
        "desktop_visual_review_required",
        "mobile_visual_review_required",
        "explicit_merge_authorization_required",
        "public_pages_verification_required",
        "bhrigu_btc_field_read_verification_required",
    ):
        require(acceptance.get(key) is True, f"policy:acceptance:{key}", failures)

    deployment = policy.get("deployment") if isinstance(policy.get("deployment"), dict) else {}
    for key in (
        "refresh_workflow_merge_command_allowed",
        "refresh_workflow_deploy_command_allowed",
        "automatic_scheduler_merge_command_allowed",
        "automatic_scheduler_deploy_command_allowed",
    ):
        require(deployment.get(key) is False, f"policy:deployment:{key}", failures)
    require(deployment.get("pages_publish_after_accepted_main_merge") is True, "policy:pages_after_merge", failures)
    require(policy.get("prohibited_source_producer_triggers") == ["schedule", "push"], "policy:producer_triggers", failures)

    boundary = policy.get("boundary") if isinstance(policy.get("boundary"), dict) else {}
    require(boundary.get("cron_control_plane") is True, "policy:boundary:cron_control_plane", failures)
    require(boundary.get("source_producer_cron") is False, "policy:boundary:source_producer_cron", failures)
    for key, value in boundary.items():
        if key not in {"cron_control_plane", "source_producer_cron"}:
            require(value is False, f"policy:boundary:{key}", failures)
    failures.extend(verify_automatic_refresh_design(policy))
    return failures


def verify_manual_workflow(text: str, policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required_markers = (
        "workflow_dispatch:", "refresh_mode:", "operator_ref:", "refresh_reason:",
        "ref: main", "crypto-astro-static-refresh-manual",
        "Verify operational cadence and single-flight preflight", "verify_operational_cadence.py",
        "gh pr list --state open --base main", "automation/crypto-astro-static-refresh-",
        "origin/main", "daily_minimum_interval_hours",
        "test_bhrigu_consumer_contract_v0_1.py", "verify:btc-producer-contract",
        "ATOMIC_REFRESH_BRANCH=PASS", "gh pr create --base main",
        "CRYPTO_ASTRO_REFRESH_MODE", "CRYPTO_ASTRO_OPERATOR_REF", "CRYPTO_ASTRO_REFRESH_REASON",
        "Materialize cadence metadata in operator review",
        "Workflow may push one fully validated generated-refresh branch",
        "gated automatic publication path", "Human-authored product PRs are not eligible",
    )
    for marker in required_markers:
        require(marker in text, f"manual:missing:{marker}", failures)
    for mode in policy.get("allowed_modes", []):
        require(mode in text, f"manual:mode:{mode}", failures)
    triggers = {
        match.group(1) for match in re.finditer(
            r"^  (workflow_dispatch|schedule|push):\s*$", text, flags=re.MULTILINE
        )
    }
    require(triggers == {"workflow_dispatch"}, f"manual:triggers:{sorted(triggers)}", failures)
    forbidden = {
        "merge_command": r"\bgh\s+pr\s+merge\b|\bgh\s+api\b[^\n]*/merges\b|^\s*git\s+merge\b",
        "deploy_command": r"actions/deploy-pages|\bdeploy-pages\b|\bgh\s+workflow\s+run\b[^\n]*pages",
        "cron": r"^\s*cron:\s*",
    }
    for name, pattern in forbidden.items():
        require(re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE) is None, f"manual:forbidden:{name}", failures)
    require('test "$OPEN_REFRESH_COUNT" = "0"' in text, "manual:open_pr_count", failures)
    return failures


def verify_cadence_workflow(text: str) -> list[str]:
    failures: list[str] = []
    for marker in (
        "name: Crypto-Astro Operational Cadence PR",
        "pull_request:",
        "test_verify_operational_cadence.py",
        "verify_operational_cadence.py",
        "crypto-astro-automatic-refresh.yml",
        "automatic_refresh_activation",
    ):
        require(marker in text, f"cadence_workflow:missing:{marker}", failures)
    return failures


def verify_operator_review(text: str) -> list[str]:
    failures: list[str] = []
    require(OPERATOR_BOUNDARY in text, "operator_review:boundary", failures)
    require("No push, no PR, no deploy." not in text, "operator_review:obsolete_boundary", failures)
    return failures


def verify_repository(repo: Path) -> dict[str, Any]:
    policy = load_json(repo / "docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json")
    checks = {
        "policy": verify_policy(policy),
        "manual_workflow": verify_manual_workflow((repo / ".github/workflows/crypto-astro-static-refresh-manual.yml").read_text(encoding="utf-8"), policy),
        "cadence_workflow": verify_cadence_workflow((repo / ".github/workflows/crypto-astro-operational-cadence-pr.yml").read_text(encoding="utf-8")),
        "operator_review": verify_operator_review((repo / "docs/crypto-astro-service/crypto_astro_operator_review.md").read_text(encoding="utf-8")),
        "automatic_matrix": verify_automatic_refresh_dry_run(policy),
    }
    failures = [f"{section}:{item}" for section, items in checks.items() for item in items]
    return {
        "schema_version": "crypto_astro_operational_cadence_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "freshness_contract_id": FRESHNESS_CONTRACT_ID,
        "automatic_status": AUTOMATIC_REFRESH_DESIGN_STATUS,
        "checks": {section: "PASS" if not items else "FAIL" for section, items in checks.items()},
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--report")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    report = verify_repository(repo)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        target = (repo / args.report).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
