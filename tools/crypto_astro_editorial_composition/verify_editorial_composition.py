#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = ROOT / "site/crypto-astro/index.html"

CHAPTERS = [
    'data-editorial-chapter="orientation"',
    'data-editorial-chapter="what-changed"',
    'data-editorial-chapter="btc-field"',
    'data-editorial-chapter="wider-market"',
    'data-editorial-chapter="trust-access"',
]
NAV_TARGETS = ["#surface", "#what-changed", "#btc-phi-cycle-hub", "#market", "#trust-access"]
PRIMARY_HREF = "https://www.bhrigu.io/crypto-astro/btc"
REQUIRED_VALUES = [
    "$2.287T",
    "$40.71B",
    "56.5%",
    "13.5%",
    "34.5%",
    "39.9%",
    "9.8%",
    "66.3%",
    "$75.55B",
]
FORBIDDEN_FIRST_LEVEL = [
    "Public Page Live",
    "Mobile route · source-bound surface",
    "Enter BTC Field Read",
    "Request private review",
    "Request Depth Research",
    "Request manual review",
    "Bias: Neutral → Bullish",
    "A/E · prepared field membranes",
    "M · dominance/liquidity vector",
    "C/T · bounded context membrane",
]


def visible_words(value: str) -> int:
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9’'/-]*", value))


def verify(html: str) -> dict[str, object]:
    failures: list[str] = []
    positions = [html.find(marker) for marker in CHAPTERS]
    if any(position < 0 for position in positions):
        failures.append("five_editorial_chapters_present")
    elif positions != sorted(positions):
        failures.append("five_editorial_chapters_ordered")

    nav_match = re.search(r'<nav class="crypto-astro-primary-nav".*?</nav>', html, flags=re.S)
    nav_targets: list[str] = []
    if nav_match:
        nav_targets = re.findall(r'href="(#[^"]+)"', nav_match.group(0))
    if nav_targets == ["#surface"] + NAV_TARGETS:
        nav_targets = nav_targets[1:]
    if nav_targets != NAV_TARGETS:
        failures.append("primary_navigation_exact")

    proof_index = html.find('<details id="proof"')
    if proof_index < 0:
        failures.append("proof_depth_appendix_present")
        first_level = html
    else:
        first_level = html[:proof_index]

    primary_ctas = re.findall(
        rf'<a[^>]+href="{re.escape(PRIMARY_HREF)}"[^>]*>.*?Ask one BTC field question.*?</a>',
        first_level,
        flags=re.S,
    )
    if len(primary_ctas) != 2:
        failures.append("primary_cta_two_consistent_placements")

    if first_level.count('href="https://www.bhrigu.io/access"') != 1:
        failures.append("one_first_level_research_access_route")
    if first_level.count('href="#proof"') != 1:
        failures.append("one_first_level_proof_route")

    if "Previous verified snapshot is not yet available." not in first_level:
        failures.append("what_changed_fail_closed_fallback")
    if first_level.count("Research context only. No trading signal, forecast, price target, or investment advice.") != 1:
        failures.append("one_global_boundary_seal")

    for phrase in FORBIDDEN_FIRST_LEVEL:
        if phrase in first_level:
            failures.append(f"forbidden_first_level:{phrase}")

    if "market-status-rail" in first_level:
        failures.append("market_status_rail_removed")
    if "CRYPTO_ASTRO_PUBLIC_SAMPLE_WEB_PANEL_v0_1:BEGIN" in first_level:
        failures.append("sample_panel_moved_to_proof")
    if "CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1:BEGIN" in first_level:
        failures.append("internal_support_modules_moved_to_proof")
    if 'class="trend-memory"' in first_level:
        failures.append("legacy_trend_memory_removed")
    if 'class="btc-boundary-v1"' in first_level:
        failures.append("duplicate_btc_boundary_removed")

    for value in REQUIRED_VALUES:
        if value not in html:
            failures.append(f"required_value_preserved:{value}")

    ids = re.findall(r'\sid="([^"]+)"', html)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        failures.append(f"duplicate_ids:{','.join(duplicates)}")

    word_count = visible_words(first_level)
    if word_count < 650 or word_count > 1200:
        failures.append("first_level_word_budget_650_1200")

    return {
        "schema_version": "crypto_astro_editorial_composition_report_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "measurements": {
            "chapter_count": len([position for position in positions if position >= 0]),
            "navigation_targets": nav_targets,
            "primary_cta_count": len(primary_ctas),
            "first_level_research_access_count": first_level.count('href="https://www.bhrigu.io/access"'),
            "first_level_proof_link_count": first_level.count('href="#proof"'),
            "first_level_word_count": word_count,
            "proof_depth_present": proof_index >= 0,
            "duplicate_ids": duplicates,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", type=Path, default=HTML_PATH)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = verify(args.html.read_text(encoding="utf-8"))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
