from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extract_inline_css import (
    CSS_PATH,
    HTML_PATH,
    LEGACY_LINK,
    ExtractionError,
    apply,
    extract_inline_css,
)


FIXTURE = """<!doctype html>
<html>
<head>
<link href="../theme/phi_theme.css" rel="stylesheet"/>
<style>
.a { color:red; }
</style>
</head>
<body>
<p>Hello</p>
<style>.b{display:grid}</style>
</body>
</html>
"""


class ExtractionTests(unittest.TestCase):
    def test_extracts_in_order_and_preserves_block_content(self) -> None:
        transformed, css, count = extract_inline_css(FIXTURE)
        self.assertEqual(count, 2)
        self.assertEqual(css, "\n.a { color:red; }\n.b{display:grid}\n")
        self.assertNotIn("<style", transformed.lower())
        self.assertEqual(transformed.count(LEGACY_LINK), 1)
        self.assertLess(
            transformed.index("../theme/phi_theme.css"),
            transformed.index("../theme/crypto_astro_inline_legacy.css"),
        )

    def test_apply_is_idempotent_after_first_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / HTML_PATH
            css = root / CSS_PATH
            html.parent.mkdir(parents=True)
            html.write_text(FIXTURE, encoding="utf-8")
            apply(html, css)
            first_html = html.read_text(encoding="utf-8")
            first_css = css.read_text(encoding="utf-8")
            self.assertEqual(apply(html, css), 0)
            self.assertEqual(html.read_text(encoding="utf-8"), first_html)
            self.assertEqual(css.read_text(encoding="utf-8"), first_css)

    def test_requires_single_insertion_anchor(self) -> None:
        with self.assertRaises(ExtractionError):
            extract_inline_css(FIXTURE.replace("../theme/phi_theme.css", "../theme/other.css"))

    def test_rejects_empty_stylesheet(self) -> None:
        with self.assertRaises(ExtractionError):
            extract_inline_css(
                '<link href="../theme/phi_theme.css" rel="stylesheet"/><style>   </style>'
            )


if __name__ == "__main__":
    unittest.main()
