#!/usr/bin/env python3
"""Fail-closed Market Cosmographer descriptive-contract validator."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

CONTRACT_REL=Path("docs/crypto-astro-service/market_cosmographer_descriptive_product_contract_v0_1.json")
SCHEMA_REL=Path("docs/crypto-astro-service/market_cosmographer_ai_descriptive_packet_schema_v0_1.json")
T0="TIER_0_RAW_SOURCE_FACT"; T1="TIER_1_DERIVED_DESCRIPTIVE_METRIC"; T2="TIER_2_STABLE_DESCRIPTIVE_METRIC"
METRICS={
"return_1d":(T2,"ALLOWED"),"return_7d":(T2,"ALLOWED"),
"return_30d":(T1,"EXPERIMENTAL_ONLY"),
"realized_volatility_30d_annualized":(T1,"EXPERIMENTAL_ONLY"),
"drawdown_from_365d_high":(T1,"EXPERIMENTAL_ONLY"),
"range_position_30d":(T2,"ALLOWED"),
"quote_volume_ratio_to_prior_30d_median":(T2,"ALLOWED"),
"trend_persistence_30d":(T1,"EXPERIMENTAL_ONLY")}
FORBIDDEN={"regime_label","direction_bias","probability_continuation","continuation_label","scenario_percentages","expected_return","price_target","trading_signal"}
RESEARCH={"H1","H2","H3","H4"}
PREDICTIVE=(r"\blikely\b",r"\bexpected\b",r"\bprobabilit(?:y|ies)\b",r"\bconfirmed edge\b",r"\bbullish\b",r"\bbearish\b",r"\bbuy\b",r"\bsell\b",r"\btarget price\b",r"\bprice target\b",r"\bwill rise\b",r"\bwill fall\b")
INTERVAL=("since ","over ","from ","previous ","prior ","between ","during ")

class ContractError(AssertionError): pass
def load_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def req(ok,msg):
    if not ok: raise ContractError(msg)
def keys(obj,required,where): req(set(required)<=set(obj),f"{where}: missing {sorted(set(required)-set(obj))}")
def sha(value,where): req(isinstance(value,str) and re.fullmatch(r"[a-f0-9]{64}",value),f"{where}: sha256")

def verify_contract(repo):
    c=load_json(repo/CONTRACT_REL); s=load_json(repo/SCHEMA_REL)
    req(c["schema_version"]=="market_cosmographer_descriptive_product_contract_v0_1","contract schema")
    req(c["status"]=="IMPLEMENTATION_CONTRACT","contract status")
    src=c["source_of_truth"]
    req(src["source_pr"]==238 and src["source_merge_sha"]=="464ca98a630af809870a4780072044bb66b59110","source binding")
    req(src["source_review_comment_id"]==5085918674 and src["evidence_result"]=="REGISTERED_ASSOCIATIONS_NOT_REPLICATED","review binding")
    req({k:(v["tier"],v["status"]) for k,v in c["metric_eligibility"].items()}==METRICS,"metric matrix")
    labels=c["label_eligibility"]
    req(labels["range_state"]["effective_status"]=="ALLOWED" and labels["range_state"]["input_metric_tier"]==T2,"range_state")
    req(labels["return_state"]["effective_status"]=="BLOCKED" and labels["return_state"]["blocked_reason"]=="INPUT_METRIC_RETURN_30D_NOT_TIER_2","return_state")
    for x in ("volatility_state","drawdown_state","volume_state","trend_state"):
        req(labels[x]["family_calibration"]=="FAIL" and labels[x]["effective_status"]=="BLOCKED",x)
    req(set(c["research_only_associations"])==RESEARCH and set(c["forbidden_product_fields"])==FORBIDDEN,"exclusion canon")
    req(c["commercial_ai_readiness"]["ready"] is False and all(v is False for v in c["boundary"].values()),"closed boundary")
    req(s["$schema"]=="https://json-schema.org/draft/2020-12/schema" and s["additionalProperties"] is False,"schema")
    required={"schema_version","packet_id","packet_generation_id","subject","observation","sources","facts","metrics","labels","changes","evidence","uncertainty","exclusions","human_read","boundary","distribution"}
    req(set(s["required"])==required,"schema required")
    req(s["properties"]["distribution"]["properties"]["commercial_ai_feed"]["const"] is False,"commercial lock")
    return {"status":"PASS","metrics":8,"labels":6,"commercial_ai_feed":"CLOSED"}

def validate_packet(p,c):
    top={"schema_version","packet_id","packet_generation_id","subject","observation","sources","facts","metrics","labels","changes","evidence","uncertainty","exclusions","human_read","boundary","distribution"}
    keys(p,top,"packet"); req(p["schema_version"]=="market_cosmographer_ai_descriptive_packet_v0_1","packet schema")
    obs=p["observation"]; keys(obs,{"observation_date","as_of_utc","input_max_timestamp_utc","generated_at_utc","freshness_policy_id","freshness_status"},"observation")
    req(obs["freshness_status"] in {"FRESH","AGING","STALE","HISTORICAL","UNKNOWN"},"freshness")
    refs=set()
    for i,x in enumerate(p["sources"]):
        keys(x,{"source_ref","provider","source_class","source_locator","expected_sha256","actual_sha256","fetched_at_utc","observed_at_utc","correction_status","rights_status"},f"source {i}")
        sha(x["expected_sha256"],"source expected"); sha(x["actual_sha256"],"source actual")
        req(x["expected_sha256"]==x["actual_sha256"] and x["correction_status"]=="CLEAR","source integrity")
        refs.add(x["source_ref"])
    facts=set()
    for x in p["facts"]:
        keys(x,{"fact_id","value","unit","evidence_tier","source_refs","eligibility"},"fact")
        req(x["evidence_tier"]==T0 and x["eligibility"]=="ALLOWED" and set(x["source_refs"])<=refs,"fact contract")
        req(x["fact_id"] not in FORBIDDEN|RESEARCH,"fact forbidden"); facts.add(x["fact_id"])
    packet_metrics={}
    for x in p["metrics"]:
        keys(x,{"metric_id","value","unit","observation_window","methodology_id","methodology_sha256","evidence_tier","stability_status","eligibility","source_fact_ids","correction_status"},"metric")
        mid=x["metric_id"]; req(mid in METRICS and (x["evidence_tier"],x["eligibility"])==METRICS[mid],"metric tier")
        req(x["stability_status"]==("PASS" if x["evidence_tier"]==T2 else x["stability_status"]) and x["correction_status"]=="CLEAR","metric state")
        if x["evidence_tier"]==T1: req(x["stability_status"] in {"FAIL","NOT_REVIEWED"},"tier1 state")
        sha(x["methodology_sha256"],"methodology"); req(set(x["source_fact_ids"])<=facts,"metric facts")
        packet_metrics[mid]=x
    labels=c["label_eligibility"]
    for x in p["labels"]:
        lid=x["label_id"]; req(lid in labels and x["input_metric_id"] in packet_metrics,"label binding")
        req(x["input_metric_id"]==labels[lid]["input_metric"] and x["input_metric_tier"]==packet_metrics[x["input_metric_id"]]["evidence_tier"],"label input")
        sha(x["threshold_contract_sha256"],"threshold")
        if x["effective_eligibility"]=="ALLOWED":
            req(lid=="range_state" and x["input_metric_tier"]==T2 and x["value"] in {"LOWER","MIDDLE","UPPER"},"allowed label")
        else: req(labels[lid]["effective_status"]=="BLOCKED" and x.get("blocked_reason") and x["value"] is None,"blocked label")
    for x in p["changes"]:
        req(x["metric_id"] in packet_metrics and packet_metrics[x["metric_id"]]["evidence_tier"]==T2,"change metric")
        req(x["comparison_status"]=="COMPARABLE" and x["methodology_match"] is True and x["correction_status"]=="CLEAR" and x["interval_label"],"change contract")
    for k in ("source_manifest_sha256","methodology_sha256","correction_ledger_sha256","no_lookahead_proof_sha256","stability_review_sha256"): sha(p["evidence"][k],k)
    req(p["uncertainty"].get("uncertainty_status")=="DISCLOSED","uncertainty")
    excluded={x["field_id"] for x in p["exclusions"]}
    required_excl=FORBIDDEN|RESEARCH|{k for k,v in METRICS.items() if v[0]==T1}|{k for k,v in labels.items() if v["effective_status"]=="BLOCKED"}|{"market_field_score"}
    req(required_excl<=excluded,f"missing exclusions {sorted(required_excl-excluded)}")
    h=p["human_read"]; keys(h,{"observation","change","evidence","uncertainty","boundary"},"human")
    req(not(set(h)&FORBIDDEN),"legacy field")
    text=" ".join(h[k] for k in ("observation","change","evidence","uncertainty")).lower()
    req(not any(re.search(q,text) for q in PREDICTIVE),"predictive language")
    if obs["freshness_status"]!="FRESH": req(not re.search(r"\b(current|currently|now)\b",h["observation"].lower()),"stale current language")
    if p["changes"]: req(any(q in h["change"].lower() for q in INTERVAL),"change interval")
    b=h["boundary"].lower()
    for q in ("does not forecast","trading signal","investment recommendation"): req(q in b,f"boundary {q}")
    req(p["boundary"]=={"descriptive_only":True,"predictive_power_proven":False,"forecast_allowed":False,"scenario_probability_allowed":False,"trading_signal_allowed":False,"price_target_allowed":False,"investment_recommendation_allowed":False},"boundary")
    req(p["distribution"]=={"mode":"INTERNAL_RESEARCH_ONLY","commercial_ai_feed":False,"data_rights_status":"PENDING","correction_sla_status":"PENDING","ai_consumer_utility_status":"PENDING"},"distribution")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,default=Path(".")); ap.add_argument("--packet",type=Path); a=ap.parse_args()
    report=verify_contract(a.repo)
    if a.packet: validate_packet(load_json(a.packet),load_json(a.repo/CONTRACT_REL)); report["packet_status"]="PASS"
    print(json.dumps(report,indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
