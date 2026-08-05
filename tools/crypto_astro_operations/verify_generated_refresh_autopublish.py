#!/usr/bin/env python3
"""Fail-closed gate and merge executor for scheduler-proven generated refresh PRs."""
from __future__ import annotations
import argparse, base64, io, json, os, re, urllib.request, urllib.error, zipfile
from pathlib import Path
from typing import Any

TITLE="Crypto-Astro: automated static market snapshot refresh"
PREFIX="automation/crypto-astro-static-refresh-"
AUTHOR="github-actions[bot]"
SCHEDULER_PATH=".github/workflows/crypto-astro-automatic-refresh.yml"
MANUAL_PATH=".github/workflows/crypto-astro-static-refresh-manual.yml"
REQUIRED_FILES={
'docs/crypto-astro-service/crypto_astro_operator_review.md','docs/crypto-astro-service/crypto_astro_snapshot_summary.md','site/crypto-astro/data/crypto_astro_module_bindings.public.json','site/crypto-astro/data/crypto_astro_snapshot.public.json','site/crypto-astro/data/crypto_astro_snapshot_delta.public.json','site/crypto-astro/data/crypto_astro_snapshot_proof.public.json','site/crypto-astro/data/crypto_astro_snapshot_registry.public.json','site/crypto-astro/data/market_field_snapshot.public.v0_1.json','site/crypto-astro/data/scoring_snapshot.public.json','site/crypto-astro/index.html'}
OPTIONAL_FILES={'site/crypto-astro/data/crypto_astro_module_bindings.public.schema.json'}
REQUIRED_WORKFLOWS={
'Crypto-Astro Refresh Current Surface Contract PR','Crypto-Astro Operational Cadence PR','Crypto-Astro Static Refresh PR Visual','Crypto-Astro Snapshot Memory PR','BTC Poster Motion Budget PR','Crypto-Astro LT-1 Import Normalization PR','Crypto-Astro Editorial Composition PR','Crypto-Astro CSS Extraction Parity PR','Crypto-Astro What Changed PR','Crypto-Astro Surface Truth PR','Φ-Validator CI','Crypto-Astro Geometry Truth PR','Crypto-Astro Assistant Dispatch PR','Crypto-Astro CSS Modules PR','Crypto-Astro BHRIGU Consumer Contract PR','Crypto-Astro Automatic Refresh Activation PR'}

class GateError(RuntimeError): pass
class Hold(RuntimeError): pass
class NotApplicable(RuntimeError): pass

class GitHub:
    def __init__(self,repo:str,token:str): self.repo=repo; self.token=token; self.base="https://api.github.com"
    def request(self,path:str,method:str="GET",data:Any=None,accept:str="application/vnd.github+json")->tuple[Any,dict]:
        body=None if data is None else json.dumps(data).encode(); req=urllib.request.Request(self.base+path,data=body,method=method,headers={"Authorization":f"Bearer {self.token}","Accept":accept,"X-GitHub-Api-Version":"2022-11-28","User-Agent":"crypto-astro-autopublish/1"})
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                raw=r.read(); return (json.loads(raw) if raw else {}),dict(r.headers)
        except urllib.error.HTTPError as e: raise GateError(f"GITHUB_API:{method}:{path}:{e.code}:{e.read().decode(errors='replace')}") from e
    def bytes(self,path:str)->bytes:
        req=urllib.request.Request(self.base+path,headers={"Authorization":f"Bearer {self.token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"crypto-astro-autopublish/1"})
        with urllib.request.urlopen(req,timeout=60) as r:return r.read()
    def graphql(self,query:str,variables:dict)->dict:
        value,_=self.request("/graphql","POST",{"query":query,"variables":variables});
        if value.get("errors"): raise GateError(f"GRAPHQL:{value['errors']}")
        return value["data"]

def parse_body(body:str)->tuple[int,str]:
    op=re.search(r"^- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_(\d+)\s*$",body or "",re.M)
    base=re.search(r"^- Base SHA: ([0-9a-f]{40})\s*$",body or "",re.M)
    issue=re.search(r"^- Assistant dispatch issue: none\s*$",body or "",re.M)
    if not op or not base or not issue: raise GateError("PR_BODY_PROVENANCE_INVALID")
    return int(op.group(1)),base.group(1)

def exact_scope(files:set[str])->bool:return files==REQUIRED_FILES or files==REQUIRED_FILES|OPTIONAL_FILES

def latest_runs_by_name(runs:list[dict])->dict[str,dict]:
    selected={}
    for run in runs:
        name=run.get("name");
        if name in REQUIRED_WORKFLOWS and (name not in selected or int(run.get("id",0))>int(selected[name].get("id",0))): selected[name]=run
    return selected

def write_output(path:str,key:str,value:str)->None:
    if path:
        with open(path,"a",encoding="utf-8") as f:f.write(f"{key}={value}\\n")

def run_gate(repo:str,token:str,trigger_run_id:int,report_path:Path,output_path:str)->int:
    gh=GitHub(repo,token); report={"schema_version":"crypto_astro_generated_refresh_autopublish_v0_1","status":"RUNNING","trigger_run_id":trigger_run_id,"merged":False}
    try:
        trigger,_=gh.request(f"/repos/{repo}/actions/runs/{trigger_run_id}")
        prs=trigger.get("pull_requests") or []
        if not prs:
            commit_prs,_=gh.request(f"/repos/{repo}/commits/{trigger['head_sha']}/pulls",accept="application/vnd.github+json")
            prs=[p for p in commit_prs if p.get("state")=="open"]
        if len(prs)!=1: raise NotApplicable("NO_SINGLE_OPEN_PR")
        pr_number=int(prs[0]["number"]); pr,_=gh.request(f"/repos/{repo}/pulls/{pr_number}")
        head_ref=pr["head"]["ref"]; partial=(head_ref.startswith(PREFIX) or pr.get("title")==TITLE)
        if not partial: raise NotApplicable("NON_GENERATED_PR")
        if pr.get("state")!="open" or pr.get("title")!=TITLE or not head_ref.startswith(PREFIX): raise GateError("GENERATED_PR_IDENTITY_AMBIGUOUS")
        if pr.get("user",{}).get("login")!=AUTHOR: raise GateError("GENERATED_PR_AUTHOR_INVALID")
        if pr.get("base",{}).get("ref")!="main": raise GateError("GENERATED_PR_BASE_INVALID")
        head_sha=pr["head"]["sha"]; manual_id_text=head_ref[len(PREFIX):]
        if not manual_id_text.isdigit(): raise GateError("MANUAL_RUN_ID_NOT_NUMERIC")
        manual_id=int(manual_id_text); scheduler_id,base_sha=parse_body(pr.get("body") or "")
        if pr["base"]["sha"]!=base_sha: raise GateError("PR_BASE_SHA_BODY_MISMATCH")
        manual,_=gh.request(f"/repos/{repo}/actions/runs/{manual_id}")
        if manual.get("path")!=MANUAL_PATH or manual.get("event")!="workflow_dispatch" or manual.get("head_sha")!=base_sha or manual.get("conclusion")!="success": raise GateError("MANUAL_RUN_PROVENANCE_INVALID")
        if manual.get("actor",{}).get("login")!="github-actions[bot]": raise GateError("MANUAL_RUN_ACTOR_INVALID")
        scheduler,_=gh.request(f"/repos/{repo}/actions/runs/{scheduler_id}")
        if scheduler.get("path")!=SCHEDULER_PATH or scheduler.get("event") not in {"schedule","workflow_dispatch"} or scheduler.get("head_sha")!=base_sha or scheduler.get("conclusion")!="success": raise GateError("SCHEDULER_RUN_PROVENANCE_INVALID")
        artifacts,_=gh.request(f"/repos/{repo}/actions/runs/{scheduler_id}/artifacts?per_page=100")
        matches=[a for a in artifacts.get("artifacts",[]) if a.get("name")==f"crypto-astro-automatic-refresh-{scheduler_id}" and not a.get("expired")]
        if len(matches)!=1: raise GateError("SCHEDULER_ARTIFACT_IDENTITY_INVALID")
        archive=gh.bytes(f"/repos/{repo}/actions/artifacts/{matches[0]['id']}/zip")
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            names=[n for n in z.namelist() if n.endswith("crypto-astro-automatic-refresh-decision.json")]
            if len(names)!=1: raise GateError("DECISION_REPORT_MISSING")
            decision=json.loads(z.read(names[0]))
        selected=((decision.get("manual_workflow_run") or {}).get("databaseId"))
        if decision.get("decision")!="MANUAL_REFRESH_DISPATCHED" or decision.get("scheduler_run_id")!=str(scheduler_id) or decision.get("main_sha")!=base_sha or decision.get("remote_main_sha")!=base_sha or int(selected or 0)!=manual_id: raise GateError("SCHEDULER_ARTIFACT_PROVENANCE_INVALID")
        files=[]; page=1
        while True:
            batch,_=gh.request(f"/repos/{repo}/pulls/{pr_number}/files?per_page=100&page={page}"); files.extend(x["filename"] for x in batch)
            if len(batch)<100:break
            page+=1
        if not exact_scope(set(files)): raise GateError(f"EXACT_REFRESH_SCOPE_INVALID:{sorted(files)}")
        runs,_=gh.request(f"/repos/{repo}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100")
        selected_runs=latest_runs_by_name(runs.get("workflow_runs",[])); missing=sorted(REQUIRED_WORKFLOWS-set(selected_runs))
        if missing: raise Hold(f"WAITING_REQUIRED_WORKFLOWS:{missing}")
        pending=sorted(n for n,r in selected_runs.items() if r.get("status")!="completed")
        if pending: raise Hold(f"WAITING_REQUIRED_WORKFLOWS:{pending}")
        failed={n:r.get("conclusion") for n,r in selected_runs.items() if r.get("conclusion")!="success"}
        if failed: raise GateError(f"REQUIRED_CI_NOT_SUCCESS:{failed}")
        owner,name=repo.split("/",1)
        q="query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100){nodes{isResolved}pageInfo{hasNextPage}}}}}"
        threads=gh.graphql(q,{"owner":owner,"name":name,"number":pr_number})["repository"]["pullRequest"]["reviewThreads"]
        if threads["pageInfo"]["hasNextPage"]: raise GateError("REVIEW_THREAD_PAGINATION_AMBIGUOUS")
        unresolved=sum(1 for x in threads["nodes"] if not x["isResolved"])
        if unresolved: raise GateError(f"UNRESOLVED_REVIEW_THREADS:{unresolved}")
        ref,_=gh.request(f"/repos/{repo}/git/ref/heads/main"); current_main=ref["object"]["sha"]
        if current_main!=base_sha: raise GateError(f"MAIN_DRIFT:{current_main}:{base_sha}")
        latest_pr,_=gh.request(f"/repos/{repo}/pulls/{pr_number}")
        if latest_pr["head"]["sha"]!=head_sha: raise GateError("EXPECTED_HEAD_DRIFT")
        print("GENERATED_PR_IDENTITY=PASS"); print("EXACT_REFRESH_SCOPE=PASS"); print("CI_MATRIX=PASS"); print("EXPECTED_HEAD_PROTECTION=PASS")
        merge,_=gh.request(f"/repos/{repo}/pulls/{pr_number}/merge","PUT",{"sha":head_sha,"merge_method":"squash","commit_title":f"{TITLE} (#{pr_number})"})
        if not merge.get("merged") or not re.fullmatch(r"[0-9a-f]{40}",str(merge.get("sha",""))): raise GateError(f"MERGE_FAILED:{merge}")
        merge_sha=merge["sha"]
        content,_=gh.request(f"/repos/{repo}/contents/site/crypto-astro/data/crypto_astro_snapshot.public.json?ref={head_sha}")
        snapshot=json.loads(base64.b64decode(content["content"]))
        report.update({"status":"PASS_MERGED","merged":True,"pr_number":pr_number,"head_sha":head_sha,"base_sha":base_sha,"merge_sha":merge_sha,"scheduler_run_id":scheduler_id,"manual_run_id":manual_id,"snapshot_timestamp":snapshot["generated_at_utc"],"required_ci":{k:v["id"] for k,v in selected_runs.items()},"unresolved_review_threads":0,"files":sorted(files)})
        write_output(output_path,"merged","true"); write_output(output_path,"merge_sha",merge_sha); write_output(output_path,"pr_number",str(pr_number)); write_output(output_path,"snapshot_timestamp",snapshot["generated_at_utc"])
        print("GATED_AUTOMATIC_MERGE=PASS")
        return 0
    except NotApplicable as e:
        report.update({"status":"NOT_APPLICABLE","reason":str(e)}); write_output(output_path,"merged","false"); return 0
    except Hold as e:
        report.update({"status":"HOLD","reason":str(e)}); write_output(output_path,"merged","false"); return 0
    except Exception as e:
        report.update({"status":"FAIL_CLOSED","reason":str(e)}); write_output(output_path,"merged","false"); return 1
    finally:
        report_path.parent.mkdir(parents=True,exist_ok=True); report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\\n")

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--repo",required=True);p.add_argument("--token",required=True);p.add_argument("--trigger-run-id",type=int,required=True);p.add_argument("--report",type=Path,required=True);p.add_argument("--github-output",default="");a=p.parse_args();return run_gate(a.repo,a.token,a.trigger_run_id,a.report,a.github_output)
if __name__=="__main__":raise SystemExit(main())
