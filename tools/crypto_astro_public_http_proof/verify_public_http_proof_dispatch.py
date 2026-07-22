#!/usr/bin/env python3
"""Fail-closed verifier for the owner-authenticated public HTTP proof bridge."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLICY_SCHEMA = "crypto_astro_public_http_proof_dispatch_policy_v0_1"
REQUEST_SCHEMA = "crypto_astro_public_http_proof_dispatch_request_v0_1"
CALLBACK_SCHEMA = "crypto_astro_public_http_proof_dispatch_callback_v0_1"
ISSUE_TITLE = "Crypto-Astro public HTTP proof dispatch request"
OWNER_LOGIN = "AiBhrigu"
TARGET_REPOSITORY = "AiBhrigu/phi-cosmography-open"
TARGET_WORKFLOW = "crypto-astro-public-http-proof.yml"
TARGET_REF = "main"
ORDERED_KEYS = ["SCHEMA", "REQUEST_ID", "OPERATOR_REF", "EXPECTED_MAIN_SHA"]
FORBIDDEN_TOKENS = ("```", "http://", "https://", "www.", "${", "$(", "\t", "\r")

POLICY_PATH = Path(
    "docs/crypto-astro-service/crypto_astro_public_http_proof_dispatch_v0_1.json"
)
DOC_PATH = Path(
    "docs/crypto-astro-service/CRYPTO_ASTRO_PUBLIC_HTTP_PROOF_DISPATCH_v0_1.md"
)
BRIDGE_PATH = Path(
    ".github/workflows/crypto-astro-public-http-proof-dispatch.yml"
)
PR_WORKFLOW_PATH = Path(
    ".github/workflows/crypto-astro-public-http-proof-dispatch-pr.yml"
)
TARGET_WORKFLOW_PATH = Path(
    ".github/workflows/crypto-astro-public-http-proof.yml"
)
VERIFIER_PATH = Path(
    "tools/crypto_astro_public_http_proof/verify_public_http_proof_dispatch.py"
)
TEST_PATH = Path(
    "tools/crypto_astro_public_http_proof/test_verify_public_http_proof_dispatch.py"
)

EXACT_IMPLEMENTATION_SCOPE = {
    str(BRIDGE_PATH),
    str(PR_WORKFLOW_PATH),
    str(VERIFIER_PATH),
    str(TEST_PATH),
    str(POLICY_PATH),
    str(DOC_PATH),
}


class DispatchValidationError(ValueError):
    """Known public-safe request validation failure."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class DispatchRequest:
    request_id: str
    operator_ref: str
    expected_main_sha: str

    def as_dict(self) -> dict[str, str]:
        return {
            "request_id": self.request_id,
            "operator_ref": self.operator_ref,
            "expected_main_sha": self.expected_main_sha,
        }


def require(condition: bool, code: str) -> None:
    if not condition:
        raise DispatchValidationError(code)


def read_text(repo: Path, path: Path) -> str:
    target = repo / path
    if not target.is_file():
        raise RuntimeError(f"MISSING_FILE:{path}")
    return target.read_text(encoding="utf-8")


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
    check(
        policy.get("trigger") == {"event": "issues", "action": "opened"},
        "policy:trigger",
    )

    request = (
        policy.get("request_contract")
        if isinstance(policy.get("request_contract"), dict)
        else {}
    )
    check(request.get("schema_value") == REQUEST_SCHEMA, "policy:request_schema")
    check(request.get("ordered_keys") == ORDERED_KEYS, "policy:ordered_keys")
    check(request.get("exact_line_count") == 4, "policy:line_count")
    check(
        request.get("max_lengths") == {"REQUEST_ID": 64, "OPERATOR_REF": 80},
        "policy:max_lengths",
    )
    check(
        request.get("forbidden_tokens") == list(FORBIDDEN_TOKENS),
        "policy:forbidden_tokens",
    )

    check(
        policy.get("identity")
        == {
            "author_login": OWNER_LOGIN,
            "author_association": "OWNER",
            "actor_login": OWNER_LOGIN,
        },
        "policy:identity",
    )

    dispatch = policy.get("dispatch") if isinstance(policy.get("dispatch"), dict) else {}
    check(dispatch.get("fixed_repository") == TARGET_REPOSITORY, "policy:repository_lock")
    check(dispatch.get("target_workflow") == TARGET_WORKFLOW, "policy:workflow_lock")
    check(dispatch.get("target_ref") == TARGET_REF, "policy:ref_lock")
    check(
        dispatch.get("required_inputs") == ["operator_ref", "expected_main_sha"],
        "policy:required_inputs",
    )
    for key in (
        "workflow_target_from_issue_forbidden",
        "repository_from_issue_forbidden",
        "ref_from_issue_forbidden",
        "command_from_issue_forbidden",
        "shell_eval_forbidden",
    ):
        check(dispatch.get(key) is True, f"policy:dispatch:{key}")

    check(
        policy.get("preflight")
        == {
            "current_main_sha_lock": True,
            "single_open_request": True,
            "zero_active_target_runs": True,
        },
        "policy:preflight",
    )
    check(
        policy.get("run_resolution")
        == {
            "event": "workflow_dispatch",
            "branch": "main",
            "head_sha_lock": True,
            "created_after_dispatch_lock": True,
            "single_new_run_required": True,
        },
        "policy:run_resolution",
    )
    check(
        policy.get("permissions")
        == {"contents": "read", "actions": "write", "issues": "write"},
        "policy:permissions",
    )

    callback = policy.get("callback") if isinstance(policy.get("callback"), dict) else {}
    check(callback.get("schema_version") == CALLBACK_SCHEMA, "policy:callback_schema")
    check(
        callback.get("required_fields")
        == [
            "REQUEST_ID",
            "WORKFLOW_RUN_ID",
            "WORKFLOW_RUN_URL",
            "EXPECTED_MAIN_SHA",
            "ACTUAL_HEAD_SHA",
            "JOB_STATUS",
            "FINAL_OUTCOME",
        ],
        "policy:callback_fields",
    )
    check(callback.get("close_issue") is True, "policy:callback_close")
    check(callback.get("lock_reason") == "resolved", "policy:callback_lock")

    boundary = policy.get("boundary") if isinstance(policy.get("boundary"), dict) else {}
    check(bool(boundary), "policy:boundary_missing")
    check(all(value is False for value in boundary.values()), "policy:boundary_open")
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
    require(
        re.fullmatch(r"[0-9a-f]{40}", current_main_sha) is not None,
        "CURRENT_MAIN_SHA_INVALID",
    )
    require("\x00" not in body, "NUL_FORBIDDEN")
    for token in FORBIDDEN_TOKENS:
        require(token not in body, "FORBIDDEN_TOKEN")

    lines = body.splitlines()
    require(len(lines) == 4, "EXACT_FOUR_LINES_REQUIRED")
    require(all(line and line == line.strip() for line in lines), "BLANK_OR_PADDED_LINE")
    require(all(line.count("=") == 1 for line in lines), "ONE_EQUALS_PER_LINE_REQUIRED")

    pairs = [line.split("=", 1) for line in lines]
    keys = [key for key, _ in pairs]
    require(keys == ORDERED_KEYS, "KEY_ORDER_OR_SET_INVALID")
    require(len(set(keys)) == len(keys), "DUPLICATE_KEY")
    values = dict(pairs)

    require(values["SCHEMA"] == REQUEST_SCHEMA, "SCHEMA_INVALID")
    require(
        re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,63}", values["REQUEST_ID"])
        is not None,
        "REQUEST_ID_INVALID",
    )
    require(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}", values["OPERATOR_REF"])
        is not None,
        "OPERATOR_REF_INVALID",
    )
    expected_sha = values["EXPECTED_MAIN_SHA"]
    require(
        re.fullmatch(r"[0-9a-f]{40}", expected_sha) is not None,
        "EXPECTED_MAIN_SHA_INVALID",
    )
    require(expected_sha == current_main_sha, "EXPECTED_MAIN_SHA_STALE")

    return DispatchRequest(
        request_id=values["REQUEST_ID"],
        operator_ref=values["OPERATOR_REF"],
        expected_main_sha=expected_sha,
    )


def verify_bridge_workflow(text: str) -> list[str]:
    failures: list[str] = []

    def check(condition: bool, code: str) -> None:
        if not condition:
            failures.append(code)

    required = [
        "name: Crypto-Astro Public HTTP Proof Dispatch",
        "issues:",
        "types: [opened]",
        f"github.event.issue.title == '{ISSUE_TITLE}'",
        "github.event.issue.user.login == 'AiBhrigu'",
        "github.event.issue.author_association == 'OWNER'",
        "github.actor == 'AiBhrigu'",
        "contents: read",
        "actions: write",
        "issues: write",
        "verify_public_http_proof_dispatch.py validate-request",
        "OPEN_REQUEST_COUNT",
        "ACTIVE_PROOF_RUN_COUNT",
        f"gh workflow run {TARGET_WORKFLOW}",
        "--ref main",
        "-f operator_ref=",
        "-f expected_main_sha=",
        "DISPATCHED_AT",
        "gh run list",
        "gh run watch",
        CALLBACK_SCHEMA,
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
    check("gh api" not in text, "bridge:arbitrary_gh_api")
    check(text.count(f"gh workflow run {TARGET_WORKFLOW}") == 1, "bridge:fixed_target_count")
    check("--repo" not in text, "bridge:repository_override")
    return failures


def verify_target_workflow(text: str) -> list[str]:
    failures: list[str] = []

    def check(condition: bool, code: str) -> None:
        if not condition:
            failures.append(code)

    required = [
        "name: Crypto-Astro Public HTTP Proof",
        "workflow_dispatch:",
        "operator_ref:",
        "expected_main_sha:",
        "contents: read",
        "test \"$CURRENT_MAIN_SHA\" = \"$EXPECTED_MAIN_SHA\"",
        "Verify exact external HTTP proof",
        "verify_public_http_proof.py",
        "Upload HTTP proof evidence",
    ]
    for marker in required:
        check(marker in text, f"target:missing:{marker}")
    check(re.search(r"^  schedule:\s*$", text, re.MULTILINE) is None, "target:schedule")
    check("contents: write" not in text, "target:contents_write")
    check("actions: write" not in text, "target:actions_write")
    check("issues: write" not in text, "target:issues_write")
    check("pages: write" not in text, "target:pages_write")
    check("actions/deploy-pages" not in text, "target:deploy")
    return failures


def verify_pr_workflow(text: str) -> list[str]:
    required = [
        "name: Crypto-Astro Public HTTP Proof Dispatch PR",
        str(BRIDGE_PATH),
        str(PR_WORKFLOW_PATH),
        str(VERIFIER_PATH),
        str(TEST_PATH),
        str(POLICY_PATH),
        str(DOC_PATH),
        "PUBLIC_HTTP_PROOF_DISPATCH_EXACT_SCOPE=PASS",
        "verify_public_http_proof_dispatch.py verify-repository",
        "test_verify_public_http_proof_dispatch",
        "verify_public_http_proof.py",
        "git diff --exit-code",
        "site/crypto-astro/index.html",
        "site/crypto-astro/data",
    ]
    failures = [f"pr_workflow:missing:{marker}" for marker in required if marker not in text]
    if re.search(r"^  schedule:\s*$", text, re.MULTILINE):
        failures.append("pr_workflow:schedule")
    if "contents: write" in text:
        failures.append("pr_workflow:contents_write")
    return failures


def verify_document(text: str) -> list[str]:
    required = [
        "# Crypto-Astro Public HTTP Proof Dispatch v0.1",
        ISSUE_TITLE,
        REQUEST_SCHEMA,
        TARGET_WORKFLOW,
        "Fixed ref: `main`",
        "zero queued, waiting, pending, requested, or in-progress runs",
        "single new workflow run",
        CALLBACK_SCHEMA,
        "no cron",
        "no contents write",
        "no A/E activation",
        "no ORION core exposure",
    ]
    return [f"document:missing:{marker}" for marker in required if marker not in text]


def verify_repository(repo: Path) -> dict[str, Any]:
    policy = load_policy(repo / POLICY_PATH)
    failures = validate_policy(policy)
    failures.extend(verify_bridge_workflow(read_text(repo, BRIDGE_PATH)))
    failures.extend(verify_target_workflow(read_text(repo, TARGET_WORKFLOW_PATH)))
    failures.extend(verify_pr_workflow(read_text(repo, PR_WORKFLOW_PATH)))
    failures.extend(verify_document(read_text(repo, DOC_PATH)))
    return {
        "schema_version": "crypto_astro_public_http_proof_dispatch_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "target_repository": TARGET_REPOSITORY,
        "target_workflow": TARGET_WORKFLOW,
        "target_ref": TARGET_REF,
        "exact_implementation_scope": sorted(EXACT_IMPLEMENTATION_SCOPE),
        "failures": failures,
    }


def write_output(path: Path | None, values: dict[str, str]) -> None:
    if path is None:
        return
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_validate_request(args: argparse.Namespace) -> int:
    body = args.body_file.read_text(encoding="utf-8")
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
        report = {
            "schema_version": "crypto_astro_public_http_proof_dispatch_request_validation_v0_1",
            "status": "FAIL_VALIDATION",
            "reason_code": exc.code,
        }
        write_report(args.report, report)
        write_output(
            args.github_output,
            {"valid": "false", "reason_code": exc.code},
        )
        print(f"PUBLIC_HTTP_PROOF_DISPATCH_REQUEST=FAIL_VALIDATION:{exc.code}")
        return 0

    report = {
        "schema_version": "crypto_astro_public_http_proof_dispatch_request_validation_v0_1",
        "status": "PASS",
        **request.as_dict(),
    }
    write_report(args.report, report)
    write_output(
        args.github_output,
        {
            "valid": "true",
            "reason_code": "PASS",
            "request_id": request.request_id,
            "operator_ref": request.operator_ref,
            "expected_main_sha": request.expected_main_sha,
        },
    )
    print("PUBLIC_HTTP_PROOF_DISPATCH_REQUEST=PASS")
    return 0


def command_verify_repository(args: argparse.Namespace) -> int:
    report = verify_repository(args.repo.resolve())
    write_report(args.report, report)
    print(f"PUBLIC_HTTP_PROOF_DISPATCH_REPOSITORY={report['status']}")
    if report["failures"]:
        for failure in report["failures"]:
            print(f"FAILURE={failure}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-request")
    validate.add_argument("--body-file", type=Path, required=True)
    validate.add_argument("--title", required=True)
    validate.add_argument("--actor-login", required=True)
    validate.add_argument("--author-login", required=True)
    validate.add_argument("--author-association", required=True)
    validate.add_argument("--current-main-sha", required=True)
    validate.add_argument("--github-output", type=Path)
    validate.add_argument("--report", type=Path, required=True)
    validate.set_defaults(func=command_validate_request)

    verify = subparsers.add_parser("verify-repository")
    verify.add_argument("--repo", type=Path, default=Path("."))
    verify.add_argument("--report", type=Path, required=True)
    verify.set_defaults(func=command_verify_repository)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
