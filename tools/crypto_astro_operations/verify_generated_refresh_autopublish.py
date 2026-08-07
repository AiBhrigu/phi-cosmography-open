#!/usr/bin/env python3
"""Fail-closed gate and merge executor for scheduler-proven generated refresh PRs."""
from __future__ import annotations
import argparse,base64,hashlib,hmac,io,json,re,urllib.error,urllib.parse,urllib.request,zipfile
from pathlib import Path
from typing import Any

TITLE="Crypto-Astro: automated static market snapshot refresh"; PREFIX="automation/crypto-astro-static-refresh-"; AUTHOR="github-actions[bot]"
SCHEDULER_PATH=".github/workflows/crypto-astro-automatic-refresh.yml"; MANUAL_PATH=".github/workflows/crypto-astro-static-refresh-manual.yml"
MAX_ARCHIVE_BYTES=16*1024*1024; MAX_ZIP_UNCOMPRESSED_BYTES=64*1024*1024; REDIRECT_STATUSES={301,302,303,307,308}
REQUIRED_FILES={'docs/crypto-astro-service/crypto_astro_operator_review.md','docs/crypto-astro-service/crypto_astro_snapshot_summary.md','site/crypto-astro/data/crypto_astro_module_bindings.public.json','site/crypto-astro/data/crypto_astro_snapshot.public.json','site/crypto-astro/data/crypto_astro_snapshot_delta.public.json','site/crypto-astro/data/crypto_astro_snapshot_proof.public.json','site/crypto-astro/data/crypto_astro_snapshot_registry.public.json','site/crypto-astro/data/market_field_snapshot.public.v0_1.json','site/crypto-astro/data/scoring_snapshot.public.json','site/crypto-astro/index.html'}
OPTIONAL_FILES={'site/crypto-astro/data/crypto_astro_module_bindings.public.schema.json'}
REQUIRED_WORKFLOWS={'Crypto-Astro Refresh Current Surface Contract PR','Crypto-Astro Operational Cadence PR','Crypto-Astro Static Refresh PR Visual','Crypto-Astro Snapshot Memory PR','BTC Poster Motion Budget PR','Crypto-Astro LT-1 Import Normalization PR','Crypto-Astro Editorial Composition PR','Crypto-Astro CSS Extraction Parity PR','Crypto-Astro What Changed PR','Crypto-Astro Surface Truth PR','Φ-Validator CI','Crypto-Astro Geometry Truth PR','Crypto-Astro Assistant Dispatch PR','Crypto-Astro CSS Modules PR','Crypto-Astro BHRIGU Consumer Contract PR','Crypto-Astro Automatic Refresh Activation PR'}
class GateError(RuntimeError):pass
class Hold(RuntimeError):pass
class NotApplicable(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def _status(r):return int(getattr(r,"status",None) or r.getcode())
def _headers(headers,name):
 if hasattr(headers,"get_all"):return [str(x) for x in (headers.get_all(name) or [])]
 value=headers.get(name) if hasattr(headers,"get") else None
 return [] if value is None else [str(x) for x in value] if isinstance(value,(list,tuple)) else [str(value)]
def _validate_url(url,api_only=False):
 try:p=urllib.parse.urlsplit(url); host=p.hostname; user=p.username; password=p.password
 except ValueError as e:raise GateError("ARTIFACT_URL_INVALID") from e
 if p.scheme.lower()!="https":raise GateError("ARTIFACT_URL_HTTPS_REQUIRED")
 if not host:raise GateError("ARTIFACT_URL_HOST_REQUIRED")
 if user is not None or password is not None:raise GateError("ARTIFACT_URL_CREDENTIALS_FORBIDDEN")
 if p.fragment:raise GateError("ARTIFACT_URL_FRAGMENT_FORBIDDEN")
 if api_only and host.lower()!="api.github.com":raise GateError("ARTIFACT_API_HOST_INVALID")
def _validate_zip(data):
 try:
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   if sum(x.file_size for x in z.infolist())>MAX_ZIP_UNCOMPRESSED_BYTES:raise GateError("ARTIFACT_ZIP_UNCOMPRESSED_SIZE_EXCEEDED")
   if z.testzip() is not None:raise GateError("ARTIFACT_ZIP_INTEGRITY_INVALID")
 except GateError:raise
 except (zipfile.BadZipFile,OSError,RuntimeError) as e:raise GateError("ARTIFACT_ZIP_MALFORMED") from e
def parse_decision_report(data):
 try:
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   names=[n for n in z.namelist() if n.endswith("crypto-astro-automatic-refresh-decision.json")]
   if len(names)!=1:raise GateError("DECISION_REPORT_MISSING")
   value=json.loads(z.read(names[0]))
 except GateError:raise
 except (zipfile.BadZipFile,KeyError,UnicodeDecodeError,json.JSONDecodeError) as e:raise GateError("DECISION_REPORT_INVALID") from e
 if not isinstance(value,dict):raise GateError("DECISION_REPORT_INVALID")
 return value

class GitHub:
 def __init__(self,repo,token):self.repo=repo;self.token=token;self.base="https://api.github.com"
 def request(self,path,method="GET",data=None,accept="application/vnd.github+json"):
  body=None if data is None else json.dumps(data).encode();req=urllib.request.Request(self.base+path,data=body,method=method,headers={"Authorization":f"Bearer {self.token}","Accept":accept,"X-GitHub-Api-Version":"2022-11-28","User-Agent":"crypto-astro-autopublish/2"})
  try:
   with urllib.request.urlopen(req,timeout=45) as r:raw=r.read();return (json.loads(raw) if raw else {}),dict(r.headers)
  except urllib.error.HTTPError as e:raise GateError(f"GITHUB_API:{method}:{path}:{e.code}") from e
 def _open_no_redirect(self,request,timeout):
  try:return urllib.request.build_opener(NoRedirect()).open(request,timeout=timeout)
  except urllib.error.HTTPError as e:return e
 def artifact_archive(self,artifact):
  api_url=artifact.get("archive_download_url")
  if not isinstance(api_url,str) or not api_url:raise GateError("ARTIFACT_ARCHIVE_URL_MISSING")
  _validate_url(api_url,True);req=urllib.request.Request(api_url,headers={"Authorization":f"Bearer {self.token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"crypto-astro-autopublish/2"})
  try:r=self._open_no_redirect(req,45)
  except Exception as e:raise GateError("ARTIFACT_API_REQUEST_FAILED") from e
  try:
   if _status(r) not in REDIRECT_STATUSES:raise GateError(f"ARTIFACT_API_REDIRECT_REQUIRED:{_status(r)}")
   locations=_headers(r.headers,"Location")
   if len(locations)!=1 or not locations[0]:raise GateError("ARTIFACT_API_LOCATION_INVALID")
   signed_url=locations[0]
  finally:r.close()
  _validate_url(signed_url);req=urllib.request.Request(signed_url,headers={"Accept":"application/octet-stream","User-Agent":"crypto-astro-autopublish/2"})
  try:r=self._open_no_redirect(req,60)
  except Exception as e:raise GateError("ARTIFACT_ARCHIVE_REQUEST_FAILED") from e
  try:
   status=_status(r)
   if status in REDIRECT_STATUSES:raise GateError("ARTIFACT_ARCHIVE_ADDITIONAL_REDIRECT")
   if status!=200:raise GateError(f"ARTIFACT_ARCHIVE_HTTP_STATUS:{status}")
   lengths=_headers(r.headers,"Content-Length")
   if len(lengths)>1:raise GateError("ARTIFACT_ARCHIVE_CONTENT_LENGTH_INVALID")
   if lengths:
    try:length=int(lengths[0])
    except ValueError as e:raise GateError("ARTIFACT_ARCHIVE_CONTENT_LENGTH_INVALID") from e
    if length<0 or length>MAX_ARCHIVE_BYTES:raise GateError("ARTIFACT_ARCHIVE_SIZE_EXCEEDED")
   data=r.read(MAX_ARCHIVE_BYTES+1)
  finally:r.close()
  if len(data)>MAX_ARCHIVE_BYTES:raise GateError("ARTIFACT_ARCHIVE_SIZE_EXCEEDED")
  result="NOT_AVAILABLE";digest=artifact.get("digest")
  if isinstance(digest,str) and re.fullmatch(r"sha256:[0-9a-fA-F]{64}",digest):
   if not hmac.compare_digest(hashlib.sha256(data).hexdigest(),digest.split(":",1)[1].lower()):raise GateError("ARTIFACT_DIGEST_MISMATCH")
   result="PASS"
  _validate_zip(data);return data,result
 def graphql(self,query,variables):
  value,_=self.request("/graphql","POST",{"query":query,"variables":variables})
  if value.get("errors"):raise GateError("GRAPHQL_ERROR")
  return value["data"]

def parse_body(body):
 op=re.search(r"^- Operator reference: CRYPTO_ASTRO_AUTOMATIC_24H_REFRESH_RUN_(\d+)\s*$",body or "",re.M);generation=re.search(r"^- Generation Base SHA: ([0-9a-f]{40})\s*$",body or "",re.M) or re.search(r"^- Base SHA: ([0-9a-f]{40})\s*$",body or "",re.M);issue=re.search(r"^- Assistant dispatch issue: none\s*$",body or "",re.M)
 if not op or not generation or not issue:raise GateError("PR_BODY_PROVENANCE_INVALID")
 return int(op.group(1)),generation.group(1)
def exact_scope(files):return files==REQUIRED_FILES or files==REQUIRED_FILES|OPTIONAL_FILES
def latest_runs_by_name(runs):
 selected={}
 for run in runs:
  name=run.get("name")
  if name in REQUIRED_WORKFLOWS and (name not in selected or int(run.get("id",0))>int(selected[name].get("id",0))):selected[name]=run
 return selected
def write_output(path,key,value):
 if path:
  with open(path,"a",encoding="utf-8") as f:f.write(f"{key}={value}\n")
def _artifact(gh,repo,scheduler_id):
 artifacts,_=gh.request(f"/repos/{repo}/actions/runs/{scheduler_id}/artifacts?per_page=100");matches=[a for a in artifacts.get("artifacts",[]) if a.get("name")==f"crypto-astro-automatic-refresh-{scheduler_id}" and not a.get("expired")]
 if len(matches)!=1:raise GateError("SCHEDULER_ARTIFACT_IDENTITY_INVALID")
 print("ARTIFACT_METADATA=PASS");data,digest=gh.artifact_archive(matches[0]);print("AUTHENTICATED_API_REQUEST=PASS\nSIGNED_REDIRECT_REQUEST_WITHOUT_AUTH=PASS\nARCHIVE_DOWNLOAD=PASS");print(f"DIGEST_RESULT={digest}");print("ZIP_INTEGRITY=PASS");return matches[0],data,digest

def run_artifact_proof(repo,token,scheduler_id,report_path):
 gh=GitHub(repo,token);report={"schema_version":"crypto_astro_artifact_redirect_read_only_proof_v0_1","status":"RUNNING","scheduler_run_id":scheduler_id,"merge_attempts":0}
 try:
  scheduler,_=gh.request(f"/repos/{repo}/actions/runs/{scheduler_id}")
  if scheduler.get("path")!=SCHEDULER_PATH or scheduler.get("event") not in {"schedule","workflow_dispatch"} or scheduler.get("conclusion")!="success":raise GateError("SCHEDULER_RUN_PROVENANCE_INVALID")
  artifact,data,digest=_artifact(gh,repo,scheduler_id);decision=parse_decision_report(data);print("DECISION_REPORT_PARSE=PASS");manual=(decision.get("manual_workflow_run") or {}).get("databaseId")
  if decision.get("decision")!="MANUAL_REFRESH_DISPATCHED" or decision.get("scheduler_run_id")!=str(scheduler_id) or decision.get("main_sha")!=scheduler.get("head_sha") or decision.get("remote_main_sha")!=scheduler.get("head_sha") or int(manual or 0)<=0:raise GateError("SCHEDULER_ARTIFACT_PROVENANCE_INVALID")
  report.update({"status":"PASS","artifact_id":artifact.get("id"),"artifact_metadata":"PASS","authenticated_api_request":"PASS","signed_redirect_request_without_auth":"PASS","archive_download":"PASS","digest_result":digest,"zip_integrity":"PASS","decision_report_parse":"PASS","manual_run_id":int(manual),"merge_attempts":0});print("MERGE_ATTEMPT=ZERO");return 0
 except Exception as e:report.update({"status":"FAIL_CLOSED","reason":str(e),"merge_attempts":0});return 1
 finally:report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")

def run_gate(repo,token,trigger_run_id,report_path,output_path):
 gh=GitHub(repo,token);report={"schema_version":"crypto_astro_generated_refresh_autopublish_v0_1","status":"RUNNING","trigger_run_id":trigger_run_id,"merged":False}
 try:
  trigger,_=gh.request(f"/repos/{repo}/actions/runs/{trigger_run_id}");prs=trigger.get("pull_requests") or []
  if not prs:
   commit_prs,_=gh.request(f"/repos/{repo}/commits/{trigger['head_sha']}/pulls",accept="application/vnd.github+json");prs=[p for p in commit_prs if p.get("state")=="open"]
  if len(prs)!=1:raise NotApplicable("NO_SINGLE_OPEN_PR")
  pr_number=int(prs[0]["number"]);pr,_=gh.request(f"/repos/{repo}/pulls/{pr_number}");head_ref=pr["head"]["ref"]
  if not (head_ref.startswith(PREFIX) or pr.get("title")==TITLE):raise NotApplicable("NON_GENERATED_PR")
  if pr.get("state")!="open" or pr.get("title")!=TITLE or not head_ref.startswith(PREFIX):raise GateError("GENERATED_PR_IDENTITY_AMBIGUOUS")
  if pr.get("user",{}).get("login")!=AUTHOR:raise GateError("GENERATED_PR_AUTHOR_INVALID")
  if pr.get("base",{}).get("ref")!="main":raise GateError("GENERATED_PR_BASE_INVALID")
  head_sha=pr["head"]["sha"];manual_text=head_ref[len(PREFIX):]
  if not manual_text.isdigit():raise GateError("MANUAL_RUN_ID_NOT_NUMERIC")
  manual_id=int(manual_text);scheduler_id,base_sha=parse_body(pr.get("body") or "")
  manual,_=gh.request(f"/repos/{repo}/actions/runs/{manual_id}")
  if manual.get("path")!=MANUAL_PATH or manual.get("event")!="workflow_dispatch" or manual.get("head_sha")!=base_sha or manual.get("conclusion")!="success":raise GateError("MANUAL_RUN_PROVENANCE_INVALID")
  if manual.get("actor",{}).get("login")!="github-actions[bot]":raise GateError("MANUAL_RUN_ACTOR_INVALID")
  scheduler,_=gh.request(f"/repos/{repo}/actions/runs/{scheduler_id}")
  if scheduler.get("path")!=SCHEDULER_PATH or scheduler.get("event") not in {"schedule","workflow_dispatch"} or scheduler.get("head_sha")!=base_sha or scheduler.get("conclusion")!="success":raise GateError("SCHEDULER_RUN_PROVENANCE_INVALID")
  artifact,data,digest=_artifact(gh,repo,scheduler_id);decision=parse_decision_report(data);print("DECISION_REPORT_PARSE=PASS");selected=(decision.get("manual_workflow_run") or {}).get("databaseId")
  if decision.get("decision")!="MANUAL_REFRESH_DISPATCHED" or decision.get("scheduler_run_id")!=str(scheduler_id) or decision.get("main_sha")!=base_sha or decision.get("remote_main_sha")!=base_sha or int(selected or 0)!=manual_id:raise GateError("SCHEDULER_ARTIFACT_PROVENANCE_INVALID")
  files=[];page=1
  while True:
   batch,_=gh.request(f"/repos/{repo}/pulls/{pr_number}/files?per_page=100&page={page}");files.extend(x["filename"] for x in batch)
   if len(batch)<100:break
   page+=1
  if not exact_scope(set(files)):raise GateError(f"EXACT_REFRESH_SCOPE_INVALID:{sorted(files)}")
  runs,_=gh.request(f"/repos/{repo}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100");selected_runs=latest_runs_by_name(runs.get("workflow_runs",[]));missing=sorted(REQUIRED_WORKFLOWS-set(selected_runs))
  if missing:raise Hold(f"WAITING_REQUIRED_WORKFLOWS:{missing}")
  pending=sorted(n for n,r in selected_runs.items() if r.get("status")!="completed")
  if pending:raise Hold(f"WAITING_REQUIRED_WORKFLOWS:{pending}")
  failed={n:r.get("conclusion") for n,r in selected_runs.items() if r.get("conclusion")!="success"}
  if failed:raise GateError(f"REQUIRED_CI_NOT_SUCCESS:{failed}")
  owner,name=repo.split("/",1);q="query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100){nodes{isResolved}pageInfo{hasNextPage}}}}}";threads=gh.graphql(q,{"owner":owner,"name":name,"number":pr_number})["repository"]["pullRequest"]["reviewThreads"]
  if threads["pageInfo"]["hasNextPage"]:raise GateError("REVIEW_THREAD_PAGINATION_AMBIGUOUS")
  unresolved=sum(1 for x in threads["nodes"] if not x["isResolved"])
  if unresolved:raise GateError(f"UNRESOLVED_REVIEW_THREADS:{unresolved}")
  ref,_=gh.request(f"/repos/{repo}/git/ref/heads/main");current_main=ref["object"]["sha"]
  latest_pr,_=gh.request(f"/repos/{repo}/pulls/{pr_number}")
  if current_main!=latest_pr["base"]["sha"]:raise GateError(f"BASE_DRIFT:{current_main}:{latest_pr['base']['sha']}")
  if current_main!=base_sha:
   allowed={'.github/workflows/crypto-astro-assistant-dispatch-pr.yml','.github/workflows/crypto-astro-automatic-refresh-pr.yml','.github/workflows/crypto-astro-generated-refresh-autopublish.yml','.github/workflows/crypto-astro-generated-refresh-ci-release.yml','.github/workflows/crypto-astro-operational-cadence-pr.yml','.github/workflows/crypto-astro-snapshot-memory-pr.yml','.github/workflows/crypto-astro-static-refresh-manual.yml','tools/crypto_astro_operations/test_verify_generated_refresh_autopublish.py','tools/crypto_astro_operations/test_verify_generated_refresh_ci_release.py','tools/crypto_astro_operations/test_verify_operational_cadence.py','tools/crypto_astro_operations/verify_generated_refresh_autopublish.py','tools/crypto_astro_operations/verify_generated_refresh_ci_release.py','tools/crypto_astro_operations/verify_operational_cadence.py'}
   comparison,_=gh.request(f"/repos/{repo}/compare/{base_sha}...{current_main}");drift={x["filename"] for x in comparison.get("files",[])}
   if not drift or not drift<=allowed:raise GateError(f"MAIN_DRIFT:{current_main}:{base_sha}:{sorted(drift)}")
  if latest_pr["head"]["sha"]!=head_sha:raise GateError("EXPECTED_HEAD_DRIFT")
  print("GENERATED_PR_IDENTITY=PASS\nEXACT_REFRESH_SCOPE=PASS\nCI_MATRIX=PASS\nEXPECTED_HEAD_PROTECTION=PASS")
  merge,_=gh.request(f"/repos/{repo}/pulls/{pr_number}/merge","PUT",{"sha":head_sha,"merge_method":"squash","commit_title":f"{TITLE} (#{pr_number})"})
  if not merge.get("merged") or not re.fullmatch(r"[0-9a-f]{40}",str(merge.get("sha",""))):raise GateError("MERGE_FAILED")
  merge_sha=merge["sha"];content,_=gh.request(f"/repos/{repo}/contents/site/crypto-astro/data/crypto_astro_snapshot.public.json?ref={head_sha}");snapshot=json.loads(base64.b64decode(content["content"]))
  report.update({"status":"PASS_MERGED","merged":True,"pr_number":pr_number,"head_sha":head_sha,"generation_base_sha":base_sha,"acceptance_base_sha":current_main,"merge_sha":merge_sha,"scheduler_run_id":scheduler_id,"manual_run_id":manual_id,"snapshot_timestamp":snapshot["generated_at_utc"],"required_ci":{k:v["id"] for k,v in selected_runs.items()},"unresolved_review_threads":0,"files":sorted(files),"artifact_id":artifact.get("id"),"artifact_metadata":"PASS","authenticated_api_request":"PASS","signed_redirect_request_without_auth":"PASS","archive_download":"PASS","digest_result":digest,"zip_integrity":"PASS","decision_report_parse":"PASS"});write_output(output_path,"merged","true");write_output(output_path,"merge_sha",merge_sha);write_output(output_path,"pr_number",str(pr_number));write_output(output_path,"snapshot_timestamp",snapshot["generated_at_utc"]);print("GATED_AUTOMATIC_MERGE=PASS");return 0
 except NotApplicable as e:report.update({"status":"NOT_APPLICABLE","reason":str(e)});write_output(output_path,"merged","false");return 0
 except Hold as e:report.update({"status":"HOLD","reason":str(e)});write_output(output_path,"merged","false");return 0
 except Exception as e:report.update({"status":"FAIL_CLOSED","reason":str(e)});write_output(output_path,"merged","false");return 1
 finally:report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")

def main():
 p=argparse.ArgumentParser();p.add_argument("--repo",required=True);p.add_argument("--token",required=True);mode=p.add_mutually_exclusive_group(required=True);mode.add_argument("--trigger-run-id",type=int);mode.add_argument("--artifact-proof-scheduler-run-id",type=int);p.add_argument("--report",type=Path,required=True);p.add_argument("--github-output",default="");a=p.parse_args()
 return run_artifact_proof(a.repo,a.token,a.artifact_proof_scheduler_run_id,a.report) if a.artifact_proof_scheduler_run_id is not None else run_gate(a.repo,a.token,a.trigger_run_id,a.report,a.github_output)
if __name__=="__main__":raise SystemExit(main())
