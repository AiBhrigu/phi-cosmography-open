#!/usr/bin/env python3
"""Mechanical inline CSS extraction for the Crypto-Astro static surface."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

HTML_PATH = Path("site/crypto-astro/index.html")
CSS_PATH = Path("site/theme/crypto_astro_inline_legacy.css")
LEGACY_LINK = '<link href="../theme/crypto_astro_inline_legacy.css" rel="stylesheet"/>'
INSERT_AFTER = '<link href="../theme/phi_theme.css" rel="stylesheet"/>'
STYLE_RE = re.compile(r"<style(?:\s[^>]*)?>(.*?)</style>", re.IGNORECASE | re.DOTALL)


class ExtractionError(RuntimeError):
    pass


def _join_blocks(blocks: list[str]) -> str:
    """Preserve each block byte-for-byte and add only a safe newline boundary."""
    parts: list[str] = []
    for block in blocks:
        parts.append(block)
        if block and not block.endswith(("\n", "\r")):
            parts.append("\n")
    return "".join(parts)


def extract_inline_css(html: str) -> tuple[str, str, int]:
    matches = list(STYLE_RE.finditer(html))
    if not matches:
        raise ExtractionError("No inline <style> blocks were found")
    if LEGACY_LINK in html:
        raise ExtractionError("Legacy stylesheet link already exists")
    if html.count(INSERT_AFTER) != 1:
        raise ExtractionError("Expected exactly one phi_theme stylesheet anchor")

    blocks = [match.group(1) for match in matches]
    bundle = _join_blocks(blocks)
    transformed = STYLE_RE.sub("", html)
    transformed = transformed.replace(INSERT_AFTER, f"{INSERT_AFTER}\n{LEGACY_LINK}", 1)

    if STYLE_RE.search(transformed):
        raise ExtractionError("Inline <style> block remains after extraction")
    if transformed.count(LEGACY_LINK) != 1:
        raise ExtractionError("Legacy stylesheet link count is not exactly one")
    if not bundle.strip():
        raise ExtractionError("Extracted stylesheet is empty")
    return transformed, bundle, len(blocks)


def read_git_file(ref: str, path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path.as_posix()}"],
            text=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as exc:
        raise ExtractionError(f"Unable to read {path} from {ref}") from exc


def apply(html_path: Path = HTML_PATH, css_path: Path = CSS_PATH) -> int:
    html = html_path.read_text(encoding="utf-8")
    matches = list(STYLE_RE.finditer(html))

    if not matches:
        if html.count(LEGACY_LINK) == 1 and css_path.is_file() and css_path.read_text(encoding="utf-8").strip():
            print("CRYPTO_ASTRO_INLINE_CSS_EXTRACTION=NOOP_ALREADY_APPLIED")
            return 0
        raise ExtractionError("No inline styles found and extracted bundle is not valid")

    transformed, bundle, count = extract_inline_css(html)
    css_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(transformed, encoding="utf-8")
    css_path.write_text(bundle, encoding="utf-8")
    print(f"CRYPTO_ASTRO_INLINE_CSS_BLOCKS_EXTRACTED={count}")
    print("CRYPTO_ASTRO_INLINE_CSS_EXTRACTION=APPLIED")
    return count


def verify_against_base(
    base_ref: str,
    html_path: Path = HTML_PATH,
    css_path: Path = CSS_PATH,
) -> int:
    base_html = read_git_file(base_ref, html_path)
    expected_html, expected_css, count = extract_inline_css(base_html)

    actual_html = html_path.read_text(encoding="utf-8")
    actual_css = css_path.read_text(encoding="utf-8")

    failures: list[str] = []
    if actual_html != expected_html:
        failures.append("HTML_NOT_EXACT_MECHANICAL_TRANSFORM")
    if actual_css != expected_css:
        failures.append("CSS_NOT_EXACT_ORDERED_EXTRACTION")
    if STYLE_RE.search(actual_html):
        failures.append("INLINE_STYLE_REMAINS")
    if actual_html.count(LEGACY_LINK) != 1:
        failures.append("LEGACY_LINK_COUNT_INVALID")
    if failures:
        raise ExtractionError(", ".join(failures))

    print(f"CRYPTO_ASTRO_INLINE_CSS_BLOCKS_VERIFIED={count}")
    print("CRYPTO_ASTRO_MECHANICAL_EXTRACTION_PARITY=PASS")
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify-base-ref")
    parser.add_argument("--html", type=Path, default=HTML_PATH)
    parser.add_argument("--css", type=Path, default=CSS_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.apply:
            apply(args.html, args.css)
        else:
            verify_against_base(args.verify_base_ref, args.html, args.css)
    except (ExtractionError, OSError) as exc:
        print(f"CRYPTO_ASTRO_INLINE_CSS_EXTRACTION=FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
