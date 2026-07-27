#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "validator", HERE / "verify_descriptive_contract.py"
)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)

D = lambda character="a": character * 64


def exclusions():
    return [
        {"field_id": field_id, "reason": reason}
        for field_id, reason in sorted(V.expected_exclusions().items())
    ]


def metric(metric_id, value, tier, status, stability):
    return {
        "metric_id": metric_id,
        "value": value,
        "unit": "ratio",
        "observation_window": "completed UTC observations",
        "methodology_id": V.METHODOLOGY_ID,
        "methodology_sha256": V.METHODOLOGY_SHA256,
        "evidence_tier": tier,
        "stability_status": stability,
        "eligibility": status,
        "source_fact_ids": ["btc_close"],
        "correction_status": "CLEAR",
    }


def packet():
    return {
        "schema_version": "market_cosmographer_ai_descriptive_packet_v0_1",
        "packet_id": "btc:2026-07-25",
        "packet_generation_id": "20260725T235959Z",
        "subject": {
            "asset_id": "bitcoin",
            "symbol": "BTC",
            "market": "BTCUSDT_SPOT",
            "interval": "1d_UTC",
            "quote_asset": "USDT",
        },
        "observation": {
            "observation_date": "2026-07-25",
            "as_of_utc": "2026-07-25T23:59:59Z",
            "input_max_timestamp_utc": "2026-07-25T23:59:59Z",
            "generated_at_utc": "2026-07-26T00:05:00Z",
            "freshness_policy_id": "btc_daily_close_v0_1",
            "freshness_status": "FRESH",
        },
        "sources": [{
            "source_ref": "binance_btcusdt_1d",
            "provider": "BINANCE_PUBLIC_DATA",
            "source_class": "CHECKSUM_BOUND_ARCHIVE",
            "source_locator": "monthly:2026-07",
            "expected_sha256": D(),
            "actual_sha256": D(),
            "fetched_at_utc": "2026-07-26T00:01:00Z",
            "observed_at_utc": "2026-07-25T23:59:59Z",
            "correction_status": "CLEAR",
            "rights_status": "INTERNAL_RESEARCH_ALLOWED",
        }],
        "facts": [{
            "fact_id": "btc_close",
            "value": 100000.0,
            "unit": "USDT",
            "evidence_tier": V.T0,
            "source_refs": ["binance_btcusdt_1d"],
            "eligibility": "ALLOWED",
        }],
        "metrics": [
            metric("return_1d", 0.01, V.T2, "ALLOWED", "PASS"),
            metric("return_7d", 0.03, V.T2, "ALLOWED", "PASS"),
            metric("range_position_30d", 0.8, V.T2, "ALLOWED", "PASS"),
            metric(
                "quote_volume_ratio_to_prior_30d_median",
                1.2,
                V.T2,
                "ALLOWED",
                "PASS",
            ),
        ],
        "labels": [{
            "label_id": "range_state",
            "value": "UPPER",
            "input_metric_id": "range_position_30d",
            "input_metric_tier": V.T2,
            "threshold_contract_id": V.METHODOLOGY_ID,
            "threshold_contract_sha256": V.METHODOLOGY_SHA256,
            "calibration_status": "PASS",
            "effective_eligibility": "ALLOWED",
        }],
        "changes": [{
            "metric_id": "return_7d",
            "current_packet_id": "btc:2026-07-25",
            "previous_packet_id": "btc:2026-07-18",
            "comparison_status": "COMPARABLE",
            "current_value": 0.03,
            "previous_value": 0.01,
            "raw_delta": 0.02,
            "delta_unit": "ratio",
            "historical_direction": "UP",
            "methodology_match": True,
            "correction_status": "CLEAR",
            "interval_label": "since the previous completed 7-day observation",
        }],
        "evidence": {
            "source_manifest_sha256": D("d"),
            "methodology_sha256": V.METHODOLOGY_SHA256,
            "correction_ledger_sha256": D("f"),
            "no_lookahead_proof_sha256": D("1"),
            "stability_review_id": V.STABILITY_REVIEW_ID,
            "stability_review_sha256": V.STABILITY_REVIEW_SHA256,
        },
        "uncertainty": {
            "uncertainty_status": "DISCLOSED",
            "reasons": [V.REQUIRED_UNCERTAINTY],
            "unstable_metric_ids": sorted(
                name for name, value in V.METRICS.items() if value[0] == V.T1
            ),
            "blocked_label_ids": sorted(V.BLOCKED_LABELS),
            "stale_source_refs": [],
            "incomparable_change_ids": [],
            "unresolved_correction_ids": [],
        },
        "exclusions": exclusions(),
        "human_read": {
            "observation": (
                "As of 2026-07-25T23:59:59Z, BTC was in the upper part "
                "of its trailing 30-day range."
            ),
            "change": (
                "The observed 7-day return increased since the previous "
                "completed 7-day observation."
            ),
            "evidence": (
                "The range and 7-day return metrics passed the accepted "
                "four-block stability review."
            ),
            "uncertainty": (
                "Predictive power has not been demonstrated. Unstable metrics "
                "and blocked labels are excluded."
            ),
            "boundary": V.CANONICAL_BOUNDARY,
        },
        "boundary": {
            "descriptive_only": True,
            "predictive_power_proven": False,
            "forecast_allowed": False,
            "scenario_probability_allowed": False,
            "trading_signal_allowed": False,
            "price_target_allowed": False,
            "investment_recommendation_allowed": False,
        },
        "distribution": {
            "mode": "INTERNAL_RESEARCH_ONLY",
            "commercial_ai_feed": False,
            "data_rights_status": "PENDING",
            "correction_sla_status": "PENDING",
            "ai_consumer_utility_status": "PENDING",
        },
    }


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = HERE.parents[1]
        cls.contract = V.load_json(cls.repo / V.CONTRACT_REL)

    def reject(self, candidate):
        with self.assertRaises(V.ContractError):
            V.validate_packet(candidate, self.contract)

    def test_contract(self):
        self.assertEqual(V.verify_contract(self.repo)["status"], "PASS")

    def test_valid_packet(self):
        V.validate_packet(packet(), self.contract)

    def test_extra_top_level_field_rejected(self):
        candidate = packet()
        candidate["regime_label"] = "Balanced Expansion"
        self.reject(candidate)

    def test_extra_nested_field_rejected(self):
        candidate = packet()
        candidate["subject"]["direction_bias"] = "Bullish"
        self.reject(candidate)

    def test_research_outcome_fact_rejected(self):
        for fact_id in ("forward_return_7d", "association_rho", "meta_rho"):
            with self.subTest(fact_id=fact_id):
                candidate = packet()
                candidate["facts"][0]["fact_id"] = fact_id
                self.reject(candidate)

    def test_return_state_blocked_by_tier1_input(self):
        candidate = packet()
        candidate["metrics"].append(
            metric("return_30d", 0.08, V.T1, "EXPERIMENTAL_ONLY", "FAIL")
        )
        candidate["labels"].append({
            "label_id": "return_state",
            "value": "POSITIVE",
            "input_metric_id": "return_30d",
            "input_metric_tier": V.T1,
            "threshold_contract_id": V.METHODOLOGY_ID,
            "threshold_contract_sha256": V.METHODOLOGY_SHA256,
            "calibration_status": "PASS",
            "effective_eligibility": "ALLOWED",
        })
        self.reject(candidate)

    def test_failed_label_families_rejected(self):
        for label_id in V.BLOCKED_LABELS - {"return_state"}:
            with self.subTest(label_id=label_id):
                candidate = packet()
                candidate["labels"].append({
                    "label_id": label_id,
                    "value": "ELEVATED",
                    "input_metric_id": "range_position_30d",
                    "input_metric_tier": V.T2,
                    "threshold_contract_id": V.METHODOLOGY_ID,
                    "threshold_contract_sha256": V.METHODOLOGY_SHA256,
                    "calibration_status": "PASS",
                    "effective_eligibility": "ALLOWED",
                })
                self.reject(candidate)

    def test_arbitrary_metric_methodology_rejected(self):
        candidate = packet()
        candidate["metrics"][0]["methodology_sha256"] = D("9")
        self.reject(candidate)

    def test_arbitrary_evidence_review_rejected(self):
        candidate = packet()
        candidate["evidence"]["stability_review_sha256"] = D("9")
        self.reject(candidate)

    def test_arbitrary_threshold_contract_rejected(self):
        candidate = packet()
        candidate["labels"][0]["threshold_contract_sha256"] = D("9")
        self.reject(candidate)

    def test_label_calibration_fail_rejected(self):
        candidate = packet()
        candidate["labels"][0]["calibration_status"] = "FAIL"
        self.reject(candidate)

    def test_predictive_language_rejected(self):
        for text in (
            "BTC is likely to rise.",
            "The market is bullish.",
            "BTC could rally over the next week.",
            "Expansion probability is 61%.",
            "This is a confirmed edge.",
            "Buy BTC.",
            "Target price is 120000.",
        ):
            with self.subTest(text=text):
                candidate = packet()
                candidate["human_read"]["observation"] = (
                    "As of 2026-07-25T23:59:59Z, " + text
                )
                self.reject(candidate)

    def test_predictive_boundary_injection_rejected(self):
        candidate = packet()
        candidate["human_read"]["boundary"] = (
            "BTC will rise. " + V.CANONICAL_BOUNDARY
        )
        self.reject(candidate)

    def test_stale_current_language_rejected(self):
        candidate = packet()
        candidate["observation"]["freshness_status"] = "STALE"
        candidate["human_read"]["observation"] = (
            "As of 2026-07-25T23:59:59Z, BTC is currently in the upper range."
        )
        self.reject(candidate)

    def test_correction_checksum_and_rights_rejected(self):
        candidate = packet()
        candidate["sources"][0]["correction_status"] = "UNRESOLVED"
        self.reject(candidate)

        candidate = packet()
        candidate["sources"][0]["actual_sha256"] = D("9")
        self.reject(candidate)

        candidate = packet()
        candidate["sources"][0]["rights_status"] = "RIGHTS_RESTRICTED"
        self.reject(candidate)

    def test_commercial_feed_rejected(self):
        candidate = packet()
        candidate["distribution"]["commercial_ai_feed"] = True
        self.reject(candidate)

    def test_change_requires_exact_interval(self):
        candidate = packet()
        candidate["human_read"]["change"] = "The observed 7-day return increased."
        self.reject(candidate)

    def test_change_delta_and_direction_rejected(self):
        candidate = packet()
        candidate["changes"][0]["raw_delta"] = 0.5
        self.reject(candidate)

        candidate = packet()
        candidate["changes"][0]["historical_direction"] = "DOWN"
        self.reject(candidate)

    def test_tier_escalation_rejected(self):
        candidate = packet()
        candidate["metrics"][0].update(
            metric_id="return_30d",
            evidence_tier=V.T2,
            eligibility="ALLOWED",
        )
        self.reject(candidate)

    def test_duplicate_identifiers_rejected(self):
        candidate = packet()
        candidate["facts"].append(copy.deepcopy(candidate["facts"][0]))
        self.reject(candidate)

        candidate = packet()
        candidate["metrics"].append(copy.deepcopy(candidate["metrics"][0]))
        self.reject(candidate)

    def test_silent_omission_and_wrong_reason_rejected(self):
        candidate = packet()
        candidate["exclusions"] = [
            item for item in candidate["exclusions"] if item["field_id"] != "H3"
        ]
        self.reject(candidate)

        candidate = packet()
        next(
            item for item in candidate["exclusions"]
            if item["field_id"] == "return_state"
        )["reason"] = "UNCALIBRATED"
        self.reject(candidate)


if __name__ == "__main__":
    unittest.main()
