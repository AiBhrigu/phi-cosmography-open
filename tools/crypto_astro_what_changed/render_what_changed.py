#!/usr/bin/env python3
"""Render the committed Snapshot Memory accepted pair into static public HTML."""
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
)
UNITS = {"percentage_points": "percentage points", "score_points": "points"}
SECTION_PATTERN = re.compile(
    r'<section id="what-changed".*?</section>\n(?=<!-- BTC_PHI_CYCLE_HUB_SURFACE_LIFT_v0_1:BEGIN -->)',
    re.S,
)
CSS_LINK = '<link href="../theme/crypto_astro_what_changed.css" rel="stylesheet"/>'
CSS_ANCHOR = '<link href="../theme/crypto_astro_surface.css" rel="stylesheet"/>'


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_time(snapshot_id: str) -> str:
    prefix = "crypto-astro:"
    if not snapshot_id.startswith(prefix) or ":" not in snapshot_id[len(prefix):]:
        raise ValueError(f"invalid snapshot id: {snapshot_id}")
    return snapshot_id[len(prefix):].rsplit(":", 1)[0]


def display_value(metric: dict, field: str) -> str:
    value = metric[field]
    if metric["type"] == "CATEGORICAL":
        return html.escape(str(value))
    precision = int(metric["display_precision"])
    quantum = Decimal("1").scaleb(-precision)
    text = format(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP), f".{precision}f")
    if metric["unit"] == "percent":
        text += "%"
    return html.escape(text)


def validate_contract(registry: dict, delta: dict) -> None:
    if registry.get("schema_version") != "crypto_astro_snapshot_registry_public_v0_1":
        raise ValueError("unexpected registry schema")
    if registry.get("selection_policy") != "EXPLICIT_ACCEPTED_PAIR":
        raise ValueError("registry is not an explicit accepted pair")
    if delta.get("schema_version") != "crypto_astro_snapshot_delta_public_v0_1":
        raise ValueError("unexpected delta schema")
    if delta.get("comparison_status") != "PARTIAL_COMPARABLE":
        raise ValueError("delta is not partial-comparable")
    if registry["current"]["snapshot_id"] != delta["current_snapshot_id"]:
        raise ValueError("current snapshot id mismatch")
    if registry["previous"]["snapshot_id"] != delta["previous_snapshot_id"]:
        raise ValueError("previous snapshot id mismatch")
    for key in (
        "read_only",
        "static_public_snapshot",
        "runtime_closed",
        "backend_api_closed",
        "payment_closed",
        "orion_core_protected",
        "no_forecast",
        "no_trading_signal",
        "no_price_target",
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
        delta_text = "Unchanged" if transition == "UNCHANGED" else html.escape(transition.title())
        direction = "unchanged" if transition == "UNCHANGED" else "changed"
    else:
        delta_text = f'{html.escape(str(metric["display_delta"]))} {html.escape(UNITS[metric["delta_unit"]])}'
        direction = str(metric["direction"]).lower()
    return f'''      <article class="what-changed-metric-v0-1" data-metric="{key}" data-direction="{direction}">
        <span>{html.escape(label)}</span>
        <strong>{delta_text}</strong>
        <small>{previous} → {current}</small>
      </article>'''


def render(registry: dict, delta: dict) -> str:
    validate_contract(registry, delta)
    cards = "\n".join(metric_card(key, label, delta["metrics"][key]) for key, label in METRICS)
    unavailable = delta["unavailable_metrics"]
    defi = unavailable["defi_tvl_usd"]
    liquidity = unavailable["liquidity_context_state"]
    if defi.get("delta_value") is not None or liquidity.get("delta_value") is not None:
        raise ValueError("unavailable metrics must not contain numeric deltas")
    current = html.escape(snapshot_time(delta["current_snapshot_id"]))
    previous = html.escape(snapshot_time(delta["previous_snapshot_id"]))
    generated = html.escape(str(delta["generated_at_utc"]))
    return f'''<section id="what-changed" class="editorial-what-changed-v0-1 editorial-chapter-v0-1 what-changed-memory-v0-1" data-editorial-chapter="what-changed" data-what-changed-status="partial-comparable" data-source-contract="crypto_astro_snapshot_delta_public_v0_1" aria-labelledby="what-changed-title">
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
  <div class="what-changed-memory-v0-1__unavailable" role="note" aria-label="Unavailable comparisons">
    <strong>Methodology boundary preserved</strong>
    <span>DeFi TVL · unavailable <code>{html.escape(defi["reason_code"])}</code></span>
    <span>Liquidity context · unavailable <code>{html.escape(liquidity["reason_code"])}</code></span>
  </div>
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
