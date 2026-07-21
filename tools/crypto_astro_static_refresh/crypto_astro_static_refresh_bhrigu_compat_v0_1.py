#!/usr/bin/env python3
"""BHRIGU consumer compatibility layer for the byte-locked Crypto-Astro refresh.

The existing hardened entrypoint and v0.5 core remain unchanged. This layer only:
- preserves the accepted public Market Field v0.2 schema;
- validates the exact producer bundle required by BHRIGU BTC Field Read;
- fails closed before a refresh branch can be committed or pushed.
"""
from __future__ import annotations

import importlib.util
import math
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_ENTRYPOINT = Path(__file__).with_name("crypto_astro_static_refresh_hardened_v0_5.py")
BHRIGU_MARKET_FIELD_SCHEMA = "crypto_astro_market_field_public_v0_2"
MAX_COMPATIBILITY_SECONDS = 300
REQUIRED_PROOF_LABELS = {
    "coingecko_global",
    "coingecko_asset_markets_btc_eth_sol_ton_icp",
    "coingecko_top250_markets",
    "coingecko_stablecoin_sample",
    "defillama_protocols",
    "defillama_dex_overview",
    "defillama_stablecoins",
}


def load_base_entrypoint():
    spec = importlib.util.spec_from_file_location("crypto_astro_static_refresh_hardened_v0_5", BASE_ENTRYPOINT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load hardened compatibility entrypoint")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_entrypoint()
core = base.core
_core_update_market_field = core.update_market_field
_core_validate_active_outputs = core.validate_active_outputs


def _record(value) -> bool:
    return isinstance(value, dict)


def _nonempty(value, max_length=512) -> bool:
    return isinstance(value, str) and 0 < len(value.strip()) <= max_length


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _timestamp(value) -> datetime | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z", value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _compatible(a, b) -> bool:
    left = _timestamp(a)
    right = _timestamp(b)
    return bool(left and right and abs((left - right).total_seconds()) <= MAX_COMPATIBILITY_SECONDS)


def validate_bhrigu_market_field(data: dict) -> list[str]:
    errors: list[str] = []
    if not _record(data):
        return ["market_field:not_object"]
    if data.get("schema_version") != BHRIGU_MARKET_FIELD_SCHEMA:
        errors.append("market_field:schema_version")
    if data.get("snapshot_mode") != "public_safe_market_field":
        errors.append("market_field:snapshot_mode")
    if data.get("source_mode") != "static_public_snapshot":
        errors.append("market_field:source_mode")
    if data.get("derived_from") != "site/crypto-astro/data/crypto_astro_snapshot.public.json":
        errors.append("market_field:derived_from")
    if data.get("derived_status") != "DERIVED_FROM_CANONICAL_SNAPSHOT":
        errors.append("market_field:derived_status")
    if _timestamp(data.get("updated_at_utc")) is None:
        errors.append("market_field:updated_at_utc")

    vectors = data.get("vectors")
    if not _record(vectors):
        errors.append("market_field:vectors")
        vectors = {}
    for key in ("A_membrane", "E_membrane"):
        membrane = vectors.get(key)
        if membrane != {"state": "prepared_inactive", "public_input": False, "disclosure": "status_only"}:
            errors.append(f"market_field:{key}")
    if not _record(vectors.get("M_market")):
        errors.append("market_field:M_market")
    context = vectors.get("CT_context")
    if not _record(context):
        errors.append("market_field:CT_context")
    else:
        if context.get("pipeline") != "sealed":
            errors.append("market_field:CT_context_pipeline")
        for key in ("state", "observation_window", "phase_context", "provenance"):
            if not _nonempty(context.get(key), 160):
                errors.append(f"market_field:CT_context_{key}")
    if "CT_temporal" in vectors:
        errors.append("market_field:legacy_CT_temporal")

    field = data.get("field_output")
    if not _record(field):
        errors.append("market_field:field_output")
    else:
        if not _finite(field.get("market_field_score")):
            errors.append("market_field:market_field_score")
        if not _nonempty(field.get("regime_label"), 160):
            errors.append("market_field:regime_label")
        if not _nonempty(field.get("direction_bias"), 160):
            errors.append("market_field:direction_bias")
    if not _record(data.get("cosmographer_read")):
        errors.append("market_field:cosmographer_read")
    if data.get("boundary") != core.BOUNDARY:
        errors.append("market_field:boundary")
    return errors


def validate_bhrigu_consumer_bundle(repo: Path) -> list[str]:
    errors: list[str] = []
    try:
        snapshot = core.load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot.public.json")
        proof = core.load_json(repo / "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json")
        market_field = core.load_json(repo / "site/crypto-astro/data/market_field_snapshot.public.v0_1.json")
    except Exception as exc:
        return [f"bundle:load_failure:{exc}"]

    if snapshot.get("schema_version") != "crypto_astro_snapshot_public_v0_1":
        errors.append("snapshot:schema_version")
    if snapshot.get("source_mode") != "static_public_snapshot":
        errors.append("snapshot:source_mode")
    if snapshot.get("boundary") != core.BOUNDARY:
        errors.append("snapshot:boundary")
    if _timestamp(snapshot.get("generated_at_utc")) is None:
        errors.append("snapshot:generated_at_utc")

    if proof.get("schema_version") != "crypto_astro_snapshot_proof_public_v0_1":
        errors.append("proof:schema_version")
    if proof.get("source_mode") != "static_public_snapshot":
        errors.append("proof:source_mode")
    if proof.get("boundary") != core.BOUNDARY:
        errors.append("proof:boundary")
    sources = proof.get("sources")
    if not isinstance(sources, list):
        errors.append("proof:sources")
        sources = []
    labels = {item.get("label") for item in sources if _record(item) and item.get("status") == "PASS"}
    if labels != REQUIRED_PROOF_LABELS:
        errors.append("proof:required_pass_labels")

    errors.extend(validate_bhrigu_market_field(market_field))
    if not _compatible(snapshot.get("generated_at_utc"), proof.get("generated_at_utc")):
        errors.append("bundle:snapshot_proof_timestamp")
    if not _compatible(snapshot.get("generated_at_utc"), market_field.get("updated_at_utc")):
        errors.append("bundle:snapshot_market_field_timestamp")
    return errors


def update_market_field(repo: Path, snapshot: dict) -> dict:
    data = _core_update_market_field(repo, snapshot)
    data["schema_version"] = BHRIGU_MARKET_FIELD_SCHEMA
    path = repo / "site/crypto-astro/data/market_field_snapshot.public.v0_1.json"
    core.write_json(path, data)
    errors = validate_bhrigu_market_field(data)
    if errors:
        raise RuntimeError(f"BHRIGU market-field contract failed after generation: {errors}")
    return data


def validate_active_outputs(repo: Path, report: dict) -> bool:
    base_ok = _core_validate_active_outputs(repo, report)
    errors = validate_bhrigu_consumer_bundle(repo)
    core.set_validation(report, "bhrigu_consumer_contract_errors", errors)
    core.set_validation(report, "bhrigu_consumer_contract", "PASS" if not errors else "FAIL")
    return base_ok and not errors


core.update_market_field = update_market_field
core.validate_active_outputs = validate_active_outputs


if __name__ == "__main__":
    raise SystemExit(core.main())
