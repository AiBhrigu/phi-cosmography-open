from __future__ import annotations
import unittest
from pathlib import Path
from tools.crypto_astro_operations.verify_generated_refresh_ci_release import (
    GateError, RECOVERY_SCHEMA, canonical_body, parse_body, parse_recovery_issue,
    validate_control_workflow, validate_pr_identity, validate_scope,
)
from tools.crypto_astro_operations.verify_generated_refresh_autopublish import REQUIRED_FILES

REPO="AiBhrigu/phi-cosmography-open"; H="b"*40; B="a"*40
def pr(**kw):
    v={"state":"open","title":"Crypto-Astro: automated static market snapshot refresh",
       "user":{"login":"github-actions[bot]"},"base":{"ref":"main","sha":B},
       "head":{"ref":"automation/crypto-astro-static-refresh-123","sha":H,"repo":{"full_name":REPO}}}
    for k,val in kw.items():
        if k=="author": v["user"]["login"]=val
        elif k=="title": v["title"]=val
        elif k=="base": v["base"]["ref"]=val
        elif k=="head_ref": v["head"]["ref"]=val
        elif k=="head_sha": v["head"]["sha"]=val
        elif k=="repo": v["head"]["repo"]["full_name"]=val
    return v
class T(unittest.TestCase):
    def test_valid_scheduler_bot_pr(self): self.assertEqual(validate_pr_identity(pr(),REPO,H)[0],123)
    def test_wrong_author(self):
        with self.assertRaisesRegex(GateError,"WRONG_AUTHOR"): validate_pr_identity(pr(author="human"),REPO,H)
    def test_human_authored(self):
        with self.assertRaises(GateError): validate_pr_identity(pr(author="AiBhrigu"),REPO,H)
    def test_fork(self):
        with self.assertRaisesRegex(GateError,"FORK_PR_REJECTED"): validate_pr_identity(pr(repo="fork/repo"),REPO,H)
    def test_wrong_title(self):
        with self.assertRaisesRegex(GateError,"WRONG_TITLE"): validate_pr_identity(pr(title="x"),REPO,H)
    def test_wrong_head_prefix(self):
        with self.assertRaisesRegex(GateError,"WRONG_HEAD_PREFIX"): validate_pr_identity(pr(head_ref="feature/x"),REPO,H)
    def test_wrong_base(self):
        with self.assertRaisesRegex(GateError,"WRONG_BASE"): validate_pr_identity(pr(base="dev"),REPO,H)
    def test_head_drift(self):
        with self.assertRaisesRegex(GateError,"HEAD_DRIFT"): validate_pr_identity(pr(),REPO,"c"*40)
    def test_scope(self): validate_scope(set(REQUIRED_FILES))
    def test_wrong_generated_scope(self):
        with self.assertRaisesRegex(GateError,"WRONG_GENERATED_SCOPE"): validate_scope(set(REQUIRED_FILES)|{"README.md"})
    def test_source_provider_change_rejected(self):
        with self.assertRaises(GateError): validate_scope(set(REQUIRED_FILES)|{"tools/provider.py"})
    def test_methodology_change_rejected(self):
        with self.assertRaises(GateError): validate_scope(set(REQUIRED_FILES)|{"tools/methodology.py"})
    def test_product_change_rejected(self):
        with self.assertRaises(GateError): validate_scope(set(REQUIRED_FILES)|{"site/product.tsx"})
    def test_routing_change_rejected(self):
        with self.assertRaises(GateError): validate_scope(set(REQUIRED_FILES)|{"lib/router.ts"})
    def test_payment_backend_rejected(self):
        with self.assertRaises(GateError): validate_scope(set(REQUIRED_FILES)|{"backend/payment.py"})
    def test_legacy_body(self):
        body=f"- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_9\n- Base SHA: {B}\n"
        self.assertEqual(parse_body(body),(9,B,B))
    def test_canonical_body_split(self):
        body=f"- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_9\n- Generation Base SHA: {B}\n- Acceptance Base SHA: {H}\n"
        self.assertEqual(parse_body(body),(9,B,H))
    def test_missing_scheduler_provenance(self):
        with self.assertRaises(GateError): parse_body(f"- Base SHA: {B}\n")
    def test_recovery_issue(self):
        body=f"SCHEMA={RECOVERY_SCHEMA}\nPR=336\nEXPECTED_HEAD_SHA={H}\nEXPECTED_GENERATION_BASE_SHA={B}\n"
        self.assertEqual(parse_recovery_issue(body),(336,H,B))
    def test_secret_gate_rejected(self):
        with self.assertRaisesRegex(GateError,"SECRET_EXPOSURE"): validate_control_workflow("permissions:\n  contents: read\nrun: ${{ secrets.X }}")
    def test_write_gate_rejected(self):
        with self.assertRaisesRegex(GateError,"WRITE_PERMISSION"): validate_control_workflow("permissions:\n  contents: write\n")
    def test_read_only_gate_accepted(self): validate_control_workflow("permissions:\n  contents: read\n")
    def test_natural_cycle_explicit_trusted_release_handoff(self):
        root=Path(__file__).resolve().parents[2]
        producer=(root/'.github/workflows/crypto-astro-static-refresh-manual.yml').read_text(encoding='utf-8')
        release=(root/'.github/workflows/crypto-astro-generated-refresh-ci-release.yml').read_text(encoding='utf-8')
        self.assertIn('actions: write', producer)
        self.assertIn('name: Dispatch trusted CI release', producer)
        self.assertIn('gh workflow run crypto-astro-generated-refresh-ci-release.yml --ref main', producer)
        self.assertIn('-f manual_run_id="$GITHUB_RUN_ID"', producer)
        self.assertIn('workflow_dispatch:', release)
        self.assertIn('manual_run_id:', release)
        self.assertIn("github.event_name == 'workflow_dispatch'", release)
        self.assertIn('github.event.workflow_run.id || inputs.manual_run_id', release)

    def test_canonical_governance_copy(self):
        body=f"- Base SHA: {B}\n- review PR only; no auto-merge and no deploy command\n- publication follows only after explicit merge authorization and accepted merge to main\n"
        out=canonical_body(body,B,H); self.assertIn("Generation Base SHA",out); self.assertIn("Acceptance Base SHA",out)
        self.assertIn("gated automatic publication",out); self.assertIn("human-authored product PRs",out)
if __name__=="__main__": unittest.main()
