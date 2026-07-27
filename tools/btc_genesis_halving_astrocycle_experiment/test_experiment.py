from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify_mod = load("verify_design", Path(__file__).with_name("verify_experiment_design.py"))
gen_mod = load(
    "generate_delta", Path(__file__).with_name("generate_protocol_delta_snapshot.py")
)


class ExperimentTests(unittest.TestCase):
    def test_design(self):
        verify_mod.verify(ROOT)

    def test_snapshot_math_and_boundary(self):
        tip = 960000
        tip_timestamp = int(datetime(2026, 7, 29, tzinfo=timezone.utc).timestamp())
        block = {"id": "0" * 64, "height": tip, "timestamp": tip_timestamp}
        snapshot = gen_mod.build_snapshot(
            ROOT, tip, block, "2026-07-29T01:00:00Z"
        )
        self.assertEqual(snapshot["delta"]["blocks_since_current_epoch_start"], 120000)
        self.assertEqual(snapshot["delta"]["blocks_to_next_halving"], 90000)
        self.assertAlmostEqual(
            snapshot["delta"]["current_epoch_progress_ratio"], 120000 / 210000
        )
        self.assertFalse(snapshot["astromodule"]["planetary_values_in_this_snapshot"])
        self.assertFalse(snapshot["boundary"]["prediction"])
        self.assertFalse(snapshot["boundary"]["calendar_eta_is_exact"])

    def test_tip_outside_epoch_fails(self):
        block = {"id": "0" * 64, "height": 1050000, "timestamp": 1770000000}
        with self.assertRaises(ValueError):
            gen_mod.build_snapshot(
                ROOT, 1050000, block, "2026-07-29T01:00:00Z"
            )

    def test_height_mismatch_fails(self):
        block = {"id": "0" * 64, "height": 959999, "timestamp": 1770000000}
        with self.assertRaises(ValueError):
            gen_mod.build_snapshot(
                ROOT, 960000, block, "2026-07-29T01:00:00Z"
            )


if __name__ == "__main__":
    unittest.main()
