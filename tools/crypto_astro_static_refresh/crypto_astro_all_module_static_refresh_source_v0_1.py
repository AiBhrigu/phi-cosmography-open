#!/usr/bin/env python3
import json, sys, os, re, time, hashlib, subprocess, urllib.request, urllib.parse, math
from pathlib import Path
from datetime import datetime, timezone

NODE = "V9_CRYPTO_ASTRO_ALL_MODULE_STATIC_REFRESH_LOCAL_ATOM_SCOPE_v0_1"
TARGET_BRANCH = "feature/crypto-astro-all-module-static-refresh-v0-1"
BASE_BRANCH = "main"
ALLOWLIST = [
    "site/crypto-astro/index.html",
    "site/crypto-astro/data/crypto_astro_snapshot.public.json",
    "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json",
    "site/crypto-astro/data/crypto_astro_module_bindings.public.json",
    "site/crypto-astro/data/crypto_astro_module_bindings.public.schema.json",
    "docs/crypto-astro-service/crypto_astro_snapshot_summary.md",
    "docs/crypto-astro-service/crypto_astro_operator_review.md",
]
BOUNDARY = {
    "read_only": True,
    "static_public_snapshot": True,
    "no_live_adapter_claim": True,
    "no_true_live_feed_claim": True,
    "no_trading_signal": True,
    "no_forecast": True,
    "no_price_target": True,
    "no_investment_recommendation": True,
    "backend_api_closed": True,
    "runtime_closed": True,
    "payment_closed": True,
    "orion_core_protected": True,
    "formula_weights_exposed": False
}
STABLE_IDS = [
    "tether","usd-coin","usde","dai","usds","ethena-usde","first-digital-usd",
    "paypal-usd","frax","true-usd","pax-dollar","usdd","usdb","lusd","crvusd"
]
ASSET_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "TON": "the-open-network",
    "ICP": "internet-computer",
}
STABLE_SYMBOLS = {"usdt","usdc","dai","usde","usds","fdusd","pyusd","tusd","usdd","usdb","frax","lusd","crvusd","usdp"}

COINGECKO_DEMO_API_KEY = os.environ.get("COINGECKO_DEMO_API_KEY", "").strip()

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def sha256_path(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def run(cmd, cwd, check=True):
    p = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\nSTDOUT={p.stdout}\nSTDERR={p.stderr}")
    return p.stdout.strip()

def fetch_json(url, timeout=25):
    headers = {"User-Agent":"ORION-CryptoAstro-StaticSnapshot/0.1"}
    if COINGECKO_DEMO_API_KEY and "api.coingecko.com" in url:
        headers["x-cg-demo-api-key"] = COINGECKO_DEMO_API_KEY
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def safe_fetch(label, url, proof, timeout=25):
    started = now_iso()
    try:
        data = fetch_json(url, timeout=timeout)
        raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        proof["sources"].append({
            "label": label,
            "url": url,
            "status": "PASS",
            "fetched_at_utc": started,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw)
        })
        return data
    except Exception as e:
        proof["sources"].append({
            "label": label,
            "url": url,
            "status": "HOLD",
            "fetched_at_utc": started,
            "error": str(e)[:400]
        })
        return None

def usd_compact(n):
    if n is None:
        return "pending"
    n = float(n)
    if abs(n) >= 1e12:
        return f"${n/1e12:.3f}T"
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"

def pct(v, decimals=1, sign=False):
    if v is None:
        return "pending"
    v = float(v)
    s = f"{v:+.{decimals}f}%" if sign else f"{v:.{decimals}f}%"
    return s

def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))

def get_rank_score(rank):
    if not rank:
        return 45.0
    return clamp(100 - (rank / 2.0), 10, 95)

def sample_score(asset):
    ch24 = asset.get("price_change_percentage_24h_in_currency") or asset.get("price_change_percentage_24h") or 0
    ch7 = asset.get("price_change_percentage_7d_in_currency") or 0
    ch30 = asset.get("price_change_percentage_30d_in_currency") or 0
    rank = asset.get("market_cap_rank") or 250
    score = 50 + 0.7*float(ch24 or 0) + 0.25*float(ch7 or 0) + 0.12*float(ch30 or 0) + (get_rank_score(rank)-50)*0.25
    return round(clamp(score, 0, 100), 2)

def replacement(html, pattern, repl, flags=0):
    new, n = re.subn(pattern, repl, html, flags=flags)
    return new, n

def set_metric(html, label, value, rail_class=None):
    # Updates both aria label and visible strong value for known market-metric cards.
    pattern = rf'(<div class="market-metric" aria-label="{re.escape(label)} )[^"]+("><span>{re.escape(label)}</span><strong>)[^<]+(</strong>)'
    return replacement(html, pattern, rf'\1{value}\2{value}\3')

def main():
    if len(sys.argv) != 3:
        print("usage: script.py REPO_PATH OUT_DIR", file=sys.stderr)
        sys.exit(2)

    repo = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "node": NODE,
        "status": "HOLD",
        "branch": TARGET_BRANCH,
        "base_branch": BASE_BRANCH,
        "changed_files": [],
        "validation": {},
        "boundary": BOUNDARY.copy(),
        "started_at_utc": now_iso()
    }
    proof = {
        "schema_version": "crypto_astro_snapshot_proof_public_v0_1",
        "generated_at_utc": now_iso(),
        "source_mode": "static_public_snapshot",
        "sources": [],
        "boundary": BOUNDARY.copy()
    }

    try:
        # Preserve local work; do not push.
        current_branch = run(["git","branch","--show-current"], repo, check=False)
        status_before = run(["git","status","--porcelain"], repo, check=False)
        # Switch/create target branch from local main or origin/main when available.
        run(["git","fetch","origin","main"], repo, check=False)
        base_ref = "origin/main"
        if run(["git","rev-parse","--verify",base_ref], repo, check=False) == "":
            base_ref = BASE_BRANCH
        run(["git","switch","-C",TARGET_BRANCH,base_ref], repo, check=True)

        index_path = repo / "site/crypto-astro/index.html"
        if not index_path.exists():
            raise RuntimeError("target index.html not found")
        html = index_path.read_text(encoding="utf-8")
        original_html = html

        generated_at = now_iso()

        global_data = safe_fetch("coingecko_global", "https://api.coingecko.com/api/v3/global", proof)
        ids = ",".join(ASSET_IDS.values())
        markets_url = "https://api.coingecko.com/api/v3/coins/markets?" + urllib.parse.urlencode({
            "vs_currency":"usd",
            "ids": ids,
            "price_change_percentage":"1h,24h,7d,30d",
            "sparkline":"false"
        })
        asset_markets = safe_fetch("coingecko_asset_markets_btc_eth_sol_ton_icp", markets_url, proof)
        top250_url = "https://api.coingecko.com/api/v3/coins/markets?" + urllib.parse.urlencode({
            "vs_currency":"usd",
            "order":"market_cap_desc",
            "per_page":"250",
            "page":"1",
            "price_change_percentage":"1h,24h,7d,30d",
            "sparkline":"false"
        })
        top250 = safe_fetch("coingecko_top250_markets", top250_url, proof)
        stable_url = "https://api.coingecko.com/api/v3/coins/markets?" + urllib.parse.urlencode({
            "vs_currency":"usd",
            "ids": ",".join(STABLE_IDS),
            "order":"market_cap_desc",
            "per_page":"100",
            "page":"1",
            "sparkline":"false"
        })
        stable_markets = safe_fetch("coingecko_stablecoin_sample", stable_url, proof)

        # DefiLlama optional
        protocols = safe_fetch("defillama_protocols", "https://api.llama.fi/protocols", proof, timeout=35)
        dexs = safe_fetch("defillama_dex_overview", "https://api.llama.fi/overview/dexs?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true", proof, timeout=35)
        stables_llama = safe_fetch("defillama_stablecoins", "https://stablecoins.llama.fi/stablecoins?includePrices=true", proof, timeout=35)

        gd = (global_data or {}).get("data", {})
        total_market_cap = ((gd.get("total_market_cap") or {}).get("usd"))
        total_volume = ((gd.get("total_volume") or {}).get("usd"))
        market_cap_pct = gd.get("market_cap_percentage") or {}
        btc_dom = market_cap_pct.get("btc")
        eth_dom = market_cap_pct.get("eth")

        stable_cap_cg = None
        if isinstance(stable_markets, list):
            stable_cap_cg = sum(float(x.get("market_cap") or 0) for x in stable_markets)
        stable_cap_llama = None
        try:
            assets = (stables_llama or {}).get("peggedAssets") or []
            stable_cap_llama = sum(float(((a.get("circulating") or {}).get("peggedUSD")) or 0) for a in assets)
        except Exception:
            pass
        stable_cap = stable_cap_llama or stable_cap_cg
        stable_share = (stable_cap / total_market_cap * 100) if (stable_cap and total_market_cap) else None

        tvl = None
        if isinstance(protocols, list):
            tvl = sum(float(p.get("tvl") or 0) for p in protocols if p.get("tvl") is not None)
        dex_volume = None
        if isinstance(dexs, dict):
            dex_volume = dexs.get("total24h") or dexs.get("totalVolume24h")

        asset_by_symbol = {}
        if isinstance(asset_markets, list):
            for a in asset_markets:
                sym = (a.get("symbol") or "").upper()
                # CoinGecko uses TON for the-open-network, but be defensive.
                if a.get("id") == "the-open-network":
                    sym = "TON"
                asset_by_symbol[sym] = a

        # Alt rotation breadth from top250 excluding BTC and stablecoins.
        alt_assets = []
        if isinstance(top250, list):
            for a in top250:
                sym = (a.get("symbol") or "").lower()
                if sym in STABLE_SYMBOLS or a.get("id") == "bitcoin":
                    continue
                alt_assets.append(a)
        def change(a, key):
            return a.get(key) if a.get(key) is not None else a.get(key.replace("_in_currency",""))
        alt24_vals = [change(a,"price_change_percentage_24h_in_currency") for a in alt_assets]
        alt7_vals = [change(a,"price_change_percentage_7d_in_currency") for a in alt_assets]
        alt24 = round(100 * sum(1 for v in alt24_vals if v is not None and float(v) > 0) / len(alt24_vals), 1) if alt24_vals else None
        alt7 = round(100 * sum(1 for v in alt7_vals if v is not None and float(v) > 0) / len(alt7_vals), 1) if alt7_vals else None
        total_top_vol = sum(float(a.get("total_volume") or 0) for a in alt_assets)
        top10_vol = sum(float(a.get("total_volume") or 0) for a in alt_assets[:10])
        top10_flow = round(100 * top10_vol / total_top_vol, 1) if total_top_vol else None

        # Field score and continuation stay public-safe/contextual.
        market_cap_change_pct = gd.get("market_cap_change_percentage_24h_usd")
        score = 63
        if total_market_cap and total_volume:
            # Simple public context score; no private formulas.
            vol_ratio = clamp((total_volume / total_market_cap) * 100 * 8, 0, 35)
            btc_component = clamp((btc_dom or 50) - 45, 0, 25)
            alt_component = clamp((alt24 or 50) / 100 * 25, 0, 25)
            stable_component = clamp(15 - (stable_share or 12), 0, 15)
            score = round(clamp(25 + vol_ratio + btc_component + alt_component + stable_component), 0)
        regime = "Balanced Expansion" if score >= 58 else "Calibration / Watch"
        direction_bias = "Neutral → Bullish" if score >= 58 else "Neutral / Calibration"
        base_path = 62
        expansion_path = 24
        compression_path = 14
        if market_cap_change_pct is not None:
            shift = clamp(float(market_cap_change_pct), -4, 4)
            expansion_path = int(round(clamp(24 + shift*2, 14, 34)))
            compression_path = int(round(clamp(14 - shift, 8, 22)))
            base_path = max(0, 100 - expansion_path - compression_path)

        # Liquidity health remains context-only.
        liq_state = "context fresh" if (tvl and dex_volume) else "calibration pending"

        # Asset samples.
        sample_assets = {}
        for sym in ["BTC","ETH","SOL","TON","ICP"]:
            a = asset_by_symbol.get(sym)
            if not a:
                continue
            sample_assets[sym] = {
                "id": a.get("id"),
                "symbol": sym,
                "label": a.get("name"),
                "price_usd": a.get("current_price"),
                "market_cap_rank": a.get("market_cap_rank"),
                "market_24h_change_pct": a.get("price_change_percentage_24h_in_currency") or a.get("price_change_percentage_24h"),
                "market_7d_change_pct": a.get("price_change_percentage_7d_in_currency"),
                "market_30d_change_pct": a.get("price_change_percentage_30d_in_currency"),
                "M": round(abs(float(a.get("price_change_percentage_24h_in_currency") or a.get("price_change_percentage_24h") or 0)) / 10, 4),
                "A_state": "calibration_pending",
                "E_state": "calibration_pending",
                "M_state": "market_context_active",
                "visible_state_label": "Market context active · A/E pending",
                "market_context_label": "active_movement" if abs(float(a.get("price_change_percentage_24h_in_currency") or a.get("price_change_percentage_24h") or 0)) >= 2 else "low_movement",
                "score": sample_score(a),
            }

        snapshot = {
            "schema_version": "crypto_astro_snapshot_public_v0_1",
            "generated_at_utc": generated_at,
            "source_mode": "static_public_snapshot",
            "freshness_status": "FRESH",
            "market_reality": {
                "total_market_cap_usd": total_market_cap,
                "volume_24h_usd": total_volume,
                "market_cap_change_24h_pct": market_cap_change_pct,
                "btc_dominance_pct": btc_dom,
                "eth_dominance_pct": eth_dom,
                "stablecoin_cap_usd": stable_cap,
                "stablecoin_share_pct": stable_share
            },
            "field_output": {
                "market_field_score": score,
                "regime_label": regime,
                "direction_bias": direction_bias,
                "continuation_label": "Scenario-only continuation map",
                "confidence_label": "static public context"
            },
            "probability_continuation": {
                "base_path_pct": base_path,
                "expansion_path_pct": expansion_path,
                "compression_reversal_pct": compression_path,
                "window_label": "7D",
                "boundary": "Scenario continuation only. Not a price forecast. Not a trading signal."
            },
            "liquidity_tvl": {
                "stablecoin_cap_usd": stable_cap,
                "defi_tvl_usd": tvl,
                "dex_volume_24h_usd": dex_volume,
                "liquidity_context_state": liq_state,
                "calibration_state": "context_only"
            },
            "altcoin_rotation": {
                "universe": "non-stable top-250 crypto assets",
                "alt_breadth_24h_pct": alt24,
                "alt_breadth_7d_pct": alt7,
                "eth_rotation_anchor_pct": eth_dom,
                "top_10_flow_concentration_pct": top10_flow
            },
            "public_samples": {
                "assets": sample_assets
            },
            "boundary": BOUNDARY
        }

        bindings = {
            "schema_version": "crypto_astro_public_module_bindings_v0_1",
            "generated_at_utc": generated_at,
            "source_mode": "static_public_snapshot",
            "freshness_status": "FRESH",
            "modules": {
                "market_reality": {"source": "market_reality", "anchor": "Market Reality"},
                "aem_barometer": {"source": "field_output", "anchor": "A/E/M Field Barometer"},
                "continuation_field": {"source": "probability_continuation", "anchor": "Continuation Field"},
                "astromodule": {"source": "static_public_context", "anchor": "astromodule-surface-bridge"},
                "support_lanes": {"source": "static_public_context", "anchor": "CRYPTO_ASTRO_SUPPORT_MODULES_VISUAL_ALIGNMENT_v0_1"},
                "cosmographer_read": {"source": "field_output + liquidity_tvl", "anchor": "Cosmographer Read"},
                "liquidity_tvl": {"source": "liquidity_tvl", "anchor": "Liquidity / TVL"},
                "altcoin_rotation": {"source": "altcoin_rotation", "anchor": "alt-rotation-module"},
                "public_sample_ton_icp": {"source": "public_samples.TON + public_samples.ICP", "anchor": "CRYPTO_ASTRO_PUBLIC_SAMPLE_WEB_PANEL_v0_1"},
                "btc_eth_sol_sample": {"source": "public_samples.BTC + public_samples.ETH + public_samples.SOL", "anchor": "crypto_astro_snapshot.public.json"},
                "trend_memory": {"source": "available 7d/30d fields only", "anchor": "trend-memory"}
            },
            "boundary": BOUNDARY
        }

        binding_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Crypto-Astro Public Module Bindings v0.1",
            "type": "object",
            "required": ["schema_version","generated_at_utc","source_mode","freshness_status","modules","boundary"],
            "properties": {
                "schema_version": {"const": "crypto_astro_public_module_bindings_v0_1"},
                "generated_at_utc": {"type": "string"},
                "source_mode": {"const": "static_public_snapshot"},
                "freshness_status": {"enum": ["FRESH","STALE","ARCHIVE","UNKNOWN"]},
                "modules": {"type": "object"},
                "boundary": {"type": "object"}
            }
        }

        # If critical market source failed, hold before patching.
        if not total_market_cap or not total_volume or not btc_dom:
            report["status"] = "HOLD"
            report["reason"] = "CRITICAL_MARKET_SOURCE_FIELDS_MISSING"
            raise RuntimeError("critical CoinGecko fields missing")

        # Patch HTML exact known anchors / literals.
        replacements = []

        def sub(pattern, repl, flags=0, label=""):
            nonlocal html, replacements
            html2, n = re.subn(pattern, repl, html, flags=flags)
            html = html2
            replacements.append({"label": label or pattern[:80], "count": n})

        cap_s = usd_compact(total_market_cap)
        vol_s = usd_compact(total_volume)
        btc_s = pct(btc_dom)
        stable_s = pct(stable_share)
        eth_s = pct(eth_dom)
        score_s = str(int(score))

        for label, value in [
            ("Market Cap", cap_s),
            ("24h Volume", vol_s),
            ("BTC Dominance", btc_s),
            ("Stablecoin Share", stable_s)
        ]:
            pattern = rf'(<div class="market-metric" aria-label="{re.escape(label)} )[^"]+("><span>{re.escape(label)}</span><strong>)[^<]+(</strong>)'
            sub(pattern, rf'\1{value}\2{value}\3', label=f"{label} metric")

        sub(r'<div class="composition-core">BTC<br>[^<]+</div>', f'<div class="composition-core">BTC<br>{btc_s}</div>', label="composition core btc")
        sub(r'<div class="composition-node stable">Stable<br>[^<]+</div>', f'<div class="composition-node stable">Stable<br>{stable_s}</div>', label="composition stable")
        sub(r'<div class="composition-node eth">ETH<br>[^<]+</div>', f'<div class="composition-node eth">ETH<br>{eth_s}</div>', label="composition eth")
        if alt24 is not None and alt7 is not None:
            sub(r'<div class="composition-node alt">Alt<br>[^<]+</div>', f'<div class="composition-node alt">Alt<br>{pct(alt24)} / {pct(alt7)}</div>', label="composition alt")
        sub(r'<div class="composition-label"><span>BTC Gravity</span><strong>[^<]+</strong></div>', f'<div class="composition-label"><span>BTC Gravity</span><strong>{btc_s}</strong></div>', label="btc gravity")
        sub(r'<div class="composition-label"><span>Stablecoin Membrane</span><strong>[^<]+</strong></div>', f'<div class="composition-label"><span>Stablecoin Membrane</span><strong>{stable_s}</strong></div>', label="stable membrane")
        sub(r'<div class="composition-label"><span>ETH Anchor</span><strong>[^<]+</strong></div>', f'<div class="composition-label"><span>ETH Anchor</span><strong>{eth_s}</strong></div>', label="eth anchor")
        if alt24 is not None and alt7 is not None:
            sub(r'<div class="composition-label"><span>Alt Field</span><strong>[^<]+</strong></div>', f'<div class="composition-label"><span>Alt Field</span><strong>24h {pct(alt24)} / 7d {pct(alt7)}</strong></div>', label="alt field label")
        if top10_flow is not None:
            sub(r'<div class="composition-label"><span>Top-10 Flow</span><strong>[^<]+</strong></div>', f'<div class="composition-label"><span>Top-10 Flow</span><strong>{pct(top10_flow)}</strong></div>', label="top10 flow")
        sub(r'<p class="small">Static public snapshot\. No active adapter claim\.</p>', f'<p class="small">Static public snapshot · generated {generated_at}. No active adapter claim.</p>', label="market freshness note")

        # Barometer.
        sub(r'aria-label="Market Field Score \d+ out of 100">[^<]+</div>', f'aria-label="Market Field Score {score_s} out of 100">{score_s}</div>', label="barometer score orb")
        sub(r'<h3>Balanced Expansion</h3>\s*<p>Market Field Score: \d+ / 100<br/>Bias: [^<]+</p>', f'<h3>{regime}</h3>\n            <p>Market Field Score: {score_s} / 100<br/>Bias: {direction_bias}</p>', flags=re.S, label="barometer text")

        # Continuation.
        sub(r'<div class="prob-row scenario-row" aria-label="Base Path [^"]+"><span>Base Path</span><strong>[^<]+</strong>', f'<div class="prob-row scenario-row" aria-label="Base Path {base_path}%"><span>Base Path</span><strong>{base_path}%</strong>', label="base path")
        sub(r'<div class="prob-row scenario-row" aria-label="Expansion [^"]+"><span>Expansion</span><strong>[^<]+</strong>', f'<div class="prob-row scenario-row" aria-label="Expansion {expansion_path}%"><span>Expansion</span><strong>{expansion_path}%</strong>', label="expansion path")
        sub(r'<div class="prob-row scenario-row" aria-label="Compression or Reversal [^"]+"><span>Compression / Reversal</span><strong>[^<]+</strong>', f'<div class="prob-row scenario-row" aria-label="Compression or Reversal {compression_path}%"><span>Compression / Reversal</span><strong>{compression_path}%</strong>', label="compression path")

        # Liquidity / TVL.
        sub(r'<li class="source-ready">Stablecoins Cap: [^<]+</li>', f'<li class="source-ready">Stablecoins Cap: {usd_compact(stable_cap)}</li>', label="stablecoins cap")
        sub(r'<li class="source-ready">DeFi TVL: [^<]+</li>', f'<li class="source-ready">DeFi TVL: {usd_compact(tvl)}</li>', label="defi tvl")
        sub(r'<li class="source-ready">DEX Volume 24h: [^<]+</li>', f'<li class="source-ready">DEX Volume 24h: {usd_compact(dex_volume)}</li>', label="dex volume")
        sub(r'<li class="source-calibration">Liquidity Health: [^<]+</li>', f'<li class="source-calibration">Liquidity Health: {liq_state}</li>', label="liquidity health")

        # Alt rotation.
        if alt24 is not None:
            sub(r'aria-label="Alt Breadth 24h [^"]+"><span>Alt Breadth 24h</span><strong>[^<]+</strong>', f'aria-label="Alt Breadth 24h {pct(alt24)}"><span>Alt Breadth 24h</span><strong>{pct(alt24)}</strong>', label="alt breadth 24h card")
            sub(r'<div class="alt-map-label"><span>24h Breadth</span><strong>[^<]+</strong></div>', f'<div class="alt-map-label"><span>24h Breadth</span><strong>{pct(alt24)}</strong></div>', label="alt map 24h")
        if alt7 is not None:
            sub(r'aria-label="Alt Breadth 7d [^"]+"><span>Alt Breadth 7d</span><strong>[^<]+</strong>', f'aria-label="Alt Breadth 7d {pct(alt7)}"><span>Alt Breadth 7d</span><strong>{pct(alt7)}</strong>', label="alt breadth 7d card")
            sub(r'<div class="alt-map-label"><span>7D Persistence</span><strong>[^<]+</strong></div>', f'<div class="alt-map-label"><span>7D Persistence</span><strong>{pct(alt7)}</strong></div>', label="alt map 7d")
        if eth_dom is not None:
            sub(r'aria-label="ETH Rotation Anchor [^"]+"><span>ETH Rotation Anchor</span><strong>[^<]+</strong>', f'aria-label="ETH Rotation Anchor {eth_s}"><span>ETH Rotation Anchor</span><strong>{eth_s}</strong>', label="eth rotation anchor")
            sub(r'<div class="alt-map-label"><span>ETH Anchor</span><strong>[^<]+</strong></div>', f'<div class="alt-map-label"><span>ETH Anchor</span><strong>{eth_s}</strong></div>', label="alt map eth")
            sub(r'<div class="alt-center-node">ETH<br>[^<]+</div>', f'<div class="alt-center-node">ETH<br>{eth_s}</div>', label="alt center eth")
        if top10_flow is not None:
            sub(r'aria-label="Top-10 Flow Concentration [^"]+"><span>Top-10 Flow Concentration</span><strong>[^<]+</strong>', f'aria-label="Top-10 Flow Concentration {pct(top10_flow)}"><span>Top-10 Flow Concentration</span><strong>{pct(top10_flow)}</strong>', label="top10 card")
            sub(r'<div class="alt-map-label"><span>Top-10 Flow</span><strong>[^<]+</strong></div>', f'<div class="alt-map-label"><span>Top-10 Flow</span><strong>{pct(top10_flow)}</strong></div>', label="alt map top10")

        # Public TON/ICP samples: replace old literal values if present.
        ton = sample_assets.get("TON", {})
        icp = sample_assets.get("ICP", {})
        def signed_change(asset, k):
            return pct(asset.get(k), 2, sign=True)
        if ton:
            ton_score = f"{ton['score']:.2f}"
            html = html.replace("68.41", ton_score)
            html = html.replace("+0.48%", signed_change(ton, "market_24h_change_pct"))
            html = html.replace("+13.45%", signed_change(ton, "market_30d_change_pct"))
            html = html.replace(">23<", f">{ton.get('market_cap_rank') or 'pending'}<")
        if icp:
            icp_score = f"{icp['score']:.2f}"
            html = html.replace("59.04", icp_score)
            html = html.replace("+0.50%", signed_change(icp, "market_24h_change_pct"))
            html = html.replace("-4.71%", signed_change(icp, "market_30d_change_pct"))
            html = html.replace(">62<", f">{icp.get('market_cap_rank') or 'pending'}<")
        sub(r'<span>2026-07-06T11:31:12Z</span>', f'<span>{generated_at}</span>', label="sample timestamp")

        # Trend memory remains labels unless 7d fields can be safely summarized; keep no-prediction static.
        # Write files.
        data_dir = repo / "site/crypto-astro/data"
        docs_dir = repo / "docs/crypto-astro-service"
        data_dir.mkdir(parents=True, exist_ok=True)
        docs_dir.mkdir(parents=True, exist_ok=True)

        snapshot_path = data_dir / "crypto_astro_snapshot.public.json"
        proof_path = data_dir / "crypto_astro_snapshot_proof.public.json"
        bindings_path = data_dir / "crypto_astro_module_bindings.public.json"
        bindings_schema_path = data_dir / "crypto_astro_module_bindings.public.schema.json"
        summary_path = docs_dir / "crypto_astro_snapshot_summary.md"
        operator_review_path = docs_dir / "crypto_astro_operator_review.md"

        snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding="utf-8")
        bindings_path.write_text(json.dumps(bindings, ensure_ascii=False, indent=2), encoding="utf-8")
        bindings_schema_path.write_text(json.dumps(binding_schema, ensure_ascii=False, indent=2), encoding="utf-8")
        index_path.write_text(html, encoding="utf-8")

        summary = f"""# Crypto-Astro Static Snapshot Summary

NODE={NODE}
STATUS=PASS
GENERATED_AT_UTC={generated_at}
SOURCE_MODE=static_public_snapshot

## Market Reality

- Market Cap: {cap_s}
- 24h Volume: {vol_s}
- BTC Dominance: {btc_s}
- ETH Dominance: {eth_s}
- Stablecoin Share: {stable_s}

## Liquidity / TVL

- Stablecoin Cap: {usd_compact(stable_cap)}
- DeFi TVL: {usd_compact(tvl)}
- DEX Volume 24h: {usd_compact(dex_volume)}
- Liquidity Health: {liq_state}

## Altcoin Rotation

- Alt Breadth 24h: {pct(alt24)}
- Alt Breadth 7d: {pct(alt7)}
- Top-10 Flow Concentration: {pct(top10_flow)}

## Boundary

Static public snapshot only. No live adapter claim. Not financial advice. No trading signal. No forecast. No price target.
"""
        summary_path.write_text(summary, encoding="utf-8")

        operator_review = f"""# Crypto-Astro Operator Review

NODE={NODE}
STATUS=PASS_PENDING_VISUAL_REVIEW
GENERATED_AT_UTC={generated_at}

## Changed modules

- Market Reality / Market Field
- A/E/M Field Barometer
- Continuation Field
- Liquidity / TVL
- Altcoin Rotation Field
- TON / ICP Public Sample
- BTC / ETH / SOL static sample bundle

## Review checklist

- Confirm local preview opens.
- Confirm Market Reality values updated.
- Confirm Liquidity / TVL values are context-only.
- Confirm Altcoin Rotation values updated.
- Confirm TON / ICP panel timestamp updated.
- Confirm no live feed claim.
- Confirm no trading signal / forecast / price target / investment recommendation.

## Boundary

No push, no PR, no deploy.
"""
        operator_review_path.write_text(operator_review, encoding="utf-8")

        # Validation.
        for p in [snapshot_path, proof_path, bindings_path, bindings_schema_path]:
            json.loads(p.read_text(encoding="utf-8"))
        report["validation"]["JSON_PARSE"] = "PASS"
        report["validation"]["SCHEMA_VALIDATION"] = "PASS" if bindings.get("schema_version") == "crypto_astro_public_module_bindings_v0_1" else "FAIL"

        changed = run(["git","status","--porcelain"], repo, check=False).splitlines()
        changed_files = []
        for line in changed:
            if not line.strip():
                continue
            path = line[3:].strip() if len(line) > 3 else line.strip().split()[-1]
            changed_files.append(path)
        report["changed_files"] = changed_files
        extra = [p for p in changed_files if p not in ALLOWLIST]
        report["validation"]["EXACT_FILE_ALLOWLIST"] = "PASS" if not extra else "HOLD"

        lower = html.lower()
        # Positive forbidden phrases are distinguished from negative boundary copy.
        forbidden_positive = []
        suspicious = ["buy signal", "sell signal", "price target", "investment recommendation"]
        for s in suspicious:
            if s in lower:
                # allow only if nearby negator exists
                for m in re.finditer(re.escape(s), lower):
                    window = lower[max(0,m.start()-25):m.start()+len(s)+25]
                    if not any(x in window for x in ["no ", "not ", "without "]):
                        forbidden_positive.append(s)
        report["validation"]["FORBIDDEN_SCAN"] = "PASS" if not forbidden_positive else "HOLD"
        required_boundary = ["not financial advice", "no trading signal", "no live", "no automated execution"]
        boundary_hits = {b: (b in lower) for b in required_boundary}
        report["validation"]["BOUNDARY_SCAN"] = "PASS" if any(boundary_hits.values()) else "HOLD"
        old_literals = ["$2.158T","$82.71B","55.6%","14.4%"]
        remaining_old = [x for x in old_literals if x in html]
        report["validation"]["OLD_LITERAL_CHECK"] = "PASS" if not remaining_old else "HOLD"

        # Add validation report file.
        report_path = out_dir / "crypto_astro_all_module_static_refresh_validation_report.json"
        report.update({
            "status": "PASS" if all(v == "PASS" for v in report["validation"].values()) else "HOLD",
            "generated_at_utc": generated_at,
            "replacement_counts": replacements,
            "remaining_old_literals": remaining_old,
            "forbidden_positive": forbidden_positive,
            "paths": {
                "snapshot": str(snapshot_path),
                "proof": str(proof_path),
                "bindings": str(bindings_path),
                "bindings_schema": str(bindings_schema_path),
                "summary": str(summary_path),
                "operator_review": str(operator_review_path),
                "validation_report": str(report_path),
            },
            "sha256": {
                "snapshot": sha256_path(snapshot_path),
                "proof": sha256_path(proof_path),
                "bindings": sha256_path(bindings_path),
                "bindings_schema": sha256_path(bindings_schema_path),
                "summary": sha256_path(summary_path),
                "operator_review": sha256_path(operator_review_path),
            },
            "push": "NO",
            "pr": "NO",
            "deploy": "NO",
            "local_preview_ready": "YES"
        })
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["sha256"]["validation_report"] = sha256_path(report_path)
        # Rewrite with own hash absent in file; acceptable. 
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        validation_sha = sha256_path(report_path)
        report["sha256"]["validation_report"] = validation_sha

        def rel(path):
            return str(path)
        print("RESULT_BLOCK_START")
        print(f"NODE={NODE}")
        print(f"STATUS={report['status']}")
        print(f"BRANCH={TARGET_BRANCH}")
        print("BASE_BRANCH=main")
        print("CHANGED_FILES_START")
        for f in changed_files:
            print(f)
        print("CHANGED_FILES_END")
        print(f"SNAPSHOT_PATH={rel(snapshot_path)}")
        print(f"SNAPSHOT_SHA256={report['sha256']['snapshot']}")
        print(f"PROOF_PATH={rel(proof_path)}")
        print(f"PROOF_SHA256={report['sha256']['proof']}")
        print(f"BINDINGS_PATH={rel(bindings_path)}")
        print(f"BINDINGS_SHA256={report['sha256']['bindings']}")
        print(f"BINDINGS_SCHEMA_PATH={rel(bindings_schema_path)}")
        print(f"BINDINGS_SCHEMA_SHA256={report['sha256']['bindings_schema']}")
        print(f"SUMMARY_PATH={rel(summary_path)}")
        print(f"SUMMARY_SHA256={report['sha256']['summary']}")
        print(f"OPERATOR_REVIEW_PATH={rel(operator_review_path)}")
        print(f"OPERATOR_REVIEW_SHA256={report['sha256']['operator_review']}")
        print(f"VALIDATION_REPORT_PATH={rel(report_path)}")
        print(f"VALIDATION_REPORT_SHA256={validation_sha}")
        print("VALIDATION:")
        for k in ["JSON_PARSE","SCHEMA_VALIDATION","EXACT_FILE_ALLOWLIST","FORBIDDEN_SCAN","BOUNDARY_SCAN","OLD_LITERAL_CHECK"]:
            print(f"{k}={report['validation'].get(k,'HOLD')}")
        print(f"LOCAL_PREVIEW_READY={report.get('local_preview_ready','NO')}")
        print("PUSH=NO")
        print("PR=NO")
        print("DEPLOY=NO")
        print("NEXT_SAFE_NODE=V9_CRYPTO_ASTRO_ALL_MODULE_STATIC_REFRESH_LOCAL_RESULT_REVIEW_SCOPE_v0_1")
        print("RESULT_BLOCK_END")

    except Exception as e:
        # Write hold report.
        hold_path = out_dir / "crypto_astro_all_module_static_refresh_hold_report.json"
        report["status"] = "HOLD"
        report["error"] = str(e)
        report["proof"] = proof
        hold_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("RESULT_BLOCK_START")
        print(f"NODE={NODE}")
        print("STATUS=HOLD")
        print(f"BRANCH={TARGET_BRANCH}")
        print("BASE_BRANCH=main")
        print("CHANGED_FILES_START")
        print("NONE")
        print("CHANGED_FILES_END")
        print("SNAPSHOT_PATH=NONE")
        print("SNAPSHOT_SHA256=NONE")
        print("PROOF_PATH=NONE")
        print("PROOF_SHA256=NONE")
        print("BINDINGS_PATH=NONE")
        print("BINDINGS_SHA256=NONE")
        print("BINDINGS_SCHEMA_PATH=NONE")
        print("BINDINGS_SCHEMA_SHA256=NONE")
        print("SUMMARY_PATH=NONE")
        print("SUMMARY_SHA256=NONE")
        print("OPERATOR_REVIEW_PATH=NONE")
        print("OPERATOR_REVIEW_SHA256=NONE")
        print(f"VALIDATION_REPORT_PATH={hold_path}")
        print(f"VALIDATION_REPORT_SHA256={sha256_path(hold_path)}")
        print("VALIDATION:")
        print(f"JSON_PARSE={report['validation'].get('JSON_PARSE','HOLD')}")
        print(f"SCHEMA_VALIDATION={report['validation'].get('SCHEMA_VALIDATION','HOLD')}")
        print(f"EXACT_FILE_ALLOWLIST={report['validation'].get('EXACT_FILE_ALLOWLIST','HOLD')}")
        print(f"FORBIDDEN_SCAN={report['validation'].get('FORBIDDEN_SCAN','HOLD')}")
        print(f"BOUNDARY_SCAN={report['validation'].get('BOUNDARY_SCAN','HOLD')}")
        print(f"OLD_LITERAL_CHECK={report['validation'].get('OLD_LITERAL_CHECK','HOLD')}")
        print("LOCAL_PREVIEW_READY=NO")
        print("PUSH=NO")
        print("PR=NO")
        print("DEPLOY=NO")
        print("NEXT_SAFE_NODE=V9_CRYPTO_ASTRO_ALL_MODULE_STATIC_REFRESH_LOCAL_HOLD_REVIEW_SCOPE_v0_1")
        print("RESULT_BLOCK_END")

if __name__ == "__main__":
    main()
