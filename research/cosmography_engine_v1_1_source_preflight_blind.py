#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt
import hashlib, json, math, time
import urllib.parse, urllib.request
from pathlib import Path

NODE="COSMOGRAPHY_DYNAMICAL_ENGINE_V1_1_EVENT_LEVEL_DISCRIMINATIVE_ENRICHMENT_FRESH_HELDOUT_COHORT_SOURCE_PREFLIGHT_AND_FREEZE_EXECUTION_v0_1"
SEED="COSMOGRAPHY_DYNAMICAL_ENGINE_V1_1_FRESH_HELDOUT_20260811"
OUT=Path("research/fresh_heldout_source_freeze_v0_1.json")

EXCLUSIONS={
"2021 CP5",
"2010 BK118","2013 AZ60","2004 VM131","2012 GU11","2000 SR331","2010 TJ","2007 BO81","1999 CZ118",
"2020 BF157","2025 BD4","895907","749801","767254","2014 WB536","602714","2013 RE124",
}
FIELDS=["spkid","pdes","full_name","kind","a","q","e","i","condition_code","data_arc","two_body","orbit_id","epoch"]
SBQ="https://ssd-api.jpl.nasa.gov/sbdb_query.api"
SBO="https://ssd-api.jpl.nasa.gov/sbdb.api"
HOR="https://ssd.jpl.nasa.gov/api/horizons.api"
COV_LABELS=["e","q","tp","node","peri","i"]

def get_json(base,params,attempts=5):
    url=base+"?"+urllib.parse.urlencode(params)
    last=None
    for k in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"BHRIGU-Cosmography-SourcePreflight/1.1"})
            with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
            return json.loads(raw.decode()),hashlib.sha256(raw).hexdigest()
        except Exception as e:
            last=repr(e)
            if k+1<attempts: time.sleep(min(2**k,8))
    raise RuntimeError(f"JPL_REQUEST_FAILED {base} {last}")

def arm(q):
    q=float(q)
    return "A" if 5<=q<15 else "B" if 15<=q<30 else "C" if 30<=q<50 else None

def rank(s,pdes,spkid):
    canon=f"{SEED}|{s}|{pdes}|{spkid}"
    return hashlib.sha256(canon.encode()).hexdigest(),canon

def cov_ok(data):
    if not isinstance(data,list) or len(data)!=6:return False,"COVARIANCE_NOT_6X6"
    try:
        m=[[float(v) for v in row] for row in data]
    except Exception:return False,"COVARIANCE_NONNUMERIC"
    if any(len(row)!=6 for row in m):return False,"COVARIANCE_NOT_6X6"
    if not all(math.isfinite(v) for row in m for v in row):return False,"COVARIANCE_NONFINITE"
    for i in range(6):
        for j in range(6):
            a,b=m[i][j],m[j][i]
            if abs(a-b)>1e-12*max(1.0,abs(a),abs(b)): return False,"COVARIANCE_NONSYMMETRIC"
    return True,None

def validate(r):
    pdes,spkid=str(r["pdes"]).strip(),str(r["spkid"]).strip()
    sb,sha1=get_json(SBO,{"sstr":pdes,"cov":"mat","full-prec":"true"})
    cov=((sb.get("orbit") or {}).get("covariance"))
    if not cov:return {"valid":False,"reason":"COVARIANCE_MISSING","sbdb_sha256":sha1}
    labels=list(cov.get("labels") or [])
    if labels!=COV_LABELS:return {"valid":False,"reason":"COVARIANCE_LABELS_NOT_EXACT_6","labels":labels,"sbdb_sha256":sha1}
    ok,why=cov_ok(cov.get("data"))
    if not ok:return {"valid":False,"reason":why,"labels":labels,"sbdb_sha256":sha1}
    hz,sha2=get_json(HOR,{"format":"json","COMMAND":f"'DES={spkid};'","OBJ_DATA":"'YES'","MAKE_EPHEM":"'NO'"})
    result=str(hz.get("result") or "")
    low=result.lower()
    if hz.get("error") or not result or "no matches found" in low or "matching small-bodies" in low:
        return {"valid":False,"reason":"HORIZONS_UNRESOLVED","sbdb_sha256":sha1,"horizons_sha256":sha2}
    return {"valid":True,"reason":"SOURCE_VALID","covariance_epoch_tdb_jd":cov.get("epoch"),
            "covariance_labels":labels,"sbdb_sha256":sha1,"horizons_sha256":sha2}

def main():
    cdata={"AND":["a|GE|50","q|GE|5","q|LT|50","e|GT|0","e|LT|1",
                  "condition_code|LE|3","data_arc|GE|1825",
                  {"OR":["two_body|EQ|F","two_body|ND"]}]}
    uni,unisha=get_json(SBQ,{"sb-kind":"a","fields":",".join(FIELDS),
                            "sb-cdata":json.dumps(cdata,separators=(",",":")),"full-prec":"true"})
    names=list(uni.get("fields") or []); data=list(uni.get("data") or [])
    if not names or not data: raise RuntimeError("SBDB_UNIVERSE_EMPTY")
    rows=[dict(zip(names,x)) for x in data]
    ranked={s:[] for s in "ABC"}; excluded_seen=[]
    for r in rows:
        pdes=str(r.get("pdes") or "").strip(); spkid=str(r.get("spkid") or "").strip()
        s=arm(r["q"])
        if not s: continue
        if pdes in EXCLUSIONS: excluded_seen.append(pdes); continue
        h,c=rank(s,pdes,spkid)
        ranked[s].append({**r,"stratum":s,"rank_sha256":h,"rank_canonical":c})
    for s in ranked: ranked[s].sort(key=lambda x:(x["rank_sha256"],x["pdes"],x["spkid"]))

    accepted={s:[] for s in "ABC"}; rejected={s:[] for s in "ABC"}
    for s in "ABC":
        for r in ranked[s]:
            if len(accepted[s])>=3: break
            a=validate(r); rec={**r,**a}
            (accepted if a["valid"] else rejected)[s].append(rec)

    counts={s:len(accepted[s]) for s in "ABC"}
    selected=[]
    if any(v<2 for v in counts.values()):
        status="FAIL_INSUFFICIENT_SOURCE_VALID_STRATUM"
    else:
        selected=accepted["A"]+accepted["B"]+accepted["C"]
        vals=sorted(counts.values()); n=len(selected)
        if n==9 and vals==[3,3,3]: status="PASS_FREEZE_3_3_3"
        elif n==8 and vals==[2,3,3]: status="PASS_FREEZE_FALLBACK_3_3_2"
        elif n==7 and vals==[2,2,3]: status="PASS_FREEZE_FALLBACK_3_2_2"
        elif n==6 and vals==[2,2,2]: status="PASS_FREEZE_FALLBACK_2_2_2"
        else: status="FAIL_FROZEN_DENOMINATOR_MISMATCH"; selected=[]

    freeze={
      "node":NODE,"status":status,"created_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "scientific_boundary":{"source_only":True,"nbody_dynamics_run":False,"family_reveal_run":False,
                             "confirmatory_statistics_run":False,"o2_primary_gate_promoted":False},
      "source_authority":{"provider":"JPL Solar System Dynamics","sbdb_query_api":SBQ,"sbdb_object_api":SBO,
                          "horizons_api":HOR,"sbdb_universe_response_sha256":unisha,
                          "sbdb_signature":uni.get("signature")},
      "frozen_contract":{"kind":"asteroid","a_au":">=50","q_au":">=5 and <50","e":">0 and <1",
          "condition_code":"<=3","data_arc_days":">=1825","two_body":"F or undefined",
          "strata":{"A":"5<=q<15","B":"15<=q<30","C":"30<=q<50"},
          "covariance":{"dimension":"6x6","labels_exact":COV_LABELS,"finite":True,"symmetric":True},
          "horizons":"unique SPK-ID resolution required","global_seed":SEED,
          "rank":"SHA256(seed|stratum|pdes|spkid), ascending",
          "target":"3/3/3","fallback":["3/3/2","3/2/2","2/2/2"],"minimum_per_stratum":2},
      "exclusions_required":sorted(EXCLUSIONS),"exclusions_required_count":len(EXCLUSIONS),
      "exclusions_seen_in_current_universe":sorted(set(excluded_seen)),
      "universe_count_before_exclusions":len(rows),
      "ranked_pool_count_after_exclusions":{s:len(ranked[s]) for s in ranked},
      "source_valid_counts":counts,
      "rejections_before_freeze":rejected,
      "selected_frozen_cohort":selected,
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    payload=json.dumps(freeze,indent=2,sort_keys=True,ensure_ascii=False)+"\n"
    OUT.write_text(payload,encoding="utf-8")
    psha=hashlib.sha256(payload.encode()).hexdigest()
    redacted={
      "node":NODE,"status":status,"universe_count":len(rows),
      "ranked_pool_count_after_exclusions":{s:len(ranked[s]) for s in ranked},
      "source_valid_counts":counts,"selected_count":len(selected),
      "rejection_counts":{s:len(rejected[s]) for s in rejected},
      "exclusions_required_count":len(EXCLUSIONS),
      "exclusions_seen_count":len(set(excluded_seen)),
      "freeze_plaintext_sha256":psha,
      "identity_disclosure":"ENCRYPTED_ONLY",
      "nbody_dynamics_run":False,
    }
    Path("research/fresh_heldout_source_freeze_redacted_v0_1.json").write_text(
      json.dumps(redacted,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(redacted,sort_keys=True))
    return 0 if status.startswith("PASS_") else 2

if __name__=="__main__": raise SystemExit(main())
