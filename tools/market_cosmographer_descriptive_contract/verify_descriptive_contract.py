#!/usr/bin/env python3
"""Fail-closed Market Cosmographer descriptive-contract validator."""
from __future__ import annotations
import argparse, json, math, re
from datetime import date, datetime
from pathlib import Path

CONTRACT_REL=Path("docs/crypto-astro-service/market_cosmographer_descriptive_product_contract_v0_1.json")
SCHEMA_REL=Path("docs/crypto-astro-service/market_cosmographer_ai_descriptive_packet_schema_v0_1.json")
T0="TIER_0_RAW_SOURCE_FACT"; T1="TIER_1_DERIVED_DESCRIPTIVE_METRIC"; T2="TIER_2_STABLE_DESCRIPTIVE_METRIC"
METHODOLOGY_ID="btc_730d_price_state_methodology_v0_1"
METHODOLOGY_SHA256="e88e62c114d81178d52391cc63f0957d3114475f9d952ccc8bf7e72489e7111b"
STABILITY_REVIEW_ID="BTC_2190D_RETROSPECTIVE_REPLICATION_ASSOCIATION_STABILITY_AND_LABEL_SUPPORT_REVIEW_SCOPE_v0_1"
STABILITY_REVIEW_SHA256="cd54909a6ef429a231e5fa3a51cd4092435e83df36f64a43dc77f136d009261c"
CANONICAL_BOUNDARY=("This read describes observed market state and historical change. "
"It does not forecast price, provide a trading signal, estimate future probabilities, "
"set a price target, or make an investment recommendation.")
REQUIRED_UNCERTAINTY="Predictive power has not been demonstrated."
FACTS={"btc_open","btc_high","btc_low","btc_close","btc_base_volume","btc_quote_volume","btc_trade_count"}
METRICS={
"return_1d":(T2,"ALLOWED"),"return_7d":(T2,"ALLOWED"),
"return_30d":(T1,"EXPERIMENTAL_ONLY"),
"realized_volatility_30d_annualized":(T1,"EXPERIMENTAL_ONLY"),
"drawdown_from_365d_high":(T1,"EXPERIMENTAL_ONLY"),
"range_position_30d":(T2,"ALLOWED"),
"quote_volume_ratio_to_prior_30d_median":(T2,"ALLOWED"),
"trend_persistence_30d":(T1,"EXPERIMENTAL_ONLY")}
BLOCKED_LABELS={"return_state","volatility_state","drawdown_state","volume_state","trend_state"}
FORBIDDEN={"regime_label","direction_bias","probability_continuation","continuation_label","scenario_percentages","expected_return","price_target","trading_signal"}
RESEARCH={"H1","H2","H3","H4","forward_return_1d","forward_return_7d","forward_return_30d",
"forward_max_drawdown_1d","forward_max_drawdown_7d","forward_max_drawdown_30d",
"association_rho","meta_rho","meta_ci_low","meta_ci_high","holm_p","expected_sign_blocks","confidence_interval"}
RESEARCH_PREFIXES=("forward_return_","forward_max_drawdown_","association_","meta_","holm_","expected_sign_")
PREDICTIVE=(
r"\blikely\b",r"\bexpected(?:\s+to)?\b",r"\bprobabilit(?:y|ies)\b",r"\bconfirmed edge\b",
r"\bbullish\b",r"\bbearish\b",r"\bupside\b",r"\bdownside\b",r"\bprice target\b",
r"\btarget price\b",r"\bforecast(?:s|ed|ing)?\b",r"\bpredict(?:s|ed|ing|ion|ive)?\b",
r"\b(?:buy|sell|hold)\b",
r"\b(?:may|might|could|should|will|set to|poised to)\b.{0,48}\b(?:rise|fall|increase|decrease|gain|drop|rally|decline|reverse)\b")
DATE_RE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE=re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

class ContractError(AssertionError): pass
def load_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def req(ok,msg):
    if not ok: raise ContractError(msg)
def exact(obj,required,where):
    req(isinstance(obj,dict),f"{where}: object")
    found=set(obj); req(found==set(required),f"{where}: keys missing={sorted(set(required)-found)} extra={sorted(found-set(required))}")
def nonempty(v,where): req(isinstance(v,str) and bool(v.strip()),f"{where}: nonempty string")
def sha(v,where): req(isinstance(v,str) and re.fullmatch(r"[a-f0-9]{64}",v),f"{where}: sha256")
def number(v,where):
    req(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v)),f"{where}: finite number")
    return float(v)
def unique(values,where): req(len(values)==len(set(values)),f"{where}: duplicate")
def iso_date(v,where):
    req(isinstance(v,str) and DATE_RE.fullmatch(v),f"{where}: date")
    try: parsed=date.fromisoformat(v)
    except ValueError as exc: raise ContractError(f"{where}: date") from exc
    req(parsed.isoformat()==v,f"{where}: canonical date")
def iso_dt(v,where):
    req(isinstance(v,str) and DATETIME_RE.fullmatch(v),f"{where}: UTC datetime")
    try: datetime.fromisoformat(v[:-1]+"+00:00")
    except ValueError as exc: raise ContractError(f"{where}: UTC datetime") from exc
def research_id(v): return v in RESEARCH or v.startswith(RESEARCH_PREFIXES)
def expected_exclusions():
    return {
    **{k:"UNSTABLE" for k,v in METRICS.items() if v[0]==T1},
    "return_state":"UNSTABLE_INPUT","volatility_state":"UNCALIBRATED",
    "drawdown_state":"UNCALIBRATED","volume_state":"UNCALIBRATED","trend_state":"UNCALIBRATED",
    **{k:"RESEARCH_ONLY" for k in RESEARCH},**{k:"PREDICTIVE" for k in FORBIDDEN},
    "market_field_score":"UNASSESSED"}

def verify_contract(repo):
    c=load_json(repo/CONTRACT_REL); s=load_json(repo/SCHEMA_REL)
    req(c["schema_version"]=="market_cosmographer_descriptive_product_contract_v0_1","contract schema")
    req(c["status"]=="IMPLEMENTATION_CONTRACT","contract status")
    src=c["source_of_truth"]
    req(src["source_pr"]==238 and src["source_merge_sha"]=="464ca98a630af809870a4780072044bb66b59110","source binding")
    req(src["source_review_comment_id"]==5085918674 and src["source_review_package_sha256"]==STABILITY_REVIEW_SHA256,"review binding")
    req(src["stability_review_id"]==STABILITY_REVIEW_ID,"review ID")
    req(src["accepted_methodology_id"]==METHODOLOGY_ID and src["accepted_methodology_sha256"]==METHODOLOGY_SHA256,"methodology binding")
    req(src["evidence_result"]=="REGISTERED_ASSOCIATIONS_NOT_REPLICATED","evidence result")
    req(set(c["tier0_fact_eligibility"])==FACTS,"fact matrix")
    req({k:(v["tier"],v["status"]) for k,v in c["metric_eligibility"].items()}==METRICS,"metric matrix")
    labels=c["label_eligibility"]; r=labels["range_state"]
    req(r["effective_status"]=="ALLOWED" and r["family_calibration"]=="PASS" and
        r["input_metric"]=="range_position_30d" and r["input_metric_tier"]==T2 and
        r["threshold_contract_id"]==METHODOLOGY_ID and r["threshold_contract_sha256"]==METHODOLOGY_SHA256,"range_state")
    req(labels["return_state"]["effective_status"]=="BLOCKED" and labels["return_state"]["blocked_reason"]=="INPUT_METRIC_RETURN_30D_NOT_TIER_2","return_state")
    for lid in ("volatility_state","drawdown_state","volume_state","trend_state"):
        req(labels[lid]["family_calibration"]=="FAIL" and labels[lid]["effective_status"]=="BLOCKED",lid)
    req(set(c["research_only_product_fields"])==RESEARCH and tuple(c["research_only_field_prefixes"])==RESEARCH_PREFIXES,"research matrix")
    req(set(c["forbidden_product_fields"])==FORBIDDEN,"forbidden matrix")
    req(c["human_contract"]["canonical_boundary"]==CANONICAL_BOUNDARY and c["human_contract"]["required_uncertainty_phrase"]==REQUIRED_UNCERTAINTY,"human canon")
    req(c["commercial_ai_readiness"]["ready"] is False and all(v is False for v in c["boundary"].values()),"closed boundary")
    req(s["$schema"]=="https://json-schema.org/draft/2020-12/schema" and s["additionalProperties"] is False,"schema")
    top={"schema_version","packet_id","packet_generation_id","subject","observation","sources","facts","metrics","labels","changes","evidence","uncertainty","exclusions","human_read","boundary","distribution"}
    req(set(s["required"])==top,"schema required")
    nodes=(s["properties"]["subject"],s["properties"]["observation"],s["properties"]["sources"]["items"],
    s["properties"]["facts"]["items"],s["properties"]["metrics"]["items"],s["properties"]["labels"]["items"],
    s["properties"]["changes"]["items"],s["properties"]["evidence"],s["properties"]["uncertainty"],
    s["properties"]["exclusions"]["items"],s["properties"]["human_read"],s["properties"]["boundary"],s["properties"]["distribution"])
    req(all(x.get("additionalProperties") is False for x in nodes),"nested schema closure")
    req(s["properties"]["human_read"]["properties"]["boundary"]["const"]==CANONICAL_BOUNDARY,"boundary schema")
    req(s["properties"]["evidence"]["properties"]["methodology_sha256"]["const"]==METHODOLOGY_SHA256,"method schema")
    req(s["properties"]["evidence"]["properties"]["stability_review_sha256"]["const"]==STABILITY_REVIEW_SHA256,"review schema")
    req(s["properties"]["distribution"]["properties"]["commercial_ai_feed"]["const"] is False,"commercial lock")
    return {"status":"PASS","facts":len(FACTS),"metrics":len(METRICS),"labels":len(labels),"research_only_fields":len(RESEARCH),"commercial_ai_feed":"CLOSED"}

def validate_packet(p,c):
    top={"schema_version","packet_id","packet_generation_id","subject","observation","sources","facts","metrics","labels","changes","evidence","uncertainty","exclusions","human_read","boundary","distribution"}
    exact(p,top,"packet"); req(p["schema_version"]=="market_cosmographer_ai_descriptive_packet_v0_1","packet schema")
    nonempty(p["packet_id"],"packet ID"); nonempty(p["packet_generation_id"],"generation ID")
    exact(p["subject"],{"asset_id","symbol","market","interval","quote_asset"},"subject")
    for k,v in p["subject"].items(): nonempty(v,f"subject {k}")
    o=p["observation"]; exact(o,{"observation_date","as_of_utc","input_max_timestamp_utc","generated_at_utc","freshness_policy_id","freshness_status"},"observation")
    iso_date(o["observation_date"],"observation date")
    for k in ("as_of_utc","input_max_timestamp_utc","generated_at_utc"): iso_dt(o[k],k)
    nonempty(o["freshness_policy_id"],"freshness policy"); req(o["freshness_status"] in {"FRESH","AGING","STALE","HISTORICAL","UNKNOWN"},"freshness")

    refs=[]
    for i,x in enumerate(p["sources"]):
        exact(x,{"source_ref","provider","source_class","source_locator","expected_sha256","actual_sha256","fetched_at_utc","observed_at_utc","correction_status","rights_status"},f"source {i}")
        for k in ("source_ref","provider","source_class","source_locator"): nonempty(x[k],f"source {i} {k}")
        sha(x["expected_sha256"],"source expected"); sha(x["actual_sha256"],"source actual")
        req(x["expected_sha256"]==x["actual_sha256"] and x["correction_status"]=="CLEAR","source integrity")
        req(x["rights_status"]=="INTERNAL_RESEARCH_ALLOWED","source rights")
        iso_dt(x["fetched_at_utc"],"source fetched"); iso_dt(x["observed_at_utc"],"source observed"); refs.append(x["source_ref"])
    req(refs,"sources required"); unique(refs,"sources"); refset=set(refs)

    facts=[]
    for i,x in enumerate(p["facts"]):
        exact(x,{"fact_id","value","unit","evidence_tier","source_refs","eligibility"},f"fact {i}")
        req(x["fact_id"] in FACTS and not research_id(x["fact_id"]) and x["fact_id"] not in FORBIDDEN,"fact ID")
        req(x["value"] is not None,"fact value"); nonempty(x["unit"],"fact unit")
        req(x["evidence_tier"]==T0 and x["eligibility"]=="ALLOWED","fact contract")
        req(isinstance(x["source_refs"],list) and x["source_refs"],"fact sources")
        unique(x["source_refs"],"fact sources"); req(set(x["source_refs"])<=refset,"fact source binding"); facts.append(x["fact_id"])
    req(facts,"facts required"); unique(facts,"facts"); factset=set(facts)

    packet_metrics={}
    for i,x in enumerate(p["metrics"]):
        exact(x,{"metric_id","value","unit","observation_window","methodology_id","methodology_sha256","evidence_tier","stability_status","eligibility","source_fact_ids","correction_status"},f"metric {i}")
        mid=x["metric_id"]; req(mid in METRICS and (x["evidence_tier"],x["eligibility"])==METRICS[mid],"metric tier")
        number(x["value"],"metric value"); nonempty(x["unit"],"metric unit"); nonempty(x["observation_window"],"metric window")
        req(x["methodology_id"]==METHODOLOGY_ID and x["methodology_sha256"]==METHODOLOGY_SHA256,"metric methodology")
        req(x["stability_status"]==("PASS" if x["evidence_tier"]==T2 else x["stability_status"]),"Tier 2 stability")
        if x["evidence_tier"]==T1: req(x["stability_status"] in {"FAIL","NOT_REVIEWED"},"Tier 1 stability")
        req(x["correction_status"]=="CLEAR" and isinstance(x["source_fact_ids"],list) and x["source_fact_ids"],"metric state")
        unique(x["source_fact_ids"],"metric facts"); req(set(x["source_fact_ids"])<=factset,"metric facts")
        req(mid not in packet_metrics,"duplicate metric"); packet_metrics[mid]=x
    req(packet_metrics,"metrics required")

    label_ids=[]
    for i,x in enumerate(p["labels"]):
        exact(x,{"label_id","value","input_metric_id","input_metric_tier","threshold_contract_id","threshold_contract_sha256","calibration_status","effective_eligibility"},f"label {i}")
        req(x["label_id"]=="range_state" and x["input_metric_id"]=="range_position_30d","label identity")
        req(x["input_metric_id"] in packet_metrics and packet_metrics[x["input_metric_id"]]["evidence_tier"]==T2 and x["input_metric_tier"]==T2,"label input")
        req(x["value"] in {"LOWER","MIDDLE","UPPER"} and x["calibration_status"]=="PASS" and x["effective_eligibility"]=="ALLOWED","label state")
        req(x["threshold_contract_id"]==METHODOLOGY_ID and x["threshold_contract_sha256"]==METHODOLOGY_SHA256,"threshold binding")
        label_ids.append(x["label_id"])
    unique(label_ids,"labels")

    changed=[]
    for i,x in enumerate(p["changes"]):
        exact(x,{"metric_id","current_packet_id","previous_packet_id","comparison_status","current_value","previous_value","raw_delta","delta_unit","historical_direction","methodology_match","correction_status","interval_label"},f"change {i}")
        mid=x["metric_id"]; req(mid in packet_metrics and packet_metrics[mid]["evidence_tier"]==T2,"change metric")
        req(x["current_packet_id"]==p["packet_id"] and x["previous_packet_id"]!=p["packet_id"],"change packet")
        nonempty(x["previous_packet_id"],"previous packet"); req(x["comparison_status"]=="COMPARABLE","comparison")
        current=number(x["current_value"],"current"); previous=number(x["previous_value"],"previous"); delta=number(x["raw_delta"],"delta")
        req(math.isclose(delta,current-previous,rel_tol=1e-12,abs_tol=1e-12),"delta mismatch")
        direction="UP" if delta>0 else "DOWN" if delta<0 else "UNCHANGED"
        req(x["historical_direction"]==direction and x["methodology_match"] is True and x["correction_status"]=="CLEAR","change state")
        nonempty(x["delta_unit"],"delta unit"); nonempty(x["interval_label"],"change interval"); changed.append(mid)
    unique(changed,"changes")

    e=p["evidence"]; exact(e,{"source_manifest_sha256","methodology_sha256","correction_ledger_sha256","no_lookahead_proof_sha256","stability_review_id","stability_review_sha256"},"evidence")
    for k in ("source_manifest_sha256","correction_ledger_sha256","no_lookahead_proof_sha256"): sha(e[k],k)
    req(e["methodology_sha256"]==METHODOLOGY_SHA256 and e["stability_review_id"]==STABILITY_REVIEW_ID and e["stability_review_sha256"]==STABILITY_REVIEW_SHA256,"evidence binding")

    u=p["uncertainty"]; exact(u,{"uncertainty_status","reasons","unstable_metric_ids","blocked_label_ids","stale_source_refs","incomparable_change_ids","unresolved_correction_ids"},"uncertainty")
    req(u["uncertainty_status"]=="DISCLOSED" and isinstance(u["reasons"],list) and REQUIRED_UNCERTAINTY in u["reasons"],"uncertainty")
    unstable={k for k,v in METRICS.items() if v[0]==T1}
    req(set(u["unstable_metric_ids"])==unstable and set(u["blocked_label_ids"])==BLOCKED_LABELS,"uncertainty disclosure")
    unique(u["unstable_metric_ids"],"unstable metrics"); unique(u["blocked_label_ids"],"blocked labels")
    req(set(u["stale_source_refs"])<=refset,"stale sources"); unique(u["stale_source_refs"],"stale sources")
    if o["freshness_status"]=="FRESH": req(not u["stale_source_refs"],"fresh packet stale source")
    req(u["unresolved_correction_ids"]==[],"unresolved corrections")

    seen={}; reasons={"UNSTABLE","UNSTABLE_INPUT","UNCALIBRATED","RESEARCH_ONLY","PREDICTIVE","RIGHTS_RESTRICTED","STALE","CORRECTION_INVALIDATED","UNASSESSED"}
    for i,x in enumerate(p["exclusions"]):
        exact(x,{"field_id","reason"},f"exclusion {i}"); nonempty(x["field_id"],"exclusion field")
        req(x["reason"] in reasons and x["field_id"] not in seen,"exclusion"); seen[x["field_id"]]=x["reason"]
    for field_id,reason in expected_exclusions().items(): req(seen.get(field_id)==reason,f"exclusion {field_id}: {reason}")

    h=p["human_read"]; exact(h,{"observation","change","evidence","uncertainty","boundary"},"human")
    for k,v in h.items(): nonempty(v,f"human {k}")
    req(o["as_of_utc"] in h["observation"],"observation timestamp")
    req(REQUIRED_UNCERTAINTY in h["uncertainty"] and h["boundary"]==CANONICAL_BOUNDARY,"human canon")
    text=" ".join((h["observation"],h["change"],h["evidence"],h["uncertainty"].replace(REQUIRED_UNCERTAINTY,""))).lower()
    req(not any(re.search(pattern,text) for pattern in PREDICTIVE),"predictive language")
    if o["freshness_status"]!="FRESH": req(not re.search(r"\b(current|currently|now|today)\b",h["observation"].lower()),"stale language")
    for x in p["changes"]: req(x["interval_label"].lower() in h["change"].lower(),f"change interval {x['metric_id']}")

    boundary={"descriptive_only":True,"predictive_power_proven":False,"forecast_allowed":False,"scenario_probability_allowed":False,"trading_signal_allowed":False,"price_target_allowed":False,"investment_recommendation_allowed":False}
    distribution={"mode":"INTERNAL_RESEARCH_ONLY","commercial_ai_feed":False,"data_rights_status":"PENDING","correction_sla_status":"PENDING","ai_consumer_utility_status":"PENDING"}
    exact(p["boundary"],set(boundary),"boundary"); req(p["boundary"]==boundary,"boundary values")
    exact(p["distribution"],set(distribution),"distribution"); req(p["distribution"]==distribution,"distribution values")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,default=Path(".")); ap.add_argument("--packet",type=Path); a=ap.parse_args()
    report=verify_contract(a.repo)
    if a.packet: validate_packet(load_json(a.packet),load_json(a.repo/CONTRACT_REL)); report["packet_status"]="PASS"
    print(json.dumps(report,indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
