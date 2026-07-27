#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("validator",HERE/"verify_descriptive_contract.py")
assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(V)
D=lambda c="a":c*64

def exclusions():
    reasons={
    "return_30d":"UNSTABLE","realized_volatility_30d_annualized":"UNSTABLE",
    "drawdown_from_365d_high":"UNSTABLE","trend_persistence_30d":"UNSTABLE",
    "return_state":"UNCALIBRATED","volatility_state":"UNCALIBRATED",
    "drawdown_state":"UNCALIBRATED","volume_state":"UNCALIBRATED","trend_state":"UNCALIBRATED",
    "H1":"RESEARCH_ONLY","H2":"RESEARCH_ONLY","H3":"RESEARCH_ONLY","H4":"RESEARCH_ONLY",
    "market_field_score":"UNASSESSED","regime_label":"PREDICTIVE","direction_bias":"PREDICTIVE",
    "probability_continuation":"PREDICTIVE","continuation_label":"PREDICTIVE",
    "scenario_percentages":"PREDICTIVE","expected_return":"PREDICTIVE",
    "price_target":"PREDICTIVE","trading_signal":"PREDICTIVE"}
    return [{"field_id":k,"reason":v} for k,v in sorted(reasons.items())]

def metric(mid,value,tier,status,stability):
    return {"metric_id":mid,"value":value,"unit":"ratio","observation_window":"completed UTC observations",
    "methodology_id":"btc_730d_price_state_methodology_v0_1","methodology_sha256":D("b"),
    "evidence_tier":tier,"stability_status":stability,"eligibility":status,
    "source_fact_ids":["btc_close"],"correction_status":"CLEAR"}

def packet():
    return {
    "schema_version":"market_cosmographer_ai_descriptive_packet_v0_1",
    "packet_id":"btc:2026-07-25","packet_generation_id":"20260725T235959Z",
    "subject":{"asset_id":"bitcoin","symbol":"BTC","market":"BTCUSDT_SPOT","interval":"1d_UTC","quote_asset":"USDT"},
    "observation":{"observation_date":"2026-07-25","as_of_utc":"2026-07-25T23:59:59Z","input_max_timestamp_utc":"2026-07-25T23:59:59Z","generated_at_utc":"2026-07-26T00:05:00Z","freshness_policy_id":"btc_daily_close_v0_1","freshness_status":"FRESH"},
    "sources":[{"source_ref":"binance_btcusdt_1d","provider":"BINANCE_PUBLIC_DATA","source_class":"CHECKSUM_BOUND_ARCHIVE","source_locator":"monthly:2026-07","expected_sha256":D(),"actual_sha256":D(),"fetched_at_utc":"2026-07-26T00:01:00Z","observed_at_utc":"2026-07-25T23:59:59Z","correction_status":"CLEAR","rights_status":"INTERNAL_RESEARCH_ALLOWED"}],
    "facts":[{"fact_id":"btc_close","value":100000.0,"unit":"USDT","evidence_tier":V.T0,"source_refs":["binance_btcusdt_1d"],"eligibility":"ALLOWED"}],
    "metrics":[metric("return_1d",.01,V.T2,"ALLOWED","PASS"),metric("return_7d",.03,V.T2,"ALLOWED","PASS"),metric("range_position_30d",.8,V.T2,"ALLOWED","PASS"),metric("quote_volume_ratio_to_prior_30d_median",1.2,V.T2,"ALLOWED","PASS")],
    "labels":[{"label_id":"range_state","value":"UPPER","input_metric_id":"range_position_30d","input_metric_tier":V.T2,"threshold_contract_id":"btc_range_state_threshold_v0_1","threshold_contract_sha256":D("c"),"calibration_status":"PASS","effective_eligibility":"ALLOWED"}],
    "changes":[{"metric_id":"return_7d","current_packet_id":"btc:2026-07-25","previous_packet_id":"btc:2026-07-18","comparison_status":"COMPARABLE","current_value":.03,"previous_value":.01,"raw_delta":.02,"delta_unit":"ratio","historical_direction":"UP","methodology_match":True,"correction_status":"CLEAR","interval_label":"since the previous completed 7-day observation"}],
    "evidence":{"source_manifest_sha256":D("d"),"methodology_sha256":D("e"),"correction_ledger_sha256":D("f"),"no_lookahead_proof_sha256":D("1"),"stability_review_id":"BTC_2190D_RETROSPECTIVE_REPLICATION","stability_review_sha256":D("2")},
    "uncertainty":{"uncertainty_status":"DISCLOSED","reasons":["Predictive power has not been demonstrated."],"unstable_metric_ids":["return_30d","realized_volatility_30d_annualized","drawdown_from_365d_high","trend_persistence_30d"],"blocked_label_ids":["return_state","volatility_state","drawdown_state","volume_state","trend_state"],"stale_source_refs":[],"incomparable_change_ids":[],"unresolved_correction_ids":[]},
    "exclusions":exclusions(),
    "human_read":{"observation":"As of 2026-07-25T23:59:59Z, BTC was in the upper part of its trailing 30-day range.","change":"The observed 7-day return increased since the previous completed 7-day observation.","evidence":"The range and 7-day return metrics passed the accepted four-block stability review.","uncertainty":"Predictive power has not been demonstrated; unstable metrics and blocked labels are excluded.","boundary":"This read describes observed state and historical change. It does not forecast price, provide a trading signal, estimate future probabilities, or make an investment recommendation."},
    "boundary":{"descriptive_only":True,"predictive_power_proven":False,"forecast_allowed":False,"scenario_probability_allowed":False,"trading_signal_allowed":False,"price_target_allowed":False,"investment_recommendation_allowed":False},
    "distribution":{"mode":"INTERNAL_RESEARCH_ONLY","commercial_ai_feed":False,"data_rights_status":"PENDING","correction_sla_status":"PENDING","ai_consumer_utility_status":"PENDING"}}

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo=HERE.parents[1]; cls.contract=V.load_json(cls.repo/V.CONTRACT_REL)
    def reject(self,p):
        with self.assertRaises(V.ContractError): V.validate_packet(p,self.contract)
    def test_contract(self): self.assertEqual(V.verify_contract(self.repo)["status"],"PASS")
    def test_valid_packet(self): V.validate_packet(packet(),self.contract)
    def test_return_state_blocked_by_tier1_input(self):
        p=packet(); p["metrics"].append(metric("return_30d",.08,V.T1,"EXPERIMENTAL_ONLY","FAIL"))
        p["labels"].append({"label_id":"return_state","value":"POSITIVE","input_metric_id":"return_30d","input_metric_tier":V.T1,"threshold_contract_id":"return_state_v0_1","threshold_contract_sha256":D("3"),"calibration_status":"PASS","effective_eligibility":"ALLOWED"})
        self.reject(p)
    def test_failed_label_families(self):
        mapping={"volatility_state":"realized_volatility_30d_annualized","drawdown_state":"drawdown_from_365d_high","volume_state":"quote_volume_ratio_to_prior_30d_median","trend_state":"trend_persistence_30d"}
        for lid,mid in mapping.items():
            with self.subTest(label=lid):
                p=packet()
                if mid not in {x["metric_id"] for x in p["metrics"]}: p["metrics"].append(metric(mid,.5,V.T1,"EXPERIMENTAL_ONLY","FAIL"))
                tier=next(x["evidence_tier"] for x in p["metrics"] if x["metric_id"]==mid)
                p["labels"].append({"label_id":lid,"value":"ELEVATED","input_metric_id":mid,"input_metric_tier":tier,"threshold_contract_id":lid+"_v0_1","threshold_contract_sha256":D("4"),"calibration_status":"PASS","effective_eligibility":"ALLOWED"})
                self.reject(p)
    def test_hypotheses_rejected(self):
        for hid in V.RESEARCH:
            with self.subTest(h=hid):
                p=packet(); p["facts"][0]["fact_id"]=hid; self.reject(p)
    def test_legacy_and_predictive_language_rejected(self):
        p=packet(); p["human_read"]["regime_label"]="Balanced Expansion"; self.reject(p)
        for text in ("BTC is likely to rise.","The market is bullish.","Expansion probability is 61%.","This is a confirmed edge.","Buy BTC.","Target price is 120000."):
            with self.subTest(text=text):
                p=packet(); p["human_read"]["observation"]=text; self.reject(p)
    def test_stale_current_language_rejected(self):
        p=packet(); p["observation"]["freshness_status"]="STALE"; p["human_read"]["observation"]="BTC is currently in the upper range."; self.reject(p)
    def test_correction_and_checksum_rejected(self):
        p=packet(); p["sources"][0]["correction_status"]="UNRESOLVED"; self.reject(p)
        p=packet(); p["sources"][0]["actual_sha256"]=D("9"); self.reject(p)
    def test_commercial_feed_rejected(self):
        p=packet(); p["distribution"]["commercial_ai_feed"]=True; self.reject(p)
    def test_change_requires_interval(self):
        p=packet(); p["human_read"]["change"]="The observed 7-day return increased."; self.reject(p)
    def test_tier_escalation_rejected(self):
        p=packet(); p["metrics"][0].update(metric_id="return_30d",evidence_tier=V.T2,eligibility="ALLOWED"); self.reject(p)
    def test_silent_omission_rejected(self):
        p=packet(); p["exclusions"]=[x for x in p["exclusions"] if x["field_id"]!="H3"]; self.reject(p)

if __name__=="__main__": unittest.main()
