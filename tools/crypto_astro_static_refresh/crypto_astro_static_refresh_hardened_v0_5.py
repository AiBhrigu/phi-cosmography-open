#!/usr/bin/env python3
"""Fail-closed compatibility entrypoint for the current Crypto-Astro public surface.

The preserved v0.5 core remains byte-locked. This entrypoint adapts only DOM bindings
whose markup changed during later verified surface work. It does not relax source,
methodology, allowlist, boundary, or rollback gates.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

CORE_PATH = Path(__file__).with_name("crypto_astro_static_refresh_hardened_v0_5_core.py")
EXPECTED_CORE_BLOB_SHA = "2a37742fc4d962be4bcbc7e8d925834102de5030"
SUPERSEDED_BINDINGS = {
    "rail:eth-anchor": "Superseded by visible composition and Altcoin Rotation ETH bindings.",
}
CURRENT_REQUIRED_HTML_BINDINGS = (
    "metric:Market Cap", "metric:24h Volume", "metric:BTC Dominance", "metric:Stablecoin Share",
    "composition:btc", "composition:stable", "composition:alt", "label:btc_gravity",
    "label:stable_membrane", "label:alt_field", "label:top10_flow", "timestamp:market_note",
    "liquidity:stable_cap", "liquidity:defi_tvl", "liquidity:dex_volume",
    "liquidity:defi_tvl_methodology_copy",
    "metric:Alt Breadth 24h", "metric:Alt Breadth 7d", "metric:Top-10 Flow Concentration",
    "alt_map:24h", "alt_map:7d", "alt_map:top10", "timestamp:coingecko_snapshot",
    "btc_hub:gravity", "btc_hub:snapshot", "btc_hub:quiet_gravity",
    "composition:eth", "label:eth_anchor", "alt_map:eth", "alt_map:eth_center",
    "field:score_orb", "alt_read:data_bound",
    "copy_slot:field_state_title", "copy_slot:field_state_badge",
    "copy_slot:field_state_body_1", "copy_slot:field_state_body_2",
    "copy_slot:state_structure_status", "copy_slot:state_pressure_status",
    "copy_slot:state_breadth_status", "copy_slot:field_synthesis_lead",
    "copy_slot:field_synthesis_body_1", "copy_slot:field_synthesis_body_2",
    "copy_slot:field_synthesis_body_3", "copy_slot:btc_gravity_status",
    "copy_slot:stablecoin_pressure_status", "copy_slot:alt_rotation_status",
    "copy_slot:liquidity_depth_status", "copy_slot:timing_context_status",
    "copy_slot:source_freshness_status", "copy_slot:method_market_reality",
    "copy_slot:method_liquidity_tvl", "copy_slot:method_altcoin_rotation",
    "copy_slot:method_aem_barometer", "copy_slot:method_continuation",
    "copy_slot:method_astromodule", "copy_slot:method_source_freshness",
    "sample:ton_visual_score", "sample:icp_visual_score",
    "sample:ton_visual_24h", "sample:icp_visual_24h",
    "sample:dual_visual_gauge", "sample:ton_score", "sample:ton_24h",
    "sample:ton_30d", "sample:ton_rank", "sample:icp_score",
    "sample:icp_24h", "sample:icp_30d", "sample:icp_rank",
    "sample:ton_barometer", "sample:icp_barometer", "sample:dual_distributed_gauge",
    "scoring:intro", "scoring:snapshot", "scoring:coverage", "scoring:heartbeat",
)


def git_blob_sha(path: Path) -> str:
    value = path.read_bytes()
    return hashlib.sha1(f"blob {len(value)}\0".encode() + value).hexdigest()


def load_locked_core():
    if not CORE_PATH.is_file():
        raise RuntimeError(f"hardened core missing: {CORE_PATH}")
    actual = git_blob_sha(CORE_PATH)
    if actual != EXPECTED_CORE_BLOB_SHA:
        raise RuntimeError(f"hardened core blob mismatch: {actual}")
    spec = importlib.util.spec_from_file_location("crypto_astro_static_refresh_hardened_v0_5_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load hardened core")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_locked_core()


def __getattr__(name: str):
    """Preserve the public v0.5 module API through the byte-locked core."""
    return getattr(core, name)


_core_patch_html = core.patch_html


def _number2(value) -> str:
    return "pending" if value is None else f"{float(value):.2f}"


def _percent2(value) -> str:
    return "pending" if value is None else f"{float(value):.2f}%"


def _width(value) -> str:
    try:
        return f"{core.clamp(float(value)):.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _replace_visual_score(html: str, label: str, score: str, width: str, key: str, counts: dict) -> str:
    pattern = (
        rf'(<div class="visual-row-v0-1"[^>]*><span>{re.escape(label)}</span>'
        rf'<div class="visual-rail-v0-1"><i style="width:)[^"]+'
        rf'("></i></div><span class="visual-value-v0-1">)[^<]+(</span></div>)'
    )
    return core.replace_counted(
        html, pattern, lambda m: f"{m.group(1)}{width}{m.group(2)}{score}{m.group(3)}", key, counts
    )


def _replace_visual_text(html: str, label: str, value: str, key: str, counts: dict) -> str:
    pattern = (
        rf'(<div class="visual-row-v0-1 visual-row-text-v0-1"[^>]*>'
        rf'<span>{re.escape(label)}</span><strong class="visual-value-v0-1">)[^<]+'
        rf'(</strong></div>)'
    )
    return core.replace_counted(html, pattern, lambda m: f"{m.group(1)}{value}{m.group(2)}", key, counts)


def _replace_distributed_score(
    html: str, aria_label: str, score: str, width: str, key: str, counts: dict
) -> str:
    pattern = (
        rf'(<div class="distributed-rail-v0-1" aria-label="{re.escape(aria_label)}">.*?'
        rf'<div class="distributed-row-v0-1"[^>]*><span>Score</span>'
        rf'<div class="distributed-track-v0-1"><i style="width:)[^"]+'
        rf'("></i></div><span class="distributed-value-v0-1">)[^<]+(</span>)'
    )
    return core.replace_counted(
        html,
        pattern,
        lambda m: f"{m.group(1)}{width}{m.group(2)}{score}{m.group(3)}",
        key,
        counts,
        flags=re.S,
    )


def _replace_distributed_text(
    html: str, aria_label: str, row_label: str, value: str, key: str, counts: dict
) -> str:
    pattern = (
        rf'(<div class="distributed-rail-v0-1" aria-label="{re.escape(aria_label)}">.*?'
        rf'<div class="distributed-row-v0-1 distributed-row-text-v0-1"[^>]*>'
        rf'<span>{re.escape(row_label)}</span><strong class="distributed-value-v0-1">)[^<]+'
        rf'(</strong>)'
    )
    return core.replace_counted(
        html, pattern, lambda m: f"{m.group(1)}{value}{m.group(2)}", key, counts, flags=re.S
    )


def patch_html(repo: Path, snapshot: dict) -> dict:
    patch_report = _core_patch_html(repo, snapshot)
    path = repo / "site/crypto-astro/index.html"
    html = core.read_text(path)
    counts = patch_report.setdefault("replace_counts", {})
    field = snapshot.get("field_output") or {}
    samples = ((snapshot.get("public_samples") or {}).get("assets") or {})

    raw_score = field.get("market_field_score")
    field_score = "pending" if raw_score is None else str(int(round(float(raw_score))))
    html = core.replace_counted(
        html,
        r'(<div class="score-orb field-gauge"[^>]*aria-label="Market Field Score )[^\"]+( out of 100">)[^<]+(</div>)',
        lambda m: f"{m.group(1)}{field_score}{m.group(2)}{field_score}{m.group(3)}",
        "field:score_orb",
        counts,
    )

    for symbol, visual_label, aria_label, prefix in (
        ("TON", "Gram (prev. Toncoin)", "Gram source sample distributed visual metrics", "ton"),
        ("ICP", "Internet Computer", "ICP comparison sample distributed visual metrics", "icp"),
    ):
        asset = samples.get(symbol) or {}
        score = _number2(asset.get("score"))
        width = _width(asset.get("score"))
        html = _replace_visual_score(html, visual_label, score, width, f"sample:{prefix}_visual_score", counts)
        html = _replace_visual_text(
            html, f"24h {symbol}", _percent2(asset.get("market_24h_change_pct")),
            f"sample:{prefix}_visual_24h", counts
        )
        html = _replace_distributed_score(html, aria_label, score, width, f"sample:{prefix}_score", counts)
        html = _replace_distributed_text(
            html, aria_label, "24h", _percent2(asset.get("market_24h_change_pct")),
            f"sample:{prefix}_24h", counts
        )
        html = _replace_distributed_text(
            html, aria_label, "30d", _percent2(asset.get("market_30d_change_pct")),
            f"sample:{prefix}_30d", counts
        )
        html = _replace_distributed_text(
            html, aria_label, "Rank", str(asset.get("market_cap_rank") or "pending"),
            f"sample:{prefix}_rank", counts
        )

    core.write_text(path, html)
    patch_report["surface_contract"] = "crypto_astro_current_surface_bindings_v0_1"
    patch_report["superseded_bindings"] = SUPERSEDED_BINDINGS.copy()
    return patch_report


def validate_html_counts(patch_report: dict, report: dict) -> bool:
    counts = patch_report.get("replace_counts") or {}
    missing = [key for key in CURRENT_REQUIRED_HTML_BINDINGS if int(counts.get(key, 0)) <= 0]
    core.set_validation(report, "html_replace_counts", counts)
    core.set_validation(report, "html_required_missing", missing)
    core.set_validation(report, "html_superseded_bindings", SUPERSEDED_BINDINGS.copy())
    core.set_validation(report, "html_surface_contract", patch_report.get("surface_contract"))
    return not missing


core.patch_html = patch_html
core.validate_html_counts = validate_html_counts


if __name__ == "__main__":
    raise SystemExit(core.main())
