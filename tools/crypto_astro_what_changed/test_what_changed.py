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
    def numeric(display, direction, unit, precision=1, previous="1", current="2", value_unit="percent", raw=None):
        return {
            "status": "COMPARABLE", "type": "NUMERIC", "previous_value": previous,
            "current_value": current, "raw_delta": raw if raw is not None else display,
            "display_delta": display, "display_precision": precision, "direction": direction,
            "delta_unit": unit, "unit": value_unit,
        }

    def setUp(self):
        self.registry = {
            "schema_version": "crypto_astro_snapshot_registry_public_v0_2",
            "selection_policy": "EXPLICIT_ACCEPTED_PAIR",
            "current": {"snapshot_id": "crypto-astro:2026-07-19T18:26:56Z:current"},
            "previous": {"snapshot_id": "crypto-astro:2026-07-12T22:05:46Z:previous"},
        }
        boundary = {
            "read_only": True, "static_public_snapshot": True, "runtime_closed": True,
            "backend_api_closed": True, "payment_closed": True, "orion_core_protected": True,
            "no_forecast": True, "no_trading_signal": True, "no_price_target": True,
            "ui_binding_opened": True, "refresh_pipeline_binding_opened": True,
        }
        self.delta = {
            "schema_version": "crypto_astro_snapshot_delta_public_v0_2",
            "comparison_status": "PARTIAL_COMPARABLE",
            "current_snapshot_id": self.registry["current"]["snapshot_id"],
            "previous_snapshot_id": self.registry["previous"]["snapshot_id"],
            "generated_at_utc": "2026-07-19T18:26:56Z", "boundary": boundary,
            "metrics": {
                "btc_gravity_pct": self.numeric("+0.28", "UP", "percentage_points", 2, "56.216", "56.500", raw="0.284"),
                "stablecoin_share_pct": self.numeric("-0.18", "DOWN", "percentage_points", 2, "13.684", "13.500", raw="-0.184"),
                "alt_breadth_24h_pct": self.numeric("+8.0", "UP", "percentage_points", 1, "26.5", "34.5", raw="8.0"),
                "alt_breadth_7d_pct": self.numeric("-1.3", "DOWN", "percentage_points", 1, "41.2", "39.9", raw="-1.3"),
                "market_field_score": self.numeric("+1.0", "UP", "score_points", 1, "60", "61", "score_0_100", "1.0"),
                "regime_label": {"status": "COMPARABLE", "type": "CATEGORICAL", "previous_value": "Balanced Expansion", "current_value": "Balanced Expansion", "transition": "UNCHANGED"},
            },
            "unavailable_metrics": {
                "defi_tvl_usd": {"delta_value": None, "reason_code": "METHODOLOGY_MISMATCH"},
                "liquidity_context_state": {"delta_value": None, "reason_code": "DEPENDENCY_METHODOLOGY_MISMATCH"},
            },
        }

    def test_partial_render_is_deterministic(self):
        self.assertEqual(renderer.render(self.registry, self.delta), renderer.render(self.registry, self.delta))
        self.assertEqual(renderer.render(self.registry, self.delta).count("data-metric="), 6)

    def test_full_utc_snapshot_timestamps(self):
        output = renderer.render(self.registry, self.delta)
        self.assertIn("2026-07-19T18:26:56Z", output)
        self.assertIn("2026-07-12T22:05:46Z", output)

    def test_full_comparable_renders_eight_cards(self):
        self.delta["comparison_status"] = "FULL_COMPARABLE"
        self.delta["metrics"]["defi_tvl_usd"] = self.numeric("+5500000000", "UP", "usd", 0, "70000000000", "75500000000", "usd", "5500000000")
        self.delta["metrics"]["liquidity_context_state"] = {"status": "COMPARABLE", "type": "CATEGORICAL", "previous_value": "context fresh", "current_value": "context fresh", "transition": "UNCHANGED"}
        self.delta["unavailable_metrics"] = {}
        output = renderer.render(self.registry, self.delta)
        self.assertEqual(output.count("data-metric="), 8)
        self.assertIn("+$5.50B", output)
        self.assertIn("All tracked metrics are comparable", output)

    def test_metric_partition_fails_closed(self):
        self.delta["unavailable_metrics"].pop("defi_tvl_usd")
        with self.assertRaises(ValueError):
            renderer.render(self.registry, self.delta)

    def test_boundary_fails_closed(self):
        self.delta["boundary"]["refresh_pipeline_binding_opened"] = False
        with self.assertRaises(ValueError):
            renderer.render(self.registry, self.delta)

    def test_snapshot_pair_must_match(self):
        self.delta["previous_snapshot_id"] = "wrong"
        with self.assertRaises(ValueError):
            renderer.render(self.registry, self.delta)


if __name__ == "__main__":
    unittest.main()
