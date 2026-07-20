#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path

HTML_PATH = Path("site/crypto-astro/index.html")
HARDENED_PATH = Path("tools/crypto_astro_static_refresh/crypto_astro_static_refresh_hardened_v0_5.py")
PRIMARY_PATH = Path("tools/crypto_astro_static_refresh/crypto_astro_all_module_static_refresh_source_v0_1.py")
BINDINGS_PATH = Path("site/crypto-astro/data/crypto_astro_module_bindings.public.json")

MARKER = "CRYPTO_ASTRO_IP_SEMANTIC_TAIL_CLOSURE_v0_1"


def replace_exact(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{label}: expected {expected}, found {count}")
    return text.replace(old, new)


html = HTML_PATH.read_text(encoding="utf-8")
hardened = HARDENED_PATH.read_text(encoding="utf-8")
primary = PRIMARY_PATH.read_text(encoding="utf-8")
bindings = json.loads(BINDINGS_PATH.read_text(encoding="utf-8"))

# Accessibility and Cosmographer public-copy closure.
html = replace_exact(html, 'aria-label="Attention lane prepared"', 'aria-label="A membrane prepared"', "A barometer aria")
html = replace_exact(html, 'aria-label="Engagement lane prepared"', 'aria-label="E membrane prepared"', "E barometer aria")
html = replace_exact(html, 'M active · A/E pending · static context', 'M active · membranes prepared · static context', "field state badge")
html = replace_exact(html, 'A/E lanes remain pending calibration.', 'Prepared field membranes remain inactive.', "field state membrane copy")
html = replace_exact(html, '<span>Pressure</span><strong data-copy-slot="state_pressure_status">A/E pending</strong>', '<span>Membranes</span><strong data-copy-slot="state_pressure_status">Prepared</strong>', "field state status")
html = replace_exact(html, 'Static context is bounded; A/E confirmation is not available.', 'Static context is bounded; prepared membrane inputs are inactive.', "field synthesis lead")
html = replace_exact(html, '<span>A/E/M Field Barometer</span>', '<span>Field Membrane Barometer</span>', "Cosmographer method label")

# Scoring preview becomes status/output only; input taxonomy and preparation sequence are sealed.
html = replace_exact(
    html,
    '<!-- ORION_SCORING_LOOP_PREVIEW_v0_1:BEGIN -->',
    '<!-- ORION_SCORING_LOOP_PREVIEW_v0_1:BEGIN -->\n<!-- CRYPTO_ASTRO_IP_SEMANTIC_TAIL_CLOSURE_v0_1:BEGIN -->',
    "tail closure begin marker",
)
html = replace_exact(
    html,
    'Read-only market context for BTC / ETH / SOL; snapshot coverage also includes TON / ICP. A/E and Φ scoring lanes remain in calibration.',
    'Read-only market context for BTC / ETH / SOL; snapshot coverage also includes TON / ICP. Prepared membranes are inactive and protected scoring remains sealed.',
    "scoring intro",
)
html = replace_exact(html, 'Φ balance: Calibration', 'Structural state: Calibration', "scoring card title", expected=3)
html = replace_exact(html, 'A/E/M differentiation pending', 'Public membrane inputs inactive', "scoring card membrane state", expected=3)
html = replace_exact(html, 'Phase windows: w1 / w3 / w7', 'Bounded phase context', "scoring card phase copy", expected=3)
html = replace_exact(html, '<div class="scoring-chip"><strong>A</strong><span>Attention source class · pending</span></div>', '<div class="scoring-chip"><strong>A</strong><span>Prepared membrane · inactive</span></div>', "scoring A chip")
html = replace_exact(html, '<div class="scoring-chip"><strong>E</strong><span>Engagement source class · pending</span></div>', '<div class="scoring-chip"><strong>E</strong><span>Prepared membrane · inactive</span></div>', "scoring E chip")
html = replace_exact(html, '<div class="scoring-chip"><strong>M</strong><span>24h market movement context · active</span></div>', '<div class="scoring-chip"><strong>M</strong><span>Market context · active</span></div>', "scoring M chip")
html = replace_exact(html, '<div class="scoring-chip"><strong>Φ Balance</strong><span>Structural score</span></div>', '<div class="scoring-chip"><strong>Structural state</strong><span>Public output</span></div>', "scoring structural output")
html = replace_exact(html, '<div class="scoring-chip"><strong>Φ Resonance</strong><span>Dynamic state</span></div>', '<div class="scoring-chip"><strong>Dynamic state</strong><span>Public output</span></div>', "scoring dynamic output")
html = replace_exact(html, '<div class="scoring-chip"><strong>Sem Phase</strong><span>Phase window</span></div>', '<div class="scoring-chip"><strong>Phase state</strong><span>Bounded output</span></div>', "scoring phase output")
html = replace_exact(html, '<p class="eyebrow scoring-subhead">Signal inputs</p>', '<p class="eyebrow scoring-subhead">Public membrane states</p>', "scoring membrane subhead")
html = replace_exact(html, '<p class="small">A/E are prepared source slots. M is the active read-only market context.</p>', '<p class="small">A/E expose status only. Public input remains inactive; M is the active read-only market context.</p>', "scoring membrane status")
html = replace_exact(html, '<div class="scoring-chip"><strong>A · Attention Context</strong><span>Search demand source slot<br/>pending calibration</span></div>', '<div class="scoring-chip"><strong>A · Prepared membrane</strong><span>public input inactive<br/>source logic sealed</span></div>', "scoring A input")
html = replace_exact(html, '<div class="scoring-chip"><strong>E · Engagement Context</strong><span>Public discussion source slot<br/>pending calibration</span></div>', '<div class="scoring-chip"><strong>E · Prepared membrane</strong><span>public input inactive<br/>source logic sealed</span></div>', "scoring E input")
html = replace_exact(html, '<div class="scoring-chip"><strong>M · Market Momentum</strong><span>Market context<br/>static public snapshot</span></div>', '<div class="scoring-chip"><strong>M · Market context</strong><span>active read-only state<br/>static public snapshot</span></div>', "scoring M input")
html = replace_exact(html, '<p class="eyebrow scoring-subhead scoring-calc-subhead">How context is prepared</p>', '<p class="eyebrow scoring-subhead scoring-calc-subhead">Public output boundary</p>', "scoring boundary subhead")
html = replace_exact(html, '<p class="small scoring-calc-intro">The public layer prepares market context first. A/E, Φ Balance, Φ Resonance, and phase context remain calibration layers.</p>', '<p class="small scoring-calc-intro">The public layer shows state and bounded outputs only. Collection, normalization, calibration, and formula logic remain protected.</p>', "scoring boundary intro")
html = replace_exact(html, '<div class="scoring-chip"><strong>1 · Raw signals</strong><span>prepared A/E slots · market context · calibration layers</span></div>', '<div class="scoring-chip"><strong>1 · Market context</strong><span>active · static · source-bound</span></div>', "scoring boundary card 1")
html = replace_exact(html, '<div class="scoring-chip"><strong>2 · A/E/M vector</strong><span>A = attention slot<br/>E = engagement slot<br/>M = market context</span></div>', '<div class="scoring-chip"><strong>2 · Prepared membranes</strong><span>A/E inactive<br/>status only</span></div>', "scoring boundary card 2")
html = replace_exact(html, '<div class="scoring-chip"><strong>3 · Normalize</strong><span>context fields stay separated until formula audit</span></div>', '<div class="scoring-chip"><strong>3 · Protected scoring</strong><span>calibration and formula logic sealed</span></div>', "scoring boundary card 3")
html = replace_exact(html, '<div class="scoring-chip"><strong>4 · Φ Balance</strong><span>calibration layer · not active scoring</span></div>', '<div class="scoring-chip"><strong>4 · Structural output</strong><span>public state only</span></div>', "scoring boundary card 4")
html = replace_exact(html, '<div class="scoring-chip"><strong>5 · Φ Resonance</strong><span>calibration layer · not active scoring</span></div>', '<div class="scoring-chip"><strong>5 · Dynamic output</strong><span>public state only</span></div>', "scoring boundary card 5")
html = replace_exact(html, '<div class="scoring-chip"><strong>6 · Sem Phase</strong><span>phase layer pending calibration</span></div>', '<div class="scoring-chip"><strong>6 · Phase output</strong><span>bounded state only</span></div>', "scoring boundary card 6")
html = replace_exact(html, '<p class="small scoring-state-note">Market context active · A/E source classes pending · Not a trading signal.</p>', '<p class="small scoring-state-note">Market context active · prepared membranes inactive · protected scoring sealed · Not a trading signal.</p>', "scoring state note")
html = replace_exact(
    html,
    '<!-- ORION_SCORING_LOOP_PREVIEW_v0_1:END -->',
    '<!-- CRYPTO_ASTRO_IP_SEMANTIC_TAIL_CLOSURE_v0_1:END -->\n<!-- ORION_SCORING_LOOP_PREVIEW_v0_1:END -->',
    "tail closure end marker",
)

# Refresh persistence: update public-copy constants without changing calculations.
hardened = replace_exact(
    hardened,
    "'and DEX context use reviewed DefiLlama sources. A/E lanes remain prepared until source policy '\n    'and calibration are reviewed. This is a static public snapshot, not a live adapter.'",
    "'and DEX context use reviewed DefiLlama sources. Prepared field membranes remain inactive; source policy '\n    'and calibration stay protected. This is a static public snapshot, not a live adapter.'",
    "hardened DeFi public copy",
)
hardened = replace_exact(hardened, "'field_state_badge': 'M active · A/E pending · static context'", "'field_state_badge': 'M active · membranes prepared · static context'", "runner field badge")
hardened = replace_exact(hardened, '"A/E lanes remain pending calibration."', '"Prepared field membranes remain inactive."', "runner field body")
hardened = replace_exact(hardened, "'state_pressure_status': 'A/E pending'", "'state_pressure_status': 'Prepared'", "runner membrane status")
hardened = replace_exact(hardened, "'field_synthesis_lead': 'Static context is bounded; A/E confirmation is not available.'", "'field_synthesis_lead': 'Static context is bounded; prepared membrane inputs are inactive.'", "runner synthesis lead")

# Public binding anchor follows the renamed visual module; internal compatibility key stays stable.
old_primary_hash = hashlib.sha256(primary.encode("utf-8")).hexdigest()
expected_match = re.search(r'EXPECTED_PRIMARY_SHA256 = "([0-9a-f]{64})"', hardened)
if not expected_match:
    raise SystemExit("hardened expected primary SHA anchor missing")
if expected_match.group(1) != old_primary_hash:
    raise SystemExit(f"primary SHA precondition mismatch: expected={expected_match.group(1)} actual={old_primary_hash}")
primary = replace_exact(primary, '"anchor": "A/E/M Field Barometer"', '"anchor": "Field Membrane Barometer"', "primary binding anchor")
new_primary_hash = hashlib.sha256(primary.encode("utf-8")).hexdigest()
hardened, hash_count = re.subn(
    r'EXPECTED_PRIMARY_SHA256 = "[0-9a-f]{64}"',
    f'EXPECTED_PRIMARY_SHA256 = "{new_primary_hash}"',
    hardened,
)
if hash_count != 1:
    raise SystemExit(f"hardened primary SHA replacement count != 1: {hash_count}")

modules = bindings.get("modules") or {}
barometer = modules.get("aem_barometer") or {}
if barometer.get("anchor") != "A/E/M Field Barometer":
    raise SystemExit(f"binding anchor precondition mismatch: {barometer.get('anchor')}")
barometer["anchor"] = "Field Membrane Barometer"

# Global fail-closed public vocabulary check.
forbidden_html = (
    "Search demand source slot",
    "Public discussion source slot",
    "Attention source class",
    "Engagement source class",
    "A = attention slot",
    "E = engagement slot",
    "A/E lanes remain pending calibration",
    "A/E confirmation is not available",
    "A/E/M Field Barometer",
    "How context is prepared",
    "Raw signals",
)
html_lower = html.lower()
for token in forbidden_html:
    if token.lower() in html_lower:
        raise SystemExit(f"forbidden public tail token remains: {token}")

required_html = (
    MARKER,
    "Field Membrane Barometer",
    "Public membrane states",
    "Public output boundary",
    "prepared membranes inactive",
    "protected scoring sealed",
    "https://www.bhrigu.io/crypto-astro/btc",
)
for token in required_html:
    if token.lower() not in html_lower:
        raise SystemExit(f"required public tail token missing: {token}")

if html.count("https://www.bhrigu.io/crypto-astro/btc") != 1:
    raise SystemExit("BTC Field Read route count drift")
if "A/E lanes remain prepared until source policy" in hardened:
    raise SystemExit("old hardened source-lane copy remains")
if "A/E pending" in hardened or "A/E confirmation is not available" in hardened:
    raise SystemExit("old hardened A/E copy remains")
if hashlib.sha256(primary.encode("utf-8")).hexdigest() != new_primary_hash:
    raise SystemExit("primary runner hash unstable")

HTML_PATH.write_text(html, encoding="utf-8")
PRIMARY_PATH.write_text(primary, encoding="utf-8")
HARDENED_PATH.write_text(hardened, encoding="utf-8")
BINDINGS_PATH.write_text(json.dumps(bindings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"IP_SEMANTIC_TAIL_CLOSURE=PASS primary_sha256={new_primary_hash}")
