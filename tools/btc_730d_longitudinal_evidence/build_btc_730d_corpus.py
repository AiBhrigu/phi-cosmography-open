#!/usr/bin/env python3
"""Checksum-bound BTCUSDT 730-state-day research corpus; no predictive claim."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,statistics,time,urllib.error,urllib.request,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path

ROOT="https://data.binance.vision/data/spot"; SYMBOL="BTCUSDT"; INTERVAL="1d"
STATE_DAYS=730; WARMUP=365; OOS=365; TAIL=30; METHOD="btc_730d_price_state_methodology_v0_1"

class CorpusError(RuntimeError): pass

def cbytes(x): return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
def pbytes(x): return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
def sha(x): return hashlib.sha256(x).hexdigest()
def day(s):
    try: d=date.fromisoformat(s)
    except ValueError as e: raise CorpusError(f"invalid day: {s}") from e
    if d.isoformat()!=s: raise CorpusError(f"noncanonical day: {s}")
    return d

def days(a,b):
    while a<=b: yield a; a+=timedelta(days=1)
def month0(d): return d.replace(day=1)
def month1(d): return date(d.year+(d.month==12),1 if d.month==12 else d.month+1,1)

def plan(a,b):
    out=[]; m=month0(a); last=month0(b)
    while m<last:
        p=m.strftime("%Y-%m"); f=f"{SYMBOL}-{INTERVAL}-{p}.zip"; u=f"{ROOT}/monthly/klines/{SYMBOL}/{INTERVAL}/{f}"
        out.append((f"monthly:{p}","monthly",p,u,u+".CHECKSUM",f[:-4]+".csv")); m=month1(m)
    for d in days(last,b):
        p=d.isoformat(); f=f"{SYMBOL}-{INTERVAL}-{p}.zip"; u=f"{ROOT}/daily/klines/{SYMBOL}/{INTERVAL}/{f}"
        out.append((f"daily:{p}","daily",p,u,u+".CHECKSUM",f[:-4]+".csv"))
    return out

def get(url,path):
    if path.exists(): return path.read_bytes()
    req=urllib.request.Request(url,headers={"User-Agent":"BHRIGU-BTC-730D/0.1","Cache-Control":"no-cache"}); err=None
    for n in range(4):
        try:
            with urllib.request.urlopen(req,timeout=45) as r:
                if r.status!=200: raise CorpusError(f"HTTP {r.status}: {url}")
                data=r.read(); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data); return data
        except (urllib.error.URLError,TimeoutError,CorpusError) as e:
            err=e
            if n<3: time.sleep(1.5*(n+1))
    raise CorpusError(f"download failed: {url}: {err}")

def checksum(data,name):
    try: parts=data.decode().strip().split()
    except UnicodeDecodeError as e: raise CorpusError("checksum not utf8") from e
    if len(parts)<2: raise CorpusError("invalid checksum")
    value,found=parts[0].lower(),parts[-1].lstrip("*")
    if len(value)!=64 or any(c not in "0123456789abcdef" for c in value) or found!=name: raise CorpusError("checksum contract failed")
    return value

def utc(raw):
    try: n=int(raw)
    except ValueError as e: raise CorpusError("invalid timestamp") from e
    return datetime.fromtimestamp(n/(1_000_000 if n>=10**15 else 1_000),tz=timezone.utc)
def num(v,name,pos=False):
    try: x=float(v)
    except ValueError as e: raise CorpusError(f"invalid {name}") from e
    if not math.isfinite(x) or x<0 or (pos and x<=0): raise CorpusError(f"invalid {name}")
    return x

def parse(spec,payload,digest):
    aid,freq,period,url,check_url,member=spec
    try: z=zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as e: raise CorpusError(f"bad zip {aid}") from e
    if z.namelist()!=[member]: raise CorpusError(f"member mismatch {aid}")
    out=[]
    with z.open(member) as raw:
        for n,r in enumerate(csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline="")),1):
            if len(r)!=12: raise CorpusError(f"{aid}:{n}: columns")
            od,cd=utc(r[0]),utc(r[6]); d=od.date()
            if od.time()!=datetime.min.time() or cd.date()!=d: raise CorpusError(f"{aid}:{n}: UTC day")
            o,h,l,c=num(r[1],"open",True),num(r[2],"high",True),num(r[3],"low",True),num(r[4],"close",True)
            bv,qv=num(r[5],"base volume"),num(r[7],"quote volume")
            try: trades=int(r[8])
            except ValueError as e: raise CorpusError("invalid trades") from e
            if trades<0 or h<max(o,c,l) or l>min(o,c,h): raise CorpusError(f"{aid}:{n}: OHLC")
            out.append({"day":d,"close_time":cd.isoformat().replace("+00:00","Z"),"open":o,"high":h,"low":l,"close":c,"base_volume":bv,"quote_volume":qv,"trades":trades,"archive_id":aid,"archive_sha256":digest})
    if not out: raise CorpusError(f"empty archive {aid}")
    return out

def sources(a,b,cache):
    by_day={}; manifest=[]
    for spec in plan(a,b):
        aid,freq,period,url,check_url,member=spec; name=url.rsplit("/",1)[-1]
        expected=checksum(get(check_url,cache/(name+".CHECKSUM")),name); payload=get(url,cache/name); actual=sha(payload)
        if actual!=expected: raise CorpusError(f"checksum mismatch {aid}")
        parsed=parse(spec,payload,actual)
        for r in parsed:
            if r["day"] in by_day and by_day[r["day"]]!=r: raise CorpusError(f"conflicting day {r['day']}")
            by_day[r["day"]]=r
        manifest.append({"archive_id":aid,"frequency":freq,"period":period,"zip_url":url,"checksum_url":check_url,"expected_sha256":expected,"actual_sha256":actual,"bytes":len(payload),"member":member,"row_count":len(parsed),"first_observation_date":parsed[0]["day"].isoformat(),"last_observation_date":parsed[-1]["day"].isoformat()})
    actual=[by_day[d] for d in sorted(by_day) if a<=d<=b]; expected=list(days(a,b))
    if [r["day"] for r in actual]!=expected: raise CorpusError("noncontiguous source window")
    return actual,manifest

def ret(a,b): return a/b-1.0
def metrics(rows,i):
    r=rows[i]; x={"return_1d":ret(r["close"],rows[i-1]["close"]) if i>=1 else None,"return_7d":ret(r["close"],rows[i-7]["close"]) if i>=7 else None,"return_30d":ret(r["close"],rows[i-30]["close"]) if i>=30 else None}
    vol=None
    if i>=30:
        closes=[q["close"] for q in rows[i-30:i+1]]; lr=[math.log(closes[j]/closes[j-1]) for j in range(1,31)]; vol=statistics.pstdev(lr)*math.sqrt(365)
    dd=ret(r["close"],max(q["high"] for q in rows[i-364:i+1])) if i>=364 else None
    pos=None
    if i>=29:
        w=rows[i-29:i+1]; lo=min(q["low"] for q in w); hi=max(q["high"] for q in w); pos=(r["close"]-lo)/(hi-lo) if hi>lo else .5
    vr=None if i<30 else r["quote_volume"]/statistics.median(q["quote_volume"] for q in rows[i-30:i])
    tp=None if i<30 else sum(rows[j]["close"]>rows[j-1]["close"] for j in range(i-29,i+1))/30
    r30=x["return_30d"]
    x.update({"realized_volatility_30d_annualized":vol,"drawdown_from_365d_high":dd,"range_position_30d":pos,"quote_volume_ratio_to_prior_30d_median":vr,"trend_persistence_30d":tp,"labels":{"return_state":None if r30 is None else "POSITIVE" if r30>.05 else "NEGATIVE" if r30<-.05 else "BOUNDED","volatility_state":None if vol is None else "LOW" if vol<.4 else "ELEVATED" if vol>.75 else "MODERATE","drawdown_state":None if dd is None else "DEEP" if dd<=-.3 else "MATERIAL" if dd<=-.15 else "CONTAINED","range_state":None if pos is None else "LOWER" if pos<.25 else "UPPER" if pos>.75 else "MIDDLE","volume_state":None if vr is None else "LOW" if vr<.75 else "ELEVATED" if vr>1.5 else "TYPICAL","trend_state":None if tp is None else "NEGATIVE" if tp<.4 else "POSITIVE" if tp>.6 else "MIXED"}})
    return rounder(x)
def forward(rows,i):
    r=rows[i]; out={"maturity_status":"COMPLETE"}
    for h in (1,7,30):
        closes=[q["close"] for q in rows[i+1:i+h+1]]; out[f"forward_return_{h}d"]=ret(rows[i+h]["close"],r["close"]); out[f"forward_max_drawdown_{h}d"]=min(0.0,min(closes)/r["close"]-1); out[f"matures_on_{h}d"]=rows[i+h]["day"].isoformat()
    return rounder(out)
def rounder(x):
    if isinstance(x,float): return round(x,12)
    if isinstance(x,dict): return {k:rounder(v) for k,v in x.items()}
    if isinstance(x,list): return [rounder(v) for v in x]
    return x

def method():
    return {"schema_version":"btc_730d_methodology_v0_1","methodology_id":METHOD,"purpose":"research-only; no predictive or trading claim","source":{"provider":"Binance Public Data","market":"BTCUSDT Spot","interval":"1d UTC","archive_integrity":"SHA-256 .CHECKSUM required","raw_archive_redistribution":False},"window":{"state_days":730,"warmup_days":365,"out_of_sample_days":365,"maturity_tail_days":30},"no_lookahead":{"state_inputs":"timestamp <= state day close","forward_outcomes":"separate and excluded from state_sha256","full_sample_normalization":False,"formula_selection_after_results":False},"rights_boundary":{"distribution_status":"RESEARCH_ARTIFACT_ONLY","commercial_ai_feed":"NOT_AUTHORIZED","public_api":False,"public_page":False}}
def state_payload(r): return {k:r[k] for k in ("observation_date","phase","source","input_max_timestamp_utc","methodology_id","methodology_sha256","metrics")}

def corpus(rows,a,b):
    state=[r for r in rows if a<=r["day"]<=b]
    if len(state)!=730: raise CorpusError("state count")
    idx={r["day"]:i for i,r in enumerate(rows)}; m=method(); msha=sha(cbytes(m)); out=[]
    for n,r in enumerate(state):
        i=idx[r["day"]]; phase="WARMUP" if n<365 else "OUT_OF_SAMPLE"
        item={"schema_version":"btc_730d_longitudinal_evidence_v0_1","observation_date":r["day"].isoformat(),"phase":phase,"source":{"provider":"BINANCE_PUBLIC_DATA","market":"BTCUSDT_SPOT","interval":"1d","archive_id":r["archive_id"],"archive_sha256":r["archive_sha256"]},"input_max_timestamp_utc":r["close_time"],"methodology_id":METHOD,"methodology_sha256":msha,"metrics":metrics(rows,i),"outcomes":None if phase=="WARMUP" else forward(rows,i)}
        item["state_sha256"]=sha(cbytes(state_payload(item))); out.append(item)
    checks=[]
    for n in (365,455,545,729):
        i=idx[state[n]["day"]]; ok=cbytes(metrics(rows,i))==cbytes(metrics(rows[:i+1],i)); checks.append({"observation_date":state[n]["day"].isoformat(),"status":"PASS" if ok else "FAIL"})
        if not ok: raise CorpusError("prefix invariance")
    proof={"schema_version":"btc_730d_no_lookahead_proof_v0_1","status":"PASS","state_rows":730,"warmup_rows":365,"out_of_sample_rows":365,"forward_fields_excluded_from_state_hash":"PASS","prefix_invariance":checks}
    return out,m,proof

def corrections(now,old=None):
    events=[]
    if old:
        a={x["archive_id"]:x for x in old.get("archives",[])}; b={x["archive_id"]:x for x in now["archives"]}
        for k in sorted(a.keys()&b.keys()):
            if a[k].get("actual_sha256")!=b[k].get("actual_sha256"): events.append({"archive_id":k,"status":"SOURCE_ARCHIVE_REPLACED","previous_sha256":a[k].get("actual_sha256"),"current_sha256":b[k].get("actual_sha256")})
    return {"schema_version":"btc_730d_source_correction_ledger_v0_1","status":"CORRECTIONS_FOUND" if events else "NO_CORRECTIONS","event_count":len(events),"events":events,"silent_overwrite_allowed":False}

def write(out,rows,manifest,m,corr,proof,a,b,tail):
    out.mkdir(parents=True,exist_ok=True); raw=b"".join(cbytes(r) for r in rows); oos=rows[365:]
    summary={"schema_version":"btc_730d_longitudinal_evidence_summary_v0_1","status":"PASS","research_claim":"HISTORICAL_ASSOCIATION_ONLY","provider":"BINANCE_PUBLIC_DATA","market":"BTCUSDT_SPOT","state_start_date":a.isoformat(),"state_end_date":b.isoformat(),"source_tail_end_date":tail.isoformat(),"state_row_count":len(rows),"warmup_row_count":365,"out_of_sample_row_count":len(oos),"complete_30d_outcome_count":sum(r["outcomes"]["maturity_status"]=="COMPLETE" for r in oos),"correction_event_count":corr["event_count"],"no_lookahead_status":proof["status"],"corpus_sha256":sha(raw),"manifest_sha256":sha(pbytes(manifest)),"methodology_sha256":sha(cbytes(m))}
    files={"btc_730d_state_corpus.jsonl":raw,"btc_730d_source_manifest.json":pbytes(manifest),"btc_730d_methodology.json":pbytes(m),"btc_730d_correction_ledger.json":pbytes(corr),"btc_730d_no_lookahead_proof.json":pbytes(proof),"btc_730d_summary.json":pbytes(summary)}
    for k,v in files.items(): (out/k).write_bytes(v)
    return summary

def build(a,b,tail,cache,out,previous=None):
    if b!=a+timedelta(days=729) or tail!=b+timedelta(days=30): raise CorpusError("window contract")
    rows,archives=sources(a,tail,cache); manifest={"schema_version":"btc_730d_source_manifest_v0_1","provider":"BINANCE_PUBLIC_DATA","market":"BTCUSDT_SPOT","interval":"1d","source_start_date":a.isoformat(),"source_end_date":tail.isoformat(),"archive_count":len(archives),"archives":archives}
    old=json.loads(previous.read_text()) if previous else None; built,m,proof=corpus(rows,a,b); return write(out,built,manifest,m,corrections(manifest,old),proof,a,b,tail)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--state-start",required=True); p.add_argument("--state-end",required=True); p.add_argument("--source-end",required=True); p.add_argument("--cache-dir",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--previous-manifest",type=Path); x=p.parse_args()
    print(json.dumps(build(day(x.state_start),day(x.state_end),day(x.source_end),x.cache_dir,x.output_dir,x.previous_manifest),indent=2,sort_keys=True))
if __name__=="__main__": main()
