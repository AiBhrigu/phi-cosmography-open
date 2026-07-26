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

    def test_single_timestamp_sourcecopy_patch(self):
        source = '''#!/usr/bin/env python3
TARGET_BRANCH = "feature/crypto-astro-all-module-static-refresh-v0-1"

def now_iso():
    return "2030-01-02T03:04:05Z"

def main():
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "status": "HOLD",
    }
    proof = {
        "generated_at_utc": now_iso(),
    }
    try:
        generated_at = now_iso()
        return report, proof, generated_at
    except Exception:
        raise
'''
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary = root / "primary.py"
            primary.write_text(source, encoding="utf-8")
            target = compat.prepare_hardened_primary(primary, root / "working")
            rendered = target.read_text(encoding="utf-8")

        self.assertEqual(rendered.count("generation_timestamp = now_iso()"), 1)
        self.assertIn('"generated_at_utc": generation_timestamp,', rendered)
        self.assertIn("generated_at = generation_timestamp", rendered)
        self.assertNotIn('"generated_at_utc": now_iso(),', rendered)
        self.assertNotIn("generated_at = now_iso()", rendered)

    def test_current_public_timestamp_constellation_exact(self):
        data = self.repo / "site/crypto-astro/data"
        snapshot = json.loads((data / "crypto_astro_snapshot.public.json").read_text(encoding="utf-8"))
        proof = json.loads((data / "crypto_astro_snapshot_proof.public.json").read_text(encoding="utf-8"))
        bindings = json.loads((data / "crypto_astro_module_bindings.public.json").read_text(encoding="utf-8"))
        registry = json.loads((data / "crypto_astro_snapshot_registry.public.json").read_text(encoding="utf-8"))
        delta = json.loads((data / "crypto_astro_snapshot_delta.public.json").read_text(encoding="utf-8"))
        market = json.loads((data / "market_field_snapshot.public.v0_1.json").read_text(encoding="utf-8"))
        scoring = json.loads((data / "scoring_snapshot.public.json").read_text(encoding="utf-8"))
        expected = snapshot["generated_at_utc"]
        constellation = {
            "snapshot": expected,
            "proof": proof["generated_at_utc"],
            "bindings": bindings["generated_at_utc"],
            "registry_current": registry["current"]["generated_at_utc"],
            "registry_proof": registry["current"]["proof_generated_at_utc"],
            "registry_generated": registry["registry_generated_at_utc"],
            "delta": delta["generated_at_utc"],
            "market_field": market["updated_at_utc"],
            "scoring": scoring["generated_at_utc"],
        }
        self.assertEqual(set(constellation.values()), {expected}, constellation)

    def test_generated_output_timestamp_gate(self):
        report = {}
        self.assertTrue(compat.validate_generation_timestamp_contract(self.repo, report), report)
        self.assertEqual(report["validation"]["single_generation_timestamp"], "PASS")

    def test_current_surface_bindings_patch_exactly_once(self):
        snapshot = copy.deepcopy(self.snapshot)
        snapshot["generated_at_utc"] = "2030-01-02T03:04:05Z"
        snapshot["market_reality"]["btc_dominance_pct"] = 67.89
        snapshot["field_output"]["market_field_score"] = 77
        snapshot["field_output"]["regime_label"] = "Guarded Rotation"
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
                "timestamp:hero_trust", "btc_hub:field_aria",
                "field:score_orb", "field:barometer_copy",
                "sample:ton_visual_score", "sample:icp_visual_score",
                "sample:ton_visual_24h", "sample:icp_visual_24h",
                "sample:ton_score", "sample:ton_24h", "sample:ton_30d", "sample:ton_rank",
                "sample:icp_score", "sample:icp_24h", "sample:icp_30d", "sample:icp_rank",
            ):
                self.assertEqual(counts.get(key), 1, key)
            self.assertEqual(report["validation"]["html_required_missing"], [])
            self.assertIn("rail:eth-anchor", report["validation"]["html_superseded_bindings"])

            rendered = target.read_text(encoding="utf-8")
            self.assertIn('Snapshot · 2030-01-02 03:04 UTC<br/>', rendered)
            self.assertIn('aria-label="BTC current field. BTC dominance is 67.9 percent.', rendered)
            self.assertIn('aria-label="Market Field Score 77 out of 100">77</div>', rendered)
            self.assertIn('<h3>Guarded Rotation</h3>', rendered)
            self.assertIn('Market Field Score: 77 / 100<br/>Observed state: Guarded Rotation', rendered)
            self.assertIn('style="width:64.2%"></i></div><span class="visual-value-v0-1">64.25', rendered)
            self.assertIn('<span>24h TON</span><strong class="visual-value-v0-1">1.23%</strong>', rendered)
            self.assertIn('<span>30d</span><strong class="distributed-value-v0-1">-4.56%</strong>', rendered)
            self.assertIn('<span>Rank</span><strong class="distributed-value-v0-1">42</strong>', rendered)


if __name__ == "__main__":
    unittest.main()
