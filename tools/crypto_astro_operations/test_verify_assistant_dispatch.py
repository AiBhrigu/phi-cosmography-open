import copy
import unittest

from verify_assistant_dispatch import (
    ALLOWED_MODES,
    DispatchValidationError,
    ISSUE_TITLE,
    OWNER_LOGIN,
    parse_request,
    validate_policy,
    verify_bridge_workflow,
    verify_manual_workflow,
)

MAIN_SHA = "7" * 40


def valid_body(**overrides):
    values = {
        "SCHEMA": "crypto_astro_assistant_dispatch_request_v0_1",
        "REQUEST_ID": "CA-RP-20260722-01",
        "REFRESH_MODE": "REPEATABILITY_PROOF",
        "OPERATOR_REF": "COSMOGRAPHER-RP-20260722-01",
        "REFRESH_REASON": "Second bounded repeatability proof from cadence-locked main.",
        "EXPECTED_MAIN_SHA": MAIN_SHA,
    }
    values.update(overrides)
    return "\n".join(f"{key}={values[key]}" for key in values)


def parse(body=None, **kwargs):
    return parse_request(
        body or valid_body(),
        title=kwargs.get("title", ISSUE_TITLE),
        actor_login=kwargs.get("actor_login", OWNER_LOGIN),
        author_login=kwargs.get("author_login", OWNER_LOGIN),
        author_association=kwargs.get("author_association", "OWNER"),
        current_main_sha=kwargs.get("current_main_sha", MAIN_SHA),
    )


def assert_invalid(testcase, code, body=None, **kwargs):
    with testcase.assertRaises(DispatchValidationError) as caught:
        parse(body, **kwargs)
    testcase.assertEqual(caught.exception.code, code)


def valid_policy():
    return {
        "schema_version": "crypto_astro_assistant_dispatch_policy_v0_1",
        "repository": "AiBhrigu/phi-cosmography-open",
        "owner_login": "AiBhrigu",
        "issue_title": ISSUE_TITLE,
        "trigger": {"event": "issues", "action": "opened"},
        "request_contract": {
            "schema_value": "crypto_astro_assistant_dispatch_request_v0_1",
            "ordered_keys": [
                "SCHEMA",
                "REQUEST_ID",
                "REFRESH_MODE",
                "OPERATOR_REF",
                "REFRESH_REASON",
                "EXPECTED_MAIN_SHA",
            ],
            "exact_line_count": 6,
            "allowed_modes": list(ALLOWED_MODES),
            "max_lengths": {"REQUEST_ID": 64, "OPERATOR_REF": 80, "REFRESH_REASON": 240},
            "forbidden_tokens": ["```", "http://", "https://", "www.", "${", "$(", "\t", "\r"],
        },
        "identity": {"author_login": "AiBhrigu", "author_association": "OWNER", "actor_login": "AiBhrigu"},
        "dispatch": {
            "target_workflow": "crypto-astro-static-refresh-manual.yml",
            "target_ref": "main",
            "fixed_repository": "AiBhrigu/phi-cosmography-open",
            "required_inputs": [
                "refresh_mode",
                "operator_ref",
                "refresh_reason",
                "expected_main_sha",
                "dispatch_request_issue",
            ],
            "workflow_target_from_issue_forbidden": True,
            "repository_from_issue_forbidden": True,
            "ref_from_issue_forbidden": True,
            "shell_eval_forbidden": True,
        },
        "permissions": {"contents": "read", "actions": "write", "issues": "write", "pull_requests": "read"},
        "callback": {
            "schema_version": "crypto_astro_assistant_dispatch_callback_v0_1",
            "required_fields": [
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
            "close_issue": True,
            "lock_reason": "resolved",
        },
        "boundary": {"cron": False, "auto_merge": False},
    }


class RequestValidationTests(unittest.TestCase):
    def test_valid_owner_request_passes(self):
        request = parse()
        self.assertEqual(request.refresh_mode, "REPEATABILITY_PROOF")
        self.assertEqual(request.expected_main_sha, MAIN_SHA)

    def test_wrong_title_rejected(self):
        assert_invalid(self, "WRONG_TITLE", title="Other")

    def test_non_owner_actor_rejected(self):
        assert_invalid(self, "ACTOR_NOT_OWNER", actor_login="someone")

    def test_non_owner_author_rejected(self):
        assert_invalid(self, "AUTHOR_NOT_OWNER", author_login="someone")

    def test_non_owner_association_rejected(self):
        assert_invalid(self, "AUTHOR_ASSOCIATION_NOT_OWNER", author_association="CONTRIBUTOR")

    def test_wrong_schema_rejected(self):
        assert_invalid(self, "SCHEMA_INVALID", valid_body(SCHEMA="bad"))

    def test_unknown_key_rejected(self):
        body = valid_body().replace("REQUEST_ID=", "UNKNOWN=")
        assert_invalid(self, "KEY_ORDER_OR_SET_INVALID", body)

    def test_duplicate_key_rejected(self):
        lines = valid_body().splitlines()
        lines[2] = lines[1]
        assert_invalid(self, "KEY_ORDER_OR_SET_INVALID", "\n".join(lines))

    def test_multiline_injection_rejected(self):
        assert_invalid(self, "EXACT_SIX_LINES_REQUIRED", valid_body() + "\nEXTRA=value")

    def test_markdown_payload_rejected(self):
        assert_invalid(self, "FORBIDDEN_TOKEN", valid_body(REFRESH_REASON="Use ```code```"))

    def test_url_rejected(self):
        assert_invalid(self, "FORBIDDEN_TOKEN", valid_body(REFRESH_REASON="Use https://example.test"))

    def test_shell_substitution_rejected(self):
        assert_invalid(self, "FORBIDDEN_TOKEN", valid_body(REFRESH_REASON="Run $(id)"))

    def test_forbidden_mode_rejected(self):
        assert_invalid(self, "REFRESH_MODE_INVALID", valid_body(REFRESH_MODE="ARBITRARY"))

    def test_invalid_sha_rejected(self):
        assert_invalid(self, "EXPECTED_MAIN_SHA_INVALID", valid_body(EXPECTED_MAIN_SHA="abc"))

    def test_stale_sha_rejected(self):
        assert_invalid(self, "EXPECTED_MAIN_SHA_STALE", valid_body(EXPECTED_MAIN_SHA="8" * 40))

    def test_empty_operator_ref_rejected(self):
        assert_invalid(self, "OPERATOR_REF_INVALID", valid_body(OPERATOR_REF=""))

    def test_overlong_operator_ref_rejected(self):
        assert_invalid(self, "OPERATOR_REF_INVALID", valid_body(OPERATOR_REF="A" * 81))

    def test_empty_reason_rejected(self):
        assert_invalid(self, "REFRESH_REASON_LENGTH_INVALID", valid_body(REFRESH_REASON=""))

    def test_overlong_reason_rejected(self):
        assert_invalid(self, "REFRESH_REASON_LENGTH_INVALID", valid_body(REFRESH_REASON="A" * 241))

    def test_padded_line_rejected(self):
        assert_invalid(self, "BLANK_OR_PADDED_LINE", valid_body() + " ")


class PolicyAndWorkflowTests(unittest.TestCase):
    def test_locked_policy_passes(self):
        self.assertEqual(validate_policy(valid_policy()), [])

    def test_policy_permission_drift_fails(self):
        policy = copy.deepcopy(valid_policy())
        policy["permissions"]["contents"] = "write"
        self.assertIn("policy:permissions", validate_policy(policy))

    def test_bridge_rejects_contents_write(self):
        text = "\n".join(
            [
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
                "gh workflow run crypto-astro-static-refresh-manual.yml",
                "--ref main",
                "-f expected_main_sha=",
                "-f dispatch_request_issue=",
                "DISPATCH_ACCEPTED",
                "gh issue close",
                "gh issue lock",
                "contents: write",
            ]
        )
        self.assertIn("bridge:contents_write", verify_bridge_workflow(text))

    def test_manual_callback_markers_required(self):
        failures = verify_manual_workflow("workflow_dispatch:\n")
        self.assertTrue(any("manual:missing" in value for value in failures))


if __name__ == "__main__":
    unittest.main()
