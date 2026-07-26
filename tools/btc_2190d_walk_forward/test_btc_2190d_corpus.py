#!/usr/bin/env python3
from __future__ import annotations

import copy
import math
import unittest
from datetime import timedelta
from pathlib import Path

from build_btc_2190d_corpus import (
    build_corpus,
    canonical_json_bytes,
    import_base_builder,
    load_design,
    prefix_indices,
    sha256,
    state_payload,
)


class WalkForwardCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[2]
        cls.base = import_base_builder(cls.repo)
        cls.design = load_design(cls.repo)
        start = cls.base.day(cls.design["window"]["state_start_date"])
        tail = cls.base.day(cls.design["window"]["source_tail_end_date"])
        cls.source_rows = []
        for index, observation_day in enumerate(cls.base.days(start, tail)):
            close = 10000.0 + index * 4.0 + 300.0 * math.sin(index / 37.0)
            cls.source_rows.append(
                {
                    "day": observation_day,
                    "close_time": (
                        f"{observation_day.isoformat()}T23:59:59.999000Z"
                    ),
                    "open": close * 0.997,
                    "high": close * 1.012,
                    "low": close * 0.988,
                    "close": close,
                    "base_volume": 100.0 + (index % 31),
                    "quote_volume": 1_000_000.0 + (index % 43) * 10_000.0,
                    "trades": 1000 + index,
                    "archive_id": f"synthetic:{observation_day.isoformat()}",
                    "archive_sha256": f"{index:064x}"[-64:],
                }
            )
        (
            cls.corpus,
            cls.registry,
            cls.protocol,
            cls.proof,
        ) = build_corpus(cls.source_rows, cls.design, cls.base)

    def test_exact_phase_and_block_counts(self):
        self.assertEqual(len(self.corpus), 2190)
        counts = {}
        for row in self.corpus:
            counts[row["block_id"]] = counts.get(row["block_id"], 0) + 1
        self.assertEqual(
            counts,
            {
                "WARMUP": 365,
                "OOS_1": 365,
                "OOS_2": 365,
                "OOS_3": 365,
                "OOS_4": 365,
                "OOS_5": 365,
            },
        )
        self.assertEqual(
            sum(row["phase"] == "OUT_OF_SAMPLE" for row in self.corpus),
            1825,
        )

    def test_outcome_and_contamination_boundaries(self):
        self.assertTrue(
            all(row["outcomes"] is None for row in self.corpus[:365])
        )
        self.assertTrue(
            all(
                row["outcomes"]["maturity_status"] == "COMPLETE"
                for row in self.corpus[365:]
            )
        )
        oos5 = [row for row in self.corpus if row["block_id"] == "OOS_5"]
        self.assertEqual(len(oos5), 365)
        self.assertTrue(
            all(row["confirmation_eligible"] is False for row in oos5)
        )
        self.assertTrue(
            all(
                row["block_role"]
                == "DISCOVERY_REFERENCE_EXCLUDED_FROM_CONFIRMATION"
                for row in oos5
            )
        )

    def test_state_hash_excludes_forward_outcomes(self):
        row = copy.deepcopy(self.corpus[365])
        original_hash = row["state_sha256"]
        row["outcomes"]["forward_return_30d"] = 999.0
        self.assertEqual(
            sha256(canonical_json_bytes(state_payload(row))), original_hash
        )
        row["metrics"]["return_30d"] = 999.0
        self.assertNotEqual(
            sha256(canonical_json_bytes(state_payload(row))), original_hash
        )

    def test_prefix_invariance_contract(self):
        points = prefix_indices(2190, 25)
        self.assertGreaterEqual(len(points), 25)
        self.assertIn(365, points)
        self.assertIn(2189, points)
        self.assertGreaterEqual(len(self.proof["prefix_invariance"]), 25)
        self.assertTrue(
            all(
                item["status"] == "PASS"
                for item in self.proof["prefix_invariance"]
            )
        )

    def test_frozen_methodology_and_hypotheses(self):
        self.assertEqual(
            self.protocol["accepted_methodology_id"],
            "btc_730d_price_state_methodology_v0_1",
        )
        self.assertEqual(
            self.protocol["accepted_methodology_sha256"],
            self.design["source_binding"]["methodology_sha256"],
        )
        self.assertEqual(
            self.protocol["registered_association_hypotheses"],
            self.design["registered_association_hypotheses"],
        )
        self.assertFalse(
            self.protocol["distribution_boundary"]["predictive_claim"]
        )
        self.assertFalse(
            self.registry["discovery_reference_used_for_confirmation"]
        )

    def test_source_window_contains_maturity_tail(self):
        state_end = self.base.day(self.design["window"]["state_end_date"])
        source_end = self.base.day(
            self.design["window"]["source_tail_end_date"]
        )
        self.assertEqual(source_end, state_end + timedelta(days=30))
        self.assertEqual(len(self.source_rows), 2220)


if __name__ == "__main__":
    unittest.main()
