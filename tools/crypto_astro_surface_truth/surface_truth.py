#!/usr/bin/env python3
"""Deterministic baseline evidence for the public Crypto-Astro static surface."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "crypto_astro_surface_truth_report_v0_1"
REQUIRED_SELECTORS = (
    "body",
    ".surface-hub",
    ".hero",
    "#btc-phi-cycle-hub",
    ".market-reality-grid",
    ".alt-rotation-module",
    ".cosmographer-watch-v0-2",
)
STYLE_SELECTORS = (
    ".surface-hub",
    ".hero",
    "#btc-phi-cycle-hub",
    ".btc-quiet-phi-core-v0-3",
    ".btc-entry-v1",
    ".market-reality-grid",
    ".alt-rotation-module",
    ".cosmographer-watch-v0-2",
)
STYLE_PROPERTIES = (
    "display",
    "position",
    "width",
    "height",
    "margin",
    "padding",
    "border-radius",
    "overflow",
    "color",
    "background-color",
    "font-size",
    "line-height",
    "opacity",
    "transform",
    "animation-name",
    "animation-play-state",
)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def canonicalize_anchor_map(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "href": (row.get("href") or "").strip(),
                "text": normalize_text(row.get("text") or ""),
            }
        )
    return sorted(normalized, key=lambda item: (item["href"], item["text"]))


def write_json(path: Path, value: Any) -> None:
    path.write_text(stable_json(value), encoding="utf-8")


def build_sha256_manifest(out_dir: Path) -> str:
    rows: list[str] = []
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file() or path.name == "sha256_manifest.txt":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {path.relative_to(out_dir).as_posix()}")
    manifest = "\n".join(rows) + "\n"
    (out_dir / "sha256_manifest.txt").write_text(manifest, encoding="utf-8")
    return sha256_text(manifest)


def _capture_screenshot(driver: Any, path: Path) -> None:
    path.write_bytes(driver.get_screenshot_as_png())


def _load(driver: Any, url: str, width: int, height: int) -> None:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    driver.set_window_size(width, height)
    driver.get(url)
    WebDriverWait(driver, 25).until(lambda d: d.find_element(By.CSS_SELECTOR, "body"))
    WebDriverWait(driver, 25).until(lambda d: d.find_element(By.ID, "btc-phi-cycle-hub"))
    driver.execute_script("window.scrollTo(0, 0)")


def run_browser(url: str, out_dir: Path) -> dict[str, Any]:
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    for arg in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--window-size=1440,1200",
    ):
        options.add_argument(arg)
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=options)
    failures: list[str] = []
    checks: dict[str, bool] = {}
    measurements: dict[str, Any] = {}

    try:
        _load(driver, url, 1440, 1200)

        selector_presence = driver.execute_script(
            """
            const selectors = arguments[0];
            return Object.fromEntries(selectors.map(selector => [selector, !!document.querySelector(selector)]));
            """,
            list(REQUIRED_SELECTORS),
        )
        for selector, present in selector_presence.items():
            checks[f"selector_present:{selector}"] = bool(present)

        visible_text = normalize_text(driver.execute_script("return document.body.innerText || '';"))
        (out_dir / "visible-text.txt").write_text(visible_text + "\n", encoding="utf-8")
        (out_dir / "visible-text.sha256").write_text(sha256_text(visible_text) + "\n", encoding="utf-8")
        checks["visible_text_nonempty"] = len(visible_text) > 500

        dom_rows = driver.execute_script(
            """
            const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','TEMPLATE']);
            const rows = [];
            const walk = (node, parent) => {
              for (const el of node.children) {
                if (skip.has(el.tagName)) continue;
                const index = rows.length;
                rows.push({
                  parent,
                  tag: el.tagName.toLowerCase(),
                  id: el.id || '',
                  classes: [...el.classList].sort(),
                  role: el.getAttribute('role') || '',
                  ariaLabel: el.getAttribute('aria-label') || '',
                  childElementCount: [...el.children].filter(c => !skip.has(c.tagName)).length
                });
                walk(el, index);
              }
            };
            walk(document.body, -1);
            return rows;
            """
        )
        dom_payload = {"schema_version": "crypto_astro_dom_structure_v0_1", "rows": dom_rows}
        write_json(out_dir / "dom-structure.json", dom_payload)
        (out_dir / "dom-structure.sha256").write_text(
            sha256_text(stable_json(dom_payload)) + "\n", encoding="utf-8"
        )
        checks["dom_structure_nonempty"] = len(dom_rows) > 100

        anchors = canonicalize_anchor_map(
            driver.execute_script(
                """
                return [...document.querySelectorAll('a[href]')].map(a => ({
                  href: a.href,
                  text: a.innerText || a.textContent || ''
                }));
                """
            )
        )
        write_json(out_dir / "anchor-href-map.json", anchors)
        checks["anchor_map_nonempty"] = len(anchors) >= 5

        public_values = driver.execute_script(
            """
            const numeric = /(?:[$€£]?\s?\d[\d,.]*\s?(?:%|B|M|K|USD)?|#\d+)/;
            const visible = el => {
              const s = getComputedStyle(el);
              const r = el.getBoundingClientRect();
              return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) !== 0
                && r.width > 0 && r.height > 0;
            };
            const selector = el => {
              if (el.id) return `#${CSS.escape(el.id)}`;
              const cls = [...el.classList].slice(0, 3).map(CSS.escape).join('.');
              return `${el.tagName.toLowerCase()}${cls ? '.' + cls : ''}`;
            };
            const rows = [];
            for (const el of document.querySelectorAll('strong,[aria-label],.market-metric,[data-copy-slot]')) {
              if (!visible(el)) continue;
              const text = (el.innerText || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim();
              if (!text || text.length > 220 || !numeric.test(text)) continue;
              rows.push({selector: selector(el), text, ariaLabel: el.getAttribute('aria-label') || ''});
            }
            return rows;
            """
        )
        write_json(out_dir / "public-value-map.json", public_values)
        checks["public_value_map_nonempty"] = len(public_values) >= 12

        computed_styles = driver.execute_script(
            """
            const selectors = arguments[0], properties = arguments[1], out = {};
            for (const selector of selectors) {
              const el = document.querySelector(selector);
              if (!el) { out[selector] = null; continue; }
              const style = getComputedStyle(el);
              out[selector] = Object.fromEntries(properties.map(p => [p, style.getPropertyValue(p).trim()]));
            }
            return out;
            """,
            list(STYLE_SELECTORS),
            list(STYLE_PROPERTIES),
        )
        style_payload = {
            "schema_version": "crypto_astro_computed_style_fingerprint_v0_1",
            "selectors": computed_styles,
        }
        write_json(out_dir / "computed-style-fingerprint.json", style_payload)
        (out_dir / "computed-style-fingerprint.sha256").write_text(
            sha256_text(stable_json(style_payload)) + "\n", encoding="utf-8"
        )
        checks["computed_style_targets_present"] = all(
            computed_styles.get(selector) is not None for selector in STYLE_SELECTORS
        )

        boxes = driver.execute_script(
            """
            const out = {};
            for (const selector of arguments[0]) {
              const el = document.querySelector(selector);
              if (!el) { out[selector] = null; continue; }
              const r = el.getBoundingClientRect();
              out[selector] = {
                x: Math.round(r.x * 100) / 100,
                y: Math.round((r.y + scrollY) * 100) / 100,
                width: Math.round(r.width * 100) / 100,
                height: Math.round(r.height * 100) / 100
              };
            }
            return out;
            """,
            list(STYLE_SELECTORS),
        )
        write_json(out_dir / "bounding-box-report.json", boxes)

        motion = driver.execute_script(
            """
            const root = document.querySelector('.btc-deep-v1');
            if (!root) return {rootFound:false, declared:0, running:0};
            const nodes = [root, ...root.querySelectorAll('*')];
            let declared = 0, running = 0;
            for (const el of nodes) {
              for (const pseudo of [null, '::before', '::after']) {
                const s = getComputedStyle(el, pseudo);
                const names = s.animationName.split(',');
                const states = s.animationPlayState.split(',');
                names.forEach((name, i) => {
                  if (name.trim() === 'none') return;
                  declared += 1;
                  const state = (states[i] || states[0] || 'running').trim();
                  if (state === 'running') running += 1;
                });
              }
            }
            return {rootFound:true, declared, running};
            """
        )
        write_json(out_dir / "motion-report.json", motion)
        checks["btc_motion_root_found"] = bool(motion.get("rootFound"))
        checks["btc_running_animations_zero"] = motion.get("running") == 0

        desktop_overflow = driver.execute_script(
            """
            const width = innerWidth;
            const offenders = [...document.querySelectorAll('body *')].filter(el => {
              const r = el.getBoundingClientRect();
              const s = getComputedStyle(el);
              return s.position !== 'fixed' && r.width > 0 && (r.left < -1 || r.right > width + 1);
            }).slice(0, 30).map(el => ({
              tag: el.tagName.toLowerCase(),
              id: el.id || '',
              classes: [...el.classList].slice(0,4),
              left: Math.round(el.getBoundingClientRect().left * 100) / 100,
              right: Math.round(el.getBoundingClientRect().right * 100) / 100
            }));
            return {
              viewportWidth: width,
              scrollWidth: document.documentElement.scrollWidth,
              offenders
            };
            """
        )
        driver.execute_script("window.scrollTo(0, 0)")
        _capture_screenshot(driver, out_dir / "desktop.png")
        btc = driver.find_element("id", "btc-phi-cycle-hub")
        driver.execute_script("arguments[0].scrollIntoView({block:'start'})", btc)
        _capture_screenshot(driver, out_dir / "desktop-btc.png")

        _load(driver, url, 390, 844)
        mobile_overflow = driver.execute_script(
            """
            const width = innerWidth;
            const offenders = [...document.querySelectorAll('body *')].filter(el => {
              const r = el.getBoundingClientRect();
              const s = getComputedStyle(el);
              return s.position !== 'fixed' && r.width > 0 && (r.left < -1 || r.right > width + 1);
            }).slice(0, 30).map(el => ({
              tag: el.tagName.toLowerCase(),
              id: el.id || '',
              classes: [...el.classList].slice(0,4),
              left: Math.round(el.getBoundingClientRect().left * 100) / 100,
              right: Math.round(el.getBoundingClientRect().right * 100) / 100
            }));
            return {
              viewportWidth: width,
              scrollWidth: document.documentElement.scrollWidth,
              offenders
            };
            """
        )
        driver.execute_script("window.scrollTo(0, 0)")
        _capture_screenshot(driver, out_dir / "mobile.png")
        btc = driver.find_element("id", "btc-phi-cycle-hub")
        driver.execute_script("arguments[0].scrollIntoView({block:'start'})", btc)
        _capture_screenshot(driver, out_dir / "mobile-btc.png")

        overflow = {"desktop": desktop_overflow, "mobile": mobile_overflow}
        write_json(out_dir / "overflow-report.json", overflow)
        checks["desktop_horizontal_overflow_none"] = (
            desktop_overflow["scrollWidth"] <= desktop_overflow["viewportWidth"] + 1
            and not desktop_overflow["offenders"]
        )
        checks["mobile_horizontal_overflow_none"] = (
            mobile_overflow["scrollWidth"] <= mobile_overflow["viewportWidth"] + 1
            and not mobile_overflow["offenders"]
        )

        severe_logs = [
            row
            for row in driver.get_log("browser")
            if row.get("level") == "SEVERE"
            and "favicon" not in (row.get("message") or "").lower()
        ]
        write_json(out_dir / "browser-severe-log.json", severe_logs)
        checks["browser_severe_none"] = not severe_logs

        failures = sorted(name for name, passed in checks.items() if not passed)
        measurements.update(
            {
                "dom_rows": len(dom_rows),
                "visible_text_characters": len(visible_text),
                "anchor_count": len(anchors),
                "public_value_rows": len(public_values),
                "desktop_scroll_width": desktop_overflow["scrollWidth"],
                "mobile_scroll_width": mobile_overflow["scrollWidth"],
                "btc_declared_animations": motion.get("declared"),
                "btc_running_animations": motion.get("running"),
            }
        )

    finally:
        driver.quit()

    report = {
        "schema_version": SCHEMA_VERSION,
        "url": url,
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "measurements": measurements,
        "failures": failures,
        "boundaries": {
            "site_html_changed_by_harness": False,
            "site_css_changed_by_harness": False,
            "snapshot_data_changed_by_harness": False,
            "browser_runtime_is_test_only": True,
        },
    }
    write_json(out_dir / "surface-truth-report.json", report)
    report["sha256_manifest_digest"] = build_sha256_manifest(out_dir)
    write_json(out_dir / "surface-truth-report.json", report)
    build_sha256_manifest(out_dir)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        report = run_browser(args.url, args.out)
    except Exception as exc:
        error = {
            "schema_version": SCHEMA_VERSION,
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        write_json(args.out / "surface-truth-report.json", error)
        build_sha256_manifest(args.out)
        raise
    print(f"CRYPTO_ASTRO_SURFACE_TRUTH={report['status']}")
    print(f"REPORT={args.out / 'surface-truth-report.json'}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
