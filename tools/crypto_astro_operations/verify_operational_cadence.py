#!/usr/bin/env python3
"""Fail-closed verifier for the Crypto-Astro manual refresh cadence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "crypto_astro_operational_cadence_v0_1"
FRESHNESS_CONTRACT_ID = "btc_market_snapshot_freshness_24h_168h_v0_1"
AUTOMATIC_REFRESH_DESIGN_ID = "crypto_astro_automatic_24h_refresh_fail_closed_design_v0_1"
AUTOMATIC_REFRESH_DESIGN_STATUS = "DESIGN_ONLY_DRY_RUN"
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


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CadenceVerificationError(f"{path}: expected JSON object")
    return value


def verify_automatic_refresh_design(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    design = (
        policy.get("automatic_refresh_design")
        if isinstance(policy.get("automatic_refresh_design"), dict)
        else {}
    )
    expected = {
        "design_id": AUTOMATIC_REFRESH_DESIGN_ID,
        "status": AUTOMATIC_REFRESH_DESIGN_STATUS,
        "activation_requires_separate_authorization": True,
        "schedule_activation_allowed": False,
        "production_activation_allowed": False,
        "proposed_check_interval_minutes": 60,
        "proposed_eligibility_age_hours": 20,
        "daily_minimum_interval_hours": 18,
        "freshness_boundary_hours": 24,
        "operational_breach_hours": 48,
        "unavailable_after_hours": 168,
        "dispatch_target": "crypto-astro-static-refresh-manual.yml",
        "dispatch_mode": "DAILY_CADENCE",
        "exact_main_lock_required": True,
        "single_flight_required": True,
        "source_health_required": True,
        "material_change_required_for_review_pr": True,
        "review_pr_only": True,
        "auto_merge_allowed": False,
        "deploy_command_allowed": False,
        "timestamp_only_refresh_allowed": False,
        "recheck_after_no_material_change_minutes": 60,
    }
    for key, value in expected.items():
        require(design.get(key) == value, f"automatic:{key}", failures)
    return failures


def evaluate_automatic_refresh_dry_run(
    policy: dict[str, Any], scenario: dict[str, Any]
) -> dict[str, Any]:
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
        elif age_hours < design["proposed_eligibility_age_hours"]:
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

    return {
        "schema_version": "crypto_astro_automatic_24h_refresh_dry_run_result_v0_1",
        "design_id": design["design_id"],
        "design_status": design["status"],
        "scenario_id": str(scenario.get("scenario_id", "unnamed")),
        "snapshot_age_hours": age_hours,
        "freshness_state": freshness_state,
        "operational_breach": age_hours > design["operational_breach_hours"],
        "decision": decision,
        "would_dispatch_existing_manual_workflow": decision == "WOULD_DISPATCH_REVIEW_PR",
        "dispatch_mode": design["dispatch_mode"] if decision == "WOULD_DISPATCH_REVIEW_PR" else None,
        "would_create_review_pr_only": decision == "WOULD_DISPATCH_REVIEW_PR",
        "would_merge": False,
        "would_deploy": False,
        "would_modify_public_data": False,
        "schedule_active": False,
        "production_active": False,
        "requires_separate_activation_authorization": True,
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
        for key in ("would_merge", "would_deploy", "would_modify_public_data", "schedule_active", "production_active"):
            require(result.get(key) is False, f"dry_run:{scenario_id}:{key}", failures)
    return failures


def verify_policy(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    require(policy.get("schema_version") == SCHEMA_VERSION, "policy:schema_version", failures)
    require(policy.get("freshness_contract_id") == FRESHNESS_CONTRACT_ID, "policy:freshness_contract_id", failures)
    require(policy.get("refresh_trigger") == "workflow_dispatch", "policy:refresh_trigger", failures)
    require(policy.get("default_mode") == "DAILY_CADENCE", "policy:default_mode", failures)
    require(policy.get("allowed_modes") == EXPECTED_MODES, "policy:allowed_modes", failures)
    require(policy.get("exception_modes") == EXPECTED_EXCEPTION_MODES, "policy:exception_modes", failures)
    require(policy.get("required_dispatch_inputs") == EXPECTED_INPUTS, "policy:required_dispatch_inputs", failures)

    cadence = policy.get("cadence") if isinstance(policy.get("cadence"), dict) else {}
    require(cadence.get("target_accepted_refresh_interval_hours") == 24, "policy:target_interval", failures)
    require(cadence.get("daily_minimum_interval_hours") == 18, "policy:daily_minimum", failures)
    require(cadence.get("target_max_operational_gap_hours") == 48, "policy:max_gap", failures)

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
    require(deployment.get("refresh_workflow_merge_command_allowed") is False, "policy:no_merge_command", failures)
    require(deployment.get("refresh_workflow_deploy_command_allowed") is False, "policy:no_deploy_command", failures)
    require(deployment.get("pages_publish_after_accepted_main_merge") is True, "policy:pages_after_merge", failures)

    require(policy.get("prohibited_refresh_triggers") == ["schedule", "push"], "policy:prohibited_triggers", failures)
    boundary = policy.get("boundary") if isinstance(policy.get("boundary"), dict) else {}
    require(boundary and all(value is False for value in boundary.values()), "policy:boundary", failures)
    failures.extend(verify_automatic_refresh_design(policy))
    return failures


def verify_manual_workflow(text: str, policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required_markers = [
        "workflow_dispatch:",
        "refresh_mode:",
        "operator_ref:",
        "refresh_reason:",
        "ref: main",
        "crypto-astro-static-refresh-manual",
        "Verify operational cadence and single-flight preflight",
        "verify_operational_cadence.py",
        "gh pr list --state open --base main",
        "automation/crypto-astro-static-refresh-",
        "origin/main",
        "daily_minimum_interval_hours",
        "test_bhrigu_consumer_contract_v0_1.py",
        "verify:btc-producer-contract",
        "ATOMIC_REFRESH_BRANCH=PASS",
        "gh pr create --base main",
        "CRYPTO_ASTRO_REFRESH_MODE",
        "CRYPTO_ASTRO_OPERATOR_REF",
        "CRYPTO_ASTRO_REFRESH_REASON",
        "Materialize cadence metadata in operator review",
        "Workflow may push one fully validated review branch",
        "It may not merge or issue a deployment command.",
        "explicit merge authorization",
    ]
    for marker in required_markers:
        require(marker in text, f"manual:missing:{marker}", failures)
    for mode in policy.get("allowed_modes", []):
        require(mode in text, f"manual:mode:{mode}", failures)

    trigger_lines = {
        match.group(1)
        for match in re.finditer(r"^  (workflow_dispatch|schedule|push):\s*$", text, flags=re.MULTILINE)
    }
    require(trigger_lines == {"workflow_dispatch"}, f"manual:triggers:{sorted(trigger_lines)}", failures)

    forbidden_patterns = {
        "merge_command": r"\bgh\s+pr\s+merge\b|\bgh\s+api\b[^\n]*\/merges\b|^\s*git\s+merge\b",
        "deploy_command": r"actions\/deploy-pages|\bdeploy-pages\b|\bgh\s+workflow\s+run\b[^\n]*pages",
        "cron": r"^\s*cron:\s*",
    }
    for name, pattern in forbidden_patterns.items():
        require(re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE) is None, f"manual:forbidden:{name}", failures)

    require("cancel-in-progress: false" in text, "manual:concurrency_cancel_policy", failures)
    require("OPEN_REFRESH_COUNT" in text and 'test "$OPEN_REFRESH_COUNT" = "0"' in text, "manual:open_pr_count", failures)
    require("git rev-parse HEAD" in text and "git rev-parse origin/main" in text, "manual:exact_main_check", failures)
    return failures


def verify_cadence_workflow(text: str) -> list[str]:
    failures: list[str] = []
    for marker in (
        "name: Crypto-Astro Operational Cadence PR",
        "pull_request:",
        ".github/workflows/crypto-astro-static-refresh-manual.yml",
        ".github/workflows/crypto-astro-operational-cadence-pr.yml",
        ".github/workflows/crypto-astro-snapshot-memory-pr.yml",
        "docs/crypto-astro-service/CRYPTO_ASTRO_OPERATIONAL_CADENCE_v0_1.md",
        "docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json",
        "tools/crypto_astro_operations/**",
        "crypto_astro_operator_review.md",
        "test_verify_operational_cadence.py",
        "verify_operational_cadence.py",
    ):
        require(marker in text, f"cadence_workflow:missing:{marker}", failures)
    require(re.search(r"^  schedule:\s*$", text, flags=re.MULTILINE) is None, "cadence_workflow:schedule", failures)
    require(re.search(r"^  push:\s*$", text, flags=re.MULTILINE) is None, "cadence_workflow:push", failures)
    return failures


def verify_operator_review(text: str) -> list[str]:
    failures: list[str] = []
    for marker in ("REFRESH_MODE=", "OPERATOR_REF=", "REFRESH_REASON=", OPERATOR_BOUNDARY):
        require(marker in text, f"operator_review:missing:{marker}", failures)
    require("No push, no PR, no deploy." not in text, "operator_review:obsolete_boundary", failures)
    return failures


def verify_repository(
    repo: Path,
    policy_path: Path,
    manual_workflow_path: Path,
    cadence_workflow_path: Path,
    operator_review_path: Path,
) -> dict[str, Any]:
    policy = load_json(policy_path)
    checks = {
        "policy": verify_policy(policy),
        "automatic_refresh_dry_run": verify_automatic_refresh_dry_run(policy),
        "manual_workflow": verify_manual_workflow(manual_workflow_path.read_text(encoding="utf-8"), policy),
        "cadence_workflow": verify_cadence_workflow(cadence_workflow_path.read_text(encoding="utf-8")),
        "operator_review": verify_operator_review(operator_review_path.read_text(encoding="utf-8")),
    }
    failures = [f"{section}:{failure}" for section, values in checks.items() for failure in values]
    return {
        "schema_version": "crypto_astro_operational_cadence_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "policy": str(policy_path.relative_to(repo)),
        "checks": {section: "PASS" if not values else "FAIL" for section, values in checks.items()},
        "automatic_refresh_design": policy["automatic_refresh_design"],
        "automatic_refresh_dry_run_matrix": automatic_refresh_dry_run_matrix(policy),
        "failures": failures,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--policy", default="docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json")
    parser.add_argument("--manual-workflow", default=".github/workflows/crypto-astro-static-refresh-manual.yml")
    parser.add_argument("--cadence-workflow", default=".github/workflows/crypto-astro-operational-cadence-pr.yml")
    parser.add_argument("--operator-review", default="docs/crypto-astro-service/crypto_astro_operator_review.md")
    parser.add_argument("--report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    resolve = lambda value: (repo / value).resolve()
    report = verify_repository(
        repo,
        resolve(args.policy),
        resolve(args.manual_workflow),
        resolve(args.cadence_workflow),
        resolve(args.operator_review),
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        report_path = resolve(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
