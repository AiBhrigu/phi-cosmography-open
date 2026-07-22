#!/usr/bin/env python3
"""Tests for the Gate 3 post-closure truth index verifier."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.crypto_astro_gate_3_closure import verify_gate_3_post_closure as verifier


class Gate3PostClosureVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[2]
        cls.capsule = verifier.load_capsule(cls.repo / verifier.CAPSULE_PATH)
        cls.index_text = (cls.repo / verifier.INDEX_PATH).read_text(encoding="utf-8")

    def test_current_repository_package_passes(self) -> None:
        report = verifier.verify_repository(self.repo)
        self.assertEqual(report["status"], "PASS", report)

    def test_rejects_production_sha_mismatch(self) -> None:
        value = copy.deepcopy(self.capsule)
        value["production_proof"]["actual_head_sha"] = "0" * 40
        failures = verifier.validate_capsule(value)
        self.assertIn("proof:exact_state", failures)

    def test_rejects_diagnostic_issue_as_pass(self) -> None:
        value = copy.deepcopy(self.capsule)
        value["diagnostic_issue_chain"][0]["final_outcome"] = "PUBLIC_HTTP_PROOF_PASS"
        failures = verifier.validate_capsule(value)
        self.assertIn("issue:160:outcome", failures)

    def test_rejects_open_boundary(self) -> None:
        value = copy.deepcopy(self.capsule)
        value["boundary"]["market_data_refresh"] = True
        failures = verifier.validate_capsule(value)
        self.assertIn("boundary:opened", failures)

    def test_rejects_missing_hold_marker(self) -> None:
        text = self.index_text.replace(
            "STATE=HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH",
            "STATE=UNLOCKED",
        )
        failures = verifier.validate_index(text)
        self.assertTrue(any(item.startswith("index:missing:STATE=") for item in failures))

    def test_json_is_deterministically_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capsule.json"
            path.write_text(
                json.dumps(self.capsule, indent=2, sort_keys=False) + "\n",
                encoding="utf-8",
            )
            reloaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(reloaded, self.capsule)


if __name__ == "__main__":
    unittest.main()
