#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED = {
    "btc_gravity_pct": "+0.28 percentage points",
    "stablecoin_share_pct": "-0.18 percentage points",
    "alt_breadth_24h_pct": "+8.0 percentage points",
    "alt_breadth_7d_pct": "-1.3 percentage points",
    "market_field_score": "+1.0 points",
    "regime_label": "Unchanged",
}
EXPECTED_TIMESTAMPS = (
    "2026-07-19T18:26:56Z",
    "2026-07-12T22:05:46Z",
)


def verify(repo: Path) -> dict:
    html_path = repo / "site/crypto-astro/index.html"
    source = html_path.read_text(encoding="utf-8")
    failures: list[str] = []
    if source.count('data-what-changed-status="partial-comparable"') != 1:
        failures.append("partial-comparable status count")
    if source.count('data-source-contract="crypto_astro_snapshot_delta_public_v0_1"') != 1:
        failures.append("source contract count")
    for key, display in EXPECTED.items():
        if source.count(f'data-metric="{key}"') != 1:
            failures.append(f"{key} count")
        if source.count(display) != 1:
            failures.append(f"{key} display")
    for timestamp in EXPECTED_TIMESTAMPS:
        if timestamp not in source:
            failures.append(f"full timestamp missing: {timestamp}")
    for code in ("METHODOLOGY_MISMATCH", "DEPENDENCY_METHODOLOGY_MISMATCH"):
        if source.count(f"<code>{code}</code>") != 1:
            failures.append(f"{code} count")
    section = re.search(r'<section id="what-changed".*?</section>', source, re.S)
    if section is None:
        failures.append("What Changed section missing")
    else:
        lowered = section.group(0).lower()
        for term in ("fetch(", "xmlhttprequest", "websocket(", "eventsource("):
            if term in lowered:
                failures.append(f"forbidden browser runtime: {term}")
    if source.count('href="https://www.bhrigu.io/crypto-astro/btc"') != 2:
        failures.append("BTC CTA count drift")
    if source.count('style="--btc-dominance:56.5%;"') != 1:
        failures.append("BTC geometry drift")
    if source.count('../theme/crypto_astro_what_changed.css') != 1:
        failures.append("CSS link count")
    result = {
        "node": "CRYPTO_ASTRO_PR_07_WHAT_CHANGED_UI_BINDING_IMPLEMENTATION_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "html_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),
        "comparable_metric_count": 6,
        "unavailable_metric_count": 2,
        "browser_fetch": False,
        "refresh_pipeline_integration": False,
    }
    if failures:
        raise AssertionError(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--report")
    args = parser.parse_args()
    result = verify(Path(args.repo).resolve())
    text = json.dumps(result, indent=2) + "\n"
    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
