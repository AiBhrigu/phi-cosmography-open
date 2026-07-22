#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("verify_public_http_proof.py")
SPEC = importlib.util.spec_from_file_location("verify_public_http_proof", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class PublicHttpProofTests(unittest.TestCase):
    def test_content_type_normalization(self) -> None:
        self.assertEqual(
            mod.normalized_content_type("application/json; charset=utf-8"),
            "application/json",
        )
        self.assertEqual(mod.normalized_content_type(None), "")

    def test_sha_lock_validation(self) -> None:
        mod.validate_sha("")
        mod.validate_sha("a" * 40)
        with self.assertRaises(mod.ProofFailure):
            mod.validate_sha("not-a-sha")

    def test_exact_bytes_mismatch_is_fail_closed(self) -> None:
        mod.assert_exact_bytes(b"same", b"same", "fixture")
        with self.assertRaises(mod.ProofFailure):
            mod.assert_exact_bytes(b"live", b"expected", "fixture")

    def test_bhrigu_read_requires_timestamp_and_success_heading(self) -> None:
        timestamp = "2026-07-22T08:02:05Z"
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
        with self.assertRaises(mod.ProofFailure):
            mod.verify_bhrigu_read(bad, expected_timestamp=timestamp)

    def test_local_source_timestamp_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            data = repo / "site/crypto-astro/data"
            data.mkdir(parents=True)
            snapshot = {"generated_at_utc": "2026-07-22T08:02:05Z"}
            proof = {"generated_at_utc": "2026-07-22T08:02:05Z"}
            field = {"updated_at_utc": "2026-07-22T08:02:05Z"}
            (data / "crypto_astro_snapshot.public.json").write_text(json.dumps(snapshot))
            (data / "crypto_astro_snapshot_proof.public.json").write_text(json.dumps(proof))
            (data / "market_field_snapshot.public.v0_1.json").write_text(json.dumps(field))
            (repo / "site/crypto-astro/index.html").write_text("<html></html>")
            self.assertEqual(
                mod.read_local_json(
                    repo,
                    "site/crypto-astro/data/crypto_astro_snapshot.public.json",
                )["generated_at_utc"],
                snapshot["generated_at_utc"],
            )


if __name__ == "__main__":
    unittest.main()
