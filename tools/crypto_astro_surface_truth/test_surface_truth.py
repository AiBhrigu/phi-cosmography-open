import tempfile
import unittest
from pathlib import Path

from surface_truth import (
    build_sha256_manifest,
    canonicalize_anchor_map,
    normalize_text,
    sha256_text,
    stable_json,
)


class SurfaceTruthUnitTests(unittest.TestCase):
    def test_normalize_text(self):
        self.assertEqual(normalize_text("  BTC\n  field\tread  "), "BTC field read")

    def test_sha256_is_deterministic(self):
        self.assertEqual(sha256_text("x"), sha256_text("x"))
        self.assertNotEqual(sha256_text("x"), sha256_text("y"))

    def test_stable_json_sorts_keys(self):
        rendered = stable_json({"b": 1, "a": 2})
        self.assertLess(rendered.index('"a"'), rendered.index('"b"'))

    def test_anchor_map_is_normalized_and_sorted(self):
        rows = [
            {"href": "https://b.example", "text": " B \n route "},
            {"href": "https://a.example", "text": "A route"},
        ]
        self.assertEqual(
            canonicalize_anchor_map(rows),
            [
                {"href": "https://a.example", "text": "A route"},
                {"href": "https://b.example", "text": "B route"},
            ],
        )

    def test_manifest_excludes_itself_and_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("a", encoding="utf-8")
            first = build_sha256_manifest(root)
            second = build_sha256_manifest(root)
            self.assertEqual(first, second)
            manifest = (root / "sha256_manifest.txt").read_text(encoding="utf-8")
            self.assertIn("a.txt", manifest)
            self.assertNotIn("sha256_manifest.txt", manifest)


if __name__ == "__main__":
    unittest.main()
