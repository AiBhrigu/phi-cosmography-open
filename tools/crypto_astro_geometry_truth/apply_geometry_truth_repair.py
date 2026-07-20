#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HTML_PATH = Path("site/crypto-astro/index.html")
MANIFEST_PATH = Path("site/theme/crypto_astro/css_order_manifest.json")
EXTENSION_PATH = Path("site/theme/crypto_astro/extensions/09_geometry_truth_repair.css")


def replace_once(value: str, old: str, new: str) -> str:
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one geometry target, found {count}: {old[:100]!r}")
    return value.replace(old, new, 1)


def main() -> int:
    html = HTML_PATH.read_text(encoding="utf-8")
    replacements = [
        (
            '<div class="market-metric" aria-label="Market Cap $2.287T"><span>Market Cap</span><strong>$2.287T</strong><div class="metric-rail cap" aria-hidden="true"><i aria-hidden="true"></i></div></div>',
            '<div class="market-metric" aria-label="Market Cap $2.287T"><span>Market Cap</span><strong>$2.287T</strong><div class="metric-context-mark" data-geometry-truth="decorative" aria-hidden="true"><i></i><i></i><i></i></div></div>',
        ),
        (
            '<div class="market-metric" aria-label="24h Volume $40.71B"><span>24h Volume</span><strong>$40.71B</strong><div class="metric-rail volume" aria-hidden="true"><i aria-hidden="true"></i></div></div>',
            '<div class="market-metric" aria-label="24h Volume $40.71B"><span>24h Volume</span><strong>$40.71B</strong><div class="metric-context-mark" data-geometry-truth="decorative" aria-hidden="true"><i></i><i></i><i></i></div></div>',
        ),
        (
            '<div class="metric-rail dominance" aria-hidden="true">',
            '<div class="metric-rail dominance" data-geometry-truth="data-bound" aria-hidden="true">',
        ),
        (
            '<div class="metric-rail stable" aria-hidden="true">',
            '<div class="metric-rail stable" data-geometry-truth="data-bound" aria-hidden="true">',
        ),
        (
            '          <div class="composition-screen" aria-label="Market composition visual field">\n            <div class="composition-ring stable" aria-hidden="true"></div>\n            <div class="composition-ring alt" aria-hidden="true"></div>\n            <div class="composition-flow" aria-hidden="true"></div>',
            '          <div class="composition-screen" data-geometry-truth="semantic" aria-label="Market composition semantic relation field">\n            <div class="composition-semantic-field" aria-hidden="true"></div>',
        ),
        (
            '          <div class="barometer-visual" aria-label="Field Membrane Barometer visual state">\n            <div class="barometer-ring temporal" aria-hidden="true"></div>\n            <div class="barometer-arc market" aria-hidden="true"></div>\n            <div class="score-orb field-gauge" role="img" aria-label="Market Field Score 61 out of 100">61</div>',
            '          <div class="barometer-visual" data-geometry-truth="semantic" aria-label="Field Membrane Barometer semantic state">\n            <div class="barometer-semantic-frame" aria-hidden="true"></div>\n            <div class="score-orb field-gauge" data-geometry-truth="data-bound" role="img" aria-label="Market Field Score 61 out of 100">61</div>',
        ),
        (
            '      <div class="astromodule-polish-rails" aria-label="Astromodule scenario component rails">\n        <div class="astromodule-polish-rail"><span>Timing</span><span class="astromodule-polish-track"><span class="astromodule-polish-fill" style="width: 72%"></span></span></div>\n        <div class="astromodule-polish-rail"><span>Stability</span><span class="astromodule-polish-track"><span class="astromodule-polish-fill" style="width: 58%"></span></span></div>\n        <div class="astromodule-polish-rail"><span>Corridor</span><span class="astromodule-polish-track"><span class="astromodule-polish-fill" style="width: 64%"></span></span></div>\n      </div>',
            '      <div class="astromodule-polish-rails astromodule-semantic-bands" data-geometry-truth="semantic" aria-label="Astromodule categorical scenario context">\n        <div class="astromodule-polish-rail"><span>Timing</span><strong>Context</strong></div>\n        <div class="astromodule-polish-rail"><span>Stability</span><strong>State</strong></div>\n        <div class="astromodule-polish-rail"><span>Corridor</span><strong>Bounded</strong></div>\n      </div>',
        ),
        (
            '<div class="score-main-v0-1">MEDIUM <span>63 / 100</span></div>',
            '<div class="score-main-v0-1">MEDIUM <span>public context band</span></div>',
        ),
        (
            '  <div class="astromodule-right-balance__score">\n    <div class="astromodule-right-balance__number">63</div>\n    <div>\n      <div class="astromodule-right-balance__track"><span class="astromodule-right-balance__fill"></span></div>\n      <div class="astromodule-right-balance__meta">medium pressure band · static proof</div>\n    </div>\n  </div>',
            '  <div class="astromodule-right-balance__score astromodule-right-balance__score--categorical" data-geometry-truth="semantic">\n    <div class="astromodule-right-balance__band">Medium</div>\n    <div class="astromodule-right-balance__meta">medium pressure band · static proof</div>\n  </div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>Score</span><div class="distributed-track-v0-1"><i style="width:53.0%"></i></div><span class="distributed-value-v0-1">53.01</span></div>',
            '  <div class="distributed-row-v0-1" data-geometry-truth="data-bound"><span>Score</span><div class="distributed-track-v0-1"><i style="width:53.0%"></i></div><span class="distributed-value-v0-1">53.01</span></div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>24h</span><div class="distributed-track-v0-1"><i style="width:19.9%"></i></div><span class="distributed-value-v0-1">-2.67%</span></div>',
            '  <div class="distributed-row-v0-1 distributed-row-text-v0-1"><span>24h</span><strong class="distributed-value-v0-1">-2.67%</strong></div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>30d</span><div class="distributed-track-v0-1"><i style="width:71.8%"></i></div><span class="distributed-value-v0-1">-9.93%</span></div>',
            '  <div class="distributed-row-v0-1 distributed-row-text-v0-1"><span>30d</span><strong class="distributed-value-v0-1">-9.93%</strong></div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>Rank</span><div class="distributed-track-v0-1"><i style="width:77.0%"></i></div><span class="distributed-value-v0-1">26</span></div>',
            '  <div class="distributed-row-v0-1 distributed-row-text-v0-1"><span>Rank</span><strong class="distributed-value-v0-1">26</strong></div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>Score</span><div class="distributed-track-v0-1"><i style="width:52.5%"></i></div><span class="distributed-value-v0-1">52.46</span></div>',
            '  <div class="distributed-row-v0-1" data-geometry-truth="data-bound"><span>Score</span><div class="distributed-track-v0-1"><i style="width:52.5%"></i></div><span class="distributed-value-v0-1">52.46</span></div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>24h</span><div class="distributed-track-v0-1"><i style="width:20.0%"></i></div><span class="distributed-value-v0-1">-1.01%</span></div>',
            '  <div class="distributed-row-v0-1 distributed-row-text-v0-1"><span>24h</span><strong class="distributed-value-v0-1">-1.01%</strong></div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>30d</span><div class="distributed-track-v0-1"><i style="width:36.8%"></i></div><span class="distributed-value-v0-1">-4.63%</span></div>',
            '  <div class="distributed-row-v0-1 distributed-row-text-v0-1"><span>30d</span><strong class="distributed-value-v0-1">-4.63%</strong></div>',
        ),
        (
            '  <div class="distributed-row-v0-1"><span>Rank</span><div class="distributed-track-v0-1"><i style="width:38.0%"></i></div><span class="distributed-value-v0-1">60</span></div>',
            '  <div class="distributed-row-v0-1 distributed-row-text-v0-1"><span>Rank</span><strong class="distributed-value-v0-1">60</strong></div>',
        ),
        (
            '<div class="distributed-rail-v0-1" aria-label="Sample pressure components">\n  <div class="distributed-row-v0-1"><span>Temporal</span><div class="distributed-track-v0-1"><i style="width:49.8%"></i></div><span class="distributed-value-v0-1">49.83</span></div>\n  <div class="distributed-row-v0-1"><span>Phase</span><div class="distributed-track-v0-1"><i style="width:48.8%"></i></div><span class="distributed-value-v0-1">48.81</span></div>\n  <div class="distributed-row-v0-1"><span>Stability</span><div class="distributed-track-v0-1"><i style="width:71.5%"></i></div><span class="distributed-value-v0-1">71.46</span></div>\n</div>',
            '<div class="sample-context-status-v0-1" aria-label="Sample component detail not published"><span>Component detail</span><strong>not published in this public sample</strong></div>',
        ),
        (
            '<div class="distributed-rail-v0-1" aria-label="Scenario confirmation lane">\n  <div class="distributed-row-v0-1"><span>Confirm</span><div class="distributed-track-v0-1"><i style="width:64%"></i></div><span class="distributed-value-v0-1">watch</span></div>\n</div>',
            '<div class="sample-context-status-v0-1" aria-label="Scenario confirmation watch"><span>Confirm</span><strong>watch</strong></div>',
        ),
        (
            '    <div class="trend-memory" aria-label="Trend Memory">\n      <span>Market Cap 7D</span>\n      <span>BTC Dominance 7D</span>\n      <span>TVL 7D</span>\n      <span>Stable Share 7D</span>\n      <span>Volume 7D</span>\n    </div>',
            '    <div class="trend-memory-unavailable" data-geometry-truth="semantic" aria-label="Trend Memory unavailable">Trend Memory · Previous verified snapshot is not available.</div>',
        ),
    ]

    for old, new in replacements:
        html = replace_once(html, old, new)
    HTML_PATH.write_text(html, encoding="utf-8")

    extension = EXTENSION_PATH.read_bytes()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["extensions"] = [
        {
            "byte_count": len(extension),
            "order": 1,
            "path": str(EXTENSION_PATH),
            "role": "geometry_truth_repair",
            "sha256": hashlib.sha256(extension).hexdigest(),
        }
    ]
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"GEOMETRY_REPLACEMENTS={len(replacements)}")
    print(f"GEOMETRY_EXTENSION_BYTES={len(extension)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
