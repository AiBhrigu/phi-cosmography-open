import copy
import unittest

from verify_operational_cadence import (
    EXPECTED_EXCEPTION_MODES,
    EXPECTED_INPUTS,
    EXPECTED_MODES,
    OPERATOR_BOUNDARY,
    verify_cadence_workflow,
    verify_manual_workflow,
    verify_operator_review,
    verify_policy,
)


def valid_policy():
    return {
        "schema_version": "crypto_astro_operational_cadence_v0_1",
        "refresh_trigger": "workflow_dispatch",
        "default_mode": "DAILY_CADENCE",
        "allowed_modes": list(EXPECTED_MODES),
        "exception_modes": list(EXPECTED_EXCEPTION_MODES),
        "required_dispatch_inputs": list(EXPECTED_INPUTS),
        "cadence": {
            "target_accepted_refresh_interval_hours": 24,
            "daily_minimum_interval_hours": 18,
            "target_max_operational_gap_hours": 48,
        },
        "freshness": {
            "fresh_hours": 72,
            "stale_limited_hours": 168,
            "unavailable_after_hours": 168,
        },
        "single_flight": {
            "concurrent_workflow_runs_forbidden": True,
            "second_open_refresh_pr_forbidden": True,
            "non_current_main_dispatch_forbidden": True,
            "auto_close_previous_refresh_pr": False,
        },
        "acceptance": {
            "bhrigu_consumer_preflight_required": True,
            "atomic_branch_proof_required": True,
            "review_pr_required": True,
            "desktop_visual_review_required": True,
            "mobile_visual_review_required": True,
            "explicit_merge_authorization_required": True,
            "public_pages_verification_required": True,
            "bhrigu_btc_field_read_verification_required": True,
        },
        "deployment": {
            "refresh_workflow_merge_command_allowed": False,
            "refresh_workflow_deploy_command_allowed": False,
            "pages_publish_after_accepted_main_merge": True,
        },
        "prohibited_refresh_triggers": ["schedule", "push"],
        "boundary": {"cron": False, "auto_merge": False},
    }


def valid_manual():
    modes = "\n".join(f"          - {mode}" for mode in EXPECTED_MODES)
    return f"""name: Crypto-Astro Static Refresh Manual
on:
  workflow_dispatch:
    inputs:
      refresh_mode:
        options:
{modes}
      operator_ref:
      refresh_reason:
concurrency:
  group: crypto-astro-static-refresh-manual
  cancel-in-progress: false
jobs:
  refresh:
    env:
      CRYPTO_ASTRO_REFRESH_MODE: input
      CRYPTO_ASTRO_OPERATOR_REF: input
      CRYPTO_ASTRO_REFRESH_REASON: input
    steps:
      - uses: actions/checkout@v5
        with:
          ref: main
      - name: Verify operational cadence and single-flight preflight
        run: |
          python tools/crypto_astro_operations/verify_operational_cadence.py
          git fetch origin main
          LOCAL_SHA=$(git rev-parse HEAD)
          MAIN_SHA=$(git rev-parse origin/main)
          OPEN_REFRESH_COUNT=$(gh pr list --state open --base main --json number)
          test "$OPEN_REFRESH_COUNT" = "0"
          echo daily_minimum_interval_hours
          echo automation/crypto-astro-static-refresh-
      - name: Materialize cadence metadata in operator review
        run: |
          echo REFRESH_MODE=
          echo OPERATOR_REF=
          echo REFRESH_REASON=
          echo Workflow may push one fully validated review branch
          echo It may not merge or issue a deployment command.
      - run: python tools/crypto_astro_static_refresh/test_bhrigu_consumer_contract_v0_1.py
      - run: npm run verify:btc-producer-contract
      - run: echo ATOMIC_REFRESH_BRANCH=PASS
      - run: gh pr create --base main --body "explicit merge authorization"
"""


def valid_cadence_workflow():
    return """name: Crypto-Astro Operational Cadence PR
on:
  pull_request:
    paths:
      - '.github/workflows/crypto-astro-static-refresh-manual.yml'
      - '.github/workflows/crypto-astro-operational-cadence-pr.yml'
      - '.github/workflows/crypto-astro-snapshot-memory-pr.yml'
      - 'docs/crypto-astro-service/CRYPTO_ASTRO_OPERATIONAL_CADENCE_v0_1.md'
      - 'docs/crypto-astro-service/crypto_astro_operational_cadence_v0_1.json'
      - 'tools/crypto_astro_operations/**'
      - 'docs/crypto-astro-service/crypto_astro_operator_review.md'
steps:
  - run: python -m unittest tools/crypto_astro_operations/test_verify_operational_cadence.py
  - run: python tools/crypto_astro_operations/verify_operational_cadence.py
"""


def valid_operator_review():
    return f"""REFRESH_MODE=DAILY_CADENCE
OPERATOR_REF=operator-f
REFRESH_REASON=daily accepted refresh
{OPERATOR_BOUNDARY}
"""


class OperationalCadenceTests(unittest.TestCase):
    def test_locked_policy_passes(self):
        self.assertEqual(verify_policy(valid_policy()), [])

    def test_daily_minimum_drift_fails(self):
        policy = copy.deepcopy(valid_policy())
        policy["cadence"]["daily_minimum_interval_hours"] = 17
        self.assertIn("policy:daily_minimum", verify_policy(policy))

    def test_schedule_trigger_fails(self):
        text = valid_manual().replace("  workflow_dispatch:\n", "  workflow_dispatch:\n  schedule:\n")
        self.assertTrue(any("manual:triggers" in value for value in verify_manual_workflow(text, valid_policy())))

    def test_merge_command_fails(self):
        text = valid_manual() + "\n      - run: gh pr merge 1\n"
        self.assertIn("manual:forbidden:merge_command", verify_manual_workflow(text, valid_policy()))

    def test_removed_consumer_gate_fails(self):
        text = valid_manual().replace("test_bhrigu_consumer_contract_v0_1.py", "consumer_removed.py")
        self.assertIn(
            "manual:missing:test_bhrigu_consumer_contract_v0_1.py",
            verify_manual_workflow(text, valid_policy()),
        )

    def test_removed_open_pr_gate_fails(self):
        text = valid_manual().replace('test "$OPEN_REFRESH_COUNT" = "0"', "echo unchecked")
        self.assertIn("manual:open_pr_count", verify_manual_workflow(text, valid_policy()))

    def test_cadence_workflow_passes(self):
        self.assertEqual(verify_cadence_workflow(valid_cadence_workflow()), [])

    def test_old_operator_boundary_fails(self):
        text = valid_operator_review() + "No push, no PR, no deploy."
        self.assertIn("operator_review:obsolete_boundary", verify_operator_review(text))

    def test_operator_review_passes(self):
        self.assertEqual(verify_operator_review(valid_operator_review()), [])


if __name__ == "__main__":
    unittest.main()
