#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import crypto_astro_static_refresh_hardened_v0_5 as compat


class CurrentSurfaceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[2]
        cls.html = (cls.repo / "site/crypto-astro/index.html").read_text(encoding="utf-8")
        cls.snapshot = json.loads(
            (cls.repo / "site/crypto-astro/data/crypto_astro_snapshot.public.json").read_text(encoding="utf-8")
        )

    def test_locked_core_blob(self):
        self.assertEqual(compat.git_blob_sha(compat.CORE_PATH), compat.EXPECTED_CORE_BLOB_SHA)

    def test_current_surface_bindings_patch_exactly_once(self):
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["field_output"]["market_field_score"] = 77
        ton = snapshot["public_samples"]["assets"]["TON"]
        icp = snapshot["public_samples"]["assets"]["ICP"]
        ton.update(score=64.25, market_24h_change_pct=1.23, market_30d_change_pct=-4.56, market_cap_rank=21)
        icp.update(score=41.5, market_24h_change_pct=-2.34, market_30d_change_pct=5.67, market_cap_rank=42)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "site/crypto-astro/index.html"
            target.parent.mkdir(parents=True)
            target.write_text(self.html, encoding="utf-8")
            patch = compat.patch_html(root, snapshot)
            report = {}
            self.assertTrue(compat.validate_html_counts(patch, report), report)
            counts = patch["replace_counts"]
            for key in (
                "field:score_orb",
                "sample:ton_visual_score", "sample:icp_visual_score",
                "sample:ton_visual_24h", "sample:icp_visual_24h",
                "sample:ton_score", "sample:ton_24h", "sample:ton_30d", "sample:ton_rank",
                "sample:icp_score", "sample:icp_24h", "sample:icp_30d", "sample:icp_rank",
            ):
                self.assertEqual(counts.get(key), 1, key)
            self.assertEqual(report["validation"]["html_required_missing"], [])
            self.assertIn("rail:eth-anchor", report["validation"]["html_superseded_bindings"])

            rendered = target.read_text(encoding="utf-8")
            self.assertIn('aria-label="Market Field Score 77 out of 100">77</div>', rendered)
            self.assertIn('style="width:64.2%"></i></div><span class="visual-value-v0-1">64.25', rendered)
            self.assertIn('<span>24h TON</span><strong class="visual-value-v0-1">1.23%</strong>', rendered)
            self.assertIn('<span>30d</span><strong class="distributed-value-v0-1">-4.56%</strong>', rendered)
            self.assertIn('<span>Rank</span><strong class="distributed-value-v0-1">42</strong>', rendered)


if __name__ == "__main__":
    unittest.main()
