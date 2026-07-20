#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

HTML_PATH = Path("site/crypto-astro/index.html")


def replace_once(value: str, old: str, new: str) -> str:
    count = value.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one visual sample target, found {count}: {old[:100]!r}")
    return value.replace(old, new, 1)


def main() -> int:
    html = HTML_PATH.read_text(encoding="utf-8")
    replacements = [
        (
            '<div class="visual-row-v0-1"><span>Gram (prev. Toncoin)</span><div class="visual-rail-v0-1"><i style="width:53.0%"></i></div><span class="visual-value-v0-1">53.01</span></div>',
            '<div class="visual-row-v0-1" data-geometry-truth="data-bound"><span>Gram (prev. Toncoin)</span><div class="visual-rail-v0-1"><i style="width:53.0%"></i></div><span class="visual-value-v0-1">53.01</span></div>',
        ),
        (
            '<div class="visual-row-v0-1"><span>Internet Computer</span><div class="visual-rail-v0-1"><i style="width:52.5%"></i></div><span class="visual-value-v0-1">52.46</span></div>',
            '<div class="visual-row-v0-1" data-geometry-truth="data-bound"><span>Internet Computer</span><div class="visual-rail-v0-1"><i style="width:52.5%"></i></div><span class="visual-value-v0-1">52.46</span></div>',
        ),
        (
            '<div class="visual-row-v0-1"><span>24h TON</span><div class="visual-rail-v0-1"><i style="width:19.9%"></i></div><span class="visual-value-v0-1">-2.67%</span></div>',
            '<div class="visual-row-v0-1 visual-row-text-v0-1"><span>24h TON</span><strong class="visual-value-v0-1">-2.67%</strong></div>',
        ),
        (
            '<div class="visual-row-v0-1"><span>24h ICP</span><div class="visual-rail-v0-1"><i style="width:20.0%"></i></div><span class="visual-value-v0-1">-1.01%</span></div>',
            '<div class="visual-row-v0-1 visual-row-text-v0-1"><span>24h ICP</span><strong class="visual-value-v0-1">-1.01%</strong></div>',
        ),
    ]
    for old, new in replacements:
        html = replace_once(html, old, new)
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"VISUAL_SAMPLE_GEOMETRY_REPLACEMENTS={len(replacements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
