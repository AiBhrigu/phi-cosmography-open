from __future__ import annotations
import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path
MODULE_PATH=Path(__file__).with_name('aggregate_btc_daily_utility.py'); SPEC=importlib.util.spec_from_file_location('daily_aggregate',MODULE_PATH); assert SPEC and SPEC.loader; aggregate_module=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(aggregate_module)

def policy():
    return {'schema_version':'market_cosmographer_btc_daily_utility_pilot_policy_v0_1','pilot_id':'market_cosmographer_btc_30_day_utility_pilot_v0_1','planned_consecutive_days':30,'start_observation_date':'2026-07-25','end_observation_date':'2026-08-23','completion_thresholds':{'accepted_daily_entries':30,'automated_gate_pass_rate':1.0,'predictive_boundary_incidents_max':0,'clarity_pass_min':24,'evidence_comprehension_pass_min':24,'useful_without_prediction_pass_min':21}}

def raw_entry(index:int)->dict:
    observation=date(2026,7,25)+timedelta(days=index-1); packet_id=f'btc:daily:{observation.isoformat()}:{index:016x}'
    return {'schema_version':'market_cosmographer_btc_daily_utility_entry_v0_1','pilot_id':policy()['pilot_id'],'pilot_day_index':index,'planned_days':30,'observation_date':observation.isoformat(),'generated_at_utc':f'{(observation+timedelta(days=1)).isoformat()}T06:00:00Z','packet_id':packet_id,'packet_sha256':f'{index:064x}','previous_packet_id':None,'previous_utility_entry_sha256':None,'source_manifest_sha256':f'{index+200:064x}','build_report_sha256':f'{index+300:064x}','read_en_sha256':f'{index+400:064x}','read_ru_sha256':f'{index+500:064x}','automated_gates':{name:'PASS' for name in aggregate_module.GATE_NAMES},'predictive_boundary_incidents':0,'manual_utility_review':{'status':'PENDING','clarity':'PENDING','evidence_comprehension':'PENDING','useful_without_prediction':'PENDING'},'distribution':'INTERNAL_RESEARCH_ONLY','commercial_ai_feed':False}

def entries(count:int)->list[dict]:
    result=[]
    for index in range(1,count+1):
        item=raw_entry(index)
        if result:
            item['previous_packet_id']=result[-1]['packet_id']; item['previous_utility_entry_sha256']=aggregate_module.sha256(aggregate_module.pretty_bytes(result[-1]))
        result.append(item)
    return result

def review(index:int,value:str='PASS')->dict:
    observation=date(2026,7,25)+timedelta(days=index-1)
    return {'schema_version':'market_cosmographer_btc_daily_utility_review_v0_1','pilot_id':policy()['pilot_id'],'observation_date':observation.isoformat(),'packet_id':f'btc:daily:{observation.isoformat()}:{index:016x}','reviewed_at_utc':f'{(observation+timedelta(days=1)).isoformat()}T10:00:00Z','clarity':value,'evidence_comprehension':value,'useful_without_prediction':value,'notes':''}

class AggregateTests(unittest.TestCase):
    def test_in_progress_with_one_entry(self):
        summary=aggregate_module.aggregate(policy(),entries(1),[]); self.assertEqual(summary['status'],'IN_PROGRESS'); self.assertEqual(summary['accepted_entries'],1)
    def test_complete_pending_review(self):
        self.assertEqual(aggregate_module.aggregate(policy(),entries(30),[])['status'],'COMPLETE_PENDING_HUMAN_REVIEW')
    def test_pass_with_thirty_positive_reviews(self):
        self.assertEqual(aggregate_module.aggregate(policy(),entries(30),[review(index) for index in range(1,31)])['status'],'PASS')
    def test_fail_below_utility_threshold(self):
        reviews=[review(index,'PASS' if index<=20 else 'FAIL') for index in range(1,31)]; self.assertEqual(aggregate_module.aggregate(policy(),entries(30),reviews)['status'],'FAIL')
    def test_gap_fails_closed(self):
        chain=entries(3)
        with self.assertRaises(aggregate_module.AggregateError): aggregate_module.aggregate(policy(),[chain[0],chain[2]],[])
    def test_predictive_boundary_incident_fails_entry(self):
        bad=entries(1)[0]; bad['predictive_boundary_incidents']=1
        with self.assertRaises(aggregate_module.AggregateError): aggregate_module.aggregate(policy(),[bad],[])
    def test_review_packet_mismatch_fails(self):
        bad_review=review(1); bad_review['packet_id']='wrong'
        with self.assertRaises(aggregate_module.AggregateError): aggregate_module.aggregate(policy(),entries(1),[bad_review])
    def test_utility_hash_chain_tampering_fails(self):
        chain=entries(2); chain[1]['previous_utility_entry_sha256']='0'*64
        with self.assertRaises(aggregate_module.AggregateError): aggregate_module.aggregate(policy(),chain,[])
    def test_review_timestamp_must_be_utc(self):
        bad_review=review(1); bad_review['reviewed_at_utc']='not-a-time'
        with self.assertRaises(aggregate_module.AggregateError): aggregate_module.aggregate(policy(),entries(1),[bad_review])
if __name__=='__main__': unittest.main()
