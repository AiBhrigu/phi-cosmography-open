#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).with_name("verify_public_http_proof.py")
SPEC = importlib.util.spec_from_file_location("verify_public_http_proof", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class PublicHttpProofTests(unittest.TestCase):
    def make_repo(
        self,
        root: Path,
        *,
        snapshot_timestamp: str = "2026-07-22T12:47:37Z",
        proof_timestamp: str = "2026-07-22T12:47:37Z",
        market_field_timestamp: str = "2026-07-22T12:47:37Z",
    ) -> Path:
        data = root / "site/crypto-astro/data"
        data.mkdir(parents=True)
        (root / "site/crypto-astro/index.html").write_text(
            "<html>BTC Field Read Ask one BTC field question</html>", encoding="utf-8"
        )
        (data / "crypto_astro_snapshot.public.json").write_text(
            json.dumps({"generated_at_utc": snapshot_timestamp}), encoding="utf-8"
        )
        (data / "crypto_astro_snapshot_proof.public.json").write_text(
            json.dumps({"generated_at_utc": proof_timestamp}), encoding="utf-8"
        )
        (data / "market_field_snapshot.public.v0_1.json").write_text(
            json.dumps({"updated_at_utc": market_field_timestamp}), encoding="utf-8"
        )
        return root

    def load_report(self, path: Path) -> dict:
        self.assertTrue(path.is_file(), f"missing report: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_content_type_normalization(self) -> None:
        self.assertEqual(
            mod.normalized_content_type("application/json; charset=utf-8"),
            "application/json",
        )
        self.assertEqual(mod.normalized_content_type(None), "")

    def test_sha_lock_validation(self) -> None:
        mod.validate_sha("")
        mod.validate_sha("a" * 40)
        with self.assertRaises(mod.ProofFailure) as ctx:
            mod.validate_sha("not-a-sha")
        self.assertEqual(ctx.exception.reason_code, "EXPECTED_MAIN_SHA_MUST_BE_40_HEX")

    def test_exact_bytes_mismatch_is_fail_closed(self) -> None:
        mod.assert_exact_bytes(b"same", b"same", "fixture")
        with self.assertRaises(mod.ProofFailure) as ctx:
            mod.assert_exact_bytes(b"live", b"expected", "fixture")
        self.assertEqual(ctx.exception.reason_code, "PUBLIC_BYTES_MISMATCH")

    def test_bhrigu_read_requires_timestamp_and_success_heading(self) -> None:
        timestamp = "2026-07-22T12:47:37Z"
        good = mod.FetchResult(
            requested_url="https://example.test",
            final_url="https://example.test",
            status=200,
            redirects=[],
            content_type="text/html",
            body=(
                "<h2>One coherent Cosmographer read</h2>"
                f"<script>{timestamp}</script>"
            ).encode(),
            headers={},
        )
        assertions = mod.verify_bhrigu_read(good, expected_timestamp=timestamp)
        self.assertTrue(all(assertions.values()))

        bad = mod.FetchResult(
            requested_url=good.requested_url,
            final_url=good.final_url,
            status=200,
            redirects=[],
            content_type="text/html",
            body=b"<h2>BTC Field Read unavailable</h2>",
            headers={},
        )
        with self.assertRaises(mod.ProofFailure) as ctx:
            mod.verify_bhrigu_read(bad, expected_timestamp=timestamp)
        self.assertEqual(ctx.exception.reason_code, "BHRIGU_READ_ASSERTION_FAILED")

    def test_local_proof_timestamp_mismatch_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(
                Path(tmp),
                snapshot_timestamp="2026-07-22T12:47:37Z",
                proof_timestamp="2026-07-22T12:47:36Z",
            )
            report_path = repo / "artifacts/report.json"
            with self.assertRaises(mod.ProofFailure) as ctx:
                mod.run_proof(
                    repo=repo,
                    report_path=report_path,
                    expected_main_sha="b" * 40,
                    timeout=1,
                    attempts=1,
                    retry_delay=0,
                )
            self.assertEqual(ctx.exception.reason_code, "LOCAL_PROOF_TIMESTAMP_MISMATCH")
            report = self.load_report(report_path)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["failure"]["reason_code"], "LOCAL_PROOF_TIMESTAMP_MISMATCH")
            self.assertEqual(report["failure"]["stage"], "local_source_validation")
            self.assertEqual(report["failure"]["target"], "proof_json")
            self.assertEqual(
                report["failure"]["details"],
                {
                    "actual_timestamp": "2026-07-22T12:47:36Z",
                    "expected_timestamp": "2026-07-22T12:47:37Z",
                },
            )
            self.assertEqual(report["local_source_validation"]["status"], "PENDING")

    def test_market_field_timestamp_mismatch_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(
                Path(tmp),
                market_field_timestamp="2026-07-22T12:47:36Z",
            )
            report_path = repo / "artifacts/report.json"
            with self.assertRaises(mod.ProofFailure):
                mod.run_proof(
                    repo=repo,
                    report_path=report_path,
                    expected_main_sha="c" * 40,
                    timeout=1,
                    attempts=1,
                    retry_delay=0,
                )
            report = self.load_report(report_path)
            self.assertEqual(
                report["failure"]["reason_code"],
                "LOCAL_MARKET_FIELD_TIMESTAMP_MISMATCH",
            )
            self.assertEqual(report["failure"]["target"], "market_field_json")

    def test_invalid_sha_still_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            report_path = repo / "artifacts/report.json"
            with self.assertRaises(mod.ProofFailure):
                mod.run_proof(
                    repo=repo,
                    report_path=report_path,
                    expected_main_sha="bad",
                    timeout=1,
                    attempts=1,
                    retry_delay=0,
                )
            report = self.load_report(report_path)
            self.assertEqual(
                report["failure"]["reason_code"], "EXPECTED_MAIN_SHA_MUST_BE_40_HEX"
            )
            self.assertEqual(report["failure"]["stage"], "input_validation")

    def test_external_failure_retains_target_url_status_redirects_and_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(Path(tmp))
            report_path = repo / "artifacts/report.json"
            failure = mod.ProofFailure(
                "FETCH_FAILED",
                stage="external_fetch",
                url=mod.TARGETS["pages_html"],
                details={
                    "requested_url": mod.TARGETS["pages_html"],
                    "final_url": mod.TARGETS["pages_html"],
                    "http_status": 503,
                    "redirects": [
                        {
                            "status": 302,
                            "from": "https://example.test/a",
                            "to": "https://example.test/b",
                        }
                    ],
                    "attempt_count": 6,
                    "last_exception_type": "HTTPError",
                    "last_exception_message": "503 Service Unavailable",
                },
            )
            with mock.patch.object(mod, "fetch_with_retry", side_effect=failure):
                with self.assertRaises(mod.ProofFailure):
                    mod.run_proof(
                        repo=repo,
                        report_path=report_path,
                        expected_main_sha="d" * 40,
                        timeout=1,
                        attempts=6,
                        retry_delay=0,
                    )
            report = self.load_report(report_path)
            target = report["targets"]["pages_html"]
            self.assertEqual(target["status"], "FAIL")
            self.assertEqual(target["requested_url"], mod.TARGETS["pages_html"])
            self.assertEqual(target["http_status"], 503)
            self.assertEqual(target["redirect_count"], 1)
            self.assertEqual(target["failure"]["reason_code"], "FETCH_FAILED")
            self.assertEqual(target["failure"]["details"]["attempt_count"], 6)

    def test_partial_success_is_retained_before_next_target_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_repo(Path(tmp))
            report_path = repo / "artifacts/report.json"
            html = (repo / mod.LOCAL_FILES["pages_html"]).read_bytes()
            first = mod.FetchResult(
                requested_url=mod.TARGETS["pages_html"],
                final_url=mod.TARGETS["pages_html"],
                status=200,
                redirects=[],
                content_type="text/html",
                body=html,
                headers={},
            )
            second_failure = mod.ProofFailure(
                "FETCH_FAILED",
                stage="external_fetch",
                url=mod.TARGETS["snapshot_json"],
                details={
                    "requested_url": mod.TARGETS["snapshot_json"],
                    "http_status": 404,
                    "redirects": [],
                    "attempt_count": 1,
                },
            )
            with mock.patch.object(
                mod, "fetch_with_retry", side_effect=[first, second_failure]
            ):
                with self.assertRaises(mod.ProofFailure):
                    mod.run_proof(
                        repo=repo,
                        report_path=report_path,
                        expected_main_sha="e" * 40,
                        timeout=1,
                        attempts=1,
                        retry_delay=0,
                    )
            report = self.load_report(report_path)
            self.assertEqual(report["targets"]["pages_html"]["status"], "PASS")
            self.assertEqual(report["targets"]["snapshot_json"]["status"], "FAIL")
            self.assertEqual(report["targets"]["snapshot_json"]["http_status"], 404)

    def test_fetch_retry_retains_each_attempt(self) -> None:
        calls = 0

        def failing_fetcher(url: str, *, timeout: float):
            nonlocal calls
            calls += 1
            raise mod.ProofFailure(
                "HTTP_ERROR",
                stage="external_fetch",
                url=url,
                details={"http_status": 502, "redirects": []},
            )

        with self.assertRaises(mod.ProofFailure) as ctx:
            mod.fetch_with_retry(
                "https://example.test",
                timeout=1,
                attempts=3,
                retry_delay=0,
                fetcher=failing_fetcher,
            )
        self.assertEqual(calls, 3)
        self.assertEqual(ctx.exception.reason_code, "FETCH_FAILED")
        self.assertEqual(ctx.exception.details["attempt_count"], 3)
        self.assertEqual(len(ctx.exception.details["attempts"]), 3)

    def test_workflow_retains_artifact_before_enforcing_failure(self) -> None:
        workflow = Path(__file__).parents[2] / ".github/workflows/crypto-astro-public-http-proof.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("name: Validate retained failure fixture", text)
        self.assertIn("LOCAL_PROOF_TIMESTAMP_MISMATCH", text)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", text)
        self.assertIn("continue-on-error: true", text)
        self.assertIn("github.run_attempt", text)
        self.assertIn("crypto-astro-public-http-proof.exit-code.txt", text)
        self.assertIn("name: Enforce proof outcome", text)
        self.assertLess(text.index("name: Upload HTTP proof evidence"), text.index("name: Enforce proof outcome"))


if __name__ == "__main__":
    unittest.main()
