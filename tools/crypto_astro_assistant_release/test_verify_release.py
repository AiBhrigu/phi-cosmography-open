from __future__ import annotations

import unittest
from pathlib import Path

from tools.crypto_astro_operations.verify_generated_refresh_autopublish import GateError
from tools.crypto_astro_assistant_release.verify_release import (
    RELEASE_SCHEMA,
    TOPOLOGY_FILES,
    canonical_acceptance_body,
    parse_pr_body,
    parse_release_issue,
    validate_dispatch_comments,
    validate_pr_identity,
    validate_rebound_pr,
)

REPO = "AiBhrigu/phi-cosmography-open"
H = "b" * 40
B = "a" * 40
A = "c" * 40


def generated_pr(*, base_ref: str = "main", base_sha: str = B, head_sha: str = H, acceptance: str = A):
    return {
        "state": "open",
        "title": "Crypto-Astro: automated static market snapshot refresh",
        "user": {"login": "github-actions[bot]"},
        "base": {"ref": base_ref, "sha": base_sha},
        "head": {
            "ref": "automation/crypto-astro-static-refresh-123",
            "sha": head_sha,
            "repo": {"full_name": REPO},
        },
        "body": (
            "- Refresh mode: DAILY_CADENCE\n"
            "- Operator reference: CRYPTO_ASTRO_TIME_AXIS_AUTOMATION_20260812\n"
            "- Reason: Accepted snapshot exceeded 18 hours.\n"
            f"- Generation Base SHA: {B}\n"
            f"- Acceptance Base SHA: {acceptance}\n"
            "- Assistant dispatch issue: 360\n"
        ),
    }


class T(unittest.TestCase):
    def test_release_issue(self):
        body = (
            f"SCHEMA={RELEASE_SCHEMA}\n"
            "PR=361\n"
            f"EXPECTED_HEAD_SHA={H}\n"
            f"EXPECTED_GENERATION_BASE_SHA={B}\n"
            "ASSISTANT_DISPATCH_ISSUE=360\n"
        )
        self.assertEqual(parse_release_issue(body), (361, H, B, 360))

    def test_release_issue_bad_head(self):
        body = (
            f"SCHEMA={RELEASE_SCHEMA}\nPR=361\nEXPECTED_HEAD_SHA=x\n"
            f"EXPECTED_GENERATION_BASE_SHA={B}\nASSISTANT_DISPATCH_ISSUE=360\n"
        )
        with self.assertRaisesRegex(GateError, "RELEASE_HEAD_INVALID"):
            parse_release_issue(body)

    def test_pr_body(self):
        body = (
            "- Refresh mode: DAILY_CADENCE\n"
            "- Operator reference: CRYPTO_ASTRO_TIME_AXIS_AUTOMATION_20260812\n"
            "- Reason: Accepted snapshot exceeded 18 hours.\n"
            f"- Generation Base SHA: {B}\n"
            f"- Acceptance Base SHA: {B}\n"
            "- Assistant dispatch issue: 360\n"
        )
        parsed = parse_pr_body(body)
        self.assertEqual(parsed["dispatch_issue"], 360)
        self.assertEqual(parsed["generation"], B)
        self.assertEqual(parsed["acceptance"], B)

    def test_pr_body_rejects_none_dispatch(self):
        body = (
            "- Refresh mode: DAILY_CADENCE\n"
            "- Operator reference: X\n"
            "- Reason: Y\n"
            f"- Generation Base SHA: {B}\n"
            f"- Acceptance Base SHA: {B}\n"
            "- Assistant dispatch issue: none\n"
        )
        with self.assertRaisesRegex(GateError, "ASSISTANT_PR_BODY_PROVENANCE_INVALID"):
            parse_pr_body(body)

    def test_canonical_acceptance_only(self):
        body = f"- Generation Base SHA: {B}\n- Acceptance Base SHA: {B}\n"
        out = canonical_acceptance_body(body, H)
        self.assertIn(f"Generation Base SHA: {B}", out)
        self.assertIn(f"Acceptance Base SHA: {H}", out)

    def test_dispatch_comments(self):
        comments = [
            {
                "user": {"login": "github-actions[bot]"},
                "body": (
                    "SCHEMA=crypto_astro_assistant_dispatch_result_v0_1\n"
                    "STATUS=DISPATCH_ACCEPTED\n"
                    "REQUEST_ID=REQ_1\n"
                    f"EXPECTED_MAIN_SHA={B}\n"
                    "TARGET_WORKFLOW=crypto-astro-static-refresh-manual.yml\n"
                    "TARGET_REF=main"
                ),
            },
            {
                "user": {"login": "github-actions[bot]"},
                "body": (
                    "SCHEMA=crypto_astro_assistant_dispatch_callback_v0_1\n"
                    "DISPATCH_REQUEST_ID=REQ_1\n"
                    "WORKFLOW_RUN_ID=123\n"
                    f"EXPECTED_MAIN_SHA={B}\n"
                    f"ACTUAL_BASE_SHA={B}\n"
                    "JOB_STATUS=success\n"
                    "MATERIAL_CHANGE=true\n"
                    "GENERATED_BRANCH=automation/crypto-astro-static-refresh-123\n"
                    f"GENERATED_PR_URL=https://github.com/{REPO}/pull/361\n"
                    "FINAL_OUTCOME=PASS_REVIEW_PR_OPENED"
                ),
            },
        ]
        validate_dispatch_comments(
            comments,
            repo=REPO,
            request_id="REQ_1",
            manual_id=123,
            generation=B,
            head_ref="automation/crypto-astro-static-refresh-123",
            pr_number=361,
        )

    def test_dispatch_comments_require_callback(self):
        comments = [
            {
                "user": {"login": "github-actions[bot]"},
                "body": (
                    "SCHEMA=crypto_astro_assistant_dispatch_result_v0_1\n"
                    "STATUS=DISPATCH_ACCEPTED\n"
                    "REQUEST_ID=REQ_1\n"
                    f"EXPECTED_MAIN_SHA={B}\n"
                    "TARGET_WORKFLOW=crypto-astro-static-refresh-manual.yml\n"
                    "TARGET_REF=main"
                ),
            }
        ]
        with self.assertRaisesRegex(GateError, "CALLBACK_PROOF_MISSING"):
            validate_dispatch_comments(
                comments,
                repo=REPO,
                request_id="REQ_1",
                manual_id=123,
                generation=B,
                head_ref="automation/crypto-astro-static-refresh-123",
                pr_number=361,
            )

    def test_rebound_accepts_original_base_sha_with_current_acceptance(self):
        body = validate_rebound_pr(
            generated_pr(base_sha=B, acceptance=A),
            REPO,
            expected_head=H,
            expected_generation=B,
            expected_dispatch_issue=360,
            expected_manual_id=123,
            expected_head_ref="automation/crypto-astro-static-refresh-123",
            expected_acceptance=A,
        )
        self.assertEqual(body["generation"], B)
        self.assertEqual(body["acceptance"], A)

    def test_rebound_still_requires_main_base_ref(self):
        with self.assertRaisesRegex(GateError, "WRONG_BASE"):
            validate_rebound_pr(
                generated_pr(base_ref="other", base_sha=B, acceptance=A),
                REPO,
                expected_head=H,
                expected_generation=B,
                expected_dispatch_issue=360,
                expected_manual_id=123,
                expected_head_ref="automation/crypto-astro-static-refresh-123",
                expected_acceptance=A,
            )

    def test_rebound_rejects_head_drift(self):
        with self.assertRaisesRegex(GateError, "HEAD_DRIFT"):
            validate_rebound_pr(
                generated_pr(head_sha="d" * 40, acceptance=A),
                REPO,
                expected_head=H,
                expected_generation=B,
                expected_dispatch_issue=360,
                expected_manual_id=123,
                expected_head_ref="automation/crypto-astro-static-refresh-123",
                expected_acceptance=A,
            )

    def test_rebound_rejects_acceptance_drift(self):
        with self.assertRaisesRegex(GateError, "BASE_OR_IDENTITY_DRIFT"):
            validate_rebound_pr(
                generated_pr(acceptance=B),
                REPO,
                expected_head=H,
                expected_generation=B,
                expected_dispatch_issue=360,
                expected_manual_id=123,
                expected_head_ref="automation/crypto-astro-static-refresh-123",
                expected_acceptance=A,
            )

    def test_validate_identity_preserves_generation(self):
        manual_id, head_ref, head_sha, body = validate_pr_identity(
            generated_pr(base_sha=B, acceptance=A),
            REPO,
            expected_head=H,
            expected_generation=B,
            expected_dispatch_issue=360,
        )
        self.assertEqual(manual_id, 123)
        self.assertEqual(head_ref, "automation/crypto-astro-static-refresh-123")
        self.assertEqual(head_sha, H)
        self.assertEqual(body["generation"], B)

    def test_control_plane_scope_is_exact_three_files(self):
        self.assertEqual(
            TOPOLOGY_FILES,
            {
                ".github/workflows/crypto-astro-assistant-generated-refresh-ci-release.yml",
                "tools/crypto_astro_assistant_release/test_verify_release.py",
                "tools/crypto_astro_assistant_release/verify_release.py",
            },
        )

    def test_runtime_workflow_has_no_merge_or_deploy(self):
        root = Path(__file__).resolve().parents[2]
        text = (
            root / ".github/workflows/crypto-astro-assistant-generated-refresh-ci-release.yml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("gh " + "pr " + "merge", text)
        self.assertNotIn("actions/" + "deploy-pages", text)
        self.assertNotIn("generated-refresh-" + "autopublish", text)
        self.assertIn("EXPLICIT_AUTHORIZED_MERGE_ONLY", text)


if __name__ == "__main__":
    unittest.main()
