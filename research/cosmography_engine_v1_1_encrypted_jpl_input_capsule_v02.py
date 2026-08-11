#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,io,json,math,time,urllib.parse,urllib.request
from pathlib import Path
NODE='COSMOGRAPHY_DYNAMICAL_ENGINE_V1_1_FRESH_HELDOUT_ENCRYPTED_JPL_INPUT_CAPSULE_v0_2'
SEED='COSMOGRAPHY_DYNAMICAL_ENGINE_V1_1_FRESH_HELDOUT_20260811'; T0_JD=2461262.50080074
SOURCE_FREEZE_SHA256='8989c1b47e7410f2b0337c3cd4b4751c68934e8015edf3ad233953ec8924459f'
SBQ='https://ssd-api.jpl.nasa.gov/sbdb_query.api'; SBO='https://ssd-api.jpl.nasa.gov/sbdb.api'; HOR='https://ssd.jpl.nasa.gov/api/horizons.api'
FIELDS=['spkid','pdes','full_name','kind','a','q','e','i','condition_code','data_arc','two_body','orbit_id','epoch']
SEM_FIELDS=['orbit_id','epoch','a','q','e','i','condition_code','data_arc','two_body']
EXCLUSIONS={'2021 CP5','2010 BK118','2013 AZ60','2004 VM131','2012 GU11','2000 SR331','2010 TJ','2007 BO81','1999 CZ118','2020 BF157','2025 BD4','895907','749801','767254','2014 WB536','602714','2013 RE124'}
EXPECTED={
'FA01':('A','0ad304c1c786d34081102dbae3c3a433938e2f869936f2820bc91306a567291d','f6d149ab832319d1bdc708a39be26736901a772cbc0b3c22d778d74eee7271ff','22d97ee0ebf38b0fe09018e6642afac92b0a33ebe0bddc8eb19f293f3d0f5b43','7ad4c0f3799ef661d7ea95107db3710208ca758b03d9a870d2f36eec392cb6ab','a59170ba444987ee77c6dec854652a316401800284fde51fb94cb7ebc9d941e2'),
'FA02':('A','0dd93b796c2ac5958a1d85a5542cdea8429a1dfefdc0e86282a48109c2390518','3e3b227bd8f05a92af32b47c678dfc98651558a0d76c6277f6278a46e2e88ac8','ba478d3030650ebb52419dc377116fca34c905884cd53b4cf3a215474e1a9a59','6a95bbff9c15a9a6253a943507012989ea73e01746c09257a42110c339d13499','83b63d3f58c654c286e04ff56a8198e73537d7f1de663b6d7bcaac1d9a9b9f73'),
'FA03':('A','1338309de1079bcd89d5c7533742b2362a0a2fd3dce639c91617fc86e486cddf','2bdc3da19a6a58ed32801c1c3adec090e89affe443016dcb6941fda3104bdfa6','d9eddfb4746fe8643da186e4b714344e822f8df636e4833ac8af46763a100c1c','ba8e021a258d6b0b705a4b98ee0f8d2dfd6309544842955226c9877b308250ac','3c79d8e1bfae887f2a5b2d31241862689d9664b7acfe3b56260d6919451ceaad'),
'FB01':('B','00fdb37de97d93f93ed71c480459e08d87d4f24a4e5080f95d8104e379ab4225','e308597a3acb88f1a72ed63cc750fb8b7ab36fdd7b6ee0e34853553ce3349d16','aec6f43627b068cea3ac71e1881984308e769a0edbd0d9be976e2a1c7d73fa03','5e8dd87a84be102f1d55fa743601b83e5902e2fbbdf8c06b04a759ceab396982','2362289a6a1043f6194678e8ae088c6479e2256759d51993e0bd85867b67907c'),
'FB02':('B','130a46af78587bed375bc73ec1e8e4f59822a2de93425f07b45124e9d9252c5c','6a2d87ee4fedba650f8d7c2744e30bfb8eff6eed02cb15cac968a91227cab3aa','9b515d937d419beee30db4df2736cf95039262ab6411e5e615f2a27b147081d6','c929b869cf5eeafad0533dda5401dd6c098dfbbc5dba493a1a42f730acf3d658','1d9da2b94258628f790e67044d06544d4c9588da99d5883003ca56672436491c'),
'FB03':('B','160b5d1c094d750ff112bee0ded27e9a89d17ae66308861c72809dce906ac19b','727dc13d4513460634761203b4f0865dbf31d9448fa80eb58b69e6436f4bf1ca','99b34b0e0e2fd2c0759e39459fe0b96545a932626bfcf03e2086187d0a31e5ef','971a66eee1f5a3122ba4f1a222d0f64f3a071a17e3d2a0ce5d8348368db51b4c','2e90d888f85db303e4be7f5ba6afa63d31e6fb2f369c8e3e3e0ea1216eb36315'),
'FC01':('C','007ca597793c5b20854fd1bb582a43a57cc611e58c1af313afcfa51a2acfa40c','5b4fdcfaf8b46621d54033f47c17a1552243e7c2cfbc93eaa8dc666591ce51c1','e94bcbdb9a1d5b87d1bcc5e8da13e49d145eced7d2b2f43097c85345cfefa884','c72abd4afcc3b445ff1cf68fa386027429d724d7067cde826e47b3f96cec8fdb','c31a37f81c6920b904e1517cf86345194cb9c8cf5cb332e19fdabd120174ff21'),
'FC02':('C','0176c005e4381dd02a9a22e58df5730951ed4cc97ce50b90a37d7c952b063640','ae2930213dcc75c647464eeab5d259f4bec23a6e763015ce057e7856fd000328','a2a66bd7681843c29265c4e50ead12c9e999fa4e0cba2dd2c2efbe4300543201','79002c61303bb1007cbd34d8092ced076d6fb6147699534a5f27c3d272e4557a','75be1aa10be41f309869f331c9702bd8a17d0847dde7480bca63e70bca282ec4'),
'FC03':('C','01dcc7b232cfe202342692f5a469efd9a400d1e85ec15d59488d63813da1b3e8','a7f7947efeeedc862ed2c740351d651ecaa08f719d3842a6b64ee85ce772cb6d','74da35aa8a8a6efc98e860f94223bf36aa58b3d2836a6fc5a3969f61a04c1dc1','c0334eacef0783a67bf710c37ddb72313412818ec3a7368caca620cefa9ed29a','710847c5c0d8aab58a27f414dccdb27ba9aa67e87e919960c67e7225689a8693')}
def fetch(base,params,quote=False):
    u=base+'?'+(urllib.parse.urlencode(params,quote_via=urllib.parse.quote) if quote else urllib.parse.urlencode(params)); last=None
    for k in range(6):
        try:
            req=urllib.request.Request(u,headers={'User-Agent':'BHRIGU-Cosmography-JPLInputCapsule/1.1'})
            with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
            return raw,json.loads(raw.decode()),u
        except Exception as e:last=type(e).__name__;time.sleep(min(2**k,8))
    raise RuntimeError('JPL_REQUEST_FAILED_'+str(last))
def arm(q):q=float(q);return 'A' if 5<=q<15 else 'B' if 15<=q<30 else 'C' if 30<=q<50 else None
def rankh(s,p,sp):return hashlib.sha256(f'{SEED}|{s}|{p}|{sp}'.encode()).hexdigest()
def semhash(r,cov):
    d={k:('' if r.get(k) is None else str(r.get(k)).strip()) for k in SEM_FIELDS};d['covariance_epoch_tdb_jd']=str(cov.get('epoch')).strip();d['covariance_labels']=list(cov.get('labels') or [])
    return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def covok(cov):
    if list(cov.get('labels') or [])!=['e','q','tp','node','peri','i']:return False
    try:m=[[float(v) for v in z] for z in cov['data']]
    except Exception:return False
    return len(m)==6 and all(len(z)==6 for z in m) and all(math.isfinite(v) for z in m for v in z) and all(abs(m[i][j]-m[j][i])<=1e-12*max(1,abs(m[i][j]),abs(m[j][i])) for i in range(6) for j in range(6))
def qq(v):return "'"+v+"'"
def vector(sp):
    p={'format':'json','COMMAND':qq(str(sp)),'OBJ_DATA':qq('NO'),'MAKE_EPHEM':qq('YES'),'EPHEM_TYPE':qq('VECTORS'),'CENTER':qq('500@10'),'TLIST':qq(f'{T0_JD:.12f}'),'TLIST_TYPE':qq('JD'),'TIME_TYPE':qq('TDB'),'REF_PLANE':qq('FRAME'),'REF_SYSTEM':qq('ICRF'),'OUT_UNITS':qq('AU-D'),'CSV_FORMAT':qq('YES'),'VEC_TABLE':qq('2')}
    raw,d,u=fetch(HOR,p,True);ls=d['result'].splitlines();a=next(i for i,x in enumerate(ls) if '$$SOE' in x);b=next(i for i,x in enumerate(ls) if '$$EOE' in x);st=None
    for line in ls[a+1:b]:
        f=[x.strip() for x in next(csv.reader(io.StringIO(line)))]
        if len(f)>=8:
            try:st=[float(f[k]) for k in range(2,8)];break
            except Exception:pass
    if st is None:raise RuntimeError('VECTOR_PARSE_FAIL')
    return st,hashlib.sha256(raw).hexdigest(),d.get('signature'),u
def main():
    c={'AND':['a|GE|50','q|GE|5','q|LT|50','e|GT|0','e|LT|1','condition_code|LE|3','data_arc|GE|1825',{'OR':['two_body|EQ|F','two_body|ND']}]}
    _,u,_=fetch(SBQ,{'sb-kind':'a','fields':','.join(FIELDS),'sb-cdata':json.dumps(c,separators=(',',':')),'full-prec':'true'});names=u['fields'];rows=[dict(zip(names,x)) for x in u['data']];objs=[];raw_drift=0
    for bid,(s,rh,ih,sh,oldsb,oldhz) in EXPECTED.items():
        cand=[]
        for r in rows:
            p=str(r.get('pdes') or '').strip();sp=str(r.get('spkid') or '').strip()
            if p not in EXCLUSIONS and arm(r.get('q'))==s and rankh(s,p,sp)==rh:cand.append(r)
        if len(cand)!=1:raise RuntimeError('RANK_RESOLUTION_'+bid)
        r=cand[0];p=str(r['pdes']).strip();sp=str(r['spkid']).strip()
        if hashlib.sha256(f'{p}|{sp}'.encode()).hexdigest()!=ih:raise RuntimeError('IDENTITY_'+bid)
        sbraw,sb,_=fetch(SBO,{'sstr':p,'cov':'mat','full-prec':'true'});cov=(sb.get('orbit') or {}).get('covariance')
        if not cov or not covok(cov):raise RuntimeError('COVARIANCE_'+bid)
        if semhash(r,cov)!=sh:raise RuntimeError('SEMANTIC_FROZEN_DRIFT_'+bid)
        cur_sb=hashlib.sha256(sbraw).hexdigest();raw_drift+=int(cur_sb!=oldsb)
        hzraw,hz,_=fetch(HOR,{'format':'json','COMMAND':f"'DES={sp};'",'OBJ_DATA':"'YES'",'MAKE_EPHEM':"'NO'"});res=str(hz.get('result') or '').lower()
        if hz.get('error') or not res or 'no matches found' in res or 'matching small-bodies' in res:raise RuntimeError('HORIZONS_RESOLUTION_'+bid)
        cur_hz=hashlib.sha256(hzraw).hexdigest();raw_drift+=int(cur_hz!=oldhz)
        st,vsha,sig,vurl=vector(sp)
        objs.append({'blind_id':bid,'stratum':s,'rank_sha256':rh,'identity_sha256':ih,'pdes':p,'spkid':sp,'sbdb_payload':sb,'frozen_semantic_sha256':sh,'sbdb_raw_sha256_current':cur_sb,'sbdb_raw_sha256_frozen_provenance':oldsb,'horizons_resolution_raw_sha256_current':cur_hz,'horizons_resolution_raw_sha256_frozen_provenance':oldhz,'t0_jd':T0_JD,'horizons_vector_state_helio_icrf_au_day':st,'horizons_vector_response_sha256':vsha,'horizons_signature':sig,'horizons_vector_url':vurl})
    out={'node':NODE,'status':'JPL_INPUT_CAPSULE_READY','source_freeze_sha256':SOURCE_FREEZE_SHA256,'objects':objs,'engine_source_included':False,'raw_response_provenance_drift_count':raw_drift,'semantic_frozen_solution_match':9}
    Path('/tmp/fresh-heldout-jpl-input-capsule.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');red={'node':NODE,'status':'JPL_INPUT_CAPSULE_SOURCE_MATCH_PASS','objects':9,'strata':'3/3/3','semantic_frozen_solution_match':9,'raw_response_provenance_drift_count':raw_drift,'vector_states_materialized':9,'plaintext_identity_upload':False,'engine_source_included':False};Path('/tmp/fresh-heldout-jpl-input-capsule-redacted.json').write_text(json.dumps(red,indent=2,sort_keys=True)+'\n');print(json.dumps(red,sort_keys=True))
if __name__=='__main__':main()
