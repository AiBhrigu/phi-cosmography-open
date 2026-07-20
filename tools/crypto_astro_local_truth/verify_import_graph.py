#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SYSTEM_LINK = '<link href="../theme/system.css" rel="stylesheet"/>'
PHI_LINK = '<link href="../theme/phi_theme.css" rel="stylesheet"/>'
SURFACE_LINK = '<link href="../theme/crypto_astro_surface.css" rel="stylesheet"/>'
SYSTEM_IMPORT_RE = re.compile(r"@import\s+url\((?:['\"])?\./system\.css(?:['\"])?\)\s*;")


def verify(root: Path, expect_direct_system: bool) -> dict[str, object]:
    html_path = root / "site/crypto-astro/index.html"
    phi_path = root / "site/theme/phi_theme.css"
    system_path = root / "site/theme/system.css"
    surface_path = root / "site/theme/crypto_astro_surface.css"

    html = html_path.read_text(encoding="utf-8")
    phi = phi_path.read_text(encoding="utf-8")

    direct_count = html.count(SYSTEM_LINK)
    phi_count = html.count(PHI_LINK)
    surface_count = html.count(SURFACE_LINK)
    import_count = len(SYSTEM_IMPORT_RE.findall(phi))

    checks = {
        "system_css_exists": system_path.is_file(),
        "surface_css_exists": surface_path.is_file(),
        "phi_link_once": phi_count == 1,
        "surface_link_once": surface_count == 1,
        "phi_imports_system_once": import_count == 1,
        "direct_system_link_expected": direct_count == (1 if expect_direct_system else 0),
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "crypto_astro_import_graph_report_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "mode": "before_normalization" if expect_direct_system else "after_normalization",
        "checks": checks,
        "failures": failures,
        "measurements": {
            "direct_system_link_count": direct_count,
            "phi_theme_link_count": phi_count,
            "surface_link_count": surface_count,
            "phi_theme_system_import_count": import_count,
            "effective_system_css_routes": direct_count + import_count,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--mode", choices=("before", "after"), required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = verify(args.root.resolve(), expect_direct_system=args.mode == "before")
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
