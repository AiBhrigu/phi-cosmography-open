import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("render_what_changed.py")
SPEC = importlib.util.spec_from_file_location("what_changed_renderer", MODULE_PATH)
renderer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(renderer)


class WhatChangedTests(unittest.TestCase):
    @staticmethod
    def numeric(display, direction, unit, precision=1, previous="1", current="2", value_unit="percent"):
        return {
            "status": "COMPARABLE",
            "type": "NUMERIC",
            "previous_value": previous,
            "current_value": current,
            "display_delta": display,
            "display_precision": precision,
            "direction": direction,
            "delta_unit": unit,
            "unit": value_unit,
        }

    def setUp(self):
        self.registry = {
            "schema_version": "crypto_astro_snapshot_registry_public_v0_1",
            "selection_policy": "EXPLICIT_ACCEPTED_PAIR",
            "current": {"snapshot_id": "crypto-astro:2026-07-19T18:26:56Z:current"},
            "previous": {"snapshot_id": "crypto-astro:2026-07-12T22:05:46Z:previous"},
        }
        self.delta = {
            "schema_version": "crypto_astro_snapshot_delta_public_v0_1",
            "comparison_status": "PARTIAL_COMPARABLE",
            "current_snapshot_id": self.registry["current"]["snapshot_id"],
            "previous_snapshot_id": self.registry["previous"]["snapshot_id"],
            "generated_at_utc": "2026-07-19T18:26:56Z",
            "boundary": {
                "read_only": True,
                "static_public_snapshot": True,
                "runtime_closed": True,
                "backend_api_closed": True,
                "payment_closed": True,
                "orion_core_protected": True,
                "no_forecast": True,
                "no_trading_signal": True,
                "no_price_target": True,
            },
            "metrics": {
                "btc_gravity_pct": self.numeric("+0.28", "UP", "percentage_points", 2, "56.216", "56.500"),
                "stablecoin_share_pct": self.numeric("-0.18", "DOWN", "percentage_points", 2, "13.684", "13.500"),
                "alt_breadth_24h_pct": self.numeric("+8.0", "UP", "percentage_points", 1, "26.5", "34.5"),
                "alt_breadth_7d_pct": self.numeric("-1.3", "DOWN", "percentage_points", 1, "41.2", "39.9"),
                "market_field_score": self.numeric("+1.0", "UP", "score_points", 1, "60", "61", "score_0_100"),
                "regime_label": {
                    "status": "COMPARABLE",
                    "type": "CATEGORICAL",
                    "previous_value": "Balanced Expansion",
                    "current_value": "Balanced Expansion",
                    "transition": "UNCHANGED",
                },
            },
            "unavailable_metrics": {
                "defi_tvl_usd": {"delta_value": None, "reason_code": "METHODOLOGY_MISMATCH"},
                "liquidity_context_state": {"delta_value": None, "reason_code": "DEPENDENCY_METHODOLOGY_MISMATCH"},
            },
        }

    def test_render_is_deterministic(self):
        self.assertEqual(renderer.render(self.registry, self.delta), renderer.render(self.registry, self.delta))

    def test_six_comparable_metrics(self):
        self.assertEqual(renderer.render(self.registry, self.delta).count("data-metric="), 6)

    def test_full_utc_snapshot_timestamps(self):
        output = renderer.render(self.registry, self.delta)
        self.assertIn("2026-07-19T18:26:56Z", output)
        self.assertIn("2026-07-12T22:05:46Z", output)

    def test_unavailable_metrics_have_no_numeric_delta(self):
        output = renderer.render(self.registry, self.delta)
        self.assertIn("DeFi TVL · unavailable", output)
        self.assertIn("Liquidity context · unavailable", output)

    def test_boundary_fails_closed(self):
        self.delta["boundary"]["runtime_closed"] = False
        with self.assertRaises(ValueError):
            renderer.render(self.registry, self.delta)

    def test_snapshot_pair_must_match(self):
        self.delta["previous_snapshot_id"] = "wrong"
        with self.assertRaises(ValueError):
            renderer.render(self.registry, self.delta)


if __name__ == "__main__":
    unittest.main()
