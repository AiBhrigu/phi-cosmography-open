#!/usr/bin/env python3
"""Evidence-bound BTC descriptive packet and deterministic RU/EN renderers."""
from __future__ import annotations

import argparse, csv, hashlib, importlib.util, io, json, math, statistics, zipfile
from datetime import date, datetime, timezone
from pathlib import Path

FIXTURE_REL=Path("tools/market_cosmographer_btc_descriptive_consumer/fixtures/btc_accepted_state_pair_v0_1.json")
VALIDATOR_REL=Path("tools/market_cosmographer_descriptive_contract/verify_descriptive_contract.py")
CONTRACT_REL=Path("docs/crypto-astro-service/market_cosmographer_descriptive_product_contract_v0_1.json")
FIXTURE_CANONICAL_SHA256="5743a78b573d801697d8705583944ad9b221d33b401478d8fdb9f9d8bff3badf"
METHODOLOGY_ID="btc_730d_price_state_methodology_v0_1"
METHODOLOGY_SHA256="e88e62c114d81178d52391cc63f0957d3114475f9d952ccc8bf7e72489e7111b"
STABILITY_REVIEW_ID="BTC_2190D_RETROSPECTIVE_REPLICATION_ASSOCIATION_STABILITY_AND_LABEL_SUPPORT_REVIEW_SCOPE_v0_1"
STABILITY_REVIEW_SHA256="cd54909a6ef429a231e5fa3a51cd4092435e83df36f64a43dc77f136d009261c"
CURRENT_DATE="2026-06-25"; PREVIOUS_DATE="2026-06-24"
CURRENT_STATE_SHA256="7b5b91af760ad50dee48c8267bd30238b58bf5249996aadbc68534d52b0f11da"
PREVIOUS_STATE_SHA256="46aeb1f3d4d0a632728d616d1cbdf3ffe1340b921a0a11970b12ccb817d214b2"
T0="TIER_0_RAW_SOURCE_FACT"; T2="TIER_2_STABLE_DESCRIPTIVE_METRIC"
TIER2_METRICS=("return_1d","return_7d","range_position_30d","quote_volume_ratio_to_prior_30d_median")
WINDOWS={
 "return_1d":"1 completed UTC day",
 "return_7d":"7 completed UTC days",
 "range_position_30d":"30 completed UTC days",
 "quote_volume_ratio_to_prior_30d_median":"current completed UTC day versus prior 30 completed UTC days",
}
FACT_BINDING={
 "return_1d":["btc_close"],"return_7d":["btc_close"],
 "range_position_30d":["btc_high","btc_low","btc_close"],
 "quote_volume_ratio_to_prior_30d_median":["btc_quote_volume"],
}

class ConsumerError(RuntimeError): pass

def canonical_bytes(v): return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
def pretty_bytes(v): return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
def sha256_bytes(v): return hashlib.sha256(v).hexdigest()
def finite(v,w):
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)): raise ConsumerError(f"{w}: finite number required")
 return float(v)
def utc(v,w):
 if not isinstance(v,str) or not v.endswith("Z"): raise ConsumerError(f"{w}: UTC datetime required")
 try: return datetime.fromisoformat(v[:-1]+"+00:00")
 except ValueError as e: raise ConsumerError(f"{w}: invalid UTC datetime") from e

def state_payload(s):
 return {k:s[k] for k in ("observation_date","phase","block_id","block_role","confirmation_eligible","source","input_max_timestamp_utc","methodology_id","methodology_sha256","metrics")}

def validate_fixture(f):
 if sha256_bytes(canonical_bytes(f))!=FIXTURE_CANONICAL_SHA256: raise ConsumerError("accepted fixture binding changed")
 for name,day,digest in (("previous_state",PREVIOUS_DATE,PREVIOUS_STATE_SHA256),("current_state",CURRENT_DATE,CURRENT_STATE_SHA256)):
  s=f[name]
  if s["observation_date"]!=day or s["state_sha256"]!=digest: raise ConsumerError(f"{name}: date/SHA binding")
  if sha256_bytes(canonical_bytes(state_payload(s)))!=digest: raise ConsumerError(f"{name}: state hash")
  if s["methodology_id"]!=METHODOLOGY_ID or s["methodology_sha256"]!=METHODOLOGY_SHA256: raise ConsumerError(f"{name}: methodology")
  if set(s["metrics"])!={"return_1d","return_7d","return_30d","realized_volatility_30d_annualized","drawdown_from_365d_high","range_position_30d","quote_volume_ratio_to_prior_30d_median","trend_persistence_30d","labels"}: raise ConsumerError(f"{name}: metric set")
  for k,v in s["metrics"].items():
   if k!="labels": finite(v,f"{name}.{k}")
 if utc(f["previous_state"]["input_max_timestamp_utc"],"previous")>=utc(f["current_state"]["input_max_timestamp_utc"],"current"): raise ConsumerError("state order")

def binance_time(raw):
 try: n=int(raw)
 except ValueError as e: raise ConsumerError("archive timestamp") from e
 return datetime.fromtimestamp(n/(1_000_000 if n>=10**15 else 1_000),tz=timezone.utc)
def number(raw,w,pos=False):
 try: x=float(raw)
 except ValueError as e: raise ConsumerError(f"archive {w}") from e
 if not math.isfinite(x) or x<0 or (pos and x<=0): raise ConsumerError(f"archive {w}")
 return x

def read_frozen_archives(folder:Path,f:dict):
 by_day={}; sources=[]
 for meta in f["archives"]:
  path=folder/meta["member"].replace(".csv",".zip")
  if not path.is_file(): raise ConsumerError(f"archive missing: {path.name}")
  payload=path.read_bytes(); actual=sha256_bytes(payload)
  if actual!=meta["expected_sha256"] or actual!=meta["actual_sha256"] or len(payload)!=meta["bytes"]: raise ConsumerError(f"archive binding: {meta['archive_id']}")
  try: z=zipfile.ZipFile(io.BytesIO(payload))
  except zipfile.BadZipFile as e: raise ConsumerError("archive ZIP") from e
  if z.namelist()!=[meta["member"]]: raise ConsumerError("archive member")
  parsed=[]
  with z.open(meta["member"]) as raw:
   for n,r in enumerate(csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline="")),1):
    if len(r)!=12: raise ConsumerError(f"archive columns {n}")
    ot,ct=binance_time(r[0]),binance_time(r[6]); d=ot.date().isoformat()
    if ot.time()!=datetime.min.time() or ct.date()!=ot.date(): raise ConsumerError("archive UTC day")
    o,h,l,c=number(r[1],"open",True),number(r[2],"high",True),number(r[3],"low",True),number(r[4],"close",True)
    bv,qv=number(r[5],"base volume"),number(r[7],"quote volume")
    try: trades=int(r[8])
    except ValueError as e: raise ConsumerError("archive trades") from e
    if trades<0 or h<max(o,l,c) or l>min(o,h,c) or d in by_day: raise ConsumerError("archive row invariant")
    row={"observation_date":d,"close_time_utc":ct.isoformat().replace("+00:00","Z"),"open":o,"high":h,"low":l,"close":c,"base_volume":bv,"quote_volume":qv,"trade_count":trades,"archive_id":meta["archive_id"]}
    by_day[d]=row; parsed.append(row)
  if len(parsed)!=meta["row_count"] or parsed[0]["observation_date"]!=meta["first_observation_date"] or parsed[-1]["observation_date"]!=meta["last_observation_date"]: raise ConsumerError("archive range")
  used=[r for r in parsed if r["observation_date"]<=CURRENT_DATE]
  if not used: raise ConsumerError("archive unused")
  sources.append({"fixture":meta,"actual_sha256":actual,"observed_at_utc":used[-1]["close_time_utc"]})
 rows=[by_day[k] for k in sorted(by_day)]
 expected=[]; cur=date(2026,5,1); end=date(2026,6,30)
 while cur<=end: expected.append(cur.isoformat()); cur=date.fromordinal(cur.toordinal()+1)
 if [r["observation_date"] for r in rows]!=expected: raise ConsumerError("archive window not contiguous")
 return rows,sources

def r12(x): return round(float(x),12)
def recompute_tier2(rows,day):
 i=next((i for i,r in enumerate(rows) if r["observation_date"]==day),None)
 if i is None or i<30: raise ConsumerError("insufficient history")
 r=rows[i]; w=rows[i-29:i+1]; lo=min(x["low"] for x in w); hi=max(x["high"] for x in w)
 return {
  "return_1d":r12(r["close"]/rows[i-1]["close"]-1),
  "return_7d":r12(r["close"]/rows[i-7]["close"]-1),
  "range_position_30d":r12((r["close"]-lo)/(hi-lo) if hi>lo else .5),
  "quote_volume_ratio_to_prior_30d_median":r12(r["quote_volume"]/statistics.median(x["quote_volume"] for x in rows[i-30:i])),
 }
def verify_metric_reproduction(rows,f):
 out={}
 for name in ("previous_state","current_state"):
  got=recompute_tier2(rows,f[name]["observation_date"]); expected={k:f[name]["metrics"][k] for k in TIER2_METRICS}
  for k in TIER2_METRICS:
   if not math.isclose(got[k],float(expected[k]),rel_tol=0,abs_tol=1e-12): raise ConsumerError(f"metric reproduction mismatch: {name}.{k}")
  out[name]=got
 return out

def load_validator(repo):
 p=repo/VALIDATOR_REL; spec=importlib.util.spec_from_file_location("descriptive_validator",p)
 if spec is None or spec.loader is None: raise ConsumerError("validator import")
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def pct(x): return f"{float(x)*100:.4f}%"
def ratio(x): return f"{float(x):.6f}"

def build_packet(f,rows,sources,generated_at_utc,validator):
 generated=utc(generated_at_utc,"generated"); cur=f["current_state"]; prev=f["previous_state"]; asof=utc(cur["input_max_timestamp_utc"],"asof")
 if generated<asof: raise ConsumerError("generated_at precedes observation")
 row=next(x for x in rows if x["observation_date"]==CURRENT_DATE)
 pid=f"btc:descriptive:{CURRENT_DATE}:{cur['state_sha256'][:16]}"; ppid=f"btc:descriptive:{PREVIOUS_DATE}:{prev['state_sha256'][:16]}"
 interval=f"between {PREVIOUS_DATE} and {CURRENT_DATE} completed UTC observations"
 packet_sources=[]; refs={}
 for s in sources:
  m=s["fixture"]; ref="binance_btcusdt_1d_"+m["archive_id"].replace(":","_").replace("-","_"); refs[m["archive_id"]]=ref
  packet_sources.append({"source_ref":ref,"provider":"BINANCE_PUBLIC_DATA","source_class":"CHECKSUM_BOUND_ARCHIVE","source_locator":m["zip_url"],"expected_sha256":m["expected_sha256"],"actual_sha256":s["actual_sha256"],"fetched_at_utc":generated_at_utc,"observed_at_utc":s["observed_at_utc"],"correction_status":"CLEAR","rights_status":"INTERNAL_RESEARCH_ALLOWED"})
 ref=refs[row["archive_id"]]
 facts=[]
 for fid,key,unit in (("btc_open","open","USDT"),("btc_high","high","USDT"),("btc_low","low","USDT"),("btc_close","close","USDT"),("btc_base_volume","base_volume","BTC"),("btc_quote_volume","quote_volume","USDT"),("btc_trade_count","trade_count","count")):
  facts.append({"fact_id":fid,"value":row[key],"unit":unit,"evidence_tier":T0,"source_refs":[ref],"eligibility":"ALLOWED"})
 metrics=[{"metric_id":k,"value":cur["metrics"][k],"unit":"ratio","observation_window":WINDOWS[k],"methodology_id":METHODOLOGY_ID,"methodology_sha256":METHODOLOGY_SHA256,"evidence_tier":T2,"stability_status":"PASS","eligibility":"ALLOWED","source_fact_ids":FACT_BINDING[k],"correction_status":"CLEAR"} for k in TIER2_METRICS]
 changes=[]
 for k in TIER2_METRICS:
  cv,pv=float(cur["metrics"][k]),float(prev["metrics"][k]); delta=r12(cv-pv)
  changes.append({"metric_id":k,"current_packet_id":pid,"previous_packet_id":ppid,"comparison_status":"COMPARABLE","current_value":cv,"previous_value":pv,"raw_delta":delta,"delta_unit":"ratio","historical_direction":"UP" if delta>0 else "DOWN" if delta<0 else "UNCHANGED","methodology_match":True,"correction_status":"CLEAR","interval_label":interval})
 exclusions=[{"field_id":k,"reason":v} for k,v in sorted(validator.expected_exclusions().items())]
 label=cur["metrics"]["labels"]["range_state"]
 human={
  "observation":f"At {cur['input_max_timestamp_utc']}, BTC closed at {row['close']:.2f} USDT. Its trailing 30-day range position was {cur['metrics']['range_position_30d']:.6f}, classified as {label}.",
  "change":f"The comparison interval was {interval}. return_1d changed from {pct(prev['metrics']['return_1d'])} to {pct(cur['metrics']['return_1d'])}; return_7d from {pct(prev['metrics']['return_7d'])} to {pct(cur['metrics']['return_7d'])}; range_position_30d from {ratio(prev['metrics']['range_position_30d'])} to {ratio(cur['metrics']['range_position_30d'])}; quote_volume_ratio_to_prior_30d_median from {ratio(prev['metrics']['quote_volume_ratio_to_prior_30d_median'])} to {ratio(cur['metrics']['quote_volume_ratio_to_prior_30d_median'])}.",
  "evidence":"The four Tier 2 metrics were independently recomputed from two checksum-bound Binance monthly archives, matched the accepted state hashes, and retained the frozen methodology and no-lookahead evidence bindings.",
  "uncertainty":"Predictive power has not been demonstrated. The observation is historical; Tier 1 metrics, blocked labels, forward outcomes, and association statistics are excluded.",
  "boundary":validator.CANONICAL_BOUNDARY,
 }
 return {
  "schema_version":"market_cosmographer_ai_descriptive_packet_v0_1","packet_id":pid,"packet_generation_id":f"btc-descriptive-v0-1:{CURRENT_DATE}:{generated_at_utc}",
  "subject":{"asset_id":"bitcoin","symbol":"BTC","market":"BTCUSDT_SPOT","interval":"1d_UTC","quote_asset":"USDT"},
  "observation":{"observation_date":CURRENT_DATE,"as_of_utc":cur["input_max_timestamp_utc"],"input_max_timestamp_utc":cur["input_max_timestamp_utc"],"generated_at_utc":generated_at_utc,"freshness_policy_id":"historical_accepted_state_v0_1","freshness_status":"HISTORICAL"},
  "sources":packet_sources,"facts":facts,"metrics":metrics,
  "labels":[{"label_id":"range_state","value":label,"input_metric_id":"range_position_30d","input_metric_tier":T2,"threshold_contract_id":METHODOLOGY_ID,"threshold_contract_sha256":METHODOLOGY_SHA256,"calibration_status":"PASS","effective_eligibility":"ALLOWED"}],
  "changes":changes,
  "evidence":{"source_manifest_sha256":f["evidence"]["source_manifest_sha256"],"methodology_sha256":METHODOLOGY_SHA256,"correction_ledger_sha256":f["evidence"]["correction_ledger_sha256"],"no_lookahead_proof_sha256":f["evidence"]["no_lookahead_proof_sha256"],"stability_review_id":STABILITY_REVIEW_ID,"stability_review_sha256":STABILITY_REVIEW_SHA256},
  "uncertainty":{"uncertainty_status":"DISCLOSED","reasons":["Predictive power has not been demonstrated.","The accepted observation is historical, not a current market read.","OOS_5 is a discovery reference block excluded from retrospective confirmation."],"unstable_metric_ids":["drawdown_from_365d_high","realized_volatility_30d_annualized","return_30d","trend_persistence_30d"],"blocked_label_ids":["drawdown_state","return_state","trend_state","volatility_state","volume_state"],"stale_source_refs":[x["source_ref"] for x in packet_sources],"incomparable_change_ids":[],"unresolved_correction_ids":[]},
  "exclusions":exclusions,"human_read":human,
  "boundary":{"descriptive_only":True,"predictive_power_proven":False,"forecast_allowed":False,"scenario_probability_allowed":False,"trading_signal_allowed":False,"price_target_allowed":False,"investment_recommendation_allowed":False},
  "distribution":{"mode":"INTERNAL_RESEARCH_ONLY","commercial_ai_feed":False,"data_rights_status":"PENDING","correction_sla_status":"PENDING","ai_consumer_utility_status":"PENDING"},
 }

def render_en(p):
 m={x["metric_id"]:x["value"] for x in p["metrics"]}; label=p["labels"][0]["value"]
 return "\n".join(["# Market Cosmographer · BTC · Historical Descriptive Read","",f"**Observation:** {p['observation']['as_of_utc']}","",p["human_read"]["observation"],"","## Allowed descriptive metrics","",f"- 1-day return: {pct(m['return_1d'])}",f"- 7-day return: {pct(m['return_7d'])}",f"- 30-day range position: {ratio(m['range_position_30d'])} ({label})",f"- Quote-volume ratio to prior 30-day median: {ratio(m['quote_volume_ratio_to_prior_30d_median'])}","","## Historical change","",p["human_read"]["change"],"","## Evidence","",p["human_read"]["evidence"],"","## Uncertainty","",p["human_read"]["uncertainty"],"","## Boundary","",p["human_read"]["boundary"],"",f"Packet ID: `{p['packet_id']}`","Distribution: `INTERNAL_RESEARCH_ONLY`",""])
def render_ru(p):
 m={x["metric_id"]:x["value"] for x in p["metrics"]}; c={x["metric_id"]:x for x in p["changes"]}; label=p["labels"][0]["value"]; label_ru={"LOWER":"нижняя часть","MIDDLE":"средняя часть","UPPER":"верхняя часть"}[label]; close=next(x["value"] for x in p["facts"] if x["fact_id"]=="btc_close")
 return "\n".join(["# Market Cosmographer · BTC · Историческое описательное чтение","",f"**Момент наблюдения:** {p['observation']['as_of_utc']}","",f"На момент наблюдения цена закрытия BTC составляла {close:.2f} USDT. Положение в завершённом 30-дневном диапазоне — {m['range_position_30d']:.6f}; классификация: {label_ru} диапазона.","","## Разрешённые описательные метрики","",f"- Доходность за 1 завершённый UTC-день: {pct(m['return_1d'])}",f"- Доходность за 7 завершённых UTC-дней: {pct(m['return_7d'])}",f"- Положение в 30-дневном диапазоне: {ratio(m['range_position_30d'])} ({label_ru})",f"- Отношение quote volume к медиане предыдущих 30 дней: {ratio(m['quote_volume_ratio_to_prior_30d_median'])}","","## Историческое изменение","",f"Интервал: {PREVIOUS_DATE} → {CURRENT_DATE}. return_1d: {pct(c['return_1d']['previous_value'])} → {pct(c['return_1d']['current_value'])}; return_7d: {pct(c['return_7d']['previous_value'])} → {pct(c['return_7d']['current_value'])}; range_position_30d: {ratio(c['range_position_30d']['previous_value'])} → {ratio(c['range_position_30d']['current_value'])}; quote-volume ratio: {ratio(c['quote_volume_ratio_to_prior_30d_median']['previous_value'])} → {ratio(c['quote_volume_ratio_to_prior_30d_median']['current_value'])}.","","## Доказательства","","Четыре метрики Tier 2 независимо пересчитаны из двух Binance-архивов, связанных контрольными суммами. Результаты совпали с принятыми state hashes, frozen methodology и no-lookahead proof.","","## Неопределённость","","Прогнозная сила не доказана. Наблюдение является историческим, а не текущим чтением рынка. Метрики Tier 1, заблокированные labels, forward outcomes и association statistics исключены.","","## Граница","","Чтение описывает только наблюдаемое состояние рынка и историческое изменение. Оно не прогнозирует цену, не предоставляет торговый сигнал, не оценивает будущие вероятности, не устанавливает ценовую цель и не является инвестиционной рекомендацией.","",f"Packet ID: `{p['packet_id']}`","Распространение: `INTERNAL_RESEARCH_ONLY`",""])

def write_outputs(out,p,reproduction,f,validator,repo):
 out.mkdir(parents=True,exist_ok=True); validator.validate_packet(p,validator.load_json(repo/CONTRACT_REL))
 pb=pretty_bytes(p); en=render_en(p).encode(); ru=render_ru(p).encode()
 report={"schema_version":"market_cosmographer_btc_descriptive_build_report_v0_1","status":"PASS","packet_id":p["packet_id"],"observation_date":CURRENT_DATE,"freshness_status":"HISTORICAL","source_pr":238,"source_artifact_digest":f["source_of_truth"]["workflow_artifact_digest"],"current_state_sha256":CURRENT_STATE_SHA256,"previous_state_sha256":PREVIOUS_STATE_SHA256,"tier2_metric_reproduction":"PASS","reproduced_metrics":reproduction,"contract_validation":"PASS","render_languages":["en","ru"],"distribution":"INTERNAL_RESEARCH_ONLY","commercial_ai_feed":"CLOSED","public_page_change":False,"public_snapshot_change":False,"output_sha256":{"btc_descriptive_packet.json":sha256_bytes(pb),"btc_descriptive_read.en.md":sha256_bytes(en),"btc_descriptive_read.ru.md":sha256_bytes(ru)}}
 for name,data in {"btc_descriptive_packet.json":pb,"btc_descriptive_read.en.md":en,"btc_descriptive_read.ru.md":ru,"btc_descriptive_build_report.json":pretty_bytes(report)}.items(): (out/name).write_bytes(data)
 return report

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,default=Path(".")); ap.add_argument("--fixture",type=Path); ap.add_argument("--archive-dir",type=Path,required=True); ap.add_argument("--generated-at-utc",required=True); ap.add_argument("--output-dir",type=Path,required=True); a=ap.parse_args()
 f=json.loads((a.fixture or a.repo/FIXTURE_REL).read_text(encoding="utf-8")); validate_fixture(f); rows,sources=read_frozen_archives(a.archive_dir,f); reproduction=verify_metric_reproduction(rows,f); validator=load_validator(a.repo); p=build_packet(f,rows,sources,a.generated_at_utc,validator); report=write_outputs(a.output_dir,p,reproduction,f,validator,a.repo); print(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
