#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("verify_current_bhrigu_dual_route.py")
SPEC = importlib.util.spec_from_file_location(
    "verify_current_bhrigu_dual_route", MODULE_PATH
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class CurrentBhriguDualRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        mod.install_current_surface_contract()

    def fetch_result(self, body: str):
        return mod.base.FetchResult(
            requested_url="https://example.test",
            final_url="https://example.test",
            status=200,
            redirects=[],
            content_type="text/html",
            body=body.encode("utf-8"),
            headers={},
        )

    def test_targets_are_exact_ru_entry_and_live_routes(self) -> None:
        self.assertEqual(
            mod.base.TARGETS["bhrigu_form"],
            "https://www.bhrigu.io/crypto-astro/btc?lang=ru",
        )
        self.assertEqual(
            mod.base.TARGETS["bhrigu_read"],
            "https://www.bhrigu.io/crypto-astro/btc/live?lang=ru",
        )

    def test_entry_requires_structural_primary_cta_and_snapshot_timestamp(self) -> None:
        timestamp = "2026-08-03T03:20:57Z"
        result = self.fetch_result(
            '<title>BTC Field Read</title>'
            f'<main data-source-generated-at="{timestamp}">'
            '<a href="/crypto-astro/btc/live?lang=ru" '
            'data-primary-btc-change-question="true">'
            'Спросить, что изменилось в Bitcoin</a>'
            "</main>"
        )
        assertions = mod.verify_current_bhrigu_entry(result)
        self.assertTrue(all(assertions.values()))
        self.assertTrue(assertions["current_primary_cta_present"])
        self.assertEqual(mod._entry_snapshot_timestamp, timestamp)

    def test_entry_rejects_copy_only_without_structural_marker(self) -> None:
        timestamp = "2026-08-03T03:20:57Z"
        result = self.fetch_result(
            '<title>BTC Field Read</title>'
            f'<main data-source-generated-at="{timestamp}">'
            '<a href="/crypto-astro/btc/live?lang=ru">Открыть BTC Field</a>'
            "</main>"
        )
        with self.assertRaises(mod.base.ProofFailure) as ctx:
            mod.verify_current_bhrigu_entry(result)
        self.assertEqual(ctx.exception.reason_code, "BHRIGU_ENTRY_ASSERTION_FAILED")

    def test_entry_rejects_legacy_cta(self) -> None:
        timestamp = "2026-08-03T03:20:57Z"
        result = self.fetch_result(
            '<title>BTC Field Read</title>'
            f'<main data-source-generated-at="{timestamp}">'
            '<a href="/crypto-astro/btc/live?lang=ru" '
            'data-primary-btc-change-question="true">Start free dialogue</a>'
            "</main>"
        )
        with self.assertRaises(mod.base.ProofFailure) as ctx:
            mod.verify_current_bhrigu_entry(result)
        self.assertEqual(ctx.exception.reason_code, "BHRIGU_ENTRY_ASSERTION_FAILED")

    def test_live_requires_same_snapshot_as_entry(self) -> None:
        timestamp = "2026-08-03T03:20:57Z"
        entry = self.fetch_result(
            '<title>BTC Field Read</title>'
            f'<main data-source-generated-at="{timestamp}">'
            '<a href="/crypto-astro/btc/live?lang=ru" '
            'data-primary-btc-change-question="true">'
            'Спросить, что изменилось в Bitcoin</a>'
            "</main>"
        )
        mod.verify_current_bhrigu_entry(entry)

        live = self.fetch_result(
            '<meta name="btc-live-dialogue" '
            'content="semantic-route-graph-v0-1">'
            '<main data-live-dialogue="btc-cosmographer-route-v0-1">'
            f'<span data-market-snapshot-generated-at>{timestamp}</span>'
            "</main>"
        )
        assertions = mod.verify_current_bhrigu_live(
            live, expected_timestamp=timestamp
        )
        self.assertTrue(all(assertions.values()))
        self.assertTrue(assertions["entry_and_live_snapshot_identity_match"])

    def test_live_rejects_entry_timestamp_mismatch(self) -> None:
        entry_timestamp = "2026-08-03T03:20:56Z"
        expected_timestamp = "2026-08-03T03:20:57Z"
        entry = self.fetch_result(
            '<title>BTC Field Read</title>'
            f'<main data-source-generated-at="{entry_timestamp}">'
            '<a href="/crypto-astro/btc/live?lang=ru" '
            'data-primary-btc-change-question="true">'
            'Спросить, что изменилось в Bitcoin</a>'
            "</main>"
        )
        mod.verify_current_bhrigu_entry(entry)

        live = self.fetch_result(
            '<meta name="btc-live-dialogue" '
            'content="semantic-route-graph-v0-1">'
            '<main data-live-dialogue="btc-cosmographer-route-v0-1">'
            f'<span data-market-snapshot-generated-at>{expected_timestamp}</span>'
            "</main>"
        )
        with self.assertRaises(mod.base.ProofFailure) as ctx:
            mod.verify_current_bhrigu_live(
                live, expected_timestamp=expected_timestamp
            )
        self.assertEqual(ctx.exception.reason_code, "BHRIGU_LIVE_ASSERTION_FAILED")


if __name__ == "__main__":
    unittest.main()
