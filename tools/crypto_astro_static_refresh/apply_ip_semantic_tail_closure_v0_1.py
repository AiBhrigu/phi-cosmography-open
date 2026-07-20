#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path

HTML_PATH = Path("site/crypto-astro/index.html")
SNAPSHOT_PATH = Path("site/crypto-astro/data/crypto_astro_snapshot.public.json")
BINDINGS_PATH = Path("site/crypto-astro/data/crypto_astro_module_bindings.public.json")
MARKET_PATH = Path("site/crypto-astro/data/market_field_snapshot.public.v0_1.json")
SCORING_PATH = Path("site/crypto-astro/data/scoring_snapshot.public.json")
OPERATOR_REVIEW_PATH = Path("docs/crypto-astro-service/crypto_astro_operator_review.md")
HARDENED_PATH = Path("tools/crypto_astro_static_refresh/crypto_astro_static_refresh_hardened_v0_5.py")
PRIMARY_PATH = Path("tools/crypto_astro_static_refresh/crypto_astro_all_module_static_refresh_source_v0_1.py")

MARKER = "CRYPTO_ASTRO_IP_SEMANTIC_TAIL_CLOSURE_v0_1"


def replace_exact(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{label}: expected {expected}, found {count}")
    return text.replace(old, new)


def replace_regex(text: str, pattern: str, repl: str, label: str, expected: int = 1, flags: int = 0) -> str:
    updated, count = re.subn(pattern, repl, text, flags=flags)
    if count != expected:
        raise SystemExit(f"{label}: expected {expected}, found {count}")
    return updated


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


html = HTML_PATH.read_text(encoding="utf-8")
hardened = HARDENED_PATH.read_text(encoding="utf-8")
primary = PRIMARY_PATH.read_text(encoding="utf-8")
operator_review = OPERATOR_REVIEW_PATH.read_text(encoding="utf-8")
snapshot = read_json(SNAPSHOT_PATH)
bindings = read_json(BINDINGS_PATH)
market = read_json(MARKET_PATH)
scoring = read_json(SCORING_PATH)

# -----------------------------------------------------------------------------
# Public HTML: final accessibility, Cosmographer, and scoring-tail closure.
# -----------------------------------------------------------------------------
html = replace_exact(html, 'aria-label="Attention lane prepared"', 'aria-label="A membrane prepared"', "A barometer aria")
html = replace_exact(html, 'aria-label="Engagement lane prepared"', 'aria-label="E membrane prepared"', "E barometer aria")
html = replace_exact(html, 'aria-label="A/E/M Field Barometer visual state"', 'aria-label="Field Membrane Barometer visual state"', "barometer visual aria")
html = replace_exact(html, 'M active · A/E pending · static context', 'M active · membranes prepared · static context', "field state badge")
html = replace_exact(html, 'A/E lanes remain pending calibration.', 'Prepared field membranes remain inactive.', "field state membrane copy")
html = replace_exact(html, '<span>Pressure</span><strong data-copy-slot="state_pressure_status">A/E pending</strong>', '<span>Membranes</span><strong data-copy-slot="state_pressure_status">Prepared</strong>', "field state status")
html = replace_exact(html, 'Static context is bounded; A/E confirmation is not available.', 'Static context is bounded; prepared membrane inputs are inactive.', "field synthesis lead")
html = replace_exact(html, '<span>A/E/M Field Barometer</span>', '<span>Field Membrane Barometer</span>', "Cosmographer method label")

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
html = replace_exact(html, 'aria-label="How context is prepared"', 'aria-label="Public output boundary"', "scoring boundary aria")
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

# -----------------------------------------------------------------------------
# Canonical primary runner: future snapshots no longer publish per-asset A/E.
# -----------------------------------------------------------------------------
primary = replace_exact(
    primary,
    '                "M": round(abs(float(a.get("price_change_percentage_24h_in_currency") or a.get("price_change_percentage_24h") or 0)) / 10, 4),\n                "A_state": "calibration_pending",\n                "E_state": "calibration_pending",\n                "M_state": "market_context_active",\n                "visible_state_label": "Market context active · A/E pending",',
    '                "M": round(abs(float(a.get("price_change_percentage_24h_in_currency") or a.get("price_change_percentage_24h") or 0)) / 10, 4),\n                "membrane_state": "prepared_inactive",\n                "M_state": "market_context_active",\n                "visible_state_label": "Market context active · prepared membranes inactive",',
    "primary sample membrane schema",
)
primary = replace_exact(primary, '"anchor": "A/E/M Field Barometer"', '"anchor": "Field Membrane Barometer"', "primary binding anchor")
primary = replace_exact(primary, '- A/E/M Field Barometer', '- Field Membrane Barometer', "primary operator review module")

# -----------------------------------------------------------------------------
# Hardened refresh: semantic copy and derived public packets persist safely.
# -----------------------------------------------------------------------------
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

vectors_pattern = r"        'vectors': \{.*?        \},\n        'field_output': field,"
vectors_replacement = """        'vectors': {
            'A_membrane': {
                'state': 'prepared_inactive',
                'public_input': False,
                'disclosure': 'status_only'
            },
            'E_membrane': {
                'state': 'prepared_inactive',
                'public_input': False,
                'disclosure': 'status_only'
            },
            'M_market': {
                'state': 'market_vector_active',
                'source_class': 'public_market_liquidity',
                'total_market_cap_usd': mr.get('total_market_cap_usd'),
                'market_cap_change_24h_pct': mr.get('market_cap_change_24h_pct'),
                'volume_24h_usd': mr.get('volume_24h_usd'),
                'btc_dominance_pct': mr.get('btc_dominance_pct'),
                'stablecoin_share_pct': mr.get('stablecoin_share_pct'),
                'stablecoin_cap_usd': liq.get('stablecoin_cap_usd') or mr.get('stablecoin_cap_usd'),
                'defi_tvl_usd': liq.get('defi_tvl_usd'),
                'defi_tvl_source_label': liq.get('defi_tvl_source_label'),
                'defi_tvl_canonical_source_id': liq.get('defi_tvl_canonical_source_id'),
                'defi_tvl_source_url': liq.get('defi_tvl_source_url'),
                'defi_tvl_source_timestamp_utc': liq.get('defi_tvl_source_timestamp_utc'),
                'defi_tvl_methodology_id': liq.get('defi_tvl_methodology_id'),
                'defi_tvl_methodology': liq.get('defi_tvl_methodology'),
                'defi_tvl_excludes_liquid_staking': liq.get('defi_tvl_excludes_liquid_staking'),
                'defi_tvl_excludes_double_counted': liq.get('defi_tvl_excludes_double_counted'),
                'dex_volume_24h_usd': liq.get('dex_volume_24h_usd'),
                'market_breadth_pct': (snapshot.get('altcoin_rotation') or {}).get('alt_breadth_24h_pct'),
                'liquidity_health': liq.get('liquidity_context_state') or 'context_only'
            },
            'CT_context': {
                'state': 'bounded',
                'observation_window': 'public_context',
                'phase_context': 'public_context',
                'provenance': 'source_bound',
                'pipeline': 'sealed'
            }
        },
        'field_output': field,"""
hardened = replace_regex(hardened, vectors_pattern, vectors_replacement, "hardened public vector schema", flags=re.S)

hardened = replace_exact(
    hardened,
    "        'cosmographer_read': {\n            'state': field.get('regime_label') or 'Static public context',\n            'meaning': 'M-vector is active while A/E lanes remain prepared for calibration.',\n            'direction': 'Watch liquidity depth, stablecoin flow, and future attention / engagement confirmation.',\n            'key_watch': 'If attention rises without liquidity depth, noise risk increases.',\n            'boundary': 'Scenario-only context. Not a price forecast. Not a trading signal.'\n        },",
    "        'cosmographer_read': {\n            'state': field.get('regime_label') or 'Static public context',\n            'meaning': 'Market context is active while prepared membranes remain inactive.',\n            'direction': 'Watch liquidity depth, stablecoin flow, breadth, and source freshness.',\n            'key_watch': 'If breadth expands without liquidity depth, noise risk increases.',\n            'boundary': 'Scenario-only context. Not a price forecast. Not a trading signal.'\n        },",
    "hardened Cosmographer derived copy",
)
hardened = replace_exact(
    hardened,
    "            'A_lane': 'calibration_pending',\n            'E_lane': 'calibration_pending',\n            'M_lane': 'market_context_active'",
    "            'A_membrane': 'prepared_inactive',\n            'E_membrane': 'prepared_inactive',\n            'M_market': 'market_context_active'",
    "hardened scoring coverage",
)
hardened = replace_exact(
    hardened,
    "        'public_state_label': 'Static public context · A/E pending · M active'",
    "        'public_state_label': 'Static public context · prepared membranes inactive · M active'",
    "hardened scoring public state",
)

# Primary runner hash remains fail-closed after primary source edits.
old_primary_hash = hashlib.sha256(PRIMARY_PATH.read_bytes()).hexdigest()
expected_match = re.search(r'EXPECTED_PRIMARY_SHA256 = "([0-9a-f]{64})"', hardened)
if not expected_match:
    raise SystemExit("hardened expected primary SHA anchor missing")
if expected_match.group(1) != old_primary_hash:
    raise SystemExit(f"primary SHA precondition mismatch: expected={expected_match.group(1)} actual={old_primary_hash}")
new_primary_hash = hashlib.sha256(primary.encode("utf-8")).hexdigest()
hardened = replace_regex(
    hardened,
    r'EXPECTED_PRIMARY_SHA256 = "[0-9a-f]{64}"',
    f'EXPECTED_PRIMARY_SHA256 = "{new_primary_hash}"',
    "hardened primary SHA",
)

# -----------------------------------------------------------------------------
# Existing public artifacts: semantic structure only; numeric values preserved.
# -----------------------------------------------------------------------------
for asset in (snapshot.get("public_samples") or {}).get("assets", {}).values():
    asset.pop("A_state", None)
    asset.pop("E_state", None)
    asset["membrane_state"] = "prepared_inactive"
    asset["visible_state_label"] = "Market context active · prepared membranes inactive"

market["schema_version"] = "crypto_astro_market_field_public_v0_2"
old_vectors = market.get("vectors") or {}
m_market = old_vectors.get("M_market")
if not isinstance(m_market, dict):
    raise SystemExit("current M_market vector missing")
market["vectors"] = {
    "A_membrane": {"state": "prepared_inactive", "public_input": False, "disclosure": "status_only"},
    "E_membrane": {"state": "prepared_inactive", "public_input": False, "disclosure": "status_only"},
    "M_market": m_market,
    "CT_context": {
        "state": "bounded",
        "observation_window": "public_context",
        "phase_context": "public_context",
        "provenance": "source_bound",
        "pipeline": "sealed",
    },
}
market["cosmographer_read"] = {
    "state": (market.get("field_output") or {}).get("regime_label") or "Static public context",
    "meaning": "Market context is active while prepared membranes remain inactive.",
    "direction": "Watch liquidity depth, stablecoin flow, breadth, and source freshness.",
    "key_watch": "If breadth expands without liquidity depth, noise risk increases.",
    "boundary": "Scenario-only context. Not a price forecast. Not a trading signal.",
}

coverage = scoring.get("coverage") or {}
for key in ("A_lane", "E_lane", "M_lane"):
    coverage.pop(key, None)
coverage.update({
    "A_membrane": "prepared_inactive",
    "E_membrane": "prepared_inactive",
    "M_market": "market_context_active",
})
for asset in (scoring.get("assets") or {}).values():
    asset.pop("A_state", None)
    asset.pop("E_state", None)
    asset["membrane_state"] = "prepared_inactive"
    asset["visible_state_label"] = "Market context active · prepared membranes inactive"
scoring["public_state_label"] = "Static public context · prepared membranes inactive · M active"

modules = bindings.get("modules") or {}
barometer = modules.get("aem_barometer") or {}
if barometer.get("anchor") != "A/E/M Field Barometer":
    raise SystemExit(f"binding anchor precondition mismatch: {barometer.get('anchor')}")
barometer["anchor"] = "Field Membrane Barometer"
operator_review = replace_exact(operator_review, "- A/E/M Field Barometer", "- Field Membrane Barometer", "current operator review module")

# -----------------------------------------------------------------------------
# Global fail-closed assertions across public surface, packets, and generators.
# -----------------------------------------------------------------------------
forbidden_html = (
    "Search demand source slot", "Public discussion source slot",
    "Attention source class", "Engagement source class",
    "A = attention slot", "E = engagement slot",
    "A/E lanes remain pending calibration", "A/E confirmation is not available",
    "A/E/M Field Barometer", "How context is prepared", "Raw signals",
)
html_lower = html.lower()
for token in forbidden_html:
    if token.lower() in html_lower:
        raise SystemExit(f"forbidden public tail token remains: {token}")

required_html = (
    MARKER, "Field Membrane Barometer", "Public membrane states",
    "Public output boundary", "prepared membranes inactive",
    "protected scoring sealed", "https://www.bhrigu.io/crypto-astro/btc",
)
for token in required_html:
    if token.lower() not in html_lower:
        raise SystemExit(f"required public tail token missing: {token}")
if html.count("https://www.bhrigu.io/crypto-astro/btc") != 1:
    raise SystemExit("BTC Field Read route count drift")

public_packets = json.dumps(
    {"snapshot": snapshot, "market": market, "scoring": scoring, "bindings": bindings},
    ensure_ascii=False,
).lower()
forbidden_packets = (
    "a_attention", "e_engagement", "ct_temporal", "search_attention",
    "x_social_engagement", "search_pressure", "query_acceleration", "topic_heat",
    "attention_divergence", "discussion_pressure", "narrative_velocity",
    "engagement_acceleration", "social_amplification", "ephemerides_support",
    "future attention", "engagement confirmation", "a/e pending",
)
for token in forbidden_packets:
    if token in public_packets:
        raise SystemExit(f"forbidden public packet token remains: {token}")

for token in ("A_state", "E_state", "A/E pending", "A/E/M Field Barometer"):
    if token in primary:
        raise SystemExit(f"old primary public generator token remains: {token}")
for token in (
    "A_attention", "E_engagement", "CT_temporal", "search_attention",
    "x_social_engagement", "ephemerides_support", "future attention / engagement",
    "A/E pending", "A/E confirmation is not available",
):
    if token in hardened:
        raise SystemExit(f"old hardened public generator token remains: {token}")
if hashlib.sha256(primary.encode("utf-8")).hexdigest() != new_primary_hash:
    raise SystemExit("primary runner hash unstable")

HTML_PATH.write_text(html, encoding="utf-8")
PRIMARY_PATH.write_text(primary, encoding="utf-8")
HARDENED_PATH.write_text(hardened, encoding="utf-8")
OPERATOR_REVIEW_PATH.write_text(operator_review, encoding="utf-8")
write_json(SNAPSHOT_PATH, snapshot)
write_json(BINDINGS_PATH, bindings)
write_json(MARKET_PATH, market)
write_json(SCORING_PATH, scoring)

print(f"IP_SEMANTIC_TAIL_CLOSURE=PASS primary_sha256={new_primary_hash}")
