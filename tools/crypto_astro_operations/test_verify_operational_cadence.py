import copy
import unittest

from verify_operational_cadence import (
    AUTOMATIC_REFRESH_DESIGN_ID,
    AUTOMATIC_REFRESH_DESIGN_STATUS,
    EXPECTED_EXCEPTION_MODES,
    EXPECTED_INPUTS,
    EXPECTED_MODES,
    FRESHNESS_CONTRACT_ID,
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
        "activation_contract_id": "crypto_astro_automatic_refresh_activation_v0_1",
        "status": AUTOMATIC_REFRESH_DESIGN_STATUS,
        "activation_requires_explicit_merge_authorization": True,
        "activation_on_default_branch_merge": True,
        "schedule_activation_allowed": True,
        "check_interval_minutes": 60,
        "eligibility_age_hours": 20,
        "daily_minimum_interval_hours": 18,
        "freshness_boundary_hours": 24,
        "operational_breach_hours": 48,
        "unavailable_after_hours": 168,
        "scheduler_workflow": "crypto-astro-automatic-refresh.yml",
        "dispatch_target": "crypto-astro-static-refresh-manual.yml",
        "dispatch_mode": "DAILY_CADENCE",
        "exact_main_lock_required": True,
        "single_flight_required": True,
        "source_health_required": True,
        "material_change_required_for_review_pr": True,
        "review_pr_only": True,
        "manual_workflow_dispatch_fallback_preserved": True,
        "auto_merge_allowed": False,
        "deploy_command_allowed": False,
        "timestamp_only_refresh_allowed": False,
        "recheck_after_no_material_change_minutes": 60,
    }


def valid_policy():
    return {
        "schema_version": "crypto_astro_operational_cadence_v0_1",
        "freshness_contract_id": FRESHNESS_CONTRACT_ID,
        "source_producer_trigger": "workflow_dispatch",
        "automatic_control_trigger": "schedule_and_workflow_dispatch",
        "default_mode": "DAILY_CADENCE",
        "allowed_modes": list(EXPECTED_MODES),
        "exception_modes": list(EXPECTED_EXCEPTION_MODES),
        "required_dispatch_inputs": list(EXPECTED_INPUTS),
        "cadence": {
            "target_accepted_refresh_interval_hours": 24,
            "daily_minimum_interval_hours": 18,
            "automatic_eligibility_age_hours": 20,
            "automatic_check_interval_minutes": 60,
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
            "automatic_scheduler_merge_command_allowed": False,
            "automatic_scheduler_deploy_command_allowed": False,
            "pages_publish_after_accepted_main_merge": True,
        },
        "prohibited_source_producer_triggers": ["schedule", "push"],
        "automatic_refresh_design": valid_automatic_refresh_design(),
        "boundary": {
            "cron_control_plane": True,
            "source_producer_cron": False,
            "auto_merge": False,
            "backend": False,
        },
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
          echo Workflow may push one fully validated generated-refresh branch
          echo Publication is permitted only through the gated automatic publication path after all required gates PASS.
          echo Human-authored product PRs are not eligible for this automatic path.
      - run: python tools/crypto_astro_static_refresh/test_bhrigu_consumer_contract_v0_1.py
      - run: npm run verify:btc-producer-contract
      - run: echo ATOMIC_REFRESH_BRANCH=PASS
      - run: gh pr create --base main --body "gated automatic publication path"
"""


def valid_cadence_workflow():
    return """name: Crypto-Astro Operational Cadence PR
on:
  pull_request:
    paths:
      - '.github/workflows/crypto-astro-automatic-refresh.yml'
      - 'docs/crypto-astro-service/crypto_astro_automatic_refresh_activation_v0_1.json'
      - 'tools/crypto_astro_operations/test_verify_operational_cadence.py'
steps:
  - run: python -m unittest tools/crypto_astro_operations/test_verify_operational_cadence.py
  - run: python tools/crypto_astro_operations/verify_operational_cadence.py
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
    def test_activated_policy_passes(self):
        self.assertEqual(verify_policy(valid_policy()), [])
        self.assertEqual(verify_automatic_refresh_design(valid_policy()), [])
        self.assertEqual(AUTOMATIC_REFRESH_DESIGN_STATUS, "ACTIVATION_REVIEW_CANDIDATE")

    def test_automatic_safety_drift_fails(self):
        for key in ("auto_merge_allowed", "deploy_command_allowed", "timestamp_only_refresh_allowed"):
            policy = copy.deepcopy(valid_policy())
            policy["automatic_refresh_design"][key] = True
            self.assertIn(f"automatic:{key}", verify_policy(policy))

    def test_decision_matrix_passes(self):
        self.assertEqual(verify_automatic_refresh_dry_run(valid_policy()), [])
        self.assertEqual(len(automatic_refresh_dry_run_matrix(valid_policy())), 15)
        self.assertEqual(dry_run(17)["decision"], "HOLD_MINIMUM_INTERVAL")
        self.assertEqual(dry_run(19)["decision"], "HOLD_BEFORE_AUTOMATIC_WINDOW")
        self.assertEqual(dry_run(20)["decision"], "WOULD_DISPATCH_REVIEW_PR")
        self.assertEqual(dry_run(22, exact_main_match=False)["decision"], "BLOCK_MAIN_DRIFT")
        self.assertEqual(dry_run(22, open_refresh_pr_count=1)["decision"], "BLOCK_OPEN_REFRESH_PR")
        self.assertEqual(dry_run(22, workflow_in_progress=True)["decision"], "BLOCK_SINGLE_FLIGHT")
        self.assertEqual(dry_run(22, source_status="FAILED")["decision"], "SOURCE_FAILURE_RECHECK")
        self.assertEqual(dry_run(22, material_change="NO")["decision"], "NO_MATERIAL_CHANGE_RECHECK")

    def test_freshness_contract_unchanged(self):
        self.assertEqual(dry_run(24)["freshness_state"], "FRESH")
        self.assertEqual(dry_run(24.0001)["freshness_state"], "STALE_LIMITED")
        self.assertEqual(dry_run(168)["freshness_state"], "STALE_LIMITED")
        self.assertEqual(dry_run(168.0001)["freshness_state"], "UNAVAILABLE")
        self.assertFalse(dry_run(48)["operational_breach"])
        self.assertTrue(dry_run(48.0001)["operational_breach"])
        self.assertEqual(dry_run(-0.1)["decision"], "BLOCK_FUTURE_SNAPSHOT")

    def test_scheduler_is_configured_but_premerge_inactive(self):
        result = dry_run(20)
        self.assertTrue(result["schedule_configured"])
        self.assertFalse(result["schedule_active_before_merge"])
        self.assertFalse(result["would_merge"])
        self.assertFalse(result["would_deploy"])
        self.assertFalse(result["would_modify_public_data"])

    def test_manual_producer_remains_dispatch_only(self):
        self.assertEqual(verify_manual_workflow(valid_manual(), valid_policy()), [])
        scheduled = valid_manual().replace("  workflow_dispatch:\n", "  workflow_dispatch:\n  schedule:\n")
        self.assertTrue(any("manual:triggers" in value for value in verify_manual_workflow(scheduled, valid_policy())))
        merged = valid_manual() + "\n      - run: gh pr merge 1\n"
        self.assertIn("manual:forbidden:merge_command", verify_manual_workflow(merged, valid_policy()))

    def test_cadence_workflow_and_operator_boundary(self):
        self.assertEqual(verify_cadence_workflow(valid_cadence_workflow()), [])
        self.assertEqual(verify_operator_review(OPERATOR_BOUNDARY), [])
        self.assertIn("operator_review:obsolete_boundary", verify_operator_review(OPERATOR_BOUNDARY + "\nNo push, no PR, no deploy."))


if __name__ == "__main__":
    unittest.main()
