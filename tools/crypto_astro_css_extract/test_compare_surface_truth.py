from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from compare_surface_truth import compare_boxes, compare_screenshot


class ComparisonTests(unittest.TestCase):
    def test_bounding_box_tolerance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base"
            head = root / "head"
            base.mkdir()
            head.mkdir()
            (base / "bounding-box-report.json").write_text(
                json.dumps({".x": {"x": 1, "y": 2, "width": 100, "height": 40}}),
                encoding="utf-8",
            )
            (head / "bounding-box-report.json").write_text(
                json.dumps({".x": {"x": 1.5, "y": 2, "width": 100.5, "height": 40}}),
                encoding="utf-8",
            )
            self.assertEqual(compare_boxes(base, head), [])

    def test_screenshot_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "left.png"
            right = root / "right.png"
            Image.new("RGBA", (10, 10), (1, 2, 3, 255)).save(left)
            Image.new("RGBA", (10, 10), (1, 2, 3, 255)).save(right)
            ratio, delta = compare_screenshot(left, right)
            self.assertEqual(ratio, 0)
            self.assertEqual(delta, 0)


if __name__ == "__main__":
    unittest.main()
