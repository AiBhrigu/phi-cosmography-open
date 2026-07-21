#!/usr/bin/env python3
"""Fail-closed verifier for the Crypto-Astro manual refresh cadence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "crypto_astro_operational_cadence_v0_1"
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


def verify_policy(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    require(policy.get("schema_version") == SCHEMA_VERSION, "policy:schema_version", failures)
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
    require(freshness.get("fresh_hours") == 72, "policy:fresh_hours", failures)
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
    require("OPEN_REFRESH_COUNT" in text and "OPEN_REFRESH_COUNT" in text, "manual:open_pr_count", failures)
    require("git rev-parse HEAD" in text and "git rev-parse origin/main" in text, "manual:exact_main_check", failures)
    return failures


def verify_cadence_workflow(text: str) -> list[str]:
    failures: list[str] = []
    for marker in (
        "name: Crypto-Astro Operational Cadence PR",
        "pull_request:",
        ".github/workflows/crypto-astro-static-refresh-manual.yml",
        ".github/workflows/crypto-astro-operational-cadence-pr.yml",
        "docs/crypto-astro-service/CRYPTO_ASTRO_OPERATIONAL_CADENCE_v0_1.md",
        "docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json",
        "tools/crypto_astro_operations/**",
        "crypto_astro_all_module_static_refresh_source_v0_1.py",
        "crypto_astro_operator_review.md",
        "test_verify_operational_cadence.py",
        "verify_operational_cadence.py",
    ):
        require(marker in text, f"cadence_workflow:missing:{marker}", failures)
    require(re.search(r"^  schedule:\s*$", text, flags=re.MULTILINE) is None, "cadence_workflow:schedule", failures)
    require(re.search(r"^  push:\s*$", text, flags=re.MULTILINE) is None, "cadence_workflow:push", failures)
    return failures


def verify_generator(text: str) -> list[str]:
    failures: list[str] = []
    for marker in (
        "CRYPTO_ASTRO_REFRESH_MODE",
        "CRYPTO_ASTRO_OPERATOR_REF",
        "CRYPTO_ASTRO_REFRESH_REASON",
        "REFRESH_MODE=",
        "OPERATOR_REF=",
        "REFRESH_REASON=",
        OPERATOR_BOUNDARY,
    ):
        require(marker in text, f"generator:missing:{marker}", failures)
    require("No push, no PR, no deploy." not in text, "generator:obsolete_boundary", failures)
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
    generator_path: Path,
    operator_review_path: Path,
) -> dict[str, Any]:
    policy = load_json(policy_path)
    checks = {
        "policy": verify_policy(policy),
        "manual_workflow": verify_manual_workflow(manual_workflow_path.read_text(encoding="utf-8"), policy),
        "cadence_workflow": verify_cadence_workflow(cadence_workflow_path.read_text(encoding="utf-8")),
        "generator": verify_generator(generator_path.read_text(encoding="utf-8")),
        "operator_review": verify_operator_review(operator_review_path.read_text(encoding="utf-8")),
    }
    failures = [f"{section}:{failure}" for section, values in checks.items() for failure in values]
    return {
        "schema_version": "crypto_astro_operational_cadence_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "policy": str(policy_path.relative_to(repo)),
        "checks": {section: "PASS" if not values else "FAIL" for section, values in checks.items()},
        "failures": failures,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--policy", default="docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json")
    parser.add_argument("--manual-workflow", default=".github/workflows/crypto-astro-static-refresh-manual.yml")
    parser.add_argument("--cadence-workflow", default=".github/workflows/crypto-astro-operational-cadence-pr.yml")
    parser.add_argument("--generator", default="tools/crypto_astro_static_refresh/crypto_astro_all_module_static_refresh_source_v0_1.py")
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
        resolve(args.generator),
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
