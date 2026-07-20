#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HTML_PATH = Path("site/crypto-astro/index.html")
MANIFEST_PATH = Path("site/theme/crypto_astro/css_order_manifest.json")
LEGACY_PATH = Path("site/theme/crypto_astro_inline_legacy.css")
GENERATED_PATH = Path("site/theme/crypto_astro_surface.css")
GEOMETRY_EXTENSION_PATH = Path("site/theme/crypto_astro/extensions/09_geometry_truth_repair.css")

FORBIDDEN_HTML = {
    "market_cap_unbound_rail": 'class="metric-rail cap"',
    "volume_unbound_rail": 'class="metric-rail volume"',
    "composition_ring": 'class="composition-ring',
    "composition_flow": 'class="composition-flow"',
    "barometer_ring": 'class="barometer-ring',
    "barometer_arc": 'class="barometer-arc',
    "astromodule_numeric_fill": 'class="astromodule-polish-fill"',
    "astromodule_unsupported_score": "63 / 100",
    "astromodule_numeric_orb": 'class="astromodule-right-balance__number"',
    "astromodule_numeric_track": 'class="astromodule-right-balance__track"',
    "sample_temporal_unsupported": ">49.83<",
    "sample_phase_unsupported": ">48.81<",
    "sample_stability_unsupported": ">71.46<",
    "sample_confirmation_unbound": 'style="width:64%"',
    "trend_memory_placeholder": 'class="trend-memory"',
    "gram_negative_24h_bar": 'style="width:19.9%"',
    "gram_negative_30d_bar": 'style="width:71.8%"',
    "gram_rank_bar": 'style="width:77.0%"',
    "icp_negative_24h_bar": 'style="width:20.0%"',
    "icp_negative_30d_bar": 'style="width:36.8%"',
    "icp_rank_bar": 'style="width:38.0%"',
}

REQUIRED_COUNTS = {
    "decorative_context_marks": ('class="metric-context-mark" data-geometry-truth="decorative"', 2),
    "data_bound_market_rails": ('class="metric-rail dominance" data-geometry-truth="data-bound"', 1),
    "data_bound_stable_rail": ('class="metric-rail stable" data-geometry-truth="data-bound"', 1),
    "semantic_composition": ('class="composition-screen" data-geometry-truth="semantic"', 1),
    "semantic_composition_field": ('class="composition-semantic-field"', 1),
    "semantic_barometer": ('class="barometer-visual" data-geometry-truth="semantic"', 1),
    "semantic_barometer_frame": ('class="barometer-semantic-frame"', 1),
    "data_bound_market_score": ('class="score-orb field-gauge" data-geometry-truth="data-bound"', 1),
    "data_bound_visual_score_rows": ('class="visual-row-v0-1" data-geometry-truth="data-bound"', 2),
    "text_only_visual_rows": ('class="visual-row-v0-1 visual-row-text-v0-1"', 2),
    "text_only_sample_rows": ('class="distributed-row-v0-1 distributed-row-text-v0-1"', 6),
    "data_bound_sample_score_rows": ('data-geometry-truth="data-bound"><span>Score</span>', 2),
    "sample_context_status": ('class="sample-context-status-v0-1"', 2),
}

REQUIRED_LITERALS = {
    "btc_dominance_preserved": "BTC Dominance 56.5%",
    "stable_share_preserved": "Stablecoin Share 13.5%",
    "market_field_score_preserved": "Market Field Score 61 out of 100",
    "gram_score_preserved": ">53.01<",
    "icp_score_preserved": ">52.46<",
    "gram_negative_24h_preserved": ">-2.67%<",
    "gram_negative_30d_preserved": ">-9.93%<",
    "icp_negative_24h_preserved": ">-1.01%<",
    "icp_negative_30d_preserved": ">-4.63%<",
}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def join_values(values: list[bytes]) -> bytes:
    output: list[bytes] = []
    for value in values:
        output.append(value)
        if value and not value.endswith((b"\n", b"\r")):
            output.append(b"\n")
    return b"".join(output)


def scan_html(html: str) -> tuple[dict[str, bool], dict[str, int]]:
    checks: dict[str, bool] = {}
    counts: dict[str, int] = {}
    for name, literal in FORBIDDEN_HTML.items():
        count = html.count(literal)
        counts[name] = count
        checks[f"forbidden_absent:{name}"] = count == 0
    for name, (literal, expected) in REQUIRED_COUNTS.items():
        count = html.count(literal)
        counts[name] = count
        checks[f"required_count:{name}"] = count == expected
    for name, literal in REQUIRED_LITERALS.items():
        count = html.count(literal)
        counts[name] = count
        checks[f"required_present:{name}"] = count >= 1

    old_astromodule = html.count('class="astromodule-polish-rails astromodule-semantic-bands" data-geometry-truth="semantic"')
    new_astromodule = html.count('class="market-card gold editorial-astromodule-v0-1"')
    counts["semantic_astromodule_context"] = old_astromodule + new_astromodule
    checks["required_form:semantic_astromodule_context"] = old_astromodule + new_astromodule == 1

    old_categorical = html.count('class="astromodule-right-balance__band"')
    new_categorical = html.count('class="editorial-astromodule-v0-1__states"')
    counts["categorical_astromodule_state"] = old_categorical + new_categorical
    checks["required_form:categorical_astromodule_state"] = old_categorical + new_categorical == 1

    old_memory = html.count('class="trend-memory-unavailable" data-geometry-truth="semantic"')
    new_memory = html.count('data-what-changed-status="unavailable"')
    counts["verified_change_memory_unavailable"] = old_memory + new_memory
    checks["required_form:verified_change_memory_unavailable"] = old_memory + new_memory == 1

    fallback_count = html.count("Previous verified snapshot is not available.") + html.count(
        "Previous verified snapshot is not yet available."
    )
    counts["previous_snapshot_fallback"] = fallback_count
    checks["required_present:previous_snapshot_fallback"] = fallback_count >= 1

    checks["gram_score_width_bound"] = 'style="width:53.0%"' in html and ">53.01<" in html
    checks["icp_score_width_bound"] = 'style="width:52.5%"' in html and ">52.46<" in html
    return checks, counts


def verify(root: Path) -> dict[str, Any]:
    html = (root / HTML_PATH).read_text(encoding="utf-8")
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    legacy = (root / LEGACY_PATH).read_bytes()
    generated = (root / GENERATED_PATH).read_bytes()

    checks, counts = scan_html(html)
    extensions = manifest.get("extensions", [])
    checks["extensions_declared"] = isinstance(extensions, list) and len(extensions) >= 1

    ordered_extension_bytes: list[bytes] = []
    geometry_entry: dict[str, Any] | None = None
    extension_measurements: list[dict[str, Any]] = []
    if checks["extensions_declared"]:
        for position, entry in enumerate(extensions, 1):
            path = root / str(entry.get("path") or "")
            exists = path.is_file()
            checks[f"extension_{position}:path_exists"] = exists
            checks[f"extension_{position}:order_bound"] = entry.get("order") == position
            if exists:
                value = path.read_bytes()
                ordered_extension_bytes.append(value)
                checks[f"extension_{position}:byte_count_bound"] = entry.get("byte_count") == len(value)
                checks[f"extension_{position}:sha256_bound"] = entry.get("sha256") == sha256(value)
                extension_measurements.append(
                    {
                        "order": position,
                        "path": str(entry.get("path")),
                        "role": str(entry.get("role")),
                        "byte_count": len(value),
                        "sha256": sha256(value),
                    }
                )
            if entry.get("path") == str(GEOMETRY_EXTENSION_PATH):
                geometry_entry = entry

    checks["geometry_extension_declared_once"] = sum(
        1 for entry in extensions if entry.get("path") == str(GEOMETRY_EXTENSION_PATH)
    ) == 1
    geometry_extension = (root / GEOMETRY_EXTENSION_PATH).read_bytes()
    checks["geometry_extension_role_bound"] = bool(geometry_entry) and geometry_entry.get("role") == "geometry_truth_repair"
    checks["geometry_extension_order_bound"] = bool(geometry_entry) and geometry_entry.get("order") == 1
    checks["geometry_extension_byte_count_bound"] = bool(geometry_entry) and geometry_entry.get("byte_count") == len(geometry_extension)
    checks["geometry_extension_sha256_bound"] = bool(geometry_entry) and geometry_entry.get("sha256") == sha256(geometry_extension)
    checks["generated_bundle_matches_base_plus_extensions"] = generated == join_values([legacy] + ordered_extension_bytes)

    geometry_text = geometry_extension.decode("utf-8")
    checks["geometry_extension_has_truth_marker"] = "CRYPTO_ASTRO_GEOMETRY_TRUTH_REPAIR_v0_1:BEGIN" in geometry_text
    checks["geometry_extension_has_no_animation"] = "animation:" not in geometry_text and "@keyframes" not in geometry_text

    failures = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "crypto_astro_geometry_truth_report_v0_2",
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "counts": counts,
        "failures": failures,
        "measurements": {
            "extension_count": len(extensions) if isinstance(extensions, list) else 0,
            "extensions": extension_measurements,
            "geometry_extension_bytes": len(geometry_extension),
            "geometry_extension_sha256": sha256(geometry_extension),
            "generated_bundle_bytes": len(generated),
            "generated_bundle_sha256": sha256(generated),
            "data_bound_geometry_count": html.count('data-geometry-truth="data-bound"'),
            "semantic_geometry_count": html.count('data-geometry-truth="semantic"'),
            "decorative_geometry_count": html.count('data-geometry-truth="decorative"'),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = verify(args.root.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
