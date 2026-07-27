from __future__ import annotations
import csv
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
MODULE_PATH = Path(__file__).with_name('generate_btc_daily_pilot.py')
SPEC = importlib.util.spec_from_file_location('daily_pilot', MODULE_PATH)
assert SPEC and SPEC.loader
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)
CANONICAL_BOUNDARY = 'This read describes observed market state and historical change. It does not forecast price, provide a trading signal, estimate future probabilities, set a price target, or make an investment recommendation.'

def exclusions():
    result = {'return_30d':'UNSTABLE','realized_volatility_30d_annualized':'UNSTABLE','drawdown_from_365d_high':'UNSTABLE','trend_persistence_30d':'UNSTABLE','return_state':'UNSTABLE_INPUT','volatility_state':'UNCALIBRATED','drawdown_state':'UNCALIBRATED','volume_state':'UNCALIBRATED','trend_state':'UNCALIBRATED','market_field_score':'UNASSESSED'}
    for field in ('H1','H2','H3','H4','forward_return_1d','forward_return_7d','forward_return_30d','forward_max_drawdown_1d','forward_max_drawdown_7d','forward_max_drawdown_30d','association_rho','meta_rho','meta_ci_low','meta_ci_high','holm_p','expected_sign_blocks','confidence_interval'):
        result[field]='RESEARCH_ONLY'
    for field in ('regime_label','direction_bias','probability_continuation','continuation_label','scenario_percentages','expected_return','price_target','trading_signal'):
        result[field]='PREDICTIVE'
    return result

class FakeValidator:
    CANONICAL_BOUNDARY = CANONICAL_BOUNDARY
    @staticmethod
    def expected_exclusions(): return exclusions()
    @staticmethod
    def load_json(_path): return {}
    @staticmethod
    def validate_packet(packet,_contract):
        assert packet['observation']['freshness_status']=='FRESH'
        assert packet['distribution']['commercial_ai_feed'] is False
        assert [item['metric_id'] for item in packet['metrics']]==list(pilot.TIER2_METRICS)
        assert [item['label_id'] for item in packet['labels']]==['range_state']
        assert packet['human_read']['boundary']==CANONICAL_BOUNDARY

def policy():
    return {
        'schema_version':'market_cosmographer_btc_daily_utility_pilot_policy_v0_1','pilot_id':'market_cosmographer_btc_30_day_utility_pilot_v0_1','status':'AUTHORIZED_INTERNAL_PILOT','start_observation_date':'2026-07-25','end_observation_date':'2026-08-23','planned_consecutive_days':30,
        'subject':{'asset_id':'bitcoin','symbol':'BTC','market':'BTCUSDT_SPOT','interval':'1d_UTC'},
        'source_policy':{'provider':'BINANCE_PUBLIC_DATA','archive_frequency':'daily','source_window_days':32,'checksum_required':True,'raw_archive_distribution':False,'repository_storage':False},
        'freshness_policy':{'freshness_policy_id':'completed_utc_daily_snapshot_36h_v0_1','fresh_max_age_hours':36,'aging_max_age_hours':72,'pilot_accepts_only':'FRESH'},
        'accepted_product_fields':{'tier2_metrics':list(pilot.TIER2_METRICS),'tier3_labels':['range_state']},
        'automated_daily_gates':[],'manual_utility_questions':[],
        'completion_thresholds':{'accepted_daily_entries':30,'automated_gate_pass_rate':1.0,'clarity_pass_min':24,'evidence_comprehension_pass_min':24,'predictive_boundary_incidents_max':0,'useful_without_prediction_pass_min':21},
        'distribution':{'backend_api':False,'commercial_ai_feed':False,'mode':'INTERNAL_RESEARCH_ONLY','payment_or_subscription':False,'public_page':False,'public_snapshot':False},
    }

def timestamp_ms(day:date,end:bool=False)->int:
    dt=datetime.combine(day,datetime.min.time(),tzinfo=timezone.utc)
    if end: dt+=timedelta(days=1)-timedelta(milliseconds=1)
    return int(dt.timestamp()*1000)

def write_daily_archive(folder:Path,day:date,index:int)->None:
    name=pilot.archive_name(day); member=pilot.member_name(day); close=50000.0+index*131.0+index%5*17.0; open_value=close-75.0; high=close+250.0; low=close-300.0; base_volume=1000.0+index*4.0; quote_volume=close*base_volume
    row=[str(timestamp_ms(day)),f'{open_value:.8f}',f'{high:.8f}',f'{low:.8f}',f'{close:.8f}',f'{base_volume:.8f}',str(timestamp_ms(day,end=True)),f'{quote_volume:.8f}',str(10000+index),'0','0','0']
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        text=io.StringIO(); csv.writer(text,lineterminator='\n').writerow(row); archive.writestr(member,text.getvalue().encode('utf-8'))
    payload=buffer.getvalue(); digest=hashlib.sha256(payload).hexdigest(); (folder/name).write_bytes(payload); (folder/f'{name}.CHECKSUM').write_text(f'{digest}  {name}\n',encoding='utf-8')

def make_window(folder:Path,start:date,end:date)->None:
    folder.mkdir(parents=True,exist_ok=True); day=start; index=0
    while day<=end:
        write_daily_archive(folder,day,index); day+=timedelta(days=1); index+=1

class DailyPilotBase(unittest.TestCase):
    def setUp(self):
        self.policy=pilot.validate_policy(policy()); self.observation=date(2026,7,25); self.start=self.observation-timedelta(days=31); self.generated='2026-07-26T06:00:00Z'
    def build(self,root:Path,previous_manifest=None):
        archive_dir=root/'archives'; output_dir=root/'output'; make_window(archive_dir,self.start,self.observation); rows,manifest=pilot.read_source_window(archive_dir,self.start,self.observation,self.generated); correction=pilot.build_correction_ledger(manifest,previous_manifest,self.observation); proof=pilot.build_no_lookahead_proof(rows,self.observation-timedelta(days=1),self.observation); packet,state,diagnostics=pilot.build_packet(self.policy,rows,manifest,correction,proof,self.observation,self.generated,FakeValidator); report=pilot.write_build_outputs(output_dir,packet,state,manifest,correction,proof,diagnostics,self.policy,FakeValidator,root); return archive_dir,output_dir,packet,report,manifest
