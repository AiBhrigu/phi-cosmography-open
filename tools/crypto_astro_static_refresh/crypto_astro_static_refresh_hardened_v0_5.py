#!/usr/bin/env python3
"""
CRYPTO_ASTRO_STATIC_REFRESH_AUTOMATED_RUNNER_v0_5

Purpose:
- Reuse the existing all-module static refresh runner as the source base.
- Patch only the operational wrapper surface needed for a debt-free refresh:
  new branch, critical source gate, derived JSON sync, HTML anchor validation,
  stale timestamp validation, and report/sha output.
- No commit, no push, no deploy.

Usage:
  python3 scripts/crypto_astro_static_refresh_hardened_v0_4.py REPO_PATH OUT_DIR

Default paths are tuned for the operator's ORION_ATOMS workspace.
"""
import json
import os
import re
import sys
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone

NODE = "CRYPTO_ASTRO_STATIC_REFRESH_AUTOMATED_RUNNER_v0_5"
PRIMARY_RUNNER_DEFAULT = Path(os.environ.get('CRYPTO_ASTRO_PRIMARY_RUNNER', str(Path(__file__).resolve().parent / 'crypto_astro_all_module_static_refresh_source_v0_1.py')))
EXPECTED_PRIMARY_SHA256 = "60173876e69a30aaeace38f31ae9968f34008ed79bf39ef5cf275b5d75b99a6e"
OLD_BRANCH = 'feature/crypto-astro-all-module-static-refresh-v0-1'
NEW_BRANCH = os.environ.get('CRYPTO_ASTRO_REFRESH_BRANCH', 'automation/crypto-astro-static-refresh-manual-v0-5')
BASE_BRANCH = 'main'
OLD_ACTIVE_TIMESTAMPS = [
    '2026-07-08T18:57:45Z',
    '2026-07-08T18:57:36Z',
]
CRITICAL_SOURCES = {
    'coingecko_global',
    'coingecko_asset_markets_btc_eth_sol_ton_icp',
    'coingecko_top250_markets',
}
OPTIONAL_SOURCES = {
    'coingecko_stablecoin_sample',
    'defillama_protocols',
    'defillama_dex_overview',
    'defillama_stablecoins',
}
AFFECTED_FILES = [
    'site/crypto-astro/index.html',
    'site/crypto-astro/data/crypto_astro_snapshot.public.json',
    'site/crypto-astro/data/crypto_astro_snapshot_proof.public.json',
    'site/crypto-astro/data/crypto_astro_module_bindings.public.json',
    'site/crypto-astro/data/crypto_astro_module_bindings.public.schema.json',
    'site/crypto-astro/data/market_field_snapshot.public.v0_1.json',
    'site/crypto-astro/data/scoring_snapshot.public.json',
    'docs/crypto-astro-service/crypto_astro_snapshot_summary.md',
    'docs/crypto-astro-service/crypto_astro_operator_review.md',
]
FORBIDDEN_POSITIVE_CLAIMS = [
    r'(?i)live adapter\s+(is\s+)?active',
    r'(?i)true live feed\s+(is\s+)?active',
    r'(?i)payment\s+(is\s+)?active',
    r'(?i)api access\s+(is\s+)?active',
    r'(?i)backend runtime\s+(is\s+)?active',
    r'(?i)investment recommendation\s*:',
    r'(?i)price target\s*:',
]
BOUNDARY = {
    'read_only': True,
    'static_public_snapshot': True,
    'no_live_adapter_claim': True,
    'no_true_live_feed_claim': True,
    'no_trading_signal': True,
    'no_forecast': True,
    'no_price_target': True,
    'no_investment_recommendation': True,
    'backend_api_closed': True,
    'runtime_closed': True,
    'payment_closed': True,
    'orion_core_protected': True,
    'formula_weights_exposed': False,
}


def set_validation(report: dict, key: str, value):
    report.setdefault('validation', {})[key] = value
    report[key] = value
    return value


def append_validation_summary(report: dict):
    validation = report.setdefault('validation', {})
    validation['summary'] = {
        'critical_sources_ok': not validation.get('critical_missing') and not validation.get('critical_failed'),
        'html_anchors_ok': not validation.get('html_required_missing'),
        'stale_timestamps_ok': not validation.get('stale_timestamp_hits'),
        'forbidden_claims_ok': not validation.get('forbidden_positive_claim_hits'),
        'unexpected_files_ok': not validation.get('unexpected_changed_files'),
    }
    return validation['summary']


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def write_text(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def run(cmd, cwd: Path, check=True):
    p = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\nSTDOUT={p.stdout}\nSTDERR={p.stderr}")
    return p


def parse_git_status_path(line: str) -> str:
    """Parse git status --short/porcelain path robustly.

    Older hardening wrappers assumed every line has a three-character prefix
    (`XY `). Some environments may emit a compact `M path` shape, which
    caused `docs/...` to be truncated to `ocs/...` and falsely blocked an
    allowed docs file. This parser keeps the full path for both shapes and
    handles rename records by validating the destination path.
    """
    raw = (line or '').rstrip('\n')
    if not raw:
        return ''
    # Standard porcelain: two status columns followed by space, e.g. " M docs/x".
    if len(raw) >= 4 and raw[2] == ' ':
        path = raw[3:].strip()
    else:
        parts = raw.split(None, 1)
        path = parts[1].strip() if len(parts) == 2 else raw.strip()
    # Rename/copy notation: old -> new. Validate the new path.
    if ' -> ' in path:
        path = path.split(' -> ', 1)[1].strip()
    return path


def usd_compact(n):
    if n is None:
        return 'pending'
    n = float(n)
    if abs(n) >= 1e12:
        return f"${n/1e12:.3f}T"
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"


def pct(v, decimals=1):
    if v is None:
        return 'pending'
    return f"{float(v):.{decimals}f}%"


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))


def replace_counted(html: str, pattern: str, repl, label: str, counts: dict, flags=0) -> str:
    new, n = re.subn(pattern, repl, html, flags=flags)
    counts[label] = n
    return new


def replace_metric_card(html: str, label: str, value: str, counts: dict) -> str:
    # Updates all matching metric cards while preserving inner rail markup.
    esc = re.escape(label)
    pattern = rf'(<div class="market-metric" aria-label="{esc} )[^\"]+(\"><span>{esc}</span><strong>)[^<]+(</strong>)'
    return replace_counted(html, pattern, lambda m: f"{m.group(1)}{value}{m.group(2)}{value}{m.group(3)}", f"metric:{label}", counts)


def patch_html(repo: Path, snapshot: dict) -> dict:
    path = repo / 'site/crypto-astro/index.html'
    html = read_text(path)
    counts = {}
    generated_at = snapshot.get('generated_at_utc') or now_iso()
    mr = snapshot.get('market_reality') or {}
    liq = snapshot.get('liquidity_tvl') or {}
    alt = snapshot.get('altcoin_rotation') or {}
    vals = {
        'market_cap': usd_compact(mr.get('total_market_cap_usd')),
        'volume': usd_compact(mr.get('volume_24h_usd')),
        'btc_dom': pct(mr.get('btc_dominance_pct'), 1),
        'stable_share': pct(mr.get('stablecoin_share_pct'), 1),
        'stable_cap': usd_compact(liq.get('stablecoin_cap_usd')),
        'defi_tvl': usd_compact(liq.get('defi_tvl_usd')),
        'dex_volume': usd_compact(liq.get('dex_volume_24h_usd')),
        'alt24': pct(alt.get('alt_breadth_24h_pct'), 1),
        'alt7': pct(alt.get('alt_breadth_7d_pct'), 1),
        'top10': pct(alt.get('top_10_flow_concentration_pct'), 1),
    }
    html = replace_metric_card(html, 'Market Cap', vals['market_cap'], counts)
    html = replace_metric_card(html, '24h Volume', vals['volume'], counts)
    html = replace_metric_card(html, 'BTC Dominance', vals['btc_dom'], counts)
    # CRYPTO_ASTRO_V10_BTC_HUB_BINDING_MICROPATCH_v0_1
    html = replace_counted(
        html,
        r'(<div class="btc-phi-cycle-metric-v0-1"><span>BTC Gravity</span><strong>)[^<]+(</strong></div>)',
        lambda m: f"{m.group(1)}{vals['btc_dom']}{m.group(2)}",
        'btc_hub:gravity',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="btc-phi-cycle-metric-v0-1"><span>Snapshot</span><strong>)[^<]+(</strong></div>)',
        lambda m: f"{m.group(1)}{generated_at}{m.group(2)}",
        'btc_hub:snapshot',
        counts,
    )
    for required_binding in ('btc_hub:gravity', 'btc_hub:snapshot'):
        if counts.get(required_binding) != 1:
            raise RuntimeError(
                f"BTC Hub binding count mismatch: "
                f"{required_binding}={counts.get(required_binding, 0)}"
            )
    html = replace_metric_card(html, 'Stablecoin Share', vals['stable_share'], counts)
    html = replace_metric_card(html, 'Alt Breadth 24h', vals['alt24'], counts)
    html = replace_metric_card(html, 'Alt Breadth 7d', vals['alt7'], counts)
    html = replace_metric_card(html, 'Top-10 Flow Concentration', vals['top10'], counts)
    # Rail widths tied to visible values.
    def width_num(v):
        try:
            return f"{clamp(float(str(v).replace('%',''))):.1f}%"
        except Exception:
            return '0.0%'
    rail_map = {
        'dominance': width_num(vals['btc_dom']),
        'stable': width_num(vals['stable_share']),
        'alt-24h': width_num(vals['alt24']),
        'alt-7d': width_num(vals['alt7']),
        'volume-concentration': width_num(vals['top10']),
    }
    for klass, width in rail_map.items():
        html = replace_counted(html, rf'(\.metric-rail\.{re.escape(klass)} i \{{ width:)[^;]+(; \}})', lambda m, w=width: f"{m.group(1)}{w}{m.group(2)}", f"rail:{klass}", counts)
    # Composition/map labels.
    html = replace_counted(html, r'<div class="composition-core">BTC<br>[^<]+</div>', f'<div class="composition-core">BTC<br>{vals["btc_dom"]}</div>', 'composition:btc', counts)
    html = replace_counted(html, r'<div class="composition-node stable">Stable<br>[^<]+</div>', f'<div class="composition-node stable">Stable<br>{vals["stable_share"]}</div>', 'composition:stable', counts)
    html = replace_counted(html, r'<div class="composition-node alt">Alt<br>[^<]+</div>', f'<div class="composition-node alt">Alt<br>{vals["alt24"]} / {vals["alt7"]}</div>', 'composition:alt', counts)
    html = replace_counted(html, r'(<div class="composition-label"><span>BTC Gravity</span><strong>)[^<]+(</strong></div>)', lambda m: f"{m.group(1)}{vals['btc_dom']}{m.group(2)}", 'label:btc_gravity', counts)
    html = replace_counted(html, r'(<div class="composition-label"><span>Stablecoin Membrane</span><strong>)[^<]+(</strong></div>)', lambda m: f"{m.group(1)}{vals['stable_share']}{m.group(2)}", 'label:stable_membrane', counts)
    html = replace_counted(html, r'(<div class="composition-label"><span>Alt Field</span><strong>)[^<]+(</strong></div>)', lambda m: f"{m.group(1)}24h {vals['alt24']} / 7d {vals['alt7']}{m.group(2)}", 'label:alt_field', counts)
    html = replace_counted(html, r'(<div class="composition-label"><span>Top-10 Flow</span><strong>)[^<]+(</strong></div>)', lambda m: f"{m.group(1)}{vals['top10']}{m.group(2)}", 'label:top10_flow', counts)
    html = replace_counted(html, r'<p class="small">Static public snapshot · generated [^<]+?\. No active adapter claim\.</p>', f'<p class="small">Static public snapshot · generated {generated_at}. No active adapter claim.</p>', 'timestamp:market_note', counts)
    html = replace_counted(html, r'<li class="source-ready">Stablecoins Cap: [^<]+</li>', f'<li class="source-ready">Stablecoins Cap: {vals["stable_cap"]}</li>', 'liquidity:stable_cap', counts)
    html = replace_counted(html, r'<li class="source-ready">DeFi TVL: [^<]+</li>', f'<li class="source-ready">DeFi TVL: {vals["defi_tvl"]}</li>', 'liquidity:defi_tvl', counts)
    html = replace_counted(html, r'<li class="source-ready">DEX Volume 24h: [^<]+</li>', f'<li class="source-ready">DEX Volume 24h: {vals["dex_volume"]}</li>', 'liquidity:dex_volume', counts)
    html = replace_counted(html, r'(<div class="alt-map-label"><span>24h Breadth</span><strong>)[^<]+(</strong></div>)', lambda m: f"{m.group(1)}{vals['alt24']}{m.group(2)}", 'alt_map:24h', counts)
    html = replace_counted(html, r'(<div class="alt-map-label"><span>7D Persistence</span><strong>)[^<]+(</strong></div>)', lambda m: f"{m.group(1)}{vals['alt7']}{m.group(2)}", 'alt_map:7d', counts)
    html = replace_counted(html, r'(<div class="alt-map-label"><span>Top-10 Flow</span><strong>)[^<]+(</strong></div>)', lambda m: f"{m.group(1)}{vals['top10']}{m.group(2)}", 'alt_map:top10', counts)
    html = replace_counted(html, r'(<span>CoinGecko snapshot</span>\s*<span>)[^<]+(</span>)', lambda m: f"{m.group(1)}{generated_at}{m.group(2)}", 'timestamp:coingecko_snapshot', counts)
    # CRYPTO_ASTRO_V11_VISIBLE_COHERENCE_BINDINGS_v0_1
    field = snapshot.get('field_output') or {}
    samples = ((snapshot.get('public_samples') or {}).get('assets') or {})
    eth_dom = pct(mr.get('eth_dominance_pct'), 1)
    raw_field_score = field.get('market_field_score')
    field_score = 'pending' if raw_field_score is None else str(int(round(float(raw_field_score))))

    def number2(value):
        return 'pending' if value is None else f"{float(value):.2f}"

    def percent2(value):
        return 'pending' if value is None else f"{float(value):.2f}%"

    def sample(symbol):
        return samples.get(symbol) or {}

    html = replace_counted(
        html,
        r'(<div class="btc-quiet-phi-core-v0-3">\s*<span>BTC</span>\s*<strong>)[^<]+(</strong>)',
        lambda m: f"{m.group(1)}{vals['btc_dom']}{m.group(2)}",
        'btc_hub:quiet_gravity',
        counts,
    )
    html = replace_counted(
        html,
        r'(\.metric-rail\.eth-anchor i \{ width:)[^;]+(; \})',
        lambda m: f"{m.group(1)}{eth_dom}{m.group(2)}",
        'rail:eth-anchor',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="composition-node eth">ETH<br>)[^<]+(</div>)',
        lambda m: f"{m.group(1)}{eth_dom}{m.group(2)}",
        'composition:eth',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="composition-label"><span>ETH Anchor</span><strong>)[^<]+(</strong></div>)',
        lambda m: f"{m.group(1)}{eth_dom}{m.group(2)}",
        'label:eth_anchor',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="alt-map-label"><span>ETH Anchor</span><strong>)[^<]+(</strong></div>)',
        lambda m: f"{m.group(1)}{eth_dom}{m.group(2)}",
        'alt_map:eth',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="alt-center-node">ETH<br>)[^<]+(</div>)',
        lambda m: f"{m.group(1)}{eth_dom}{m.group(2)}",
        'alt_map:eth_center',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="score-orb field-gauge" role="img" aria-label="Market Field Score )[^"]+( out of 100">)[^<]+(</div>)',
        lambda m: f"{m.group(1)}{field_score}{m.group(2)}{field_score}{m.group(3)}",
        'field:score_orb',
        counts,
    )

    def replace_copy_slot(source, slot, value, label):
        pattern = rf'(<(?P<tag>[a-z0-9]+)[^>]*data-copy-slot="{re.escape(slot)}"[^>]*>).*?(</(?P=tag)>)'
        return replace_counted(
            source,
            pattern,
            lambda m: f"{m.group(1)}{value}{m.group(3)}",
            label,
            counts,
            flags=re.S | re.I,
        )

    slot_values = {
        'field_state_title': field.get('regime_label') or 'Static public context',
        'field_state_badge': 'M active · A/E pending · static context',
        'field_state_body_1': (
            f"Public market context is active. BTC dominance is {vals['btc_dom']}; "
            f"stablecoin share is {vals['stable_share']}."
        ),
        'field_state_body_2': (
            f"Alt breadth is {vals['alt24']} over 24h and {vals['alt7']} over 7d. "
            "A/E lanes remain pending calibration."
        ),
        'state_structure_status': 'M active',
        'state_pressure_status': 'A/E pending',
        'state_breadth_status': f"{vals['alt24']} / {vals['alt7']}",
        'field_synthesis_lead': 'Static context is bounded; A/E confirmation is not available.',
        'field_synthesis_body_1': (
            f"Market cap is {vals['market_cap']} with {vals['volume']} in 24h volume. "
            f"DeFi TVL is {vals['defi_tvl']}."
        ),
        'field_synthesis_body_2': (
            f"Alt breadth is {vals['alt24']} over 24h and {vals['alt7']} over 7d; "
            f"top-10 flow concentration is {vals['top10']}."
        ),
        'field_synthesis_body_3': (
            f"Temporal context is bounded. Source snapshot generated {generated_at}; "
            "no live adapter is active."
        ),
        'btc_gravity_status': vals['btc_dom'],
        'stablecoin_pressure_status': f"{vals['stable_share']} share",
        'alt_rotation_status': f"{vals['alt24']} / {vals['alt7']}",
        'liquidity_depth_status': f"{vals['defi_tvl']} TVL",
        'timing_context_status': 'Bounded',
        'source_freshness_status': f"Fresh · {generated_at[:10]}",
        'method_market_reality': 'M active',
        'method_liquidity_tvl': 'Context fresh',
        'method_altcoin_rotation': f"{vals['alt24']} / {vals['alt7']}",
        'method_aem_barometer': f"{field_score} / 100",
        'method_continuation': 'Scenario only',
        'method_astromodule': 'Bounded',
        'method_source_freshness': 'Fresh',
    }
    for slot, value in slot_values.items():
        html = replace_copy_slot(html, slot, value, f'copy_slot:{slot}')

    alt_read = f'''<div class="alt-read-grid" aria-label="Altcoin Rotation Read">
        <div class="alt-read-node"><strong>State</strong><span>Selective short-term rotation with concentrated liquidity.</span></div>
        <div class="alt-read-node"><strong>Meaning</strong><span>24h breadth is {vals['alt24']}; 7D persistence is {vals['alt7']} and remains limited.</span></div>
        <div class="alt-read-node"><strong>Direction</strong><span>Watch whether 7D breadth expands while top-10 concentration falls.</span></div>
        <div class="alt-read-node"><strong>Key watch</strong><span>If breadth rises while liquidity stays concentrated, peripheral noise risk remains elevated.</span></div>
      </div>'''
    html = replace_counted(
        html,
        r'<div class="alt-read-grid" aria-label="Altcoin Rotation Read">.*?</div>\s*(?=\n\s*<p class="small">Universe:)',
        alt_read,
        'alt_read:data_bound',
        counts,
        flags=re.S,
    )

    ton = sample('TON')
    icp = sample('ICP')
    ton_score = number2(ton.get('score'))
    icp_score = number2(icp.get('score'))
    ton_score_width = width_num(ton.get('score'))
    icp_score_width = width_num(icp.get('score'))

    def replace_visual_score(source, label, score_value, score_width, key):
        pattern = (
            rf'(<div class="visual-row-v0-1"><span>{re.escape(label)}</span>'
            rf'<div class="visual-rail-v0-1"><i style="width:)[^%]+'
            rf'(%;?"></i></div><span class="visual-value-v0-1">)[^<]+(</span></div>)'
        )
        return replace_counted(
            source,
            pattern,
            lambda m: f"{m.group(1)}{score_width}{m.group(2)}{score_value}{m.group(3)}",
            key,
            counts,
        )

    def replace_visual_value(source, label, value, key):
        pattern = (
            rf'(<div class="visual-row-v0-1"><span>{re.escape(label)}</span>'
            rf'<div class="visual-rail-v0-1"><i style="width:[^"]+"></i></div>'
            rf'<span class="visual-value-v0-1">)[^<]+(</span></div>)'
        )
        return replace_counted(
            source,
            pattern,
            lambda m: f"{m.group(1)}{value}{m.group(2)}",
            key,
            counts,
        )

    html = replace_visual_score(html, 'Gram (prev. Toncoin)', ton_score, ton_score_width, 'sample:ton_visual_score')
    html = replace_visual_score(html, 'Internet Computer', icp_score, icp_score_width, 'sample:icp_visual_score')
    html = replace_visual_value(html, '24h TON', percent2(ton.get('market_24h_change_pct')), 'sample:ton_visual_24h')
    html = replace_visual_value(html, '24h ICP', percent2(icp.get('market_24h_change_pct')), 'sample:icp_visual_24h')
    html = replace_counted(
        html,
        r'(<div class="visual-gauge-row-v0-1">\s*<div class="visual-gauge-v0-1"><strong>)[^<]+(</strong>.*?<div class="visual-gauge-v0-1"><strong>)[^<]+(</strong>)',
        lambda m: f"{m.group(1)}{ton_score}{m.group(2)}{icp_score}{m.group(3)}",
        'sample:dual_visual_gauge',
        counts,
        flags=re.S,
    )

    def replace_distributed_value(source, aria_label, row_label, value, key, width=None):
        if width is None:
            pattern = (
                rf'(<div class="distributed-rail-v0-1" aria-label="{re.escape(aria_label)}">.*?'
                rf'<span>{re.escape(row_label)}</span><div class="distributed-track-v0-1">'
                rf'<i style="width:[^"]+"></i></div><span class="distributed-value-v0-1">)'
                rf'[^<]+(</span>)'
            )
            repl = lambda m: f"{m.group(1)}{value}{m.group(2)}"
        else:
            pattern = (
                rf'(<div class="distributed-rail-v0-1" aria-label="{re.escape(aria_label)}">.*?'
                rf'<span>{re.escape(row_label)}</span><div class="distributed-track-v0-1">'
                rf'<i style="width:)[^%]+(%"></i></div><span class="distributed-value-v0-1">)'
                rf'[^<]+(</span>)'
            )
            repl = lambda m: f"{m.group(1)}{width}{m.group(2)}{value}{m.group(3)}"
        return replace_counted(source, pattern, repl, key, counts, flags=re.S)

    ton_aria = 'Gram source sample distributed visual metrics'
    icp_aria = 'ICP comparison sample distributed visual metrics'
    for aria_label, asset, score_value, score_width, prefix in (
        (ton_aria, ton, ton_score, ton_score_width, 'ton'),
        (icp_aria, icp, icp_score, icp_score_width, 'icp'),
    ):
        html = replace_distributed_value(html, aria_label, 'Score', score_value, f'sample:{prefix}_score', score_width)
        html = replace_distributed_value(html, aria_label, '24h', percent2(asset.get('market_24h_change_pct')), f'sample:{prefix}_24h')
        html = replace_distributed_value(html, aria_label, '30d', percent2(asset.get('market_30d_change_pct')), f'sample:{prefix}_30d')
        html = replace_distributed_value(html, aria_label, 'Rank', str(asset.get('market_cap_rank')), f'sample:{prefix}_rank')

    html = replace_counted(
        html,
        r'(<div class="sample-metric"><span>TON barometer</span><strong>)[^<]+(</strong></div>)',
        lambda m: f"{m.group(1)}{ton_score}{m.group(2)}",
        'sample:ton_barometer',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="sample-metric"><span>ICP barometer</span><strong>)[^<]+(</strong></div>)',
        lambda m: f"{m.group(1)}{icp_score}{m.group(2)}",
        'sample:icp_barometer',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="distributed-dual-gauge-v0-1"[^>]*>\s*<div class="distributed-gauge-v0-1"><strong>)[^<]+(</strong>.*?<div class="distributed-gauge-v0-1"><strong>)[^<]+(</strong>)',
        lambda m: f"{m.group(1)}{ton_score}{m.group(2)}{icp_score}{m.group(3)}",
        'sample:dual_distributed_gauge',
        counts,
        flags=re.S,
    )
    html = replace_counted(
        html,
        r'(<h2>ORION × BHRIGU · Scoring Loop Preview</h2>\s*<p>).*?(</p>)',
        (
            r'\1Read-only market context for BTC / ETH / SOL; snapshot coverage also includes '
            r'TON / ICP. A/E and Φ scoring lanes remain in calibration.\2'
        ),
        'scoring:intro',
        counts,
        flags=re.S,
    )
    html = replace_counted(
        html,
        r'(<div class="scoring-data" id="score-data-snapshot"><strong>Snapshot</strong><span>)[^<]+(</span></div>)',
        lambda m: f"{m.group(1)}Generated {generated_at}{m.group(2)}",
        'scoring:snapshot',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="scoring-data" id="score-data-coverage"><strong>Coverage</strong><span>)[^<]+(</span></div>)',
        lambda m: f"{m.group(1)}{len(samples)} assets · 3 displayed{m.group(2)}",
        'scoring:coverage',
        counts,
    )
    html = replace_counted(
        html,
        r'(<div class="scoring-data" id="score-data-heartbeat"><strong>Heartbeat</strong><span>)[^<]+(</span></div>)',
        r'\1static · no schedule\2',
        'scoring:heartbeat',
        counts,
    )

    write_text(path, html)
    return {'values': vals, 'replace_counts': counts}


def update_bindings(repo: Path, snapshot: dict) -> dict:
    path = repo / 'site/crypto-astro/data/crypto_astro_module_bindings.public.json'
    data = load_json(path)
    data['generated_at_utc'] = snapshot.get('generated_at_utc') or now_iso()
    data['source_mode'] = 'static_public_snapshot'
    data['freshness_status'] = snapshot.get('freshness_status') or 'FRESH'
    data.setdefault('boundary', {}).update(BOUNDARY)
    write_json(path, data)
    return data


def update_market_field(repo: Path, snapshot: dict) -> dict:
    path = repo / 'site/crypto-astro/data/market_field_snapshot.public.v0_1.json'
    mr = snapshot.get('market_reality') or {}
    liq = snapshot.get('liquidity_tvl') or {}
    field = snapshot.get('field_output') or {}
    cont = snapshot.get('probability_continuation') or {}
    generated_at = snapshot.get('generated_at_utc') or now_iso()
    data = {
        'schema_version': 'crypto_astro_market_field_public_v0_1',
        'snapshot_mode': 'public_safe_market_field',
        'updated_at_utc': generated_at,
        'source_mode': 'static_public_snapshot',
        'derived_from': 'site/crypto-astro/data/crypto_astro_snapshot.public.json',
        'derived_status': 'DERIVED_FROM_CANONICAL_SNAPSHOT',
        'vectors': {
            'A_attention': {
                'state': 'prepared_pending_calibration',
                'source_class': 'search_attention',
                'search_pressure': None,
                'query_acceleration': None,
                'topic_heat': None,
                'attention_divergence': None,
                'notes': 'Prepared source lane only. No live search adapter claim.'
            },
            'E_engagement': {
                'state': 'prepared_pending_calibration',
                'source_class': 'x_social_engagement',
                'discussion_pressure': None,
                'narrative_velocity': None,
                'engagement_acceleration': None,
                'social_amplification': None,
                'notes': 'Prepared source lane only. No live X.com/social adapter claim.'
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
                'dex_volume_24h_usd': liq.get('dex_volume_24h_usd'),
                'market_breadth_pct': (snapshot.get('altcoin_rotation') or {}).get('alt_breadth_24h_pct'),
                'liquidity_health': liq.get('liquidity_context_state') or 'context_only'
            },
            'CT_temporal': {
                'state': 'bounded_validated',
                'source_class': 'cosmographic_temporal',
                'phase_density': None,
                'harmonic_tension': None,
                'resonance_level': None,
                'eclipse_proximity': None,
                'structural_stability': None,
                'ephemerides_support': 'bounded_validated'
            }
        },
        'field_output': field,
        'probability_continuation': cont,
        'cosmographer_read': {
            'state': field.get('regime_label') or 'Static public context',
            'meaning': 'M-vector is active while A/E lanes remain prepared for calibration.',
            'direction': 'Watch liquidity depth, stablecoin flow, and future attention / engagement confirmation.',
            'key_watch': 'If attention rises without liquidity depth, noise risk increases.',
            'boundary': 'Scenario-only context. Not a price forecast. Not a trading signal.'
        },
        'boundary': BOUNDARY.copy()
    }
    write_json(path, data)
    return data


def update_scoring(repo: Path, snapshot: dict) -> dict:
    path = repo / 'site/crypto-astro/data/scoring_snapshot.public.json'
    generated_at = snapshot.get('generated_at_utc') or now_iso()
    assets = (snapshot.get('public_samples') or {}).get('assets') or {}
    data = {
        'schema_version': 'crypto_astro_scoring_snapshot_public_v0_2',
        'generated_at_utc': generated_at,
        'source_label': 'Static public JSON · derived from canonical Crypto-Astro snapshot',
        'source_mode': 'static_public_snapshot',
        'derived_from': 'site/crypto-astro/data/crypto_astro_snapshot.public.json',
        'derived_status': 'DERIVED_FROM_CANONICAL_SNAPSHOT',
        'coverage': {
            'assets': sorted(assets.keys()),
            'sample_count': len(assets),
            'A_lane': 'calibration_pending',
            'E_lane': 'calibration_pending',
            'M_lane': 'market_context_active'
        },
        'heartbeat_sec': None,
        'assets': assets,
        'boundary': BOUNDARY.copy(),
        'public_copy': {
            'state': 'Static public scoring snapshot derived from canonical Crypto-Astro snapshot.',
            'boundary': 'No trading signal. No forecast. No price target. Not investment advice.'
        },
        'market_source': 'CoinGecko + reviewed DeFi/TVL sources where available',
        'market_source_mode': 'static_public_snapshot',
        'market_generated_at_utc': generated_at,
        'public_state_label': 'Static public context · A/E pending · M active'
    }
    write_json(path, data)
    return data


def validate_sources(repo: Path, report: dict) -> bool:
    proof_path = repo / 'site/crypto-astro/data/crypto_astro_snapshot_proof.public.json'
    proof = load_json(proof_path)
    statuses = {s.get('label'): s.get('status') for s in proof.get('sources', [])}
    missing = sorted(CRITICAL_SOURCES - set(statuses.keys()))
    failed = sorted([k for k in CRITICAL_SOURCES if statuses.get(k) != 'PASS'])
    optional_hold = sorted([k for k in OPTIONAL_SOURCES if statuses.get(k) and statuses.get(k) != 'PASS'])
    set_validation(report, 'source_statuses', statuses)
    set_validation(report, 'critical_missing', missing)
    set_validation(report, 'critical_failed', failed)
    set_validation(report, 'optional_hold', optional_hold)
    return not missing and not failed


def validate_active_outputs(repo: Path, report: dict) -> bool:
    stale_hits = []
    forbidden_hits = []
    for rel in AFFECTED_FILES:
        p = repo / rel
        if not p.exists():
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        for ts in OLD_ACTIVE_TIMESTAMPS:
            if ts in text:
                stale_hits.append({'file': rel, 'timestamp': ts})
        for pattern in FORBIDDEN_POSITIVE_CLAIMS:
            if re.search(pattern, text):
                forbidden_hits.append({'file': rel, 'pattern': pattern})
    set_validation(report, 'stale_timestamp_hits', stale_hits)
    set_validation(report, 'forbidden_positive_claim_hits', forbidden_hits)
    return not stale_hits and not forbidden_hits


def validate_html_counts(patch_report: dict, report: dict) -> bool:
    required_positive = [
        'metric:Market Cap', 'metric:24h Volume', 'metric:BTC Dominance', 'metric:Stablecoin Share',
        'composition:btc', 'composition:stable', 'composition:alt', 'label:btc_gravity',
        'label:stable_membrane', 'label:alt_field', 'label:top10_flow', 'timestamp:market_note',
        'liquidity:stable_cap', 'liquidity:defi_tvl', 'liquidity:dex_volume',
        'metric:Alt Breadth 24h', 'metric:Alt Breadth 7d', 'metric:Top-10 Flow Concentration',
        'alt_map:24h', 'alt_map:7d', 'alt_map:top10', 'timestamp:coingecko_snapshot',
        'btc_hub:gravity', 'btc_hub:snapshot', 'btc_hub:quiet_gravity',
        'rail:eth-anchor', 'composition:eth', 'label:eth_anchor', 'alt_map:eth', 'alt_map:eth_center',
        'field:score_orb', 'alt_read:data_bound',
        'copy_slot:field_state_title', 'copy_slot:field_state_badge',
        'copy_slot:field_state_body_1', 'copy_slot:field_state_body_2',
        'copy_slot:state_structure_status', 'copy_slot:state_pressure_status',
        'copy_slot:state_breadth_status', 'copy_slot:field_synthesis_lead',
        'copy_slot:field_synthesis_body_1', 'copy_slot:field_synthesis_body_2',
        'copy_slot:field_synthesis_body_3', 'copy_slot:btc_gravity_status',
        'copy_slot:stablecoin_pressure_status', 'copy_slot:alt_rotation_status',
        'copy_slot:liquidity_depth_status', 'copy_slot:timing_context_status',
        'copy_slot:source_freshness_status', 'copy_slot:method_market_reality',
        'copy_slot:method_liquidity_tvl', 'copy_slot:method_altcoin_rotation',
        'copy_slot:method_aem_barometer', 'copy_slot:method_continuation',
        'copy_slot:method_astromodule', 'copy_slot:method_source_freshness',
        'sample:ton_visual_score', 'sample:icp_visual_score',
        'sample:ton_visual_24h', 'sample:icp_visual_24h',
        'sample:dual_visual_gauge', 'sample:ton_score', 'sample:ton_24h',
        'sample:ton_30d', 'sample:ton_rank', 'sample:icp_score',
        'sample:icp_24h', 'sample:icp_30d', 'sample:icp_rank',
        'sample:ton_barometer', 'sample:icp_barometer', 'sample:dual_distributed_gauge',
        'scoring:intro', 'scoring:snapshot', 'scoring:coverage', 'scoring:heartbeat'
    ]
    counts = patch_report.get('replace_counts') or {}
    missing = [k for k in required_positive if int(counts.get(k, 0)) <= 0]
    set_validation(report, 'html_replace_counts', counts)
    set_validation(report, 'html_required_missing', missing)
    return not missing


def backup_files(repo: Path, backup_dir: Path):
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for rel in AFFECTED_FILES:
        src = repo / rel
        if src.exists():
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            manifest.append({'file': rel, 'sha256': sha256_path(src)})
    return manifest


def restore_files(repo: Path, backup_dir: Path):
    for src in backup_dir.rglob('*'):
        if src.is_file():
            rel = src.relative_to(backup_dir)
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def prepare_hardened_primary(primary: Path, working_dir: Path) -> Path:
    text = primary.read_text(encoding='utf-8')
    text = text.replace(f'TARGET_BRANCH = "{OLD_BRANCH}"', f'TARGET_BRANCH = "{NEW_BRANCH}"')
    # Extend allowlist for derived JSON if the original runner ever uses it for changed-file validation.
    needle = '    "site/crypto-astro/data/crypto_astro_module_bindings.public.schema.json",\n'
    insert = needle + '    "site/crypto-astro/data/market_field_snapshot.public.v0_1.json",\n    "site/crypto-astro/data/scoring_snapshot.public.json",\n'
    if needle in text and 'market_field_snapshot.public.v0_1.json' not in text.split('ALLOWLIST =', 1)[1].split(']', 1)[0]:
        text = text.replace(needle, insert, 1)
    # Repair numeric-leading replacement backreference hazard in the source-copy primary runner.
    # The original replacement string uses \1{value} / \2{value}; when value starts with a digit
    # such as 56.0%, Python can interpret \156 as an octal/backreference escape, corrupting
    # BTC Dominance and Stablecoin Share metric cards before the wrapper validation runs.
    old_backref = "sub(pattern, rf'\\1{value}\\2{value}\\3', label=f\"{label} metric\")"
    new_backref = "sub(pattern, lambda m, value=value: f'{m.group(1)}{value}{m.group(2)}{value}{m.group(3)}', label=f\"{label} metric\")"
    if old_backref in text:
        text = text.replace(old_backref, new_backref, 1)
    else:
        marker = 'label=f\"{label} metric\"'
        if marker in text:
            raise RuntimeError('primary metric replacement marker found but exact backref pattern was not patched')
    working_dir.mkdir(parents=True, exist_ok=True)
    dst = working_dir / 'crypto_astro_all_module_static_refresh_hardened_sourcecopy_v0_3.py'
    dst.write_text(text, encoding='utf-8')
    dst.chmod(0o755)
    return dst


def main():
    default_repo = Path('/mnt/c/Users/top-a/Downloads/ORION_ATOMS/phi-cosmography-open')
    default_out = Path(os.environ.get('CRYPTO_ASTRO_REFRESH_OUT', str(Path.cwd() / '.crypto_astro_static_refresh_output')))
    repo = Path(sys.argv[1]).resolve() if len(sys.argv) >= 2 else default_repo
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) >= 3 else default_out
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = now_iso().replace(':','').replace('-','')
    backup_dir = out_dir / f'backup_before_hardened_refresh_{run_id}'
    report = {
        'node': NODE,
        'status': 'HOLD',
        'repo': str(repo),
        'started_at_utc': now_iso(),
        'primary_runner': str(PRIMARY_RUNNER_DEFAULT),
        'expected_primary_sha256': EXPECTED_PRIMARY_SHA256,
        'target_branch': NEW_BRANCH,
        'auto_commit': 'NO',
        'auto_push': 'NO',
        'auto_pr': 'NO',
        'auto_deploy': 'NO',
        'boundary': BOUNDARY.copy(),
        'validation': {}
    }
    report_path = out_dir / 'crypto_astro_static_refresh_automated_v0_5_report.json'
    md_report_path = out_dir / 'crypto_astro_static_refresh_automated_v0_5_report.md'
    try:
        if not repo.exists():
            raise RuntimeError(f'repo not found: {repo}')
        status = run(['git','status','--porcelain'], repo, check=True).stdout.strip()
        report['pre_git_status'] = status
        if status:
            raise RuntimeError('repo has uncommitted changes; refusing hardened refresh')
        head = run(['git','rev-parse','HEAD'], repo, check=True).stdout.strip()
        report['pre_head'] = head
        primary = PRIMARY_RUNNER_DEFAULT
        if not primary.exists():
            raise RuntimeError(f'primary runner not found: {primary}')
        primary_sha = sha256_path(primary)
        report['primary_runner_sha256'] = primary_sha
        if primary_sha != EXPECTED_PRIMARY_SHA256:
            raise RuntimeError(f'primary runner sha mismatch: {primary_sha}')
        report['backup_manifest'] = backup_files(repo, backup_dir)
        working_primary = prepare_hardened_primary(primary, out_dir / 'working')
        report['working_primary'] = str(working_primary)
        report['working_primary_sha256'] = sha256_path(working_primary)
        report['primary_sourcecopy_backref_repair'] = 'APPLIED'
        primary_out = out_dir / 'primary_runner_output'
        primary_out.mkdir(parents=True, exist_ok=True)
        p = run([sys.executable, str(working_primary), str(repo), str(primary_out)], repo, check=False)
        report['primary_returncode'] = p.returncode
        report['primary_stdout_tail'] = p.stdout[-6000:]
        report['primary_stderr_tail'] = p.stderr[-6000:]
        if p.returncode != 0:
            restore_files(repo, backup_dir)
            raise RuntimeError('hardened sourcecopy primary runner failed; restored backup')
        critical_ok = validate_sources(repo, report)
        if not critical_ok:
            restore_files(repo, backup_dir)
            report['status'] = 'HOLD_CRITICAL_SOURCE'
            raise RuntimeError('critical sources did not PASS; restored backup and refused HTML/public patch')
        snapshot_path = repo / 'site/crypto-astro/data/crypto_astro_snapshot.public.json'
        snapshot = load_json(snapshot_path)
        patch_report = patch_html(repo, snapshot)
        update_bindings(repo, snapshot)
        update_market_field(repo, snapshot)
        update_scoring(repo, snapshot)
        html_ok = validate_html_counts(patch_report, report)
        active_ok = validate_active_outputs(repo, report)
        if not html_ok or not active_ok:
            restore_files(repo, backup_dir)
            raise RuntimeError('post-patch validation failed; restored backup')
        changed = run(['git','status','--short'], repo, check=True).stdout.strip().splitlines()
        report['changed_files_short'] = changed
        allowed_prefixes = set(AFFECTED_FILES)
        parsed_changed_files = [parse_git_status_path(line) for line in changed]
        report['changed_files_parsed'] = parsed_changed_files
        unexpected = []
        for rel in parsed_changed_files:
            if rel and rel not in allowed_prefixes:
                unexpected.append(rel)
        set_validation(report, 'unexpected_changed_files', unexpected)
        if unexpected:
            restore_files(repo, backup_dir)
            raise RuntimeError(f'unexpected changed files; restored backup: {unexpected}')
        report['sha256'] = {rel: sha256_path(repo / rel) for rel in AFFECTED_FILES if (repo / rel).exists()}
        report['completed_at_utc'] = now_iso()
        report['status'] = 'PASS'
        report['next_safe_node'] = 'CRYPTO_ASTRO_STATIC_REFRESH_AUTOMATION_MANUAL_DISPATCH_REVIEW_SCOPE_v0_5'
    except Exception as e:
        report.setdefault('completed_at_utc', now_iso())
        if report.get('status') == 'HOLD':
            report['status'] = 'FAIL'
        report['error'] = str(e)
        report['next_safe_node'] = 'CRYPTO_ASTRO_STATIC_REFRESH_HARDENING_FAILURE_REVIEW_SCOPE_v0_1'
    finally:
        append_validation_summary(report)
        write_json(report_path, report)
        md = [
            f"# {NODE}",
            "",
            f"STATUS={report.get('status')}",
            f"REPO={report.get('repo')}",
            f"TARGET_BRANCH={report.get('target_branch')}",
            f"PRIMARY_RUNNER_SHA256={report.get('primary_runner_sha256')}",
            f"REPORT_JSON={report_path}",
            f"REPORT_JSON_SHA256={sha256_path(report_path)}",
            "",
            "## Boundary",
            "No commit. No push. No PR. No deploy. No payment/API/backend activation. No trading signal/forecast/price target.",
            "",
            "## Validation summary",
        ]
        for k, v in (report.get('validation', {}).get('summary') or {}).items():
            md.append(f"- {k}: {v}")
        md += ["", "## Source statuses"]
        for k, v in (report.get('validation', {}).get('source_statuses') or report.get('source_statuses') or {}).items():
            md.append(f"- {k}: {v}")
        if report.get('validation', {}).get('critical_missing'):
            md += ["", "## Critical missing", json.dumps(report['validation']['critical_missing'], ensure_ascii=False, indent=2)]
        if report.get('validation', {}).get('critical_failed'):
            md += ["", "## Critical failed", json.dumps(report['validation']['critical_failed'], ensure_ascii=False, indent=2)]
        md += ["", "## HTML replacement counts"]
        for k, v in sorted((report.get('validation', {}).get('html_replace_counts') or report.get('html_replace_counts') or {}).items()):
            md.append(f"- {k}: {v}")
        if report.get('validation', {}).get('html_required_missing'):
            md += ["", "## HTML required missing", json.dumps(report['validation']['html_required_missing'], ensure_ascii=False, indent=2)]
        if report.get('validation', {}).get('stale_timestamp_hits'):
            md += ["", "## Stale timestamp hits", json.dumps(report['validation']['stale_timestamp_hits'], ensure_ascii=False, indent=2)]
        if report.get('validation', {}).get('forbidden_positive_claim_hits'):
            md += ["", "## Forbidden positive claim hits", json.dumps(report['validation']['forbidden_positive_claim_hits'], ensure_ascii=False, indent=2)]
        if report.get('validation', {}).get('unexpected_changed_files'):
            md += ["", "## Unexpected changed files", json.dumps(report['validation']['unexpected_changed_files'], ensure_ascii=False, indent=2)]
        md += ["", "## Changed files"]
        for line in report.get('changed_files_short') or []:
            md.append(f"- `{line}`")
        if report.get('primary_stdout_tail'):
            md += ["", "## Primary runner stdout tail", "```text", report.get('primary_stdout_tail', '')[-6000:], "```"]
        if report.get('primary_stderr_tail'):
            md += ["", "## Primary runner stderr tail", "```text", report.get('primary_stderr_tail', '')[-6000:], "```"]
        if report.get('error'):
            md += ["", "## Error", str(report['error'])]
        write_text(md_report_path, '\n'.join(md) + '\n')
        print('RESULT_BLOCK_START')
        print(f'NODE={NODE}')
        print(f"STATUS={report.get('status')}")
        print(f'TARGET_BRANCH={NEW_BRANCH}')
        print(f'REPORT_JSON_PATH={report_path}')
        print(f'REPORT_JSON_SHA256={sha256_path(report_path)}')
        print(f'REPORT_MD_PATH={md_report_path}')
        print(f'REPORT_MD_SHA256={sha256_path(md_report_path)}')
        print(f"NEXT_SAFE_NODE={report.get('next_safe_node')}")
        if report.get('status') != 'PASS':
            print(f"ERROR={str(report.get('error') or '')[:220]}")
            print(f"HTML_REQUIRED_MISSING={len(report.get('validation', {}).get('html_required_missing') or [])}")
            print(f"STALE_TIMESTAMP_HITS={len(report.get('validation', {}).get('stale_timestamp_hits') or [])}")
            print(f"FORBIDDEN_CLAIM_HITS={len(report.get('validation', {}).get('forbidden_positive_claim_hits') or [])}")
        print('RESULT_BLOCK_END')
        if report.get('status') != 'PASS':
            sys.exit(1)


if __name__ == '__main__':
    main()
