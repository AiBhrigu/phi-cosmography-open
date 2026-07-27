#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "btc_descriptive_consumer", HERE / "generate_btc_descriptive_read.py"
)
assert SPEC and SPEC.loader
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)


class FakeValidator:
    CANONICAL_BOUNDARY = (
        "This read describes observed market state and historical change. "
        "It does not forecast price, provide a trading signal, estimate future probabilities, "
        "set a price target, or make an investment recommendation."
    )

    @staticmethod
    def expected_exclusions():
        tier1 = {
            "return_30d": "UNSTABLE",
            "realized_volatility_30d_annualized": "UNSTABLE",
            "drawdown_from_365d_high": "UNSTABLE",
            "trend_persistence_30d": "UNSTABLE",
        }
        labels = {
            "return_state": "UNSTABLE_INPUT",
            "volatility_state": "UNCALIBRATED",
            "drawdown_state": "UNCALIBRATED",
            "volume_state": "UNCALIBRATED",
            "trend_state": "UNCALIBRATED",
        }
        research = {
            "H1",
            "H2",
            "H3",
            "H4",
            "forward_return_1d",
            "forward_return_7d",
            "forward_return_30d",
            "forward_max_drawdown_1d",
            "forward_max_drawdown_7d",
            "forward_max_drawdown_30d",
            "association_rho",
            "meta_rho",
            "meta_ci_low",
            "meta_ci_high",
            "holm_p",
            "expected_sign_blocks",
            "confidence_interval",
        }
        forbidden = {
            "regime_label",
            "direction_bias",
            "probability_continuation",
            "continuation_label",
            "scenario_percentages",
            "expected_return",
            "price_target",
            "trading_signal",
        }
        result = {**tier1, **labels}
        result.update({key: "RESEARCH_ONLY" for key in research})
        result.update({key: "PREDICTIVE" for key in forbidden})
        result["market_field_score"] = "UNASSESSED"
        return result


class ConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_path = HERE / "fixtures" / "btc_accepted_state_pair_v0_1.json"
        cls.fixture = json.loads(cls.fixture_path.read_text(encoding="utf-8"))

    def test_accepted_fixture_passes(self):
        G.validate_fixture(copy.deepcopy(self.fixture))

    def test_tampered_state_metric_rejected(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["current_state"]["metrics"]["return_1d"] += 0.001
        with self.assertRaises(G.ConsumerError):
            G.validate_fixture(fixture)

    def test_forward_outcomes_cannot_enter_input_state(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["current_state"]["outcomes"] = {"forward_return_1d": 0.1}
        with self.assertRaises(G.ConsumerError):
            G.validate_fixture(fixture)

    def test_wrong_artifact_digest_rejected(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["source_of_truth"]["workflow_artifact_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(G.ConsumerError):
            G.validate_fixture(fixture)

    def test_wrong_archive_binding_rejected(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["archives"][0]["expected_sha256"] = "0" * 64
        with self.assertRaises(G.ConsumerError):
            G.validate_fixture(fixture)

    def test_state_hash_is_canonical_and_bound(self):
        for key, expected in (
            ("previous_state", G.PREVIOUS_STATE_SHA256),
            ("current_state", G.CURRENT_STATE_SHA256),
        ):
            state = self.fixture[key]
            self.assertEqual(
                G.sha256_bytes(G.canonical_bytes(G.state_payload(state))), expected
            )

    def test_recompute_tier2_formulas(self):
        rows = []
        for i in range(40):
            close = 100.0 + i
            rows.append(
                {
                    "observation_date": f"2026-01-{i+1:02d}" if i < 31 else f"2026-02-{i-30:02d}",
                    "high": close + 2.0,
                    "low": close - 2.0,
                    "close": close,
                    "quote_volume": 1000.0 + i * 10.0,
                }
            )
        metrics = G.recompute_tier2(rows, rows[-1]["observation_date"])
        self.assertAlmostEqual(metrics["return_1d"], 139 / 138 - 1, places=12)
        self.assertAlmostEqual(metrics["return_7d"], 139 / 132 - 1, places=12)
        low = min(row["low"] for row in rows[-30:])
        high = max(row["high"] for row in rows[-30:])
        self.assertAlmostEqual(
            metrics["range_position_30d"], (139 - low) / (high - low), places=12
        )

    def test_reproduction_mismatch_is_fail_closed(self):
        rows = []
        for day_number in range(1, 62):
            if day_number <= 31:
                observation_date = f"2026-05-{day_number:02d}"
            else:
                observation_date = f"2026-06-{day_number-31:02d}"
            rows.append(
                {
                    "observation_date": observation_date,
                    "high": 100.0 + day_number,
                    "low": 98.0 + day_number,
                    "close": 99.0 + day_number,
                    "quote_volume": 1000.0 + day_number,
                }
            )
        with self.assertRaises(G.ConsumerError):
            G.verify_metric_reproduction(rows, self.fixture)

    def synthetic_sources(self):
        output = []
        for item in self.fixture["archives"]:
            output.append(
                {
                    "fixture": item,
                    "actual_sha256": item["expected_sha256"],
                    "observed_at_utc": (
                        "2026-05-31T23:59:59.999999Z"
                        if item["archive_id"] == "monthly:2026-05"
                        else "2026-06-25T23:59:59.999999Z"
                    ),
                }
            )
        return output

    def synthetic_current_row(self):
        return {
            "observation_date": G.CURRENT_DATE,
            "open": 62000.0,
            "high": 62500.0,
            "low": 61000.0,
            "close": 61700.0,
            "base_volume": 1000.0,
            "quote_volume": 61_700_000.0,
            "trade_count": 100_000,
            "archive_id": "monthly:2026-06",
        }

    def test_packet_build_is_deterministic(self):
        generated = "2026-07-27T06:00:00Z"
        first = G.build_packet(
            self.fixture,
            [self.synthetic_current_row()],
            self.synthetic_sources(),
            generated,
            FakeValidator,
        )
        second = G.build_packet(
            self.fixture,
            [self.synthetic_current_row()],
            self.synthetic_sources(),
            generated,
            FakeValidator,
        )
        self.assertEqual(G.canonical_bytes(first), G.canonical_bytes(second))
        self.assertEqual(first["observation"]["freshness_status"], "HISTORICAL")
        self.assertFalse(first["distribution"]["commercial_ai_feed"])
        self.assertEqual([item["metric_id"] for item in first["metrics"]], list(G.TIER2_METRICS))
        self.assertEqual(first["labels"][0]["label_id"], "range_state")

    def test_generated_at_before_observation_rejected(self):
        with self.assertRaises(G.ConsumerError):
            G.build_packet(
                self.fixture,
                [self.synthetic_current_row()],
                self.synthetic_sources(),
                "2026-06-24T00:00:00Z",
                FakeValidator,
            )

    def test_ru_and_en_renderers_keep_internal_boundary(self):
        packet = G.build_packet(
            self.fixture,
            [self.synthetic_current_row()],
            self.synthetic_sources(),
            "2026-07-27T06:00:00Z",
            FakeValidator,
        )
        en = G.render_en(packet)
        ru = G.render_ru(packet)
        self.assertIn("INTERNAL_RESEARCH_ONLY", en)
        self.assertIn("INTERNAL_RESEARCH_ONLY", ru)
        self.assertIn("Predictive power has not been demonstrated.", en)
        self.assertIn("Прогнозная сила не доказана.", ru)
        self.assertNotIn("bullish", en.lower())
        self.assertNotIn("bearish", en.lower())

    def test_archive_missing_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(G.ConsumerError):
                G.read_frozen_archives(Path(temp), self.fixture)

    def test_nonfinite_metric_rejected(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["current_state"]["metrics"]["return_1d"] = math.nan
        with self.assertRaises(G.ConsumerError):
            G.validate_fixture(fixture)


if __name__ == "__main__":
    unittest.main()
