from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_css_modules import ModuleBuildError, build, join_modules


class CssModuleBuildTests(unittest.TestCase):
    def test_join_modules_preserves_order_and_safe_boundaries(self) -> None:
        self.assertEqual(join_modules([b"a{}", b"b{}\n"]), b"a{}\nb{}\n")

    def test_build_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module_a = b"a{}"
            module_b = b"b{}\n"
            bundle = join_modules([module_a, module_b])
            (root / "mods").mkdir()
            (root / "mods/a.css").write_bytes(module_a)
            (root / "mods/b.css").write_bytes(module_b)
            (root / "legacy.css").write_bytes(bundle)
            manifest = {
                "schema_version": "crypto_astro_css_order_manifest_v0_1",
                "source_base_sha": "unused",
                "source_html_path": "unused",
                "legacy_source_path": "legacy.css",
                "generated_bundle_path": "surface.css",
                "modules": [
                    {
                        "order": 1,
                        "source_style_block_index": 1,
                        "path": "mods/a.css",
                        "byte_count": len(module_a),
                        "sha256": hashlib.sha256(module_a).hexdigest(),
                    },
                    {
                        "order": 2,
                        "source_style_block_index": 2,
                        "path": "mods/b.css",
                        "byte_count": len(module_b),
                        "sha256": hashlib.sha256(module_b).hexdigest(),
                    },
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = build(root, Path("manifest.json"), write=True, verify_source_base=False)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual((root / "surface.css").read_bytes(), bundle)
            checked = build(root, Path("manifest.json"), write=False, verify_source_base=False)
            self.assertEqual(checked["bundle_sha256"], hashlib.sha256(bundle).hexdigest())

    def test_hash_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "module.css").write_bytes(b"a{}")
            (root / "legacy.css").write_bytes(b"a{}\n")
            manifest = {
                "schema_version": "crypto_astro_css_order_manifest_v0_1",
                "source_base_sha": "unused",
                "source_html_path": "unused",
                "legacy_source_path": "legacy.css",
                "generated_bundle_path": "surface.css",
                "modules": [
                    {
                        "order": 1,
                        "source_style_block_index": 1,
                        "path": "module.css",
                        "byte_count": 3,
                        "sha256": "0" * 64,
                    }
                ],
            }
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ModuleBuildError):
                build(root, Path("manifest.json"), write=True, verify_source_base=False)

    def test_stale_generated_bundle_fails_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            value = b"a{}\n"
            (root / "module.css").write_bytes(b"a{}")
            (root / "legacy.css").write_bytes(value)
            (root / "surface.css").write_bytes(b"stale")
            manifest = {
                "schema_version": "crypto_astro_css_order_manifest_v0_1",
                "source_base_sha": "unused",
                "source_html_path": "unused",
                "legacy_source_path": "legacy.css",
                "generated_bundle_path": "surface.css",
                "modules": [
                    {
                        "order": 1,
                        "source_style_block_index": 1,
                        "path": "module.css",
                        "byte_count": 3,
                        "sha256": hashlib.sha256(b"a{}").hexdigest(),
                    }
                ],
            }
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ModuleBuildError):
                build(root, Path("manifest.json"), write=False, verify_source_base=False)


if __name__ == "__main__":
    unittest.main()
