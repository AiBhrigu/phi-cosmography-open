#!/usr/bin/env python3
"""Render dynamic Snapshot Memory v0.2 into the static What Changed section."""
from __future__ import annotations

import argparse
import html
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

METRICS = (
    ("btc_gravity_pct", "BTC gravity"),
    ("stablecoin_share_pct", "Stablecoin share"),
    ("alt_breadth_24h_pct", "Alt breadth · 24h"),
    ("alt_breadth_7d_pct", "Alt breadth · 7d"),
    ("market_field_score", "Market Field Score"),
    ("regime_label", "Regime"),
    ("defi_tvl_usd", "DeFi TVL"),
    ("liquidity_context_state", "Liquidity context"),
)
LABELS = dict(METRICS)
UNITS = {"percentage_points": "percentage points", "score_points": "points"}
SECTION_PATTERN = re.compile(
    r'<section id="what-changed".*?</section>\n(?=<!-- BTC_PHI_CYCLE_HUB_SURFACE_LIFT_v0_1:BEGIN -->)',
    re.S,
)
CSS_LINK = '<link href="../theme/crypto_astro_what_changed.css" rel="stylesheet"/>'
CSS_ANCHOR = '<link href="../theme/crypto_astro_surface.css" rel="stylesheet"/>'
# Stable public presentation marker. The underlying data contract is validated as v0.2.
PUBLIC_SOURCE_MARKER = "crypto_astro_snapshot_delta_public_v0_1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_time(snapshot_id: str) -> str:
    prefix = "crypto-astro:"
    if not snapshot_id.startswith(prefix) or ":" not in snapshot_id[len(prefix):]:
        raise ValueError(f"invalid snapshot id: {snapshot_id}")
    return snapshot_id[len(prefix):].rsplit(":", 1)[0]


def compact_usd(value: Decimal, *, signed=False) -> str:
    sign = "+" if signed and value > 0 else "-" if value < 0 else ""
    absolute = abs(value)
    for divisor, suffix in ((Decimal("1e12"), "T"), (Decimal("1e9"), "B"), (Decimal("1e6"), "M")):
        if absolute >= divisor:
            scaled = (absolute / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return f"{sign}${scaled:.2f}{suffix}"
    rounded = absolute.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"{sign}${rounded:,.0f}"


def display_value(metric: dict, field: str) -> str:
    value = metric[field]
    if metric["type"] == "CATEGORICAL":
        return html.escape(str(value))
    decimal = Decimal(str(value))
    if metric["unit"] == "usd":
        return html.escape(compact_usd(decimal))
    precision = int(metric["display_precision"])
    quantum = Decimal("1").scaleb(-precision)
    text = format(decimal.quantize(quantum, rounding=ROUND_HALF_UP), f".{precision}f")
    if metric["unit"] == "percent":
        text += "%"
    return html.escape(text)


def validate_contract(registry: dict, delta: dict) -> None:
    if registry.get("schema_version") != "crypto_astro_snapshot_registry_public_v0_2":
        raise ValueError("unexpected registry schema")
    if registry.get("selection_policy") != "EXPLICIT_ACCEPTED_PAIR":
        raise ValueError("registry is not an explicit accepted pair")
    if delta.get("schema_version") != "crypto_astro_snapshot_delta_public_v0_2":
        raise ValueError("unexpected delta schema")
    if delta.get("comparison_status") not in {"FULL_COMPARABLE", "PARTIAL_COMPARABLE", "UNAVAILABLE"}:
        raise ValueError("unexpected comparison status")
    if registry["current"]["snapshot_id"] != delta["current_snapshot_id"]:
        raise ValueError("current snapshot id mismatch")
    if registry["previous"]["snapshot_id"] != delta["previous_snapshot_id"]:
        raise ValueError("previous snapshot id mismatch")
    metrics = set(delta.get("metrics") or {})
    unavailable = set(delta.get("unavailable_metrics") or {})
    if metrics | unavailable != set(LABELS) or metrics & unavailable:
        raise ValueError("metric partition mismatch")
    expected_status = "FULL_COMPARABLE" if len(metrics) == len(LABELS) else "PARTIAL_COMPARABLE" if metrics else "UNAVAILABLE"
    if delta["comparison_status"] != expected_status:
        raise ValueError("comparison status mismatch")
    for key in (
        "read_only", "static_public_snapshot", "runtime_closed", "backend_api_closed",
        "payment_closed", "orion_core_protected", "no_forecast", "no_trading_signal",
        "no_price_target", "ui_binding_opened", "refresh_pipeline_binding_opened",
    ):
        if delta.get("boundary", {}).get(key) is not True:
            raise ValueError(f"boundary mismatch: {key}")


def metric_card(key: str, label: str, metric: dict) -> str:
    if metric.get("status") != "COMPARABLE":
        raise ValueError(f"metric is not comparable: {key}")
    previous = display_value(metric, "previous_value")
    current = display_value(metric, "current_value")
    if metric["type"] == "CATEGORICAL":
        transition = str(metric.get("transition", "")).upper()
        delta_text = "Unchanged" if transition == "UNCHANGED" else "Changed"
        direction = "unchanged" if transition == "UNCHANGED" else "changed"
    elif metric["delta_unit"] == "usd":
        delta_text = compact_usd(Decimal(str(metric["raw_delta"])), signed=True)
        direction = str(metric["direction"]).lower()
    else:
        delta_text = f'{html.escape(str(metric["display_delta"]))} {html.escape(UNITS[metric["delta_unit"]])}'
        direction = str(metric["direction"]).lower()
    return f'''      <article class="what-changed-metric-v0-1" data-metric="{key}" data-direction="{direction}">
        <span>{html.escape(label)}</span>
        <strong>{delta_text}</strong>
        <small>{previous} → {current}</small>
      </article>'''


def unavailable_block(items: dict) -> str:
    if not items:
        return '''  <div class="what-changed-memory-v0-1__unavailable" role="note" aria-label="Comparison methodology status">
    <strong>Methodology continuity verified</strong>
    <span>All tracked metrics are comparable for this accepted pair.</span>
  </div>'''
    rows = "\n".join(
        f'    <span>{html.escape(LABELS[key])} · unavailable <code>{html.escape(str(items[key]["reason_code"]))}</code></span>'
        for key, _ in METRICS if key in items
    )
    return f'''  <div class="what-changed-memory-v0-1__unavailable" role="note" aria-label="Unavailable comparisons">
    <strong>Methodology boundary preserved</strong>
{rows}
  </div>'''


def render(registry: dict, delta: dict) -> str:
    validate_contract(registry, delta)
    cards = "\n".join(metric_card(key, label, delta["metrics"][key])
                      for key, label in METRICS if key in delta["metrics"])
    current = html.escape(snapshot_time(delta["current_snapshot_id"]))
    previous = html.escape(snapshot_time(delta["previous_snapshot_id"]))
    generated = html.escape(str(delta["generated_at_utc"]))
    status = delta["comparison_status"].lower().replace("_", "-")
    return f'''<section id="what-changed" class="editorial-what-changed-v0-1 editorial-chapter-v0-1 what-changed-memory-v0-1" data-editorial-chapter="what-changed" data-what-changed-status="{status}" data-source-contract="{PUBLIC_SOURCE_MARKER}" aria-labelledby="what-changed-title">
  <div class="what-changed-memory-v0-1__head">
    <div>
      <p class="eyebrow">What Changed</p>
      <h2 id="what-changed-title">Verified change memory</h2>
      <p>Current and previous accepted snapshots are compared only where source, methodology, universe, and proof bindings remain compatible.</p>
    </div>
    <dl class="what-changed-memory-v0-1__snapshots" aria-label="Compared snapshot timestamps">
      <div><dt>Current</dt><dd>{current}</dd></div>
      <div><dt>Previous</dt><dd>{previous}</dd></div>
    </dl>
  </div>
  <div class="what-changed-memory-v0-1__grid" aria-label="Verified comparable changes">
{cards}
  </div>
{unavailable_block(delta["unavailable_metrics"])}
  <p class="what-changed-memory-v0-1__meta">Static accepted-pair comparison · generated {generated}. No relative percentages, cached reconstruction, live feed, forecast, or trading signal.</p>
</section>'''


def apply(repo: Path) -> None:
    registry = load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot_registry.public.json")
    delta = load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot_delta.public.json")
    path = repo / "site/crypto-astro/index.html"
    source = path.read_text(encoding="utf-8")
    updated, count = SECTION_PATTERN.subn(render(registry, delta) + "\n", source)
    if count != 1:
        raise ValueError(f"What Changed section count mismatch: {count}")
    if CSS_LINK not in updated:
        if updated.count(CSS_ANCHOR) != 1:
            raise ValueError("CSS anchor count mismatch")
        updated = updated.replace(CSS_ANCHOR, CSS_ANCHOR + "\n" + CSS_LINK)
    if updated.count(CSS_LINK) != 1:
        raise ValueError("What Changed CSS link count mismatch")
    path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    apply(Path(args.repo).resolve())
