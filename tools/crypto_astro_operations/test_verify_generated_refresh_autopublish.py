from __future__ import annotations

import io
import json
import unittest
import urllib.error
import urllib.request
import zipfile
from email.message import Message
from unittest.mock import Mock

from tools.crypto_astro_operations.verify_generated_refresh_autopublish import (
    GateError,
    GitHub,
    MAX_ARCHIVE_BYTES,
    NoRedirect,
    OPTIONAL_FILES,
    REQUIRED_FILES,
    REQUIRED_WORKFLOWS,
    exact_scope,
    latest_runs_by_name,
    parse_body,
    parse_decision_report,
)


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"", headers: list[tuple[str, str]] | None = None):
        self.status = status
        self._body = io.BytesIO(body)
        self.headers = Message()
        for key, value in headers or []:
            self.headers[key] = value

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def close(self) -> None:
        self._body.close()


def decision_zip() -> bytes:
    decision = {
        "decision": "MANUAL_REFRESH_DISPATCHED",
        "scheduler_run_id": "12345",
        "main_sha": "a" * 40,
        "remote_main_sha": "a" * 40,
        "manual_workflow_run": {"databaseId": 67890},
    }
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("crypto-astro-automatic-refresh-decision.json", json.dumps(decision))
    return output.getvalue()


def artifact_for(archive: bytes, digest: str | None = None) -> dict:
    value = {
        "id": 1,
        "archive_download_url": "https://api.github.com/repos/AiBhrigu/phi-cosmography-open/actions/artifacts/1/zip",
    }
    if digest is not None:
        value["digest"] = digest
    return value


class GeneratedRefreshAutopublishTest(unittest.TestCase):
    def setUp(self) -> None:
        self.archive = decision_zip()
        self.signed_url = "https://signed.example.test/archive.zip?sig=redacted"
        self.client = GitHub("AiBhrigu/phi-cosmography-open", "unit-test-token")

    def responses(self, second_status: int = 200, second_body: bytes | None = None):
        first = FakeResponse(302, headers=[("Location", self.signed_url)])
        second = FakeResponse(
            second_status,
            self.archive if second_body is None else second_body,
            headers=[("Content-Length", str(len(self.archive if second_body is None else second_body)))],
        )
        opener = Mock(side_effect=[first, second])
        self.client._open_no_redirect = opener
        return opener

    def test_exact_scope(self):
        self.assertTrue(exact_scope(set(REQUIRED_FILES)))
        self.assertTrue(exact_scope(set(REQUIRED_FILES) | set(OPTIONAL_FILES)))
        self.assertFalse(exact_scope(set(REQUIRED_FILES) | {"README.md"}))

    def test_required_ci_count_and_names_are_unchanged(self):
        self.assertEqual(len(REQUIRED_WORKFLOWS), 16)
        self.assertIn("Crypto-Astro Automatic Refresh Activation PR", REQUIRED_WORKFLOWS)
        self.assertIn("Φ-Validator CI", REQUIRED_WORKFLOWS)

    def test_parse_scheduler_provenance(self):
        body = (
            "- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_12345\n"
            "- Base SHA: " + "a" * 40 + "\n"
            "- Assistant dispatch issue: none\n"
        )
        self.assertEqual(parse_body(body), (12345, "a" * 40))

    def test_missing_issue_marker_fails(self):
        with self.assertRaises(GateError):
            parse_body(
                "- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_12345\n"
                "- Base SHA: " + "a" * 40 + "\n"
            )

    def test_latest_runs_selected(self):
        name = next(iter(REQUIRED_WORKFLOWS))
        selected = latest_runs_by_name([{"id": 1, "name": name}, {"id": 2, "name": name}])
        self.assertEqual(selected[name]["id"], 2)

    def test_no_redirect_handler_disables_automatic_redirect(self):
        handler = NoRedirect()
        request = urllib.request.Request("https://api.github.com/test")
        self.assertIsNone(handler.redirect_request(request, None, 302, "Found", {}, self.signed_url))

    def test_initial_request_has_auth_and_signed_request_has_none(self):
        opener = self.responses()
        archive, digest_result = self.client.artifact_archive(artifact_for(self.archive))
        self.assertEqual(archive, self.archive)
        self.assertEqual(digest_result, "NOT_AVAILABLE")
        initial_request = opener.call_args_list[0].args[0]
        signed_request = opener.call_args_list[1].args[0]
        self.assertEqual(initial_request.get_header("Authorization"), "Bearer unit-test-token")
        signed_headers = {key.lower(): value for key, value in signed_request.header_items()}
        self.assertNotIn("authorization", signed_headers)
        self.assertNotIn("cookie", signed_headers)
        self.assertNotIn("unit-test-token", signed_request.full_url)

    def test_http_redirect_target_rejected(self):
        self.client._open_no_redirect = Mock(
            return_value=FakeResponse(302, headers=[("Location", "http://signed.example.test/archive.zip")])
        )
        with self.assertRaisesRegex(GateError, "ARTIFACT_URL_HTTPS_REQUIRED"):
            self.client.artifact_archive(artifact_for(self.archive))

    def test_redirect_credentials_rejected(self):
        self.client._open_no_redirect = Mock(
            return_value=FakeResponse(
                302,
                headers=[("Location", "https://user:password@signed.example.test/archive.zip")],
            )
        )
        with self.assertRaisesRegex(GateError, "ARTIFACT_URL_CREDENTIALS_FORBIDDEN"):
            self.client.artifact_archive(artifact_for(self.archive))

    def test_redirect_fragment_rejected(self):
        self.client._open_no_redirect = Mock(
            return_value=FakeResponse(302, headers=[("Location", self.signed_url + "#fragment")])
        )
        with self.assertRaisesRegex(GateError, "ARTIFACT_URL_FRAGMENT_FORBIDDEN"):
            self.client.artifact_archive(artifact_for(self.archive))

    def test_missing_location_rejected(self):
        self.client._open_no_redirect = Mock(return_value=FakeResponse(302))
        with self.assertRaisesRegex(GateError, "ARTIFACT_API_LOCATION_INVALID"):
            self.client.artifact_archive(artifact_for(self.archive))

    def test_multiple_locations_rejected(self):
        self.client._open_no_redirect = Mock(
            return_value=FakeResponse(
                302,
                headers=[("Location", self.signed_url), ("Location", "https://other.test/archive.zip")],
            )
        )
        with self.assertRaisesRegex(GateError, "ARTIFACT_API_LOCATION_INVALID"):
            self.client.artifact_archive(artifact_for(self.archive))

    def test_additional_redirect_rejected(self):
        self.responses(second_status=302)
        with self.assertRaisesRegex(GateError, "ARTIFACT_ARCHIVE_ADDITIONAL_REDIRECT"):
            self.client.artifact_archive(artifact_for(self.archive))

    def test_non_200_archive_rejected(self):
        self.responses(second_status=403)
        with self.assertRaisesRegex(GateError, "ARTIFACT_ARCHIVE_HTTP_STATUS:403"):
            self.client.artifact_archive(artifact_for(self.archive))

    def test_signed_request_failure_is_sanitized(self):
        first = FakeResponse(302, headers=[("Location", self.signed_url)])
        self.client._open_no_redirect = Mock(
            side_effect=[first, urllib.error.URLError("failed: " + self.signed_url + ":unit-test-token")]
        )
        with self.assertRaises(GateError) as raised:
            self.client.artifact_archive(artifact_for(self.archive))
        rendered = str(raised.exception)
        self.assertEqual(rendered, "ARTIFACT_ARCHIVE_REQUEST_FAILED")
        self.assertNotIn("sig=", rendered)
        self.assertNotIn("unit-test-token", rendered)

    def test_digest_mismatch_rejected(self):
        self.responses()
        with self.assertRaisesRegex(GateError, "ARTIFACT_DIGEST_MISMATCH"):
            self.client.artifact_archive(artifact_for(self.archive, "sha256:" + "0" * 64))

    def test_valid_digest_accepted(self):
        import hashlib

        self.responses()
        digest = "sha256:" + hashlib.sha256(self.archive).hexdigest()
        archive, digest_result = self.client.artifact_archive(artifact_for(self.archive, digest))
        self.assertEqual(archive, self.archive)
        self.assertEqual(digest_result, "PASS")

    def test_malformed_zip_rejected(self):
        malformed = b"not-a-zip"
        first = FakeResponse(302, headers=[("Location", self.signed_url)])
        second = FakeResponse(200, malformed, headers=[("Content-Length", str(len(malformed)))])
        self.client._open_no_redirect = Mock(side_effect=[first, second])
        with self.assertRaisesRegex(GateError, "ARTIFACT_ZIP_MALFORMED"):
            self.client.artifact_archive(artifact_for(malformed))

    def test_bounded_archive_size_enforced(self):
        first = FakeResponse(302, headers=[("Location", self.signed_url)])
        second = FakeResponse(200, b"", headers=[("Content-Length", str(MAX_ARCHIVE_BYTES + 1))])
        self.client._open_no_redirect = Mock(side_effect=[first, second])
        with self.assertRaisesRegex(GateError, "ARTIFACT_ARCHIVE_SIZE_EXCEEDED"):
            self.client.artifact_archive(artifact_for(b""))

    def test_valid_archive_and_decision_json_accepted(self):
        self.responses()
        archive, _ = self.client.artifact_archive(artifact_for(self.archive))
        decision = parse_decision_report(archive)
        self.assertEqual(decision["decision"], "MANUAL_REFRESH_DISPATCHED")
        self.assertEqual(decision["manual_workflow_run"]["databaseId"], 67890)


if __name__ == "__main__":
    unittest.main()
