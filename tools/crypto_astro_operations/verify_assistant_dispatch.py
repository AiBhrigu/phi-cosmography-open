#!/usr/bin/env python3
"""Fail-closed verifier for the owner-authenticated Crypto-Astro dispatch bridge."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLICY_SCHEMA = "crypto_astro_assistant_dispatch_policy_v0_1"
REQUEST_SCHEMA = "crypto_astro_assistant_dispatch_request_v0_1"
CALLBACK_SCHEMA = "crypto_astro_assistant_dispatch_callback_v0_1"
ISSUE_TITLE = "Crypto-Astro assistant dispatch request"
OWNER_LOGIN = "AiBhrigu"
TARGET_REPOSITORY = "AiBhrigu/phi-cosmography-open"
TARGET_WORKFLOW = "crypto-astro-static-refresh-manual.yml"
TARGET_REF = "main"
ORDERED_KEYS = [
    "SCHEMA",
    "REQUEST_ID",
    "REFRESH_MODE",
    "OPERATOR_REF",
    "REFRESH_REASON",
    "EXPECTED_MAIN_SHA",
]
ALLOWED_MODES = [
    "DAILY_CADENCE",
    "PRE_REPORT",
    "MATERIAL_MARKET_EVENT",
    "REPEATABILITY_PROOF",
    "SOURCE_OR_SCHEMA_REPAIR",
]
FORBIDDEN_TOKENS = ("```", "http://", "https://", "www.", "${", "$(", "\t", "\r")
OPERATOR_BOUNDARY = (
    "Workflow may push one fully validated review branch and open one review PR. "
    "It may not merge or issue a deployment command. Publication follows only "
    "after explicit merge authorization."
)


class DispatchValidationError(ValueError):
    """Known public-safe request validation failure."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class DispatchRequest:
    request_id: str
    refresh_mode: str
    operator_ref: str
    refresh_reason: str
    expected_main_sha: str

    def as_dict(self) -> dict[str, str]:
        return {
            "request_id": self.request_id,
            "refresh_mode": self.refresh_mode,
            "operator_ref": self.operator_ref,
            "refresh_reason": self.refresh_reason,
            "expected_main_sha": self.expected_main_sha,
        }


def require(condition: bool, code: str) -> None:
    if not condition:
        raise DispatchValidationError(code)


def load_policy(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("POLICY_NOT_OBJECT")
    return value


def validate_policy(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    def check(condition: bool, code: str) -> None:
        if not condition:
            failures.append(code)

    check(policy.get("schema_version") == POLICY_SCHEMA, "policy:schema_version")
    check(policy.get("repository") == TARGET_REPOSITORY, "policy:repository")
    check(policy.get("owner_login") == OWNER_LOGIN, "policy:owner_login")
    check(policy.get("issue_title") == ISSUE_TITLE, "policy:issue_title")

    trigger = policy.get("trigger") if isinstance(policy.get("trigger"), dict) else {}
    check(trigger == {"event": "issues", "action": "opened"}, "policy:trigger")

    request = policy.get("request_contract") if isinstance(policy.get("request_contract"), dict) else {}
    check(request.get("schema_value") == REQUEST_SCHEMA, "policy:request_schema")
    check(request.get("ordered_keys") == ORDERED_KEYS, "policy:ordered_keys")
    check(request.get("exact_line_count") == 6, "policy:line_count")
    check(request.get("allowed_modes") == ALLOWED_MODES, "policy:allowed_modes")
    check(request.get("max_lengths") == {"REQUEST_ID": 64, "OPERATOR_REF": 80, "REFRESH_REASON": 240}, "policy:max_lengths")
    check(request.get("forbidden_tokens") == list(FORBIDDEN_TOKENS), "policy:forbidden_tokens")

    identity = policy.get("identity") if isinstance(policy.get("identity"), dict) else {}
    check(
        identity == {
            "author_login": OWNER_LOGIN,
            "author_association": "OWNER",
            "actor_login": OWNER_LOGIN,
        },
        "policy:identity",
    )

    dispatch = policy.get("dispatch") if isinstance(policy.get("dispatch"), dict) else {}
    check(dispatch.get("target_workflow") == TARGET_WORKFLOW, "policy:target_workflow")
    check(dispatch.get("target_ref") == TARGET_REF, "policy:target_ref")
    check(dispatch.get("fixed_repository") == TARGET_REPOSITORY, "policy:fixed_repository")
    check(
        dispatch.get("required_inputs")
        == ["refresh_mode", "operator_ref", "refresh_reason", "expected_main_sha", "dispatch_request_issue"],
        "policy:required_inputs",
    )
    for key in (
        "workflow_target_from_issue_forbidden",
        "repository_from_issue_forbidden",
        "ref_from_issue_forbidden",
        "shell_eval_forbidden",
    ):
        check(dispatch.get(key) is True, f"policy:dispatch:{key}")

    check(
        policy.get("permissions")
        == {"contents": "read", "actions": "write", "issues": "write", "pull_requests": "read"},
        "policy:permissions",
    )

    callback = policy.get("callback") if isinstance(policy.get("callback"), dict) else {}
    check(callback.get("schema_version") == CALLBACK_SCHEMA, "policy:callback_schema")
    check(
        callback.get("required_fields")
        == [
            "DISPATCH_REQUEST_ID",
            "WORKFLOW_RUN_ID",
            "WORKFLOW_RUN_URL",
            "EXPECTED_MAIN_SHA",
            "ACTUAL_BASE_SHA",
            "JOB_STATUS",
            "MATERIAL_CHANGE",
            "GENERATED_BRANCH",
            "GENERATED_PR_URL",
            "FINAL_OUTCOME",
        ],
        "policy:callback_fields",
    )
    check(callback.get("close_issue") is True, "policy:callback_close")
    check(callback.get("lock_reason") == "resolved", "policy:callback_lock")

    boundary = policy.get("boundary") if isinstance(policy.get("boundary"), dict) else {}
    check(bool(boundary) and all(value is False for value in boundary.values()), "policy:boundary")
    return failures


def parse_request(
    body: str,
    *,
    title: str,
    actor_login: str,
    author_login: str,
    author_association: str,
    current_main_sha: str,
) -> DispatchRequest:
    require(title == ISSUE_TITLE, "WRONG_TITLE")
    require(actor_login == OWNER_LOGIN, "ACTOR_NOT_OWNER")
    require(author_login == OWNER_LOGIN, "AUTHOR_NOT_OWNER")
    require(author_association == "OWNER", "AUTHOR_ASSOCIATION_NOT_OWNER")
    require(re.fullmatch(r"[0-9a-f]{40}", current_main_sha) is not None, "CURRENT_MAIN_SHA_INVALID")
    require("\x00" not in body, "NUL_FORBIDDEN")
    for token in FORBIDDEN_TOKENS:
        require(token not in body, "FORBIDDEN_TOKEN")

    lines = body.splitlines()
    require(len(lines) == 6, "EXACT_SIX_LINES_REQUIRED")
    require(all(line and line == line.strip() for line in lines), "BLANK_OR_PADDED_LINE")
    require(all(line.count("=") == 1 for line in lines), "ONE_EQUALS_PER_LINE_REQUIRED")

    pairs = [line.split("=", 1) for line in lines]
    keys = [key for key, _ in pairs]
    require(keys == ORDERED_KEYS, "KEY_ORDER_OR_SET_INVALID")
    require(len(set(keys)) == len(keys), "DUPLICATE_KEY")
    values = dict(pairs)

    require(values["SCHEMA"] == REQUEST_SCHEMA, "SCHEMA_INVALID")
    require(re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,63}", values["REQUEST_ID"]) is not None, "REQUEST_ID_INVALID")
    require(values["REFRESH_MODE"] in ALLOWED_MODES, "REFRESH_MODE_INVALID")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}", values["OPERATOR_REF"]) is not None, "OPERATOR_REF_INVALID")

    reason = values["REFRESH_REASON"]
    require(1 <= len(reason) <= 240, "REFRESH_REASON_LENGTH_INVALID")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 .,;:_()/-]{0,239}", reason) is not None, "REFRESH_REASON_CHARACTERS_INVALID")
    require("://" not in reason and "www." not in reason, "REFRESH_REASON_URL_FORBIDDEN")

    expected_sha = values["EXPECTED_MAIN_SHA"]
    require(re.fullmatch(r"[0-9a-f]{40}", expected_sha) is not None, "EXPECTED_MAIN_SHA_INVALID")
    require(expected_sha == current_main_sha, "EXPECTED_MAIN_SHA_STALE")

    return DispatchRequest(
        request_id=values["REQUEST_ID"],
        refresh_mode=values["REFRESH_MODE"],
        operator_ref=values["OPERATOR_REF"],
        refresh_reason=reason,
        expected_main_sha=expected_sha,
    )


def verify_bridge_workflow(text: str) -> list[str]:
    failures: list[str] = []

    def check(condition: bool, code: str) -> None:
        if not condition:
            failures.append(code)

    required = [
        "name: Crypto-Astro Assistant Dispatch",
        "issues:",
        "types: [opened]",
        f"github.event.issue.title == '{ISSUE_TITLE}'",
        "github.event.issue.user.login == 'AiBhrigu'",
        "github.event.issue.author_association == 'OWNER'",
        "github.actor == 'AiBhrigu'",
        "contents: read",
        "actions: write",
        "issues: write",
        "pull-requests: read",
        "verify_assistant_dispatch.py validate-request",
        "OPEN_DISPATCH_COUNT",
        "OPEN_REFRESH_COUNT",
        f"gh workflow run {TARGET_WORKFLOW}",
        "--ref main",
        "-f expected_main_sha=",
        "-f dispatch_request_issue=",
        "DISPATCH_ACCEPTED",
        "gh issue close",
        "gh issue lock",
    ]
    for marker in required:
        check(marker in text, f"bridge:missing:{marker}")

    check(re.search(r"^  schedule:\s*$", text, re.MULTILINE) is None, "bridge:schedule")
    check(re.search(r"^  push:\s*$", text, re.MULTILINE) is None, "bridge:push")
    check("repository_dispatch:" not in text, "bridge:repository_dispatch")
    check("workflow_dispatch:" not in text, "bridge:self_workflow_dispatch")
    check("contents: write" not in text, "bridge:contents_write")
    check("pull-requests: write" not in text, "bridge:pull_requests_write")
    check("pages: write" not in text, "bridge:pages_write")
    check("id-token: write" not in text, "bridge:id_token_write")
    check("secrets." not in text, "bridge:secret_reference")
    check("eval " not in text and "bash -c" not in text and "sh -c" not in text, "bridge:shell_eval")
    check(text.count(f"gh workflow run {TARGET_WORKFLOW}") == 1, "bridge:fixed_target_count")
    check("gh api" not in text, "bridge:arbitrary_gh_api")
    return failures


def verify_manual_workflow(text: str) -> list[str]:
    failures: list[str] = []

    def check(condition: bool, code: str) -> None:
        if not condition:
            failures.append(code)

    required = [
        "expected_main_sha:",
        "dispatch_request_issue:",
        "CRYPTO_ASTRO_EXPECTED_MAIN_SHA",
        "CRYPTO_ASTRO_DISPATCH_REQUEST_ISSUE",
        "EXPECTED_MAIN_SHA_REQUIRED_WITH_DISPATCH_ISSUE",
        "DISPATCH_REQUEST_ISSUE_MUST_BE_NUMERIC",
        "test \"$LOCAL_SHA\" = \"$CRYPTO_ASTRO_EXPECTED_MAIN_SHA\"",
        "id: source_refresh",
        "id: consumer",
        "id: memory",
        "id: atomic",
        "id: open_pr",
        "pr_url=",
        "name: Return assistant dispatch callback",
        "always()",
        CALLBACK_SCHEMA,
        "WORKFLOW_RUN_ID=",
        "WORKFLOW_RUN_URL=",
        "FINAL_OUTCOME=",
        "gh issue comment",
        "gh issue close",
        "gh issue lock",
    ]
    for marker in required:
        check(marker in text, f"manual:missing:{marker}")

    check("issues: write" in text, "manual:issues_write")
    check(re.search(r"^  schedule:\s*$", text, re.MULTILINE) is None, "manual:schedule")
    check(re.search(r"^  push:\s*$", text, re.MULTILINE) is None, "manual:push")
    check("gh pr merge" not in text, "manual:auto_merge")
    check("actions/deploy-pages" not in text, "manual:deploy_command")
    return failures


def verify_pr_workflow(text: str) -> list[str]:
    required = [
        "name: Crypto-Astro Assistant Dispatch PR",
        ".github/workflows/crypto-astro-assistant-dispatch.yml",
        ".github/workflows/crypto-astro-assistant-dispatch-pr.yml",
        ".github/workflows/crypto-astro-static-refresh-manual.yml",
        ".github/workflows/crypto-astro-operational-cadence-pr.yml",
        ".github/workflows/crypto-astro-snapshot-memory-pr.yml",
        "CRYPTO_ASTRO_ASSISTANT_DISPATCH_v0_1.md",
        "crypto_astro_assistant_dispatch_v0_1.json",
        "verify_assistant_dispatch.py",
        "test_verify_assistant_dispatch.py",
        "ASSISTANT_DISPATCH_EXACT_SCOPE=PASS",
        "git diff --exit-code",
    ]
    return [f"pr_workflow:missing:{marker}" for marker in required if marker not in text]


def verify_repository(repo: Path) -> dict[str, Any]:
    policy_path = repo / "docs/crypto-astro-service/crypto_astro_assistant_dispatch_v0_1.json"
    policy = load_policy(policy_path)
    checks = {
        "policy": validate_policy(policy),
        "bridge_workflow": verify_bridge_workflow((repo / ".github/workflows/crypto-astro-assistant-dispatch.yml").read_text(encoding="utf-8")),
        "manual_workflow": verify_manual_workflow((repo / ".github/workflows/crypto-astro-static-refresh-manual.yml").read_text(encoding="utf-8")),
        "pr_workflow": verify_pr_workflow((repo / ".github/workflows/crypto-astro-assistant-dispatch-pr.yml").read_text(encoding="utf-8")),
    }
    cadence_text = (repo / ".github/workflows/crypto-astro-operational-cadence-pr.yml").read_text(encoding="utf-8")
    snapshot_text = (repo / ".github/workflows/crypto-astro-snapshot-memory-pr.yml").read_text(encoding="utf-8")
    checks["cadence_applicability"] = [
        "cadence:assistant_scope_missing"
        for _ in [0]
        if "assistant_dispatch_scope" not in cadence_text or "ASSISTANT_DISPATCH_FILE_SCOPE=PASS" not in cadence_text
    ]
    checks["snapshot_memory_applicability"] = [
        "snapshot:assistant_scope_missing"
        for _ in [0]
        if "assistant_dispatch_maintenance" not in snapshot_text or "assistant_dispatch_maintenance" not in snapshot_text
    ]
    failures = [f"{section}:{value}" for section, values in checks.items() for value in values]
    return {
        "schema_version": "crypto_astro_assistant_dispatch_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "policy_path": str(policy_path.relative_to(repo)),
        "checks": {section: "PASS" if not values else "FAIL" for section, values in checks.items()},
        "failures": failures,
    }


def write_outputs(path: str, values: dict[str, str]) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def validate_request_command(args: argparse.Namespace) -> int:
    body = Path(args.body_file).read_text(encoding="utf-8")
    try:
        request = parse_request(
            body,
            title=args.title,
            actor_login=args.actor_login,
            author_login=args.author_login,
            author_association=args.author_association,
            current_main_sha=args.current_main_sha,
        )
    except DispatchValidationError as exc:
        payload = {
            "schema_version": "crypto_astro_assistant_dispatch_request_validation_v0_1",
            "status": "FAIL",
            "reason_code": exc.code,
        }
        write_outputs(args.github_output, {"valid": "false", "reason_code": exc.code})
    else:
        payload = {
            "schema_version": "crypto_astro_assistant_dispatch_request_validation_v0_1",
            "status": "PASS",
            **request.as_dict(),
        }
        write_outputs(
            args.github_output,
            {
                "valid": "true",
                "reason_code": "PASS",
                **request.as_dict(),
            },
        )
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        report = Path(args.report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(rendered, encoding="utf-8")
    return 0


def verify_repository_command(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    report = verify_repository(repo)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.report:
        path = (repo / args.report).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify-repository")
    verify.add_argument("--repo", default=".")
    verify.add_argument("--report")

    request = sub.add_parser("validate-request")
    request.add_argument("--body-file", required=True)
    request.add_argument("--title", required=True)
    request.add_argument("--actor-login", required=True)
    request.add_argument("--author-login", required=True)
    request.add_argument("--author-association", required=True)
    request.add_argument("--current-main-sha", required=True)
    request.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT", ""))
    request.add_argument("--report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "validate-request":
        return validate_request_command(args)
    return verify_repository_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
