#!/usr/bin/env python3
import csv,hashlib,io,math,tempfile,unittest,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import build_btc_730d_corpus as c

def stamps(d,micro):
    a=datetime(d.year,d.month,d.day,tzinfo=timezone.utc); f=1_000_000 if micro else 1_000
    return str(int(a.timestamp()*f)),str(int((a+timedelta(days=1)).timestamp()*f)-1)
def rows(start,n):
    out=[]; close=30000.0
    for i in range(n):
        d=start+timedelta(days=i); close*=math.exp(.0005+.018*math.sin(i/17)+.006*math.cos(i/5)); o=close*(1-.004*math.sin(i/3)); hi=max(o,close)*1.012; lo=min(o,close)*.988; a,z=stamps(d,d>=date(2025,1,1))
        out.append({"day":d,"close_time":c.utc(z).isoformat().replace('+00:00','Z'),"open":o,"high":hi,"low":lo,"close":close,"base_volume":1000+i,"quote_volume":(1000+i)*close,"trades":5000+i,"archive_id":f"synthetic:{d:%Y-%m}","archive_sha256":hashlib.sha256(f"archive:{d:%Y-%m}".encode()).hexdigest()})
    return out
def zipped(d,micro):
    name=f"BTCUSDT-1d-{d}.zip"; member=name[:-4]+'.csv'; a,z=stamps(d,micro); row=[a,'100','110','90','105','12',z,'1260','42','7','735','0']; txt=io.StringIO(newline=''); csv.writer(txt).writerow(row); b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as ar: ar.writestr(member,txt.getvalue())
    data=b.getvalue(); spec=(f"daily:{d}",'daily',str(d),'https://x/'+name,'https://x/'+name+'.CHECKSUM',member); return spec,data,hashlib.sha256(data).hexdigest()

class Test(unittest.TestCase):
    def test_timestamp_units(self):
        self.assertEqual(c.utc(stamps(date(2024,12,31),False)[0]).date(),date(2024,12,31)); self.assertEqual(c.utc(stamps(date(2025,1,1),True)[0]).date(),date(2025,1,1))
    def test_archive_parse(self):
        for d,m in ((date(2024,12,31),False),(date(2025,1,1),True)):
            spec,data,digest=zipped(d,m); got=c.parse(spec,data,digest); self.assertEqual(got[0]['day'],d); self.assertEqual(got[0]['close'],105)
    def test_checksum(self):
        digest='a'*64; self.assertEqual(c.checksum(f"{digest}  x.zip\n".encode(),'x.zip'),digest)
        with self.assertRaises(c.CorpusError): c.checksum(f"{digest}  y.zip\n".encode(),'x.zip')
    def test_plan(self):
        got=[x[0] for x in c.plan(date(2024,6,26),date(2024,8,3))]; self.assertEqual(got[:2],['monthly:2024-06','monthly:2024-07']); self.assertEqual(got[-1],'daily:2024-08-03')
    def test_730_contract_and_no_lookahead(self):
        a=date(2024,6,26); b=a+timedelta(days=729); raw=rows(a,760); built,m,proof=c.corpus(raw,a,b)
        self.assertEqual(len(built),730); self.assertEqual(sum(x['phase']=='WARMUP' for x in built),365); self.assertEqual(sum(x['phase']=='OUT_OF_SAMPLE' for x in built),365); self.assertTrue(all(x['outcomes'] is None for x in built[:365])); self.assertTrue(all(x['outcomes']['maturity_status']=='COMPLETE' for x in built[365:])); self.assertEqual(proof['status'],'PASS'); self.assertTrue(all(x['status']=='PASS' for x in proof['prefix_invariance']))
    def test_state_hash_excludes_outcomes(self):
        a=date(2024,6,26); built,_,_=c.corpus(rows(a,760),a,a+timedelta(days=729)); x=dict(built[500]); old=x['state_sha256']; x['outcomes']={'fake':True}; self.assertEqual(c.sha(c.cbytes(c.state_payload(x))),old)
    def test_direct_prefix_invariance(self):
        raw=rows(date(2023,1,1),500)
        for i in (364,400,499): self.assertEqual(c.metrics(raw,i),c.metrics(raw[:i+1],i))
    def test_corrections(self):
        old={'archives':[{'archive_id':'m','actual_sha256':'a'*64}]}; new={'archives':[{'archive_id':'m','actual_sha256':'b'*64}]}; got=c.corrections(new,old); self.assertEqual(got['event_count'],1); self.assertFalse(got['silent_overwrite_allowed'])
    def test_determinism(self):
        a=date(2024,6,26); raw=rows(a,760); x,_,p=c.corpus(raw,a,a+timedelta(days=729)); y,_,q=c.corpus(raw,a,a+timedelta(days=729)); self.assertEqual(b''.join(c.cbytes(z) for z in x),b''.join(c.cbytes(z) for z in y)); self.assertEqual(c.pbytes(p),c.pbytes(q))
    def test_no_raw_output(self):
        a=date(2024,6,26); b=a+timedelta(days=729); tail=b+timedelta(days=30); built,m,p=c.corpus(rows(a,760),a,b); manifest={'archives':[]}; corr=c.corrections(manifest)
        with tempfile.TemporaryDirectory() as t:
            summary=c.write(Path(t),built,manifest,m,corr,p,a,b,tail); names=[x.name for x in Path(t).iterdir()]; self.assertEqual(len(names),6); self.assertFalse(any(x.endswith(('.zip','.csv')) for x in names)); self.assertEqual(summary['complete_30d_outcome_count'],365)
if __name__=='__main__': unittest.main(verbosity=2)
