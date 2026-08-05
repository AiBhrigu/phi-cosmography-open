#!/usr/bin/env python3
"""Fail-closed verifier for automatic Snapshot cadence and gated publication."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "crypto_astro_automatic_refresh_activation_v0_1"
ACTIVATION_ID = "BTC_MARKET_SNAPSHOT_AUTOMATIC_CADENCE_SELF_DIRTY_PROBE_GATED_PUBLICATION_AND_CURRENT_FRESHNESS_RESTORE_v0_1"
SCHEDULER = ".github/workflows/crypto-astro-automatic-refresh.yml"
VALIDATOR = ".github/workflows/crypto-astro-automatic-refresh-pr.yml"
PUBLISHER = ".github/workflows/crypto-astro-generated-refresh-autopublish.yml"
MANUAL_WORKFLOW = "crypto-astro-static-refresh-manual.yml"
CRON = "17 * * * *"


def require(condition: bool, code: str, failures: list[str]) -> None:
    if not condition: failures.append(code)

def load_json(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise RuntimeError(f"{path}: expected object")
    return value

def evaluate_decision(policy: dict[str,Any], *, snapshot_age_hours: float, exact_main_match: bool=True, open_refresh_pr_count:int=0, active_manual_run_count:int=0, source_probe:str="PASS", material_change:bool|None=True)->str:
    f=policy["freshness_contract"]
    if snapshot_age_hours < 0: return "BLOCK_FUTURE_SNAPSHOT"
    if snapshot_age_hours < f["daily_minimum_interval_hours"]: return "HOLD_MINIMUM_INTERVAL"
    if snapshot_age_hours < f["automatic_eligibility_age_hours"]: return "HOLD_BEFORE_AUTOMATIC_WINDOW"
    if not exact_main_match: return "BLOCK_MAIN_DRIFT"
    if open_refresh_pr_count: return "BLOCK_OPEN_REFRESH_PR"
    if active_manual_run_count: return "BLOCK_SINGLE_FLIGHT"
    if source_probe != "PASS": return "SOURCE_FAILURE_RECHECK"
    if material_change is False: return "NO_MATERIAL_CHANGE_RECHECK"
    if material_change is not True: return "BLOCK_MATERIAL_CHANGE_UNKNOWN"
    return "DISPATCH_MANUAL_REFRESH"

def verify_policy(policy:dict[str,Any])->list[str]:
    failures=[]
    require(policy.get("schema_version")==SCHEMA_VERSION,"policy:schema",failures)
    require(policy.get("activation_id")==ACTIVATION_ID,"policy:activation",failures)
    require(policy.get("status")=="ACTIVE_GATED_PUBLICATION","policy:status",failures)
    require(policy.get("scheduler_workflow")==SCHEDULER,"policy:scheduler",failures)
    require(policy.get("validation_workflow")==VALIDATOR,"policy:validator",failures)
    require(policy.get("publication_workflow")==PUBLISHER,"policy:publisher",failures)
    schedule=policy.get("schedule",{})
    require(schedule.get("cron")==CRON,"policy:cron",failures)
    require(schedule.get("check_interval_minutes")==60,"policy:hourly",failures)
    source=policy.get("source_truth",{})
    require(source.get("approved_source_identity_count")==7,"policy:sources",failures)
    require(source.get("clean_repository_gate_preserved") is True,"policy:clean_gate",failures)
    diagnostics=policy.get("diagnostics",{})
    require(diagnostics.get("location")=="runner.temp","policy:diagnostics_location",failures)
    require(diagnostics.get("source_checkout_must_remain_clean_before_probe") is True,"policy:clean_before_probe",failures)
    dispatch=policy.get("dispatch",{})
    require(dispatch.get("target_workflow")==MANUAL_WORKFLOW,"policy:manual_workflow",failures)
    require(dispatch.get("scheduler_run_provenance_required") is True,"policy:provenance",failures)
    pub=policy.get("publication",{})
    for key in ("automatic_merge","generated_refresh_only","exact_generated_file_scope","all_required_ci_success","unresolved_review_threads_zero","expected_head_sha_protection","candidate_base_equals_current_main","scheduler_artifact_provenance","fail_closed_on_ambiguity","pages_workflow_dispatch_after_merge","public_http_proof_after_pages"):
        require(pub.get(key) is True,f"policy:publication:{key}",failures)
    require(pub.get("required_ci_workflow_count")==16,"policy:ci_count",failures)
    for key in ("human_authored_product_prs","methodology_changes","source_provider_changes","new_assets","routing_or_question_corpus_changes","visual_redesign","payment_accounts_backend_orion_changes"):
        require(pub.get(key) is False,f"policy:publication_boundary:{key}",failures)
    boundary=policy.get("boundary",{})
    require(boundary and all(value is False for value in boundary.values()),"policy:boundary",failures)
    return failures

def verify_scheduler(text:str)->list[str]:
    failures=[]
    required=("name: Crypto-Astro Automatic Snapshot Refresh","cron: '17 * * * *'","workflow_dispatch:","contents: read","pull-requests: read","actions: write","RUNNER_TEMP","GITHUB_ENV","DIAGNOSTICS_LOCATION=RUNNER_TEMP","CLEAN_WORKSPACE_BEFORE_PROBE=PASS","git status --porcelain","crypto_astro_static_refresh_bhrigu_compat_v0_1.py","CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_","gh workflow run crypto-astro-static-refresh-manual.yml","actions/upload-artifact@v4")
    for marker in required: require(marker in text,f"scheduler:missing:{marker}",failures)
    require("artifacts/crypto-astro-automatic-refresh-decision.json" not in text,"scheduler:tracked_decision_path",failures)
    require("--report artifacts/automatic-refresh-activation-verification.json" not in text,"scheduler:tracked_activation_report",failures)
    require("${{ runner.temp }}" not in text,"scheduler:invalid_job_level_runner_context",failures)
    triggers={m.group(1) for m in re.finditer(r"^  (schedule|workflow_dispatch|push|pull_request):\s*$",text,re.M)}
    require(triggers=={"schedule","workflow_dispatch"},f"scheduler:triggers:{sorted(triggers)}",failures)
    for name,pattern in {"contents_write":r"^\s*contents:\s*write\s*$","git_push":r"\bgit\s+push\b","merge":r"\bgh\s+pr\s+merge\b|/merge['\"]","deploy":r"deploy-pages|gh workflow run pages.yml","direct_pr":r"gh\s+pr\s+create"}.items():
        require(re.search(pattern,text,re.M|re.I) is None,f"scheduler:forbidden:{name}",failures)
    return failures

def verify_publisher(text:str)->list[str]:
    failures=[]
    required=("name: Crypto-Astro Generated Refresh Gated Publication","workflow_run:","contents: write","pull-requests: write","actions: write","verify_generated_refresh_autopublish.py","EXPECTED_HEAD_PROTECTION=PASS","GATED_AUTOMATIC_MERGE=PASS","gh workflow run pages.yml","verify_public_http_proof.py","if: steps.gate.outputs.merged == 'true'")
    for marker in required: require(marker in text,f"publisher:missing:{marker}",failures)
    require("pull_request_target:" not in text,"publisher:forbidden_pull_request_target",failures)
    require("schedule:" not in text,"publisher:forbidden_schedule",failures)
    return failures

def verify_repository(repo:Path)->dict[str,Any]:
    policy=load_json(repo/"docs/crypto-astro-service/crypto_astro_automatic_refresh_activation_v0_1.json")
    checks={"policy":verify_policy(policy),"scheduler":verify_scheduler((repo/SCHEDULER).read_text()),"publisher":verify_publisher((repo/PUBLISHER).read_text())}
    matrix={"17h":evaluate_decision(policy,snapshot_age_hours=17),"19h":evaluate_decision(policy,snapshot_age_hours=19),"20h":evaluate_decision(policy,snapshot_age_hours=20),"main_drift":evaluate_decision(policy,snapshot_age_hours=22,exact_main_match=False),"open_pr":evaluate_decision(policy,snapshot_age_hours=22,open_refresh_pr_count=1),"single_flight":evaluate_decision(policy,snapshot_age_hours=22,active_manual_run_count=1),"source_failure":evaluate_decision(policy,snapshot_age_hours=22,source_probe="FAIL"),"no_material_change":evaluate_decision(policy,snapshot_age_hours=22,material_change=False),"future":evaluate_decision(policy,snapshot_age_hours=-0.1)}
    expected={"17h":"HOLD_MINIMUM_INTERVAL","19h":"HOLD_BEFORE_AUTOMATIC_WINDOW","20h":"DISPATCH_MANUAL_REFRESH","main_drift":"BLOCK_MAIN_DRIFT","open_pr":"BLOCK_OPEN_REFRESH_PR","single_flight":"BLOCK_SINGLE_FLIGHT","source_failure":"SOURCE_FAILURE_RECHECK","no_material_change":"NO_MATERIAL_CHANGE_RECHECK","future":"BLOCK_FUTURE_SNAPSHOT"}
    checks["decision_matrix"]=[f"matrix:{k}:{matrix.get(k)}" for k,v in expected.items() if matrix.get(k)!=v]
    failures=[f"{section}:{item}" for section,items in checks.items() for item in items]
    return {"schema_version":"crypto_astro_automatic_refresh_activation_verification_v0_2","status":"PASS" if not failures else "FAIL","checks":{k:"PASS" if not v else "FAIL" for k,v in checks.items()},"decision_matrix":matrix,"failures":failures}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--repo",default="."); p.add_argument("--report"); a=p.parse_args(); repo=Path(a.repo).resolve(); report=verify_repository(repo); rendered=json.dumps(report,indent=2,sort_keys=True)+"\\n"; print(rendered,end="")
    if a.report:
        target=Path(a.report).resolve(); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(rendered)
    return 0 if report["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
