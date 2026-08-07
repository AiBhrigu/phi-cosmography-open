#!/usr/bin/env python3
"""Trusted default-branch control plane for scheduler-generated refresh PR CI release."""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
from typing import Any

from tools.crypto_astro_operations.verify_generated_refresh_autopublish import (
    AUTHOR, MANUAL_PATH, PREFIX, REQUIRED_FILES, OPTIONAL_FILES, REQUIRED_WORKFLOWS,
    SCHEDULER_PATH, TITLE, GateError, GitHub, _artifact, exact_scope, parse_decision_report,
)

RECOVERY_TITLE = "Crypto-Astro generated refresh CI release request"
RECOVERY_SCHEMA = "crypto_astro_generated_refresh_ci_release_request_v0_1"
TOPOLOGY_FILES = {
    '.github/workflows/crypto-astro-assistant-dispatch-pr.yml',
    '.github/workflows/crypto-astro-automatic-refresh-pr.yml',
    '.github/workflows/crypto-astro-generated-refresh-autopublish.yml',
    '.github/workflows/crypto-astro-generated-refresh-ci-release.yml',
    '.github/workflows/crypto-astro-operational-cadence-pr.yml',
    '.github/workflows/crypto-astro-snapshot-memory-pr.yml',
    '.github/workflows/crypto-astro-static-refresh-manual.yml',
    'tools/crypto_astro_operations/test_verify_generated_refresh_autopublish.py',
    'tools/crypto_astro_operations/test_verify_generated_refresh_ci_release.py',
    'tools/crypto_astro_operations/test_verify_operational_cadence.py',
    'tools/crypto_astro_operations/verify_generated_refresh_autopublish.py',
    'tools/crypto_astro_operations/verify_generated_refresh_ci_release.py',
    'tools/crypto_astro_operations/verify_operational_cadence.py',
}
WRITE_TOKEN = re.compile(r"^\s*(contents|actions|pull-requests|issues|checks|deployments|packages|statuses|id-token):\s*write\s*$", re.M)

def fail(msg: str): raise GateError(msg)

def parse_body(body: str) -> tuple[int, str, str]:
    op = re.search(r"^- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_(\d+)\s*$", body or "", re.M)
    gen = re.search(r"^- Generation Base SHA: ([0-9a-f]{40})\s*$", body or "", re.M)
    legacy = re.search(r"^- Base SHA: ([0-9a-f]{40})\s*$", body or "", re.M)
    acc = re.search(r"^- Acceptance Base SHA: ([0-9a-f]{40})\s*$", body or "", re.M)
    if not op or not (gen or legacy): fail("PR_BODY_PROVENANCE_INVALID")
    generation = (gen or legacy).group(1)
    acceptance = acc.group(1) if acc else generation
    return int(op.group(1)), generation, acceptance

def parse_recovery_issue(body: str) -> tuple[int, str, str]:
    fields = {}
    for raw in (body or "").splitlines():
        if "=" in raw:
            k, v = raw.split("=", 1); fields[k.strip()] = v.strip()
    if fields.get("SCHEMA") != RECOVERY_SCHEMA: fail("RECOVERY_SCHEMA_INVALID")
    try: pr = int(fields["PR"])
    except Exception as e: raise GateError("RECOVERY_PR_INVALID") from e
    head = fields.get("EXPECTED_HEAD_SHA", "")
    base = fields.get("EXPECTED_GENERATION_BASE_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", head): fail("RECOVERY_HEAD_INVALID")
    if not re.fullmatch(r"[0-9a-f]{40}", base): fail("RECOVERY_GENERATION_BASE_INVALID")
    return pr, head, base

def validate_pr_identity(pr: dict[str, Any], repo: str, expected_head: str | None = None) -> tuple[int, str, str]:
    if pr.get("state") != "open": fail("PR_NOT_OPEN")
    if pr.get("title") != TITLE: fail("WRONG_TITLE")
    if pr.get("user", {}).get("login") != AUTHOR: fail("WRONG_AUTHOR")
    if pr.get("base", {}).get("ref") != "main": fail("WRONG_BASE")
    if pr.get("head", {}).get("repo", {}).get("full_name") != repo: fail("FORK_PR_REJECTED")
    head_ref = pr.get("head", {}).get("ref", "")
    if not head_ref.startswith(PREFIX): fail("WRONG_HEAD_PREFIX")
    head_sha = pr.get("head", {}).get("sha", "")
    if expected_head and head_sha != expected_head: fail("HEAD_DRIFT")
    suffix = head_ref[len(PREFIX):]
    if not suffix.isdigit(): fail("MANUAL_RUN_PROVENANCE_INVALID")
    return int(suffix), head_ref, head_sha

def validate_scope(files: set[str]) -> None:
    if not exact_scope(files): fail("WRONG_GENERATED_SCOPE")

def validate_control_workflow(text: str) -> None:
    if "secrets." in text or "${{ secrets" in text: fail("SECRET_EXPOSURE_TO_UNTRUSTED_HEAD")
    if WRITE_TOKEN.search(text): fail("PR_GATE_WRITE_PERMISSION_FORBIDDEN")

def canonical_body(body: str, generation: str, acceptance: str) -> str:
    text = body
    if re.search(r"^- Generation Base SHA:", text, re.M):
        text = re.sub(r"^- Generation Base SHA: [0-9a-f]{40}\s*$", f"- Generation Base SHA: {generation}", text, flags=re.M)
    else:
        text = re.sub(r"^- Base SHA: [0-9a-f]{40}\s*$", f"- Generation Base SHA: {generation}", text, flags=re.M)
    if re.search(r"^- Acceptance Base SHA:", text, re.M):
        text = re.sub(r"^- Acceptance Base SHA: [0-9a-f]{40}\s*$", f"- Acceptance Base SHA: {acceptance}", text, flags=re.M)
    else:
        anchor = f"- Generation Base SHA: {generation}"
        text = text.replace(anchor, anchor + f"\n- Acceptance Base SHA: {acceptance}", 1)
    text = text.replace(
        "- review PR only; no auto-merge and no deploy command",
        "- scheduler-proven generated refresh is eligible for gated automatic publication only after all required gates PASS",
    )
    text = text.replace(
        "- publication follows only after explicit merge authorization and accepted merge to main",
        "- human-authored product PRs are never eligible for generated-refresh automatic merge",
    )
    return text

def compare_topology_only(gh: GitHub, repo: str, generation: str, current_main: str) -> set[str]:
    if generation == current_main: return set()
    value, _ = gh.request(f"/repos/{repo}/compare/{generation}...{current_main}")
    files = {x["filename"] for x in value.get("files", [])}
    if not files or not files <= TOPOLOGY_FILES: fail(f"MAIN_DRIFT:{sorted(files)}")
    return files

def list_pr_files(gh: GitHub, repo: str, pr_number: int) -> set[str]:
    files=set(); page=1
    while True:
        batch,_=gh.request(f"/repos/{repo}/pulls/{pr_number}/files?per_page=100&page={page}")
        files.update(x["filename"] for x in batch)
        if len(batch)<100: return files
        page+=1

def validate_provenance(gh: GitHub, repo: str, pr: dict[str, Any], manual_id: int, generation: str, scheduler_id: int) -> None:
    manual,_=gh.request(f"/repos/{repo}/actions/runs/{manual_id}")
    if manual.get("path")!=MANUAL_PATH or manual.get("event")!="workflow_dispatch" or manual.get("head_sha")!=generation or manual.get("conclusion")!="success":
        fail("MANUAL_RUN_PROVENANCE_INVALID")
    if manual.get("actor",{}).get("login")!="github-actions[bot]": fail("MANUAL_RUN_ACTOR_INVALID")
    scheduler,_=gh.request(f"/repos/{repo}/actions/runs/{scheduler_id}")
    if scheduler.get("path")!=SCHEDULER_PATH or scheduler.get("event") not in {"schedule","workflow_dispatch"} or scheduler.get("head_sha")!=generation or scheduler.get("conclusion")!="success":
        fail("SCHEDULER_RUN_PROVENANCE_INVALID")
    _,data,_=_artifact(gh,repo,scheduler_id); decision=parse_decision_report(data)
    selected=(decision.get("manual_workflow_run") or {}).get("databaseId")
    if decision.get("decision")!="MANUAL_REFRESH_DISPATCHED" or decision.get("scheduler_run_id")!=str(scheduler_id) or decision.get("main_sha")!=generation or decision.get("remote_main_sha")!=generation or int(selected or 0)!=manual_id:
        fail("SCHEDULER_ARTIFACT_PROVENANCE_INVALID")

def current_main_sha(gh: GitHub, repo: str) -> str:
    ref,_=gh.request(f"/repos/{repo}/git/ref/heads/main")
    return ref["object"]["sha"]

def required_runs(gh: GitHub, repo: str, head_sha: str, allow_missing: bool=False) -> dict[str, dict[str,Any]]:
    value,_=gh.request(f"/repos/{repo}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100")
    out={}
    for run in value.get("workflow_runs",[]):
        name=run.get("name")
        if name in REQUIRED_WORKFLOWS and (name not in out or int(run["id"])>int(out[name]["id"])): out[name]=run
    missing=REQUIRED_WORKFLOWS-set(out)
    if missing and not allow_missing: fail(f"MISSING_REQUIRED_WORKFLOWS:{sorted(missing)}")
    return out

def wait_required_runs(gh: GitHub, repo: str, head_sha: str, timeout: int=120) -> dict[str,dict[str,Any]]:
    deadline=time.time()+timeout
    while time.time()<deadline:
        out=required_runs(gh,repo,head_sha,allow_missing=True)
        if set(out)==REQUIRED_WORKFLOWS: return out
        time.sleep(4)
    fail("MISSING_REQUIRED_WORKFLOWS_TIMEOUT")

def approve_and_wait(gh: GitHub, repo: str, head_sha: str, runs: dict[str,dict[str,Any]], timeout: int=1800) -> dict[str,int]:
    approved=already=0
    for name,run in runs.items():
        concl=run.get("conclusion")
        if concl=="success": already+=1; continue
        if concl!="action_required": fail(f"REQUIRED_RUN_UNEXPECTED_STATE:{name}:{concl}")
        jobs,_=gh.request(f"/repos/{repo}/actions/runs/{run['id']}/jobs?per_page=100")
        if jobs.get("total_count",len(jobs.get("jobs",[]))) != 0 or jobs.get("jobs"): fail(f"PRE_APPROVAL_JOB_EXECUTION:{name}")
        workflow,_=gh.request(f"/repos/{repo}/contents/{run['path']}?ref={current_main_sha(gh,repo)}")
        import base64
        validate_control_workflow(base64.b64decode(workflow["content"]).decode())
        gh.request(f"/repos/{repo}/actions/runs/{run['id']}/approve","POST")
        approved+=1
    deadline=time.time()+timeout
    while time.time()<deadline:
        current=required_runs(gh,repo,head_sha)
        if all(r.get("status")=="completed" for r in current.values()):
            bad={n:r.get("conclusion") for n,r in current.items() if r.get("conclusion")!="success"}
            if bad: fail(f"REQUIRED_CI_NOT_SUCCESS:{bad}")
            return {"approved":approved,"already_success":already,"success":len(current)}
        time.sleep(8)
    fail("REQUIRED_CI_TIMEOUT")

def run(repo:str,token:str,manual_run_id:int|None,issue_number:int|None,report_path:Path)->int:
    gh=GitHub(repo,token); report={"schema_version":"crypto_astro_generated_refresh_ci_release_v0_1","status":"RUNNING"}
    issue=None
    try:
        expected_head=None; expected_generation=None; pr_number=None
        if issue_number:
            issue,_=gh.request(f"/repos/{repo}/issues/{issue_number}")
            owner=repo.split("/",1)[0]
            if issue.get("title")!=RECOVERY_TITLE or issue.get("user",{}).get("login")!=owner: fail("RECOVERY_ISSUE_NOT_OWNER_AUTHENTICATED")
            pr_number,expected_head,expected_generation=parse_recovery_issue(issue.get("body",""))
        elif manual_run_id:
            manual,_=gh.request(f"/repos/{repo}/actions/runs/{manual_run_id}")
            if manual.get("path")!=MANUAL_PATH or manual.get("conclusion")!="success": fail("MANUAL_TRIGGER_INVALID")
            head_ref=PREFIX+str(manual_run_id)
            prs,_=gh.request(f"/repos/{repo}/pulls?state=open&base=main&head={repo.split('/')[0]}:{head_ref}&per_page=10")
            if len(prs)!=1: fail("GENERATED_PR_NOT_UNIQUE")
            pr_number=int(prs[0]["number"])
        else: fail("TRIGGER_REQUIRED")
        pr,_=gh.request(f"/repos/{repo}/pulls/{pr_number}")
        manual_id,_,head_sha=validate_pr_identity(pr,repo,expected_head)
        scheduler_id,generation,acceptance=parse_body(pr.get("body",""))
        if expected_generation and generation!=expected_generation: fail("GENERATION_BASE_DRIFT")
        validate_scope(list_pr_files(gh,repo,pr_number))
        validate_provenance(gh,repo,pr,manual_id,generation,scheduler_id)
        main=current_main_sha(gh,repo)
        drift=compare_topology_only(gh,repo,generation,main)
        if issue_number:
            new_body=canonical_body(pr.get("body",""),generation,main)
            if new_body!=pr.get("body",""):
                gh.request(f"/repos/{repo}/pulls/{pr_number}","PATCH",{"body":new_body})
            acceptance=main
        elif main!=generation: fail("MAIN_DRIFT")
        pr2,_=gh.request(f"/repos/{repo}/pulls/{pr_number}")
        _,_,head_after=validate_pr_identity(pr2,repo,head_sha)
        _,generation_after,acceptance_after=parse_body(pr2.get("body",""))
        if generation_after!=generation or acceptance_after!=acceptance or pr2.get("base",{}).get("sha")!=acceptance: fail("BASE_DRIFT")
        runs=wait_required_runs(gh,repo,head_sha)
        result=approve_and_wait(gh,repo,head_sha,runs)
        report.update({"status":"PASS","pr":pr_number,"head_sha":head_sha,"generation_base_sha":generation,
                       "acceptance_base_sha":acceptance,"topology_drift_files":sorted(drift),"required_ci":result,
                       "untrusted_code_before_identity_gate":0,"secret_exposure_to_untrusted_head":0})
        return 0
    except Exception as e:
        report.update({"status":"FAIL_CLOSED","reason":str(e)})
        return 1
    finally:
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",required=True);p.add_argument("--token",required=True)
    p.add_argument("--manual-run-id",type=int);p.add_argument("--issue-number",type=int);p.add_argument("--report",required=True)
    a=p.parse_args(); raise SystemExit(run(a.repo,a.token,a.manual_run_id,a.issue_number,Path(a.report)))
if __name__=="__main__": main()
