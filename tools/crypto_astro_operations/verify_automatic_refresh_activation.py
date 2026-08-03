#!/usr/bin/env python3
"""Fail-closed verifier for the separate automatic Snapshot scheduler."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "crypto_astro_automatic_refresh_activation_v0_1"
ACTIVATION_ID = "BTC_COSMOGRAPHER_MARKET_SNAPSHOT_AUTOMATIC_REFRESH_SOURCE_TRUTH_REPAIR_v0_1"
DESIGN_ID = "crypto_astro_automatic_24h_refresh_fail_closed_design_v0_1"
SCHEDULER = ".github/workflows/crypto-astro-automatic-refresh.yml"
VALIDATOR = ".github/workflows/crypto-astro-automatic-refresh-pr.yml"
MANUAL_WORKFLOW = "crypto-astro-static-refresh-manual.yml"
CRON = "17 * * * *"


class ActivationVerificationError(RuntimeError):
    pass


def require(condition: bool, code: str, failures: list[str]) -> None:
    if not condition:
        failures.append(code)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActivationVerificationError(f"{path}: expected object")
    return value


def evaluate_decision(
    policy: dict[str, Any],
    *,
    snapshot_age_hours: float,
    exact_main_match: bool = True,
    open_refresh_pr_count: int = 0,
    active_manual_run_count: int = 0,
    source_probe: str = "PASS",
    material_change: bool | None = True,
) -> str:
    freshness = policy["freshness_contract"]
    if snapshot_age_hours < 0:
        return "BLOCK_FUTURE_SNAPSHOT"
    if snapshot_age_hours < freshness["daily_minimum_interval_hours"]:
        return "HOLD_MINIMUM_INTERVAL"
    if snapshot_age_hours < freshness["automatic_eligibility_age_hours"]:
        return "HOLD_BEFORE_AUTOMATIC_WINDOW"
    if not exact_main_match:
        return "BLOCK_MAIN_DRIFT"
    if open_refresh_pr_count:
        return "BLOCK_OPEN_REFRESH_PR"
    if active_manual_run_count:
        return "BLOCK_SINGLE_FLIGHT"
    if source_probe != "PASS":
        return "SOURCE_FAILURE_RECHECK"
    if material_change is False:
        return "NO_MATERIAL_CHANGE_RECHECK"
    if material_change is not True:
        return "BLOCK_MATERIAL_CHANGE_UNKNOWN"
    return "DISPATCH_MANUAL_REFRESH"


def verify_policy(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    require(policy.get("schema_version") == SCHEMA_VERSION, "policy:schema_version", failures)
    require(policy.get("activation_id") == ACTIVATION_ID, "policy:activation_id", failures)
    require(policy.get("supersedes_design_id") == DESIGN_ID, "policy:supersedes_design_id", failures)
    require(policy.get("status") == "REVIEW_CANDIDATE", "policy:status", failures)
    require(policy.get("activation_on_default_branch_merge") is True, "policy:activation_on_merge", failures)
    require(policy.get("scheduler_workflow") == SCHEDULER, "policy:scheduler_workflow", failures)
    require(policy.get("validation_workflow") == VALIDATOR, "policy:validation_workflow", failures)

    schedule = policy.get("schedule") if isinstance(policy.get("schedule"), dict) else {}
    require(schedule.get("cron") == CRON, "policy:cron", failures)
    require(schedule.get("check_interval_minutes") == 60, "policy:check_interval", failures)
    require(schedule.get("workflow_dispatch_fallback") is True, "policy:dispatch_fallback", failures)

    freshness = policy.get("freshness_contract") if isinstance(policy.get("freshness_contract"), dict) else {}
    require(freshness.get("contract_id") == "btc_market_snapshot_freshness_24h_168h_v0_1", "policy:freshness_contract", failures)
    require(freshness.get("daily_minimum_interval_hours") == 18, "policy:minimum", failures)
    require(freshness.get("automatic_eligibility_age_hours") == 20, "policy:eligibility", failures)
    require(freshness.get("fresh_through_hours") == 24, "policy:fresh_boundary", failures)
    require(freshness.get("operational_breach_after_hours") == 48, "policy:breach", failures)
    require(freshness.get("unavailable_after_hours") == 168, "policy:unavailable", failures)

    source = policy.get("source_truth") if isinstance(policy.get("source_truth"), dict) else {}
    require(source.get("probe_implementation") == "tools/crypto_astro_static_refresh/crypto_astro_static_refresh_bhrigu_compat_v0_1.py", "policy:probe", failures)
    require(source.get("methodology_test") == "tools/crypto_astro_static_refresh/test_defi_tvl_methodology_v0_1.py", "policy:methodology", failures)
    require(source.get("no_synthetic_fallback") is True, "policy:no_synthetic_fallback", failures)
    require(source.get("material_change_required") is True, "policy:material_change", failures)
    require(source.get("timestamp_only_refresh_allowed") is False, "policy:no_timestamp_only", failures)

    dispatch = policy.get("dispatch") if isinstance(policy.get("dispatch"), dict) else {}
    require(dispatch.get("target_workflow") == MANUAL_WORKFLOW, "policy:target_workflow", failures)
    require(dispatch.get("target_ref") == "main", "policy:target_ref", failures)
    require(dispatch.get("mode") == "DAILY_CADENCE", "policy:dispatch_mode", failures)
    for key in (
        "exact_main_lock_before_probe",
        "second_open_refresh_pr_forbidden",
        "queued_or_running_manual_refresh_forbidden",
        "review_pr_only",
        "manual_workflow_dispatch_fallback_preserved",
    ):
        require(dispatch.get(key) is True, f"policy:dispatch:{key}", failures)

    require(
        policy.get("permissions") == {"contents": "read", "pull_requests": "read", "actions": "write"},
        "policy:permissions",
        failures,
    )
    publication = policy.get("publication") if isinstance(policy.get("publication"), dict) else {}
    require(publication.get("auto_merge") is False, "policy:no_auto_merge", failures)
    require(publication.get("deploy_command") is False, "policy:no_deploy", failures)
    require(publication.get("public_mutation_before_explicit_merge") is False, "policy:no_public_mutation", failures)
    require(publication.get("pages_publish_after_authorized_merge") is True, "policy:pages_after_merge", failures)
    diagnostics = policy.get("diagnostics") if isinstance(policy.get("diagnostics"), dict) else {}
    require(diagnostics and all(value is True for value in diagnostics.values()), "policy:diagnostics", failures)
    boundary = policy.get("boundary") if isinstance(policy.get("boundary"), dict) else {}
    require(boundary and all(value is False for value in boundary.values()), "policy:boundary", failures)
    return failures


def verify_scheduler(text: str) -> list[str]:
    failures: list[str] = []
    required = (
        "name: Crypto-Astro Automatic Snapshot Refresh",
        "schedule:",
        "cron: '17 * * * *'",
        "workflow_dispatch:",
        "actions: write",
        "contents: read",
        "pull-requests: read",
        "cancel-in-progress: false",
        "ref: main",
        "git rev-parse origin/main",
        "gh run list --workflow crypto-astro-static-refresh-manual.yml",
        "test_defi_tvl_methodology_v0_1.py",
        "crypto_astro_static_refresh_bhrigu_compat_v0_1.py",
        "NO_DOUBLE_COUNTING=PASS",
        "NO_SYNTHETIC_FALLBACK=PASS",
        "NO_MATERIAL_CHANGE_RECHECK",
        "gh workflow run crypto-astro-static-refresh-manual.yml",
        "refresh_mode=DAILY_CADENCE",
        "Prove dispatched manual workflow is observable",
        "actions/upload-artifact@v4",
        "if-no-files-found: error",
    )
    for marker in required:
        require(marker in text, f"scheduler:missing:{marker}", failures)
    require(
        re.search(r"['\"]gh['\"],\s*['\"]pr['\"],\s*['\"]list['\"]", text) is not None
        and "'--state', 'open'" in text
        and "'--base', 'main'" in text,
        "scheduler:open_pr_query",
        failures,
    )
    triggers = {
        match.group(1)
        for match in re.finditer(r"^  (schedule|workflow_dispatch|push|pull_request):\s*$", text, flags=re.MULTILINE)
    }
    require(triggers == {"schedule", "workflow_dispatch"}, f"scheduler:triggers:{sorted(triggers)}", failures)
    require(len(re.findall(r"^\s*- cron:\s*'17 \* \* \* \*'\s*$", text, flags=re.MULTILINE)) == 1, "scheduler:cron_exact", failures)
    forbidden = {
        "contents_write": r"^\s*contents:\s*write\s*$",
        "git_push": r"\bgit\s+push\b",
        "git_commit": r"\bgit\s+commit\b",
        "pr_merge": r"\bgh\s+pr\s+merge\b|\bgh\s+api\b[^\n]*/merges\b",
        "deploy": r"actions/deploy-pages|\bvercel\b|\bdeploy-pages\b",
        "direct_pr_create": r"\bgh\s+pr\s+create\b",
    }
    for name, pattern in forbidden.items():
        require(re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE) is None, f"scheduler:forbidden:{name}", failures)
    return failures


def verify_repository(repo: Path) -> dict[str, Any]:
    policy_path = repo / "docs/crypto-astro-service/crypto_astro_automatic_refresh_activation_v0_1.json"
    workflow_path = repo / SCHEDULER
    policy = load_json(policy_path)
    checks = {
        "policy": verify_policy(policy),
        "scheduler": verify_scheduler(workflow_path.read_text(encoding="utf-8")),
    }
    matrix = {
        "17h": evaluate_decision(policy, snapshot_age_hours=17),
        "19h": evaluate_decision(policy, snapshot_age_hours=19),
        "20h": evaluate_decision(policy, snapshot_age_hours=20),
        "main_drift": evaluate_decision(policy, snapshot_age_hours=22, exact_main_match=False),
        "open_pr": evaluate_decision(policy, snapshot_age_hours=22, open_refresh_pr_count=1),
        "single_flight": evaluate_decision(policy, snapshot_age_hours=22, active_manual_run_count=1),
        "source_failure": evaluate_decision(policy, snapshot_age_hours=22, source_probe="FAIL"),
        "no_material_change": evaluate_decision(policy, snapshot_age_hours=22, material_change=False),
        "future": evaluate_decision(policy, snapshot_age_hours=-0.1),
    }
    expected = {
        "17h": "HOLD_MINIMUM_INTERVAL",
        "19h": "HOLD_BEFORE_AUTOMATIC_WINDOW",
        "20h": "DISPATCH_MANUAL_REFRESH",
        "main_drift": "BLOCK_MAIN_DRIFT",
        "open_pr": "BLOCK_OPEN_REFRESH_PR",
        "single_flight": "BLOCK_SINGLE_FLIGHT",
        "source_failure": "SOURCE_FAILURE_RECHECK",
        "no_material_change": "NO_MATERIAL_CHANGE_RECHECK",
        "future": "BLOCK_FUTURE_SNAPSHOT",
    }
    checks["decision_matrix"] = [
        f"matrix:{key}:{matrix.get(key)}" for key, expected_value in expected.items()
        if matrix.get(key) != expected_value
    ]
    failures = [f"{section}:{item}" for section, items in checks.items() for item in items]
    return {
        "schema_version": "crypto_astro_automatic_refresh_activation_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "policy": str(policy_path.relative_to(repo)),
        "scheduler": str(workflow_path.relative_to(repo)),
        "checks": {section: "PASS" if not items else "FAIL" for section, items in checks.items()},
        "decision_matrix": matrix,
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
