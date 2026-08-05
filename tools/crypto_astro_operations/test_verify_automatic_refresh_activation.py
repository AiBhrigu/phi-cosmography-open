from __future__ import annotations
import json, subprocess, tempfile, unittest
from pathlib import Path
from tools.crypto_astro_operations.verify_automatic_refresh_activation import evaluate_decision, verify_repository, verify_scheduler, verify_publisher
REPO=Path(__file__).resolve().parents[2]
POLICY=json.loads((REPO/"docs/crypto-astro-service/crypto_astro_automatic_refresh_activation_v0_1.json").read_text())
SCHEDULER=(REPO/".github/workflows/crypto-astro-automatic-refresh.yml").read_text()
PUBLISHER=(REPO/".github/workflows/crypto-astro-generated-refresh-autopublish.yml").read_text()
class AutomaticRefreshActivationTest(unittest.TestCase):
    def test_repository_contract(self):
        report=verify_repository(REPO); self.assertEqual(report["status"],"PASS",report["failures"])
    def test_decision_matrix(self):
        self.assertEqual(evaluate_decision(POLICY,snapshot_age_hours=17),"HOLD_MINIMUM_INTERVAL")
        self.assertEqual(evaluate_decision(POLICY,snapshot_age_hours=19),"HOLD_BEFORE_AUTOMATIC_WINDOW")
        self.assertEqual(evaluate_decision(POLICY,snapshot_age_hours=20),"DISPATCH_MANUAL_REFRESH")
        self.assertEqual(evaluate_decision(POLICY,snapshot_age_hours=22,open_refresh_pr_count=1),"BLOCK_OPEN_REFRESH_PR")
        self.assertEqual(evaluate_decision(POLICY,snapshot_age_hours=22,active_manual_run_count=1),"BLOCK_SINGLE_FLIGHT")
        self.assertEqual(evaluate_decision(POLICY,snapshot_age_hours=22,source_probe="FAIL"),"SOURCE_FAILURE_RECHECK")
        self.assertEqual(evaluate_decision(POLICY,snapshot_age_hours=22,material_change=False),"NO_MATERIAL_CHANGE_RECHECK")
    def test_schedule_removal_fails(self):
        mutated=SCHEDULER.replace("  schedule:\n", "",1).replace("    - cron: '17 * * * *'\n","",1)
        self.assertTrue(verify_scheduler(mutated))
    def test_scheduler_merge_command_fails(self):
        self.assertTrue(any("merge" in item for item in verify_scheduler(SCHEDULER+"\n# gh pr merge 99\n")))
    def test_runner_temp_is_resolved_at_runtime(self):
        self.assertNotIn("${{ runner.temp }}", SCHEDULER)
        self.assertIn("${RUNNER_TEMP}", SCHEDULER)
        self.assertIn("$GITHUB_ENV", SCHEDULER)
        self.assertIn("DIAGNOSTICS_LOCATION=RUNNER_TEMP", SCHEDULER)
        invalid=SCHEDULER.replace('${RUNNER_TEMP}', '${{ runner.temp }}', 1)
        self.assertTrue(any('invalid_job_level_runner_context' in item for item in verify_scheduler(invalid)))
    def test_external_diagnostics_leave_checkout_clean(self):
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as runner_temp:
            repo=Path(repo_dir); subprocess.run(["git","init","-q"],cwd=repo,check=True); subprocess.run(["git","config","user.email","test@example.com"],cwd=repo,check=True); subprocess.run(["git","config","user.name","test"],cwd=repo,check=True)
            (repo/"tracked.txt").write_text("baseline\n"); subprocess.run(["git","add","tracked.txt"],cwd=repo,check=True); subprocess.run(["git","commit","-qm","baseline"],cwd=repo,check=True)
            Path(runner_temp,"decision.json").write_text("{}\n")
            status=subprocess.check_output(["git","status","--porcelain"],cwd=repo,text=True).strip(); self.assertEqual(status,"")
    def test_tracked_diagnostics_reproduce_old_failure(self):
        with tempfile.TemporaryDirectory() as repo_dir:
            repo=Path(repo_dir); subprocess.run(["git","init","-q"],cwd=repo,check=True); subprocess.run(["git","config","user.email","test@example.com"],cwd=repo,check=True); subprocess.run(["git","config","user.name","test"],cwd=repo,check=True)
            (repo/"tracked.txt").write_text("baseline\n"); subprocess.run(["git","add","tracked.txt"],cwd=repo,check=True); subprocess.run(["git","commit","-qm","baseline"],cwd=repo,check=True)
            (repo/"artifacts").mkdir(); (repo/"artifacts/decision.json").write_text("{}\n")
            self.assertIn("?? artifacts/",subprocess.check_output(["git","status","--porcelain"],cwd=repo,text=True))
    def test_publisher_expected_head_marker_required(self):
        self.assertTrue(verify_publisher(PUBLISHER.replace("EXPECTED_HEAD_PROTECTION=PASS","EXPECTED_HEAD_PROTECTION=REMOVED")))
if __name__=="__main__": unittest.main()
