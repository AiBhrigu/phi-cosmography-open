#!/usr/bin/env python3
"""Trusted CI release for owner-authenticated assistant-dispatch generated refresh PRs.

This bridge approves the existing read-only PR acceptance workflows after proving:
owner-authenticated dispatch issue -> exact successful producer -> exact bot PR -> exact
generated refresh scope. It never merges or deploys.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from tools.crypto_astro_operations.verify_assistant_dispatch import (
    ISSUE_TITLE as DISPATCH_ISSUE_TITLE,
    OWNER_LOGIN,
    parse_request,
)
from tools.crypto_astro_operations.verify_generated_refresh_autopublish import (
    AUTHOR,
    MANUAL_PATH,
    PREFIX,
    TITLE,
    GateError,
    GitHub,
    exact_scope,
)
from tools.crypto_astro_operations.verify_generated_refresh_ci_release import (
    approve_and_wait,
    current_main_sha,
    list_pr_files,
    wait_required_runs,
)

RELEASE_TITLE = "Crypto-Astro assistant generated refresh CI release request"
RELEASE_SCHEMA = "crypto_astro_assistant_generated_refresh_ci_release_request_v0_1"
CALLBACK_SCHEMA = "crypto_astro_assistant_generated_refresh_ci_release_callback_v0_1"
TOPOLOGY_FILES = {
    ".github/workflows/crypto-astro-assistant-generated-refresh-ci-release.yml",
    "tools/crypto_astro_assistant_release/verify_release.py",
    "tools/crypto_astro_assistant_release/test_verify_release.py",
}


def fail(message: str) -> None:
    raise GateError(message)


def fields(body: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in (body or "").splitlines():
        if "=" in raw:
            key, value = raw.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def parse_release_issue(body: str) -> tuple[int, str, str, int]:
    value = fields(body)
    if value.get("SCHEMA") != RELEASE_SCHEMA:
        fail("RELEASE_SCHEMA_INVALID")
    try:
        pr_number = int(value["PR"])
        dispatch_issue = int(value["ASSISTANT_DISPATCH_ISSUE"])
    except Exception as exc:
        raise GateError("RELEASE_NUMERIC_FIELD_INVALID") from exc
    head = value.get("EXPECTED_HEAD_SHA", "")
    generation = value.get("EXPECTED_GENERATION_BASE_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        fail("RELEASE_HEAD_INVALID")
    if not re.fullmatch(r"[0-9a-f]{40}", generation):
        fail("RELEASE_GENERATION_BASE_INVALID")
    return pr_number, head, generation, dispatch_issue


def parse_pr_body(body: str) -> dict[str, Any]:
    patterns = {
        "refresh_mode": r"^- Refresh mode: ([A-Z_]+)\s*$",
        "operator_ref": r"^- Operator reference: ([A-Za-z0-9][A-Za-z0-9._:-]{0,159})\s*$",
        "reason": r"^- Reason: (.+)\s*$",
        "generation": r"^- Generation Base SHA: ([0-9a-f]{40})\s*$",
        "acceptance": r"^- Acceptance Base SHA: ([0-9a-f]{40})\s*$",
        "dispatch_issue": r"^- Assistant dispatch issue: ([0-9]+)\s*$",
    }
    matches = {key: re.search(pattern, body or "", re.M) for key, pattern in patterns.items()}
    if not all(matches.values()):
        fail("ASSISTANT_PR_BODY_PROVENANCE_INVALID")
    return {
        "refresh_mode": matches["refresh_mode"].group(1),
        "operator_ref": matches["operator_ref"].group(1),
        "reason": matches["reason"].group(1),
        "generation": matches["generation"].group(1),
        "acceptance": matches["acceptance"].group(1),
        "dispatch_issue": int(matches["dispatch_issue"].group(1)),
    }


def parse_comment(body: str) -> dict[str, str]:
    return fields(body)


def validate_dispatch_comments(
    comments: list[dict[str, Any]],
    *,
    repo: str,
    request_id: str,
    manual_id: int,
    generation: str,
    head_ref: str,
    pr_number: int,
) -> None:
    accepted = False
    callback = False
    expected_pr_url = f"https://github.com/{repo}/pull/{pr_number}"
    for comment in comments:
        if comment.get("user", {}).get("login") != "github-actions[bot]":
            continue
        value = parse_comment(comment.get("body", ""))
        if (
            value.get("SCHEMA") == "crypto_astro_assistant_dispatch_result_v0_1"
            and value.get("STATUS") == "DISPATCH_ACCEPTED"
            and value.get("REQUEST_ID") == request_id
            and value.get("EXPECTED_MAIN_SHA") == generation
            and value.get("TARGET_WORKFLOW") == "crypto-astro-static-refresh-manual.yml"
            and value.get("TARGET_REF") == "main"
        ):
            accepted = True
        if (
            value.get("SCHEMA") == "crypto_astro_assistant_dispatch_callback_v0_1"
            and value.get("DISPATCH_REQUEST_ID") == request_id
            and value.get("WORKFLOW_RUN_ID") == str(manual_id)
            and value.get("EXPECTED_MAIN_SHA") == generation
            and value.get("ACTUAL_BASE_SHA") == generation
            and value.get("JOB_STATUS") == "success"
            and value.get("MATERIAL_CHANGE") == "true"
            and value.get("GENERATED_BRANCH") == head_ref
            and value.get("GENERATED_PR_URL") == expected_pr_url
            and value.get("FINAL_OUTCOME") == "PASS_REVIEW_PR_OPENED"
        ):
            callback = True
    if not accepted:
        fail("ASSISTANT_DISPATCH_ACCEPTED_PROOF_MISSING")
    if not callback:
        fail("ASSISTANT_DISPATCH_CALLBACK_PROOF_MISSING")


def validate_pr_identity(
    pr: dict[str, Any],
    repo: str,
    *,
    expected_head: str,
    expected_generation: str,
    expected_dispatch_issue: int,
) -> tuple[int, str, str, dict[str, Any]]:
    if pr.get("state") != "open":
        fail("PR_NOT_OPEN")
    if pr.get("title") != TITLE:
        fail("WRONG_TITLE")
    if pr.get("user", {}).get("login") != AUTHOR:
        fail("WRONG_AUTHOR")
    if pr.get("base", {}).get("ref") != "main":
        fail("WRONG_BASE")
    if pr.get("head", {}).get("repo", {}).get("full_name") != repo:
        fail("FORK_PR_REJECTED")
    head_ref = pr.get("head", {}).get("ref", "")
    if not head_ref.startswith(PREFIX):
        fail("WRONG_HEAD_PREFIX")
    suffix = head_ref[len(PREFIX):]
    if not suffix.isdigit():
        fail("MANUAL_RUN_PROVENANCE_INVALID")
    head_sha = pr.get("head", {}).get("sha", "")
    if head_sha != expected_head:
        fail("HEAD_DRIFT")
    body = parse_pr_body(pr.get("body", ""))
    if body["generation"] != expected_generation:
        fail("GENERATION_BASE_DRIFT")
    if body["dispatch_issue"] != expected_dispatch_issue:
        fail("ASSISTANT_DISPATCH_ISSUE_DRIFT")
    return int(suffix), head_ref, head_sha, body


def validate_rebound_pr(
    pr: dict[str, Any],
    repo: str,
    *,
    expected_head: str,
    expected_generation: str,
    expected_dispatch_issue: int,
    expected_manual_id: int,
    expected_head_ref: str,
    expected_acceptance: str,
) -> dict[str, Any]:
    manual_after, head_ref_after, head_after, body_after = validate_pr_identity(
        pr,
        repo,
        expected_head=expected_head,
        expected_generation=expected_generation,
        expected_dispatch_issue=expected_dispatch_issue,
    )
    if (
        manual_after != expected_manual_id
        or head_ref_after != expected_head_ref
        or head_after != expected_head
        or body_after["acceptance"] != expected_acceptance
    ):
        fail("BASE_OR_IDENTITY_DRIFT")
    return body_after


def compare_topology_only(gh: GitHub, repo: str, generation: str, current_main: str) -> set[str]:
    if generation == current_main:
        return set()
    value, _ = gh.request(f"/repos/{repo}/compare/{generation}...{current_main}")
    changed = {item["filename"] for item in value.get("files", [])}
    if not changed or not changed <= TOPOLOGY_FILES:
        fail(f"MAIN_DRIFT:{sorted(changed)}")
    return changed


def canonical_acceptance_body(body: str, current_main: str) -> str:
    text, count = re.subn(
        r"^- Acceptance Base SHA: [0-9a-f]{40}\s*$",
        f"- Acceptance Base SHA: {current_main}",
        body or "",
        count=1,
        flags=re.M,
    )
    if count != 1:
        fail("ACCEPTANCE_BASE_LINE_MISSING")
    return text


def run(repo: str, token: str, issue_number: int, report_path: Path) -> int:
    gh = GitHub(repo, token)
    report: dict[str, Any] = {
        "schema_version": "crypto_astro_assistant_generated_refresh_ci_release_v0_1",
        "status": "RUNNING",
        "publication_mode": "EXPLICIT_AUTHORIZED_MERGE_ONLY",
        "merge_attempts": 0,
        "deploy_attempts": 0,
    }
    try:
        release_issue, _ = gh.request(f"/repos/{repo}/issues/{issue_number}")
        if (
            release_issue.get("title") != RELEASE_TITLE
            or release_issue.get("user", {}).get("login") != OWNER_LOGIN
            or release_issue.get("author_association") != "OWNER"
        ):
            fail("RELEASE_ISSUE_NOT_OWNER_AUTHENTICATED")
        pr_number, expected_head, expected_generation, dispatch_issue_number = parse_release_issue(
            release_issue.get("body", "")
        )

        pr, _ = gh.request(f"/repos/{repo}/pulls/{pr_number}")
        manual_id, head_ref, head_sha, pr_body = validate_pr_identity(
            pr,
            repo,
            expected_head=expected_head,
            expected_generation=expected_generation,
            expected_dispatch_issue=dispatch_issue_number,
        )
        if not exact_scope(list_pr_files(gh, repo, pr_number)):
            fail("WRONG_GENERATED_SCOPE")

        manual, _ = gh.request(f"/repos/{repo}/actions/runs/{manual_id}")
        if (
            manual.get("path") != MANUAL_PATH
            or manual.get("event") != "workflow_dispatch"
            or manual.get("head_sha") != expected_generation
            or manual.get("conclusion") != "success"
        ):
            fail("MANUAL_RUN_PROVENANCE_INVALID")
        if manual.get("actor", {}).get("login") != "github-actions[bot]":
            fail("MANUAL_RUN_ACTOR_INVALID")

        dispatch_issue, _ = gh.request(f"/repos/{repo}/issues/{dispatch_issue_number}")
        if (
            dispatch_issue.get("title") != DISPATCH_ISSUE_TITLE
            or dispatch_issue.get("user", {}).get("login") != OWNER_LOGIN
            or dispatch_issue.get("author_association") != "OWNER"
            or dispatch_issue.get("state") != "closed"
            or dispatch_issue.get("locked") is not True
        ):
            fail("ASSISTANT_DISPATCH_ISSUE_INVALID")
        request = parse_request(
            dispatch_issue.get("body", ""),
            title=DISPATCH_ISSUE_TITLE,
            actor_login=OWNER_LOGIN,
            author_login=OWNER_LOGIN,
            author_association="OWNER",
            current_main_sha=expected_generation,
        )
        if (
            request.refresh_mode != pr_body["refresh_mode"]
            or request.operator_ref != pr_body["operator_ref"]
            or request.refresh_reason != pr_body["reason"]
            or request.expected_main_sha != expected_generation
        ):
            fail("ASSISTANT_DISPATCH_REQUEST_PR_MISMATCH")

        comments, _ = gh.request(f"/repos/{repo}/issues/{dispatch_issue_number}/comments?per_page=100")
        validate_dispatch_comments(
            comments,
            repo=repo,
            request_id=request.request_id,
            manual_id=manual_id,
            generation=expected_generation,
            head_ref=head_ref,
            pr_number=pr_number,
        )

        main = current_main_sha(gh, repo)
        drift = compare_topology_only(gh, repo, expected_generation, main)
        new_body = canonical_acceptance_body(pr.get("body", ""), main)
        if new_body != pr.get("body", ""):
            gh.request(f"/repos/{repo}/pulls/{pr_number}", "PATCH", {"body": new_body})

        pr_after, _ = gh.request(f"/repos/{repo}/pulls/{pr_number}")
        if current_main_sha(gh, repo) != main:
            fail("MAIN_MOVED_DURING_RELEASE")
        validate_rebound_pr(
            pr_after,
            repo,
            expected_head=head_sha,
            expected_generation=expected_generation,
            expected_dispatch_issue=dispatch_issue_number,
            expected_manual_id=manual_id,
            expected_head_ref=head_ref,
            expected_acceptance=main,
        )

        runs = wait_required_runs(gh, repo, head_sha)
        result = approve_and_wait(gh, repo, head_sha, runs)
        report.update(
            {
                "status": "PASS",
                "pr": pr_number,
                "head_sha": head_sha,
                "generation_base_sha": expected_generation,
                "acceptance_base_sha": main,
                "assistant_dispatch_issue": dispatch_issue_number,
                "manual_run_id": manual_id,
                "topology_drift_files": sorted(drift),
                "required_ci": result,
                "publication_mode": "EXPLICIT_AUTHORIZED_MERGE_ONLY",
                "merge_attempts": 0,
                "deploy_attempts": 0,
            }
        )
        return 0
    except Exception as exc:
        report.update({"status": "FAIL_CLOSED", "reason": str(exc)})
        return 1
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.repo, args.token, args.issue_number, Path(args.report)))


if __name__ == "__main__":
    main()
