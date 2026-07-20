#!/usr/bin/env python3
"""Compare two Crypto-Astro surface-truth evidence directories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXACT_FILES = (
    "visible-text.sha256",
    "dom-structure.sha256",
    "anchor-href-map.json",
    "public-value-map.json",
    "computed-style-fingerprint.json",
    "motion-report.json",
    "overflow-report.json",
    "browser-severe-log.json",
)
SCREENSHOTS = ("desktop.png", "desktop-btc.png", "mobile.png", "mobile-btc.png")
BOX_TOLERANCE_PX = 1.0
PIXEL_CHANGE_RATIO_MAX = 0.0005


class ComparisonError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_exact_files(base: Path, head: Path) -> list[str]:
    failures: list[str] = []
    for name in EXACT_FILES:
        if (base / name).read_bytes() != (head / name).read_bytes():
            failures.append(f"EXACT_MISMATCH:{name}")
    return failures


def compare_boxes(base: Path, head: Path, tolerance: float = BOX_TOLERANCE_PX) -> list[str]:
    left = load_json(base / "bounding-box-report.json")
    right = load_json(head / "bounding-box-report.json")
    failures: list[str] = []
    if set(left) != set(right):
        return ["BOUNDING_BOX_SELECTOR_SET_MISMATCH"]
    for selector in sorted(left):
        if left[selector] is None or right[selector] is None:
            if left[selector] != right[selector]:
                failures.append(f"BOUNDING_BOX_PRESENCE_MISMATCH:{selector}")
            continue
        for field in ("x", "y", "width", "height"):
            delta = abs(float(left[selector][field]) - float(right[selector][field]))
            if delta > tolerance:
                failures.append(f"BOUNDING_BOX_DELTA:{selector}:{field}:{delta:.3f}")
    return failures


def compare_screenshot(base_path: Path, head_path: Path) -> tuple[float, int]:
    from PIL import Image, ImageChops

    left = Image.open(base_path).convert("RGBA")
    right = Image.open(head_path).convert("RGBA")
    if left.size != right.size:
        raise ComparisonError(f"SCREENSHOT_SIZE_MISMATCH:{base_path.name}")
    diff = ImageChops.difference(left, right)
    changed = 0
    max_delta = 0
    for pixel in diff.getdata():
        delta = max(pixel)
        if delta:
            changed += 1
            max_delta = max(max_delta, delta)
    total = left.size[0] * left.size[1]
    return changed / total if total else 0.0, max_delta


def compare_screenshots(base: Path, head: Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    metrics: dict[str, Any] = {}
    for name in SCREENSHOTS:
        ratio, max_delta = compare_screenshot(base / name, head / name)
        metrics[name] = {"changed_pixel_ratio": ratio, "max_channel_delta": max_delta}
        if ratio > PIXEL_CHANGE_RATIO_MAX:
            failures.append(f"SCREENSHOT_PIXEL_RATIO:{name}:{ratio:.8f}")
    return failures, metrics


def compare_reports(base: Path, head: Path) -> list[str]:
    failures: list[str] = []
    for label, root in (("base", base), ("head", head)):
        report = load_json(root / "surface-truth-report.json")
        if report.get("status") != "PASS":
            failures.append(f"SURFACE_TRUTH_STATUS:{label}:{report.get('status')}")
        if report.get("failures"):
            failures.append(f"SURFACE_TRUTH_FAILURES:{label}")
    return failures


def compare(base: Path, head: Path) -> dict[str, Any]:
    failures = compare_exact_files(base, head)
    failures.extend(compare_boxes(base, head))
    screenshot_failures, screenshot_metrics = compare_screenshots(base, head)
    failures.extend(screenshot_failures)
    failures.extend(compare_reports(base, head))
    return {
        "schema_version": "crypto_astro_css_extraction_parity_v0_1",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "box_tolerance_px": BOX_TOLERANCE_PX,
        "pixel_change_ratio_max": PIXEL_CHANGE_RATIO_MAX,
        "screenshots": screenshot_metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compare(args.base, args.head)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"CRYPTO_ASTRO_CSS_EXTRACTION_PARITY={report['status']}")
        if report["failures"]:
            print("\n".join(report["failures"]), file=sys.stderr)
            return 1
        return 0
    except (ComparisonError, OSError, ValueError, KeyError) as exc:
        print(f"CRYPTO_ASTRO_CSS_EXTRACTION_PARITY=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
