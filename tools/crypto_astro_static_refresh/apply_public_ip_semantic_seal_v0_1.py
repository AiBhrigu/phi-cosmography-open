from pathlib import Path

HTML_PATH = Path("site/crypto-astro/index.html")
SYSTEM_CSS_PATH = Path("site/theme/system.css")
SEAL_CSS_PATH = Path("site/theme/ip_semantic_seal.css")

MARKER = "CRYPTO_ASTRO_PUBLIC_IP_SEMANTIC_SEAL_v0_1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


html = HTML_PATH.read_text(encoding="utf-8")
system_css = SYSTEM_CSS_PATH.read_text(encoding="utf-8")

# Surface-level semantic membrane copy.
html = replace_once(
    html,
    '<a class="badge gold" href="#market">A/E · asset/event lanes</a>',
    '<a class="badge gold" href="#market">A/E · prepared field membranes</a>',
    "hero A/E membrane badge",
)
html = replace_once(
    html,
    '<a class="badge blue" href="#btc-phi-cycle-hub">C/T · cycle/time context</a>',
    '<a class="badge blue" href="#btc-phi-cycle-hub">C/T · bounded context membrane</a>',
    "hero C/T membrane badge",
)
html = replace_once(
    html,
    '<span>Cycle / Time layer · bounded timing context</span>',
    '<span>Bounded context membrane · window · phase · provenance</span>',
    "status rail C/T wording",
)
html = replace_once(
    html,
    '<p class="eyebrow">A/E/M Field Barometer</p>',
    '<p class="eyebrow">Field Membrane Barometer</p>',
    "barometer title",
)
html = replace_once(
    html,
    '<p>A compact field score showing how attention lanes, engagement lanes, market liquidity, and temporal context are positioned.</p>',
    '<p>A compact field score showing how prepared membranes, market liquidity, and bounded context are positioned.</p>',
    "barometer description",
)
html = replace_once(
    html,
    '<p class="small">Market-led field. Attention and engagement lanes are prepared; temporal context remains bounded.</p>',
    '<p class="small">Market-led field. Prepared membranes remain inactive; bounded context remains source-bound.</p>',
    "barometer boundary copy",
)

# Astromodule public C/T seal: meaning remains visible, implementation vocabulary is removed.
html = replace_once(
    html,
    'Organizes ephemerides context, AstroPatterns memory, market state, observation windows, and source provenance into timing-scenario context.',
    'Organizes verified context, field memory, market state, observation windows, and provenance into bounded timing-scenario context.',
    "Astromodule field reader copy",
)
html = replace_once(
    html,
    '<p>Market context · Ephemerides · AstroPatterns · Observation window · Provenance</p>',
    '<p>Verified context · Field memory · Observation window · Provenance</p>',
    "Astromodule input field copy",
)
html = replace_once(
    html,
    '<p>Raw ephemerides · weights · verification.</p>',
    '<p>Protected research depth · verification.</p>',
    "Astromodule operator depth copy",
)

# Source Lanes become status-only public membranes.
html = replace_once(
    html,
    '<!-- CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1:BEGIN -->',
    '<!-- CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1:BEGIN -->\n        <!-- CRYPTO_ASTRO_PUBLIC_IP_SEMANTIC_SEAL_v0_1:BEGIN -->',
    "semantic seal begin marker",
)
html = replace_once(
    html,
    '<article class="market-card support-module-card-v0-1 source-lanes-support-v0-1">',
    '<article class="market-card support-module-card-v0-1 source-lanes-support-v0-1" aria-label="Prepared public field membranes">',
    "source membrane aria label",
)
html = replace_once(
    html,
    '<p class="eyebrow">Source Lanes</p>',
    '<p class="eyebrow">Field Membranes</p>',
    "source membrane title",
)
html = replace_once(
    html,
    '<p>A and E mark future attention and engagement source lanes, keeping the surface ready for reviewed validation layers without changing the current public identity.</p>',
    '<p>Two prepared membranes mark reserved public input positions. They expose status only; source identity, collection logic, and calibration remain sealed.</p>',
    "source membrane description",
)
html = replace_once(
    html,
    '<div><strong>A · Attention</strong><p>prepared / search demand</p><div class="lane-rail prepared" aria-hidden="true"></div></div>',
    '<div><strong>A · Prepared</strong><p>public input inactive</p><div class="lane-rail prepared" aria-hidden="true"></div></div>',
    "A membrane copy",
)
html = replace_once(
    html,
    '<div><strong>E · Engagement</strong><p>prepared / public discussion</p><div class="lane-rail prepared" aria-hidden="true"></div></div>',
    '<div><strong>E · Prepared</strong><p>public input inactive</p><div class="lane-rail prepared" aria-hidden="true"></div></div>',
    "E membrane copy",
)
html = replace_once(
    html,
    '<p class="small">Prepared lanes only; future validation layers require reviewed source policy and calibration.</p>',
    '<p class="small">No live adapter · no public feed · no source pipeline disclosure.</p>',
    "source membrane boundary",
)

# C/T becomes a bounded context membrane, not a visible pipeline map.
html = replace_once(
    html,
    '<article class="market-card blue support-module-card-v0-1 temporal-support-v0-1" aria-label="C/T Temporal Ephemerides Support">',
    '<article class="market-card blue support-module-card-v0-1 temporal-support-v0-1" aria-label="C/T bounded context membrane">',
    "C/T aria label",
)
html = replace_once(
    html,
    '<p class="eyebrow">C/T Temporal · Ephemerides Support</p>',
    '<p class="eyebrow">C/T · Bounded Context Membrane</p>',
    "C/T title",
)
html = replace_once(
    html,
    '<p>Bounded timing-cycle context for Crypto-Astro research notes. It frames observation windows, cycle context, and source provenance.</p>',
    '<p>Frames observation window, phase context, and provenance for public research orientation.</p>',
    "C/T public meaning",
)
html = replace_once(
    html,
    '<p class="small">Static support layer; execution and advice boundaries remain in the trust seal below.</p>',
    '<p class="small">Semantic context only · no public pipeline · no live fetch · no forecast · no execution.</p>',
    "C/T boundary",
)
html = replace_once(
    html,
    '<!-- CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1:END -->',
    '<!-- CRYPTO_ASTRO_PUBLIC_IP_SEMANTIC_SEAL_v0_1:END -->\n        <!-- CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1:END -->',
    "semantic seal end marker",
)
html = replace_once(
    html,
    'A/E lanes remain prepared until source policy and calibration are reviewed.',
    'Prepared field membranes remain inactive; source policy and calibration stay protected.',
    "liquidity source membrane note",
)

# BTC / Aspect-Cycle semantic-only seal.
html = replace_once(
    html,
    '<p class="btc-truth-v1"><strong>Verified geometry:</strong> the gold circumference is bound only to BTC dominance. Surrounding trajectories identify context classes and do not imply measured weights.</p>',
    '<p class="btc-truth-v1"><strong>Verified geometry:</strong> the gold circumference is bound only to BTC dominance. Surrounding trajectories identify semantic context and do not represent additional measured variables.</p>',
    "BTC geometry wording",
)
html = replace_once(
    html,
    '<span>Bounded relational field</span><h3 id="aspect-cycle-v1">Aspect-Cycle Core</h3><p>Relates pressure, phase, event memory, BTC confirmation, and human review inside one bounded research field.</p>',
    '<span>Sealed semantic field</span><h3 id="aspect-cycle-v1">Aspect-Cycle Core</h3><p>Shows public semantic states only: pressure, phase, event memory, BTC confirmation, and human review.</p>',
    "Aspect-Cycle header seal",
)
html = replace_once(
    html,
    'aria-label="Aspect-Cycle relational field. The corridor is semantic and does not display internal calculation weights."',
    'aria-label="Aspect-Cycle sealed semantic field. Public nodes describe meaning only; protected calculation structure is not exposed."',
    "Aspect-Cycle aria seal",
)
html = replace_once(
    html,
    '</article></div>\n  </section>\n  <section class="btc-private-v1" aria-label="Private research depth">',
    '</article></div>\n    <p class="btc-cycle-seal-v0-1">Public semantics only · protected calculation structure sealed</p>\n  </section>\n  <section class="btc-private-v1" aria-label="Protected research aperture">',
    "Aspect-Cycle seal strip",
)
html = replace_once(
    html,
    '<div><span>Secondary depth</span><strong>Private research depth</strong></div><em>Source-bound · operator-reviewed · context-only</em>',
    '<div><span>Protected aperture</span><strong>Research depth by review</strong></div><em>Source-bound · operator-reviewed · no public method detail</em>',
    "protected research aperture copy",
)

# New scoped visual membrane layer.
seal_css = r'''/* CRYPTO_ASTRO_PUBLIC_IP_SEMANTIC_SEAL_v0_1:BEGIN
   Public surfaces show state and meaning. Source identity, collection logic,
   calibration, protected calculation structure, and private packet assembly remain sealed. */

.source-lanes-support-v0-1,
.temporal-support-v0-1 {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  min-height: 15rem;
}

.source-lanes-support-v0-1 > *,
.temporal-support-v0-1 > * {
  position: relative;
  z-index: 2;
}

.source-lanes-support-v0-1 {
  border-color: rgba(118, 173, 255, 0.24) !important;
  background:
    radial-gradient(ellipse at 24% 52%, rgba(91,157,255,0.12), transparent 31%),
    radial-gradient(ellipse at 76% 52%, rgba(91,157,255,0.08), transparent 31%),
    linear-gradient(145deg, rgba(3,8,18,0.98), rgba(8,18,38,0.78)) !important;
}

.source-lanes-support-v0-1::before,
.source-lanes-support-v0-1::after {
  content: "";
  position: absolute;
  z-index: 0;
  top: 34%;
  width: 42%;
  height: 48%;
  border: 1px solid rgba(118,173,255,0.18);
  border-radius: 50%;
  pointer-events: none;
  box-shadow: inset 0 0 44px rgba(91,157,255,0.035), 0 0 38px rgba(91,157,255,0.035);
}

.source-lanes-support-v0-1::before { left: 5%; transform: rotate(-8deg); }
.source-lanes-support-v0-1::after { right: 5%; transform: rotate(8deg); }

.source-lanes-support-v0-1 .source-lane-line {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.source-lanes-support-v0-1 .source-lane-line > div {
  min-height: 6.4rem;
  padding: 1rem;
  border: 1px solid rgba(118,173,255,0.18) !important;
  background: rgba(3,8,18,0.64) !important;
  backdrop-filter: blur(8px);
}

.source-lanes-support-v0-1 .source-lane-line > div:first-child {
  border-radius: 52% 20% 38% 18% / 38% 18% 54% 24%;
}

.source-lanes-support-v0-1 .source-lane-line > div:last-child {
  border-radius: 20% 52% 18% 38% / 18% 38% 24% 54%;
}

.source-lanes-support-v0-1 .source-lane-line strong {
  color: rgba(220,235,255,0.92);
  letter-spacing: 0.08em;
}

.source-lanes-support-v0-1 .lane-rail {
  height: 2px;
  margin-top: 0.9rem;
  background: linear-gradient(90deg, transparent, rgba(118,173,255,0.54), transparent);
  box-shadow: 0 0 16px rgba(91,157,255,0.20);
}

.temporal-support-v0-1 {
  border-color: rgba(245,199,106,0.24) !important;
  background:
    radial-gradient(circle at 73% 50%, rgba(245,199,106,0.14), transparent 18%),
    radial-gradient(circle at 73% 50%, transparent 0 25%, rgba(91,157,255,0.10) 25.4% 25.8%, transparent 26% 39%, rgba(245,199,106,0.08) 39.4% 39.8%, transparent 40%),
    linear-gradient(145deg, rgba(3,8,18,0.98), rgba(11,18,35,0.82)) !important;
}

.temporal-support-v0-1::before {
  content: "";
  position: absolute;
  z-index: 0;
  right: 8%;
  top: 20%;
  width: 8.5rem;
  aspect-ratio: 1;
  border: 1px solid rgba(245,199,106,0.28);
  border-right-color: transparent;
  border-radius: 50%;
  transform: rotate(28deg);
  box-shadow: 0 0 46px rgba(245,199,106,0.08);
}

.temporal-support-v0-1::after {
  content: "";
  position: absolute;
  z-index: 0;
  right: 15%;
  top: 16%;
  bottom: 16%;
  width: 1px;
  background: linear-gradient(transparent, rgba(118,173,255,0.46), rgba(245,199,106,0.42), transparent);
}

.btc-cycle-seal-v0-1 {
  width: fit-content;
  max-width: calc(100% - 2rem);
  margin: -0.15rem auto 0;
  padding: 0.62rem 1rem;
  border: 1px solid rgba(245,199,106,0.20);
  border-radius: 999px;
  color: rgba(229,215,178,0.82);
  background: rgba(3,8,18,0.78);
  font-size: 0.68rem;
  font-weight: 760;
  letter-spacing: 0.10em;
  text-align: center;
  text-transform: uppercase;
  box-shadow: 0 0 30px rgba(245,199,106,0.055);
}

.btc-private-v1[aria-label="Protected research aperture"] {
  border-color: rgba(118,173,255,0.18);
  background: linear-gradient(110deg, rgba(91,157,255,0.035), rgba(245,199,106,0.035));
}

@media (max-width: 720px) {
  .source-lanes-support-v0-1,
  .temporal-support-v0-1 { min-height: auto; }
  .source-lanes-support-v0-1 .source-lane-line { grid-template-columns: 1fr; }
  .source-lanes-support-v0-1 .source-lane-line > div { border-radius: 18px 34px !important; }
  .temporal-support-v0-1::before { right: -1.5rem; opacity: 0.58; }
  .temporal-support-v0-1::after { right: 1.5rem; opacity: 0.48; }
  .btc-cycle-seal-v0-1 { max-width: 94%; border-radius: 18px; }
}
/* CRYPTO_ASTRO_PUBLIC_IP_SEMANTIC_SEAL_v0_1:END */
'''

if "Φ" in seal_css:
    raise SystemExit("IP semantic seal CSS must not introduce a literal Phi")

import_line = "@import url('./ip_semantic_seal.css');"
if import_line not in system_css:
    anchor = "@import url('./btc_poster_grade.css');"
    if system_css.count(anchor) != 1:
        raise SystemExit(f"system.css poster import anchor count != 1: {system_css.count(anchor)}")
    system_css = system_css.replace(anchor, anchor + "\n" + import_line, 1)
if system_css.count(import_line) != 1:
    raise SystemExit(f"IP semantic seal import count != 1: {system_css.count(import_line)}")

# Fail-closed semantic assertions before writing.
required = (
    MARKER,
    "Field Membranes",
    "A · Prepared",
    "E · Prepared",
    "C/T · Bounded Context Membrane",
    "Sealed semantic field",
    "Public semantics only · protected calculation structure sealed",
    "Research depth by review",
    "https://www.bhrigu.io/crypto-astro/btc",
)
for token in required:
    if token not in html:
        raise SystemExit(f"required semantic token missing: {token}")

forbidden_global = (
    "prepared / search demand",
    "prepared / public discussion",
    "AstroPatterns memory",
    "Raw ephemerides",
)
for token in forbidden_global:
    if token.lower() in html.lower():
        raise SystemExit(f"forbidden public semantic token remains: {token}")

btc_start = html.index("<!-- BTC_PHI_CYCLE_HUB_SURFACE_LIFT_v0_1:BEGIN -->")
btc_end = html.index("<!-- BTC_PHI_CYCLE_HUB_SURFACE_LIFT_v0_1:END -->", btc_start)
btc_section = html[btc_start:btc_end].lower()
for token in ("semenko", "sun–pluto", "sun-pluto", "orbs", "ranked hits", "crypto-events overlay", "internal calculation weights"):
    if token in btc_section:
        raise SystemExit(f"protected Aspect-Cycle token remains: {token}")

if html.count("https://www.bhrigu.io/crypto-astro/btc") != 1:
    raise SystemExit("BTC Field Read route count drift")

HTML_PATH.write_text(html, encoding="utf-8")
SYSTEM_CSS_PATH.write_text(system_css, encoding="utf-8")
SEAL_CSS_PATH.write_text(seal_css, encoding="utf-8")

print("PUBLIC_IP_SEMANTIC_SEAL_PATCH=PASS")
