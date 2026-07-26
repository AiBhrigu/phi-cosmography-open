#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from render_what_changed import SECTION_PATTERN, load_json, render


def verify(repo: Path) -> dict:
    html_path = repo / "site/crypto-astro/index.html"
    source = html_path.read_text(encoding="utf-8")
    registry = load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot_registry.public.json")
    delta = load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot_delta.public.json")
    failures: list[str] = []
    section = SECTION_PATTERN.search(source)
    expected = render(registry, delta)
    if section is None:
        failures.append("What Changed section missing")
    elif section.group(0).rstrip("\n") != expected:
        failures.append("rendered section differs from deterministic contract")
    if source.count('href="https://www.bhrigu.io/crypto-astro/btc"') != 2:
        failures.append("BTC CTA count drift")
    snapshot = load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot.public.json")
    dominance = f'{float(snapshot["market_reality"]["btc_dominance_pct"]):.1f}%'
    if source.count(f'style="--btc-dominance:{dominance};"') != 1:
        failures.append("BTC geometry drift")
    if source.count('../theme/crypto_astro_what_changed.css') != 1:
        failures.append("CSS link count")
    lowered = expected.lower()
    for term in ("fetch(", "xmlhttprequest", "websocket(", "eventsource("):
        if term in lowered:
            failures.append(f"forbidden browser runtime: {term}")
    metrics = delta["metrics"]
    unavailable = delta["unavailable_metrics"]
    for key in metrics:
        if source.count(f'data-metric="{key}"') != 1:
            failures.append(f"{key} count")
    for key, item in unavailable.items():
        if source.count(f'<code>{item["reason_code"]}</code>') != 1:
            failures.append(f"{key} unavailable reason count")
    result = {
        "node": "CRYPTO_ASTRO_REFRESH_PIPELINE_SNAPSHOT_MEMORY_BINDING_IMPLEMENTATION_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "html_sha256": hashlib.sha256(html_path.read_bytes()).hexdigest(),
        "comparison_status": delta["comparison_status"],
        "comparable_metric_count": len(metrics),
        "unavailable_metric_count": len(unavailable),
        "browser_fetch": False,
        "refresh_pipeline_integration": True,
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
