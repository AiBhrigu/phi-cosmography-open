import copy
import unittest

from verify_operational_cadence import (
    AUTOMATIC_REFRESH_DESIGN_ID,
    AUTOMATIC_REFRESH_DESIGN_STATUS,
    EXPECTED_EXCEPTION_MODES,
    FRESHNESS_CONTRACT_ID,
    EXPECTED_INPUTS,
    EXPECTED_MODES,
    OPERATOR_BOUNDARY,
    automatic_refresh_dry_run_matrix,
    evaluate_automatic_refresh_dry_run,
    verify_automatic_refresh_design,
    verify_automatic_refresh_dry_run,
    verify_cadence_workflow,
    verify_manual_workflow,
    verify_operator_review,
    verify_policy,
)


def valid_automatic_refresh_design():
    return {
        "design_id": AUTOMATIC_REFRESH_DESIGN_ID,
        "status": AUTOMATIC_REFRESH_DESIGN_STATUS,
        "activation_requires_separate_authorization": True,
        "schedule_activation_allowed": False,
        "production_activation_allowed": False,
        "proposed_check_interval_minutes": 60,
        "proposed_eligibility_age_hours": 20,
        "daily_minimum_interval_hours": 18,
        "freshness_boundary_hours": 24,
        "operational_breach_hours": 48,
        "unavailable_after_hours": 168,
        "dispatch_target": "crypto-astro-static-refresh-manual.yml",
        "dispatch_mode": "DAILY_CADENCE",
        "exact_main_lock_required": True,
        "single_flight_required": True,
        "source_health_required": True,
        "material_change_required_for_review_pr": True,
        "review_pr_only": True,
        "auto_merge_allowed": False,
        "deploy_command_allowed": False,
        "timestamp_only_refresh_allowed": False,
        "recheck_after_no_material_change_minutes": 60,
    }


def valid_policy():
    return {
        "schema_version": "crypto_astro_operational_cadence_v0_1",
        "freshness_contract_id": FRESHNESS_CONTRACT_ID,
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
            "fresh_hours": 24,
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
        "automatic_refresh_design": valid_automatic_refresh_design(),
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


def dry_run(age, **overrides):
    scenario = {
        "scenario_id": "fixture",
        "snapshot_age_hours": age,
        "exact_main_match": True,
        "open_refresh_pr_count": 0,
        "workflow_in_progress": False,
        "source_status": "HEALTHY",
        "material_change": "YES",
    }
    scenario.update(overrides)
    return evaluate_automatic_refresh_dry_run(valid_policy(), scenario)


class OperationalCadenceTests(unittest.TestCase):
    def test_locked_policy_passes(self):
        self.assertEqual(verify_policy(valid_policy()), [])

    def test_automatic_refresh_design_passes_and_remains_inactive(self):
        policy = valid_policy()
        self.assertEqual(verify_automatic_refresh_design(policy), [])
        design = policy["automatic_refresh_design"]
        self.assertEqual(design["status"], "DESIGN_ONLY_DRY_RUN")
        self.assertFalse(design["schedule_activation_allowed"])
        self.assertFalse(design["production_activation_allowed"])
        self.assertFalse(design["auto_merge_allowed"])
        self.assertFalse(design["deploy_command_allowed"])

    def test_automatic_activation_drift_fails(self):
        for key in (
            "schedule_activation_allowed",
            "production_activation_allowed",
            "auto_merge_allowed",
            "deploy_command_allowed",
            "timestamp_only_refresh_allowed",
        ):
            policy = copy.deepcopy(valid_policy())
            policy["automatic_refresh_design"][key] = True
            self.assertIn(f"automatic:{key}", verify_policy(policy))

    def test_dry_run_matrix_passes(self):
        self.assertEqual(verify_automatic_refresh_dry_run(valid_policy()), [])
        self.assertEqual(len(automatic_refresh_dry_run_matrix(valid_policy())), 15)

    def test_dry_run_minimum_and_automatic_window(self):
        self.assertEqual(dry_run(17)["decision"], "HOLD_MINIMUM_INTERVAL")
        self.assertEqual(dry_run(18)["decision"], "HOLD_BEFORE_AUTOMATIC_WINDOW")
        self.assertEqual(dry_run(19.99)["decision"], "HOLD_BEFORE_AUTOMATIC_WINDOW")
        eligible = dry_run(20)
        self.assertEqual(eligible["decision"], "WOULD_DISPATCH_REVIEW_PR")
        self.assertTrue(eligible["would_dispatch_existing_manual_workflow"])
        self.assertTrue(eligible["would_create_review_pr_only"])

    def test_dry_run_single_flight_and_exact_main_blocks(self):
        self.assertEqual(dry_run(22, exact_main_match=False)["decision"], "BLOCK_MAIN_DRIFT")
        self.assertEqual(dry_run(22, open_refresh_pr_count=1)["decision"], "BLOCK_OPEN_REFRESH_PR")
        self.assertEqual(dry_run(22, workflow_in_progress=True)["decision"], "BLOCK_SINGLE_FLIGHT")

    def test_dry_run_source_failure_and_no_change_have_no_side_effects(self):
        failed = dry_run(22, source_status="FAILED", material_change="UNKNOWN")
        no_change = dry_run(22, material_change="NO")
        self.assertEqual(failed["decision"], "SOURCE_FAILURE_RECHECK")
        self.assertEqual(no_change["decision"], "NO_MATERIAL_CHANGE_RECHECK")
        for result in (failed, no_change):
            self.assertFalse(result["would_modify_public_data"])
            self.assertFalse(result["would_merge"])
            self.assertFalse(result["would_deploy"])
            self.assertFalse(result["schedule_active"])
            self.assertFalse(result["production_active"])

    def test_dry_run_freshness_boundaries(self):
        self.assertEqual(dry_run(24)["freshness_state"], "FRESH")
        self.assertEqual(dry_run(24.0001)["freshness_state"], "STALE_LIMITED")
        self.assertEqual(dry_run(72)["freshness_state"], "STALE_LIMITED")
        self.assertEqual(dry_run(168)["freshness_state"], "STALE_LIMITED")
        self.assertEqual(dry_run(168.0001)["freshness_state"], "UNAVAILABLE")
        self.assertFalse(dry_run(48)["operational_breach"])
        self.assertTrue(dry_run(48.0001)["operational_breach"])
        self.assertEqual(dry_run(-0.1)["decision"], "BLOCK_FUTURE_SNAPSHOT")

    def test_legacy_72h_fresh_boundary_fails(self):
        policy = copy.deepcopy(valid_policy())
        policy["freshness"]["fresh_hours"] = 72
        self.assertIn("policy:fresh_hours", verify_policy(policy))

    def test_freshness_contract_id_drift_fails(self):
        policy = copy.deepcopy(valid_policy())
        policy["freshness_contract_id"] = "legacy_72h_contract"
        self.assertIn("policy:freshness_contract_id", verify_policy(policy))

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
