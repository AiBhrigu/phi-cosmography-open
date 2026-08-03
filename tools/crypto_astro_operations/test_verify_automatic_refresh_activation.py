from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.crypto_astro_operations.verify_automatic_refresh_activation import (
    evaluate_decision,
    verify_repository,
    verify_scheduler,
)


REPO = Path(__file__).resolve().parents[2]
POLICY = json.loads((REPO / "docs/crypto-astro-service/crypto_astro_automatic_refresh_activation_v0_1.json").read_text())
WORKFLOW = (REPO / ".github/workflows/crypto-astro-automatic-refresh.yml").read_text()


class AutomaticRefreshActivationTest(unittest.TestCase):
    def test_repository_contract(self) -> None:
        report = verify_repository(REPO)
        self.assertEqual(report["status"], "PASS", report["failures"])

    def test_decision_matrix(self) -> None:
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=17), "HOLD_MINIMUM_INTERVAL")
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=19), "HOLD_BEFORE_AUTOMATIC_WINDOW")
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=20), "DISPATCH_MANUAL_REFRESH")
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=22, open_refresh_pr_count=1), "BLOCK_OPEN_REFRESH_PR")
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=22, active_manual_run_count=1), "BLOCK_SINGLE_FLIGHT")
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=22, source_probe="FAIL"), "SOURCE_FAILURE_RECHECK")
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=22, material_change=False), "NO_MATERIAL_CHANGE_RECHECK")
        self.assertEqual(evaluate_decision(POLICY, snapshot_age_hours=-0.1), "BLOCK_FUTURE_SNAPSHOT")

    def test_schedule_removal_fails(self) -> None:
        mutated = WORKFLOW.replace("  schedule:\n", "", 1).replace("    - cron: '17 * * * *'\n", "", 1)
        self.assertTrue(any("schedule" in item or "triggers" in item for item in verify_scheduler(mutated)))

    def test_merge_command_fails(self) -> None:
        mutated = WORKFLOW + "\n# gh pr merge 999\n"
        self.assertTrue(any("pr_merge" in item for item in verify_scheduler(mutated)))


if __name__ == "__main__":
    unittest.main()
