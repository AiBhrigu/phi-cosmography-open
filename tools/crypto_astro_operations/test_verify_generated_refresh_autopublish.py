from __future__ import annotations
import unittest
from tools.crypto_astro_operations.verify_generated_refresh_autopublish import REQUIRED_FILES, OPTIONAL_FILES, REQUIRED_WORKFLOWS, exact_scope, latest_runs_by_name, parse_body, GateError
class GeneratedRefreshAutopublishTest(unittest.TestCase):
    def test_exact_scope(self):
        self.assertTrue(exact_scope(set(REQUIRED_FILES))); self.assertTrue(exact_scope(set(REQUIRED_FILES)|set(OPTIONAL_FILES))); self.assertFalse(exact_scope(set(REQUIRED_FILES)|{"README.md"}))
    def test_required_ci_count(self): self.assertEqual(len(REQUIRED_WORKFLOWS),16)
    def test_parse_scheduler_provenance(self):
        body="- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_12345\n- Base SHA: " + "a"*40 + "\n- Assistant dispatch issue: none\n"
        self.assertEqual(parse_body(body),(12345,"a"*40))
    def test_missing_issue_marker_fails(self):
        with self.assertRaises(GateError): parse_body("- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_12345\n- Base SHA: "+"a"*40+"\n")
    def test_latest_runs_selected(self):
        name=next(iter(REQUIRED_WORKFLOWS)); selected=latest_runs_by_name([{"id":1,"name":name},{"id":2,"name":name}]); self.assertEqual(selected[name]["id"],2)
if __name__=="__main__":unittest.main()
