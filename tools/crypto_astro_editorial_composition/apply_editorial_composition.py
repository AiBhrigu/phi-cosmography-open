#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = ROOT / "site/crypto-astro/index.html"
MANIFEST_PATH = ROOT / "site/theme/crypto_astro/css_order_manifest.json"
EXTENSION_PATH = ROOT / "site/theme/crypto_astro/extensions/10_editorial_composition.css"


def replace_once(text: str, pattern: str, replacement: str, label: str, flags: int = re.S) -> str:
    result, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return result


def extract_once(text: str, pattern: str, label: str) -> tuple[str, str]:
    match = re.search(pattern, text, flags=re.S)
    if not match:
        raise RuntimeError(f"{label}: block not found")
    return text[: match.start()] + text[match.end() :], match.group(0).strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    html = HTML_PATH.read_text(encoding="utf-8")
    if 'data-editorial-composition="v0_1"' in html:
        print("EDITORIAL_COMPOSITION_ALREADY_APPLIED=YES")
        return 0

    navigation = '''<nav class="crypto-astro-primary-nav" data-editorial-navigation="v0_1" aria-label="Crypto-Astro primary navigation">
  <a class="crypto-astro-primary-nav__brand" href="#surface">Crypto-Astro</a>
  <div class="crypto-astro-primary-nav__links">
    <a href="#surface">Current</a>
    <a href="#what-changed">What Changed</a>
    <a href="#btc-phi-cycle-hub">BTC</a>
    <a href="#market">Market</a>
    <a href="#trust-access">Trust &amp; Access</a>
  </div>
</nav>
'''
    html = replace_once(
        html,
        r'<section class="surface-hub" aria-label="Crypto-Astro Phi service status hub">.*?</section>\s*',
        navigation,
        "primary navigation",
    )

    orientation = '''<section id="surface" class="hero surface-anchor editorial-orientation-v0-1 editorial-chapter-v0-1" data-editorial-composition="v0_1" data-editorial-chapter="orientation" aria-label="Crypto-Astro orientation">
  <div>
    <div class="kicker">Verified crypto-market context</div>
    <h1>Crypto-Astro Market Field</h1>
    <p class="lead">A source-bound view of Bitcoin gravity, market structure, liquidity, rotation, timing context, and reviewed synthesis.</p>
  </div>
  <div class="editorial-orientation-v0-1__actions">
    <a class="editorial-primary-cta-v0-1" href="https://www.bhrigu.io/crypto-astro/btc">Ask one BTC field question</a>
    <p class="editorial-orientation-v0-1__trust">Snapshot · 2026-07-19 18:26 UTC<br/>Research context · source proof available</p>
  </div>
</section>

<section id="what-changed" class="editorial-what-changed-v0-1 editorial-chapter-v0-1" data-editorial-chapter="what-changed" aria-labelledby="what-changed-title">
  <div>
    <p class="eyebrow">What Changed</p>
    <h2 id="what-changed-title">Verified change memory</h2>
    <p>This layer compares the current accepted snapshot with the previous accepted snapshot. It remains unavailable until both source and methodology bindings are verified.</p>
  </div>
  <div class="editorial-what-changed-v0-1__state" data-what-changed-status="unavailable">
    <strong>Previous verified snapshot is not yet available.</strong>
    <span>No historical value has been inferred from cached pages or presentation geometry.</span>
  </div>
</section>
'''
    html = replace_once(
        html,
        r'<section id="surface" class="hero surface-anchor" aria-label="Crypto-Astro Market Field public-safe surface">.*?</section>\s*',
        orientation,
        "orientation and what changed",
    )

    html = replace_once(
        html,
        r'<!-- CRYPTO_ASTRO_MOBILE_ROUTE_LAYER_v0_1:BEGIN -->.*?<!-- CRYPTO_ASTRO_MOBILE_ROUTE_LAYER_v0_1:END -->\s*',
        "",
        "legacy mobile route",
    )

    html = html.replace(
        '<section id="btc-phi-cycle-hub" class="section surface-anchor btc-deep-v1" aria-label="BTC current field and Aspect-Cycle research bridge">',
        '<section id="btc-phi-cycle-hub" class="section surface-anchor btc-deep-v1 editorial-chapter-v0-1" data-editorial-chapter="btc-field" aria-label="BTC current field and Aspect-Cycle research bridge">',
        1,
    )
    html = replace_once(
        html,
        r'<header class="btc-head-v1">.*?</header>',
        '<header class="btc-head-v1"><p class="eyebrow">BTC Field</p><h2>Bitcoin gravity and cycle context</h2><p>BTC dominance anchors the current snapshot. The field view connects that verified market value with bounded semantic context and one reviewed question route.</p></header>',
        "BTC chapter header",
    )
    html = replace_once(
        html,
        r'<a class="btc-field-read-entry-v0-1 btc-entry-v1" href="https://www\.bhrigu\.io/crypto-astro/btc".*?</a>',
        '<a class="btc-field-read-entry-v0-1 btc-entry-v1" href="https://www.bhrigu.io/crypto-astro/btc" aria-label="Ask one BTC field question"><span class="btc-field-read-entry-glyph-v0-1" aria-hidden="true">◉</span><strong>Ask one BTC field question</strong><em>Source-bound BTC Field Read</em><span class="btc-entry-arrow-v1" aria-hidden="true">→</span></a>',
        "BTC primary CTA",
    )
    html = html.replace("View wider Market Field confirmation", "View wider market context", 1)
    html = replace_once(
        html,
        r'\s*<section class="btc-private-v1" aria-label="Protected research aperture">.*?</section>',
        "",
        "BTC competing research CTA",
    )
    html = replace_once(
        html,
        r'\s*<div class="btc-boundary-v1">.*?</div>',
        "",
        "BTC duplicate boundary",
    )

    html = html.replace(
        '<section id="market" class="section surface-anchor" aria-label="Crypto-Astro Market Field">',
        '<section id="market" class="section surface-anchor editorial-chapter-v0-1" data-editorial-chapter="wider-market" aria-label="Wider crypto market context">',
        1,
    )
    html = replace_once(
        html,
        r'<section id="market".*?<div class="section-head">.*?</div>',
        '<section id="market" class="section surface-anchor editorial-chapter-v0-1" data-editorial-chapter="wider-market" aria-label="Wider crypto market context">\n  <div class="section-head editorial-chapter-head-v0-1">\n    <div class="kicker">Wider Market</div>\n    <h2>Market structure around Bitcoin</h2>\n    <p>Verified values are read together: market reality, liquidity, breadth, concentration, timing context, and synthesis.</p>\n  </div>',
        "wider market header",
    )
    html = replace_once(
        html,
        r'\s*<div class="market-status-rail" aria-label="Crypto-Astro Market Field status rail">.*?</div>',
        "",
        "market status rail",
    )

    html, continuation = extract_once(
        html,
        r'\s*<article class="market-card">\s*<p class="eyebrow">Continuation Field</p>.*?</article>',
        "continuation field",
    )

    html = html.replace(
        '<p>A compact field score showing how prepared membranes, market liquidity, and bounded context are positioned.</p>',
        '<p>A compact score and categorical state for the verified market snapshot.</p>',
        1,
    )
    html = html.replace(
        '<div class="barometer-lane attention" aria-label="A membrane prepared">A<br/><span>prepared</span></div>',
        '<div class="barometer-lane attention" aria-label="Input context prepared">Input<br/><span>prepared</span></div>',
        1,
    )
    html = html.replace(
        '<div class="barometer-lane engagement" aria-label="E membrane prepared">E<br/><span>prepared</span></div>',
        '<div class="barometer-lane engagement" aria-label="Evidence context prepared">Evidence<br/><span>prepared</span></div>',
        1,
    )
    html = html.replace(
        '<div class="barometer-lane market" aria-label="Market vector active">M<br/><span>active</span></div>',
        '<div class="barometer-lane market" aria-label="Market structure active">Market<br/><span>active</span></div>',
        1,
    )
    html = html.replace(
        '<div class="barometer-lane temporal" aria-label="Temporal context bounded">C/T<br/><span>bounded</span></div>',
        '<div class="barometer-lane temporal" aria-label="Timing context bounded">Timing<br/><span>bounded</span></div>',
        1,
    )
    html = html.replace(
        '<p>Market Field Score: 61 / 100<br/>Bias: Neutral → Bullish</p>',
        '<p>Market Field Score: 61 / 100<br/>Observed state: Balanced Expansion</p>',
        1,
    )

    compact_astromodule = '''<article class="market-card gold editorial-astromodule-v0-1" id="astromodule-surface-bridge" aria-label="Astromodule timing context">
  <div>
    <p class="eyebrow">Timing Context</p>
    <h3>Astromodule context</h3>
    <p>Phase, pressure, resonance, and structural stability are shown as categorical research context. No public percentage, forecast, or execution instruction is implied.</p>
  </div>
  <div class="editorial-astromodule-v0-1__states" aria-label="Astromodule categorical states">
    <div><span>Pressure</span><strong>Medium</strong></div>
    <div><span>Phase</span><strong>Active</strong></div>
    <div><span>Resonance</span><strong>Moderate-high</strong></div>
    <div><span>Stability</span><strong>Transitional-stable</strong></div>
  </div>
</article>'''
    html = replace_once(
        html,
        r'<article class="market-card gold astromodule-card astromodule-wide-panel-v0-1" id="astromodule-surface-bridge".*?</article>',
        compact_astromodule,
        "compact Astromodule",
    )

    html, support_modules = extract_once(
        html,
        r'<!-- CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1:BEGIN -->.*?<!-- CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1:END -->',
        "support modules",
    )
    html, astromodule_depth = extract_once(
        html,
        r'\s*<article class="market-card astromodule-depth-note-v0-1".*?</article>',
        "Astromodule depth note",
    )
    html, access_preview = extract_once(
        html,
        r'<!-- CRYPTO_ASTRO_ACCESS_PATH_PREVIEW_v0_1:BEGIN -->.*?<!-- CRYPTO_ASTRO_ACCESS_PATH_PREVIEW_v0_1:END -->',
        "access preview",
    )
    html, public_sample = extract_once(
        html,
        r'<!-- CRYPTO_ASTRO_PUBLIC_SAMPLE_WEB_PANEL_v0_1:BEGIN -->.*?<!-- CRYPTO_ASTRO_PUBLIC_SAMPLE_WEB_PANEL_v0_1:END -->',
        "public sample panel",
    )
    html, private_note = extract_once(
        html,
        r'<!-- CRYPTO_ASTRO_PRIVATE_NOTE_CTA_v0_1:BEGIN -->.*?<!-- CRYPTO_ASTRO_PRIVATE_NOTE_CTA_v0_1:END -->',
        "private note CTA",
    )
    html = replace_once(
        html,
        r'\s*<div class="trend-memory" aria-label="Trend Memory">.*?</div>',
        "",
        "legacy trend memory",
    )

    replacements = {
        "M active · membranes prepared · static context": "Market-led · reviewed context",
        ">M active<": ">Market active<",
        "Prepared field membranes remain inactive.": "Additional input context remains inactive.",
        "Prepared membranes remain inactive;": "Additional input context remains inactive;",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    trust = '''<section id="trust-access" class="editorial-trust-access-v0-1 editorial-chapter-v0-1" data-editorial-chapter="trust-access" aria-labelledby="trust-access-title">
  <span id="access" class="editorial-anchor-alias-v0-1" aria-hidden="true"></span>
  <div>
    <p class="eyebrow">Trust &amp; Access</p>
    <h2 id="trust-access-title">Proof remains public; deeper research remains reviewed.</h2>
    <p>Every visible value stays tied to the verified snapshot and public source trail. A reviewed research request may extend the context without exposing protected calculation structure.</p>
    <p class="editorial-boundary-v0-1">Research context only. No trading signal, forecast, price target, or investment advice.</p>
  </div>
  <div class="editorial-trust-access-v0-1__actions">
    <a class="editorial-proof-link-v0-1" href="#proof">View source proof</a>
    <a class="editorial-access-link-v0-1" href="https://www.bhrigu.io/access">Research access</a>
  </div>
</section>
'''

    proof_body = f'''<details id="proof" class="proof-depth-appendix-v0-1">
  <summary>Source proof and research appendix</summary>
  <div class="proof-depth-appendix-v0-1__body">
    <div class="proof-moved-grid-v0-1">
      {continuation}
    </div>
    {support_modules}
    {astromodule_depth}
    {access_preview}
    {public_sample}
    {private_note}
'''
    html = html.replace('<section id="proof" class="truth-grid surface-anchor"', '<section class="truth-grid surface-anchor"', 1)
    html = html.replace('<section class="truth-grid surface-anchor"', trust + proof_body + '<section class="truth-grid surface-anchor"', 1)
    html = html.replace(
        '<!-- CRYPTO_ASTRO_PHI_SERVICE_SURFACE_v0_1:END -->',
        '  </div>\n</details>\n<!-- CRYPTO_ASTRO_PHI_SERVICE_SURFACE_v0_1:END -->',
        1,
    )

    HTML_PATH.write_text(html, encoding="utf-8")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    extension_bytes = EXTENSION_PATH.read_bytes()
    extension_entry = {
        "byte_count": len(extension_bytes),
        "order": 2,
        "path": "site/theme/crypto_astro/extensions/10_editorial_composition.css",
        "role": "editorial_composition_and_cta",
        "sha256": sha256_bytes(extension_bytes),
    }
    extensions = [row for row in manifest.get("extensions", []) if row.get("path") != extension_entry["path"]]
    for index, row in enumerate(extensions, 1):
        row["order"] = index
    extension_entry["order"] = len(extensions) + 1
    extensions.append(extension_entry)
    manifest["extensions"] = extensions
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("EDITORIAL_COMPOSITION_APPLIED=YES")
    print(f"EDITORIAL_EXTENSION_SHA256={extension_entry['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
