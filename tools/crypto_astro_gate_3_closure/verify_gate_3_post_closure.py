#!/usr/bin/env python3
"""Fail-closed verifier for the Crypto-Astro Gate 3 closure index."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "crypto_astro_gate_3_post_closure_memory_handoff_v0_1"
NODE = "CRYPTO_ASTRO_GATE_3_POST_CLOSURE_SOURCE_OF_TRUTH_INDEX_AND_MEMORY_HANDOFF_SCOPE_v0_1"
REPOSITORY = "AiBhrigu/phi-cosmography-open"
CURRENT_MAIN_SHA = "4f00ec234b1bb3db43c5687cf678b77ff5d98eaa"
FINAL_ISSUE = 167
FINAL_RUN = 29914563042
FINAL_ARTIFACT = 8527304778
FINAL_DIGEST = "sha256:b692458b3c1fc9ff16d9962d7464326606b4dc251d748ea52913463982e511e9"

CAPSULE_PATH = Path("docs/crypto-astro-service/crypto_astro_gate_3_post_closure_memory_handoff_v0_1.json")
INDEX_PATH = Path("docs/crypto-astro-service/CRYPTO_ASTRO_GATE_3_POST_CLOSURE_SOURCE_OF_TRUTH_INDEX_v0_1.md")
EXPECTED_SOURCE_FILES = [
    ".github/workflows/crypto-astro-public-http-proof.yml",
    ".github/workflows/crypto-astro-public-http-proof-dispatch.yml",
    ".github/workflows/crypto-astro-public-http-proof-dispatch-pr.yml",
    "tools/crypto_astro_public_http_proof/verify_public_http_proof.py",
    "tools/crypto_astro_public_http_proof/verify_public_http_proof_dispatch.py",
    "docs/crypto-astro-service/CRYPTO_ASTRO_PUBLIC_HTTP_PROOF_DISPATCH_v0_1.md",
    "docs/crypto-astro-service/crypto_astro_public_http_proof_dispatch_v0_1.json",
]
EXPECTED_PRS = [
    (158, "ba798b436accae805d326dc78977a3af05da4dfd", "4fc4d460587ef434563b0b17b05c68f9caf0ced0"),
    (159, "23cb754ec4c2b4c7de487d19918c58123dd413a9", "a2da529c075699c82c963befb34f946ba211c1b0"),
    (162, "2cd1a43d2004334621a2b5f496d6efa0ce68a418", "a5d9183da68cfec93eb9fdbaeb57a7469d8454a9"),
    (164, "350b899500dfa27abc10aa80e070833468afa11f", "ce499d0176b05cacde550f7d3ecf430dc6d1b704"),
    (166, "5c0d68fbcc2d7cb34eddb924bfaf84935fd31a26", CURRENT_MAIN_SHA),
]
EXPECTED_ISSUES = [160, 161, 163, 165]
EXPECTED_CALLBACKS = {160: 5044642377, 161: 5044666925, 163: 5044735135, 165: 5044861593}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def check(ok: bool, code: str, failures: list[str]) -> None:
    if not ok:
        failures.append(code)


def load_capsule(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("CAPSULE_NOT_OBJECT")
    return value


def validate_capsule(value: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    check(value.get("schema_version") == SCHEMA, "capsule:schema", failures)
    check(value.get("node") == NODE, "capsule:node", failures)
    check(value.get("handoff_status") == "READY_FOR_REVIEW", "capsule:handoff_status", failures)
    check(value.get("repository") == REPOSITORY, "capsule:repository", failures)
    check(value.get("source_of_truth_files") == EXPECTED_SOURCE_FILES, "capsule:source_files", failures)

    gate = value.get("gate_3") if isinstance(value.get("gate_3"), dict) else {}
    expected_gate = {
        "axis": "PUBLIC_HTTP_PROOF_DISPATCH",
        "status": "PASS",
        "production_state": "OWNER_AUTHENTICATED_DISPATCH_BRIDGE_LIVE_VERIFIED",
        "current_main_sha": CURRENT_MAIN_SHA,
        "canonical_snapshot_timestamp": "2026-07-22T08:02:05Z",
        "closure_observed_at_utc": "2026-07-22T11:08:38Z",
        "operator_f_manual_actions": "NONE",
        "boundary": "CLEAN",
    }
    check(gate == expected_gate, "gate:exact_state", failures)
    check(SHA_RE.fullmatch(str(gate.get("current_main_sha", ""))) is not None, "gate:sha_format", failures)

    prs = value.get("pr_chain") if isinstance(value.get("pr_chain"), list) else []
    observed = []
    for item in prs:
        if not isinstance(item, dict):
            failures.append("pr:item_not_object")
            continue
        number = item.get("number")
        observed.append((number, item.get("head_sha"), item.get("merge_sha")))
        check(item.get("state") == "merged", f"pr:{number}:state", failures)
        check(isinstance(item.get("review_evidence_run_id"), int), f"pr:{number}:run", failures)
        check(isinstance(item.get("review_evidence_artifact_id"), int), f"pr:{number}:artifact", failures)
        check(DIGEST_RE.fullmatch(str(item.get("review_evidence_digest", ""))) is not None, f"pr:{number}:digest", failures)
    check(observed == EXPECTED_PRS, "pr:order_or_sha", failures)

    issues = value.get("diagnostic_issue_chain") if isinstance(value.get("diagnostic_issue_chain"), list) else []
    check([item.get("number") for item in issues if isinstance(item, dict)] == EXPECTED_ISSUES, "issue:order", failures)
    for item in issues:
        if not isinstance(item, dict):
            failures.append("issue:item_not_object")
            continue
        number = item.get("number")
        check(item.get("classification") == "SAFE_FAIL_CLOSED_DIAGNOSTIC", f"issue:{number}:classification", failures)
        check(item.get("final_outcome") == "FAIL_PREFLIGHT", f"issue:{number}:outcome", failures)
        check(item.get("target_workflow_dispatched") is False, f"issue:{number}:dispatch", failures)
        check(item.get("workflow_run_id") is None, f"issue:{number}:run", failures)
        check(item.get("callback_comment_id") == EXPECTED_CALLBACKS.get(number), f"issue:{number}:callback", failures)
        expected_reason = "FAIL_TARGET_WORKFLOW_VIEW" if number == 165 else None
        check(item.get("exact_reason_code") == expected_reason, f"issue:{number}:reason", failures)

    repairs = value.get("accepted_repair_mapping") if isinstance(value.get("accepted_repair_mapping"), list) else []
    check([item.get("repair_pr") for item in repairs if isinstance(item, dict)] == [162, 164, 166], "repair:order", failures)

    proof = value.get("production_proof") if isinstance(value.get("production_proof"), dict) else {}
    expected_proof = {
        "classification": "SOLE_POST_MERGE_OWNER_DISPATCH_PRODUCTION_PASS",
        "issue_number": FINAL_ISSUE,
        "request_id": "CA-HTTP-20260722-05",
        "operator_ref": "COSMOGRAPHER-HTTP-20260722-05",
        "dispatch_accepted_comment_id": 5045063716,
        "callback_comment_id": 5045066607,
        "workflow_run_id": FINAL_RUN,
        "workflow_name": "Crypto-Astro Public HTTP Proof",
        "workflow_file": "crypto-astro-public-http-proof.yml",
        "event": "workflow_dispatch",
        "branch": "main",
        "expected_main_sha": CURRENT_MAIN_SHA,
        "actual_head_sha": CURRENT_MAIN_SHA,
        "job_status": "success",
        "final_outcome": "PUBLIC_HTTP_PROOF_PASS",
        "issue_state": "closed",
        "issue_state_reason": "completed",
        "artifact_id": FINAL_ARTIFACT,
        "artifact_name": "crypto-astro-public-http-proof-29914563042",
        "artifact_digest": FINAL_DIGEST,
        "http_targets_total": 6,
        "http_200": 6,
        "redirects_total": 0,
    }
    check(proof == expected_proof, "proof:exact_state", failures)

    rules = "\n".join(value.get("truth_rules", [])) if isinstance(value.get("truth_rules"), list) else ""
    for marker in (
        "Only issue 167 with workflow run 29914563042",
        "Issues 160, 161, 163 and 165 are safe fail-closed diagnostics",
        "did not refresh market data",
        "requires a separate explicit authorization",
    ):
        check(marker in rules, f"rules:missing:{marker}", failures)

    hold = value.get("hold") if isinstance(value.get("hold"), dict) else {}
    check(hold == {
        "state": "HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH",
        "automatic_refresh": False,
        "automatic_dispatch": False,
        "operator_action_required": False,
    }, "hold:exact_state", failures)

    boundary = value.get("boundary") if isinstance(value.get("boundary"), dict) else {}
    check(bool(boundary), "boundary:missing", failures)
    check(all(item is False for item in boundary.values()), "boundary:opened", failures)
    return failures


def validate_index(text: str) -> list[str]:
    failures: list[str] = []
    markers = [
        "# Crypto-Astro Gate 3 Post-Closure Source-of-Truth Index v0.1",
        CURRENT_MAIN_SHA,
        "Only issue #167 and run `29914563042`",
        "Issues #160, #161, #163 and #165 remain safe diagnostic failures.",
        "Final outcome: `PUBLIC_HTTP_PROOF_PASS`",
        "STATE=HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH",
        FINAL_DIGEST,
        "They do not prove public-route failure",
    ]
    for marker in markers:
        check(marker in text, f"index:missing:{marker}", failures)
    for number in (158, 159, 162, 164, 166, 160, 161, 163, 165, 167):
        check(f"#{number}" in text, f"index:missing_number:{number}", failures)
    return failures


def verify_repository(repo: Path) -> dict[str, Any]:
    failures: list[str] = []
    capsule_path = repo / CAPSULE_PATH
    index_path = repo / INDEX_PATH
    if not capsule_path.is_file():
        failures.append(f"missing:{CAPSULE_PATH}")
    else:
        value = load_capsule(capsule_path)
        failures.extend(validate_capsule(value))
        for source in EXPECTED_SOURCE_FILES:
            check((repo / source).is_file(), f"missing_source:{source}", failures)
    if not index_path.is_file():
        failures.append(f"missing:{INDEX_PATH}")
    else:
        failures.extend(validate_index(index_path.read_text(encoding="utf-8")))
    return {
        "schema_version": "crypto_astro_gate_3_post_closure_verification_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "repository": REPOSITORY,
        "current_main_sha": CURRENT_MAIN_SHA,
        "production_issue": FINAL_ISSUE,
        "production_run": FINAL_RUN,
        "production_artifact": FINAL_ARTIFACT,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = verify_repository(args.repo.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
