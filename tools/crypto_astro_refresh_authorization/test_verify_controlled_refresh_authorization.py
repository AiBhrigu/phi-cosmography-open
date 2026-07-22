#!/usr/bin/env python3
"""Tests for the controlled refresh authorization packet verifier."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

from tools.crypto_astro_refresh_authorization import verify_controlled_refresh_authorization as verifier


class ControlledRefreshAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[2]
        cls.packet = verifier.load_packet(cls.repo / verifier.PACKET_PATH)
        cls.index_text = (cls.repo / verifier.INDEX_PATH).read_text(encoding="utf-8")

    def test_current_package_passes(self) -> None:
        report = verifier.verify_repository(self.repo)
        self.assertEqual(report["status"], "PASS", report)

    def test_rejects_execution_authorized(self) -> None:
        value = copy.deepcopy(self.packet)
        value["execution_authorized"] = True
        self.assertIn("packet:execution_authorized", verifier.validate_packet(value))

    def test_rejects_protocol_sum(self) -> None:
        value = copy.deepcopy(self.packet)
        value["defi_tvl_methodology_lock"]["protocol_sum_forbidden"] = False
        self.assertIn("defi:protocol_sum_forbidden", verifier.validate_packet(value))

    def test_rejects_legacy_protocols_value_url(self) -> None:
        value = copy.deepcopy(self.packet)
        value["defi_tvl_methodology_lock"]["source_url"] = "https://api.llama.fi/protocols"
        self.assertIn("defi:url", verifier.validate_packet(value))

    def test_rejects_missing_required_generated_file(self) -> None:
        value = copy.deepcopy(self.packet)
        value["exact_generated_pr_scope"]["required_changed_files"].pop()
        self.assertIn("scope:required", verifier.validate_packet(value))

    def test_rejects_runner_change_permission(self) -> None:
        value = copy.deepcopy(self.packet)
        value["exact_generated_pr_scope"]["runner_or_workflow_changes_forbidden"] = False
        self.assertIn("scope:no_runner_workflow", verifier.validate_packet(value))

    def test_rejects_open_boundary(self) -> None:
        value = copy.deepcopy(self.packet)
        value["boundary"]["backend"] = True
        self.assertIn("boundary:opened", verifier.validate_packet(value))

    def test_rejects_repeated_dispatch(self) -> None:
        value = copy.deepcopy(self.packet)
        value["rollback_and_hold"]["no_repeat_dispatch_without_new_authorization"] = False
        self.assertIn("rollback:no_repeat", verifier.validate_packet(value))

    def test_rejects_visual_review_disabled(self) -> None:
        value = copy.deepcopy(self.packet)
        value["visual_review_lock"]["mobile_required"] = False
        self.assertIn("visual:mobile", verifier.validate_packet(value))

    def test_rejects_missing_public_proof_gate(self) -> None:
        value = copy.deepcopy(self.packet)
        value["fail_closed_gates"].remove("FAIL_PUBLIC_HTTP_PROOF")
        self.assertIn("fail_codes:exact", verifier.validate_packet(value))

    def test_rejects_removed_hold_marker(self) -> None:
        text = self.index_text.replace(
            "HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH",
            "UNLOCKED",
        )
        failures = verifier.validate_index(text)
        self.assertTrue(any(item.startswith("index:missing:HOLD_") for item in failures))


if __name__ == "__main__":
    unittest.main()
