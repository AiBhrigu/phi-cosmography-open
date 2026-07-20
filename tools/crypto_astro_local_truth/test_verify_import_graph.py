from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from verify_import_graph import verify


class VerifyImportGraphTests(unittest.TestCase):
    def make_root(self, *, direct_system: bool = True, import_count: int = 1) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "site/crypto-astro").mkdir(parents=True)
        (root / "site/theme").mkdir(parents=True)

        links = []
        if direct_system:
            links.append('<link href="../theme/system.css" rel="stylesheet"/>')
        links.extend(
            [
                '<link href="../theme/phi_theme.css" rel="stylesheet"/>',
                '<link href="../theme/crypto_astro_surface.css" rel="stylesheet"/>',
            ]
        )
        (root / "site/crypto-astro/index.html").write_text("\n".join(links), encoding="utf-8")
        (root / "site/theme/phi_theme.css").write_text(
            "\n".join(["@import url('./system.css');"] * import_count),
            encoding="utf-8",
        )
        (root / "site/theme/system.css").write_text(":root{}\n", encoding="utf-8")
        (root / "site/theme/crypto_astro_surface.css").write_text("body{}\n", encoding="utf-8")
        return root

    def test_before_normalization_passes_with_two_effective_routes(self) -> None:
        report = verify(self.make_root(), expect_direct_system=True)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["measurements"]["effective_system_css_routes"], 2)

    def test_after_normalization_passes_with_one_effective_route(self) -> None:
        report = verify(self.make_root(direct_system=False), expect_direct_system=False)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["measurements"]["effective_system_css_routes"], 1)

    def test_missing_phi_import_fails_closed(self) -> None:
        report = verify(self.make_root(direct_system=False, import_count=0), expect_direct_system=False)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("phi_imports_system_once", report["failures"])

    def test_duplicate_phi_import_fails_closed(self) -> None:
        report = verify(self.make_root(direct_system=False, import_count=2), expect_direct_system=False)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("phi_imports_system_once", report["failures"])


if __name__ == "__main__":
    unittest.main()
