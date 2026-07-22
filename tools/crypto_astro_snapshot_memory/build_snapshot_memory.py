#!/usr/bin/env python3
"""Offline, fail-closed accepted-pair builder for Crypto-Astro Snapshot Memory.

The registry keeps two separate Git axes:

* ``commit_sha`` is the immutable generated-data provenance commit.
* ``data_origin_commit_sha`` is the accepted base materialization from which
  that generated-data commit was created.

This distinction preserves exact provenance while remaining compatible with
review PRs that are accepted through squash merge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

SNAPSHOT_PATH = "site/crypto-astro/data/crypto_astro_snapshot.public.json"
PROOF_PATH = "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json"
BINDINGS_PATH = "site/crypto-astro/data/crypto_astro_module_bindings.public.json"
RUNNER_PATH = "tools/crypto_astro_static_refresh/crypto_astro_static_refresh_hardened_v0_5.py"
REGISTRY_PATH = "site/crypto-astro/data/crypto_astro_snapshot_registry.public.json"
DELTA_PATH = "site/crypto-astro/data/crypto_astro_snapshot_delta.public.json"
TRACKED_METRICS = (
    "btc_gravity_pct",
    "stablecoin_share_pct",
    "alt_breadth_24h_pct",
    "alt_breadth_7d_pct",
    "market_field_score",
    "regime_label",
    "defi_tvl_usd",
    "liquidity_context_state",
)

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
    "formula_weights_exposed": False,
    "crawler_input_forbidden": True,
    "html_presentation_input_forbidden": True,
    "ui_binding_opened": True,
    "refresh_pipeline_binding_opened": True,
}

URLS = {
    "coingecko_global": "https://api.coingecko.com/api/v3/global",
    "coingecko_top250_markets": (
        "https://api.coingecko.com/api/v3/coins/markets?"
        "vs_currency=usd&order=market_cap_desc&per_page=250&page=1&"
        "price_change_percentage=1h%2C24h%2C7d%2C30d&sparkline=false"
    ),
    "defillama_stablecoins": "https://stablecoins.llama.fi/stablecoins?includePrices=true",
}

STATIC_METRICS = {
    "btc_gravity_pct": {
        "path": "market_reality.btc_dominance_pct", "kind": "numeric",
        "unit": "percent", "delta_unit": "percentage_points", "precision": 2,
        "methodology_id": "coingecko_global_btc_dominance_direct_v0_1",
        "sources": ["coingecko_global"], "binding": "market_reality",
    },
    "stablecoin_share_pct": {
        "path": "market_reality.stablecoin_share_pct", "kind": "numeric",
        "unit": "percent", "delta_unit": "percentage_points", "precision": 2,
        "methodology_id": "stablecoin_share_prefer_llama_then_coingecko_over_total_cap_v0_1",
        "sources": ["defillama_stablecoins", "coingecko_global"], "binding": "market_reality",
    },
    "alt_breadth_24h_pct": {
        "path": "altcoin_rotation.alt_breadth_24h_pct", "kind": "numeric",
        "unit": "percent", "delta_unit": "percentage_points", "precision": 1,
        "methodology_id": "top250_nonstable_ex_btc_positive_breadth_24h_v0_1",
        "sources": ["coingecko_top250_markets"], "binding": "altcoin_rotation",
        "universe": "altcoin_rotation.universe",
    },
    "alt_breadth_7d_pct": {
        "path": "altcoin_rotation.alt_breadth_7d_pct", "kind": "numeric",
        "unit": "percent", "delta_unit": "percentage_points", "precision": 1,
        "methodology_id": "top250_nonstable_ex_btc_positive_breadth_7d_v0_1",
        "sources": ["coingecko_top250_markets"], "binding": "altcoin_rotation",
        "universe": "altcoin_rotation.universe",
    },
    "market_field_score": {
        "path": "field_output.market_field_score", "kind": "numeric",
        "unit": "score_0_100", "delta_unit": "score_points", "precision": 1,
        "methodology_id": "public_market_field_score_v0_1",
        "sources": ["coingecko_global", "coingecko_top250_markets", "defillama_stablecoins"],
        "binding": "aem_barometer",
    },
    "regime_label": {
        "path": "field_output.regime_label", "kind": "categorical",
        "unit": "state", "methodology_id": "public_regime_threshold_58_v0_1",
        "sources": ["coingecko_global", "coingecko_top250_markets", "defillama_stablecoins"],
        "binding": "aem_barometer",
    },
}

BINDING_SOURCES = {
    "market_reality": "market_reality",
    "altcoin_rotation": "altcoin_rotation",
    "aem_barometer": "field_output",
}

DEFI_METHOD_URLS = {
    "defillama_historical_chain_tvl_ex_double_count_v0_1": "https://api.llama.fi/v2/historicalChainTvl",
    "defillama_protocols_sum_v0_1": "https://api.llama.fi/protocols",
}


class ContractError(RuntimeError):
    def __init__(self, reason_code: str, message: str):
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code


@dataclass(frozen=True)
class SnapshotBundle:
    role: str
    commit_sha: str
    data_origin_commit_sha: str
    runner_blob_sha: str
    snapshot_bytes: bytes
    proof_bytes: bytes
    bindings_bytes: bytes
    snapshot: dict[str, Any]
    proof: dict[str, Any]
    bindings: dict[str, Any]

    @property
    def snapshot_sha256(self) -> str:
        return hashlib.sha256(self.snapshot_bytes).hexdigest()

    @property
    def proof_sha256(self) -> str:
        return hashlib.sha256(self.proof_bytes).hexdigest()

    @property
    def bindings_sha256(self) -> str:
        return hashlib.sha256(self.bindings_bytes).hexdigest()

    @property
    def snapshot_blob_sha(self) -> str:
        return git_blob_sha(self.snapshot_bytes)

    @property
    def proof_blob_sha(self) -> str:
        return git_blob_sha(self.proof_bytes)

    @property
    def bindings_blob_sha(self) -> str:
        return git_blob_sha(self.bindings_bytes)


def git_blob_sha(value: bytes) -> str:
    return hashlib.sha1(f"blob {len(value)}\0".encode() + value).hexdigest()


def parse_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ContractError("SCHEMA_MISMATCH", f"{label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("SCHEMA_MISMATCH", f"{label} root")
    return value


def make_bundle(**kwargs: Any) -> SnapshotBundle:
    return SnapshotBundle(
        **kwargs,
        snapshot=parse_json(kwargs["snapshot_bytes"], f'{kwargs["role"]} snapshot'),
        proof=parse_json(kwargs["proof_bytes"], f'{kwargs["role"]} proof'),
        bindings=parse_json(kwargs["bindings_bytes"], f'{kwargs["role"]} bindings'),
    )


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, cwd=repo, capture_output=True, check=False)


def resolve_ref(repo: Path, ref: str, reason: str = "PROVENANCE_COMMIT_MISSING") -> str:
    result = run(repo, "git", "rev-parse", "--verify", f"{ref}^{{commit}}")
    if result.returncode:
        raise ContractError(reason, f"ref {ref}")
    return result.stdout.decode().strip()


def git_show(repo: Path, ref: str, path: str, reason: str) -> bytes:
    result = run(repo, "git", "show", f"{ref}:{path}")
    if result.returncode:
        raise ContractError(reason, f"{ref}:{path}")
    return result.stdout


def is_ancestor(repo: Path, previous: str, current: str) -> bool:
    return run(repo, "git", "merge-base", "--is-ancestor", previous, current).returncode == 0


def timestamp(value: Any, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("TIMESTAMP_ORDER_INVALID", label) from exc
    if parsed.tzinfo is None:
        raise ContractError("TIMESTAMP_ORDER_INVALID", label)
    return parsed.astimezone(timezone.utc)


def at(bundle: SnapshotBundle, path: str) -> Any:
    value: Any = bundle.snapshot
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            code = "CURRENT_MISSING" if bundle.role == "current" else "PREVIOUS_MISSING"
            raise ContractError(code, path)
        value = value[key]
    return value


def number(value: Any, metric_id: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ContractError("NON_FINITE_VALUE", metric_id)
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ContractError("NON_FINITE_VALUE", metric_id) from exc
    if not result.is_finite():
        raise ContractError("NON_FINITE_VALUE", metric_id)
    return result


def display_delta(value: Decimal, precision: int) -> str:
    rounded = value.quantize(Decimal("1").scaleb(-precision), rounding=ROUND_HALF_UP)
    return f"{rounded:+.{precision}f}"


def direction(value: Decimal) -> str:
    return "UP" if value > 0 else "DOWN" if value < 0 else "UNCHANGED"


def source_map(bundle: SnapshotBundle) -> dict[str, dict[str, Any]]:
    items = bundle.proof.get("sources")
    if not isinstance(items, list):
        raise ContractError("SCHEMA_MISMATCH", f"{bundle.role} proof.sources")
    return {
        item["label"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("label"), str)
    }


def validate_sources(bundle: SnapshotBundle, labels: list[str]) -> None:
    sources = source_map(bundle)
    for label in labels:
        item = sources.get(label)
        if not item or item.get("status") != "PASS":
            raise ContractError("PROOF_NOT_PASS", f"{bundle.role} {label}")
        expected_url = URLS.get(label)
        if expected_url and item.get("url") != expected_url:
            raise ContractError("SOURCE_URL_MISMATCH", f"{bundle.role} {label}")


def validate_binding(bundle: SnapshotBundle, module: str) -> None:
    modules = bundle.bindings.get("modules")
    if not isinstance(modules, dict) or not isinstance(modules.get(module), dict):
        raise ContractError("SOURCE_BINDING_MISSING", f"{bundle.role} {module}")
    if modules[module].get("source") != BINDING_SOURCES[module]:
        raise ContractError("SOURCE_BINDING_MISSING", f"{bundle.role} {module}.source")


def validate_shape(bundle: SnapshotBundle) -> None:
    expected = (
        ("snapshot", bundle.snapshot, "crypto_astro_snapshot_public_v0_1"),
        ("proof", bundle.proof, "crypto_astro_snapshot_proof_public_v0_1"),
        ("bindings", bundle.bindings, "crypto_astro_public_module_bindings_v0_1"),
    )
    for name, document, schema in expected:
        if document.get("schema_version") != schema:
            raise ContractError("SCHEMA_MISMATCH", f"{bundle.role} {name}")
        if document.get("source_mode") != "static_public_snapshot":
            raise ContractError("SCHEMA_MISMATCH", f"{bundle.role} {name} source_mode")
        boundary = document.get("boundary")
        if not isinstance(boundary, dict):
            raise ContractError("BOUNDARY_MISMATCH", f"{bundle.role} {name}")
        for key in (
            "read_only", "static_public_snapshot", "no_live_adapter_claim",
            "no_true_live_feed_claim", "no_trading_signal", "no_forecast",
            "no_price_target", "no_investment_recommendation", "backend_api_closed",
            "runtime_closed", "payment_closed", "orion_core_protected",
        ):
            if boundary.get(key) is not True:
                raise ContractError("BOUNDARY_MISMATCH", f"{bundle.role} {name}.{key}")
        if boundary.get("formula_weights_exposed") is not False:
            raise ContractError("BOUNDARY_MISMATCH", f"{bundle.role} {name}.formula_weights_exposed")
    if bundle.bindings.get("generated_at_utc") != bundle.snapshot.get("generated_at_utc"):
        raise ContractError("SOURCE_BINDING_MISSING", f"{bundle.role} timestamp")
    skew = abs((
        timestamp(bundle.snapshot["generated_at_utc"], "snapshot")
        - timestamp(bundle.proof["generated_at_utc"], "proof")
    ).total_seconds())
    if skew > 120:
        raise ContractError("TIMESTAMP_ORDER_INVALID", f"{bundle.role} skew")


def entry(bundle: SnapshotBundle) -> dict[str, Any]:
    generated = bundle.snapshot["generated_at_utc"]
    return {
        "role": bundle.role,
        "snapshot_id": f"crypto-astro:{generated}:{bundle.snapshot_sha256[:12]}",
        "commit_sha": bundle.commit_sha,
        "data_origin_commit_sha": bundle.data_origin_commit_sha,
        "snapshot_path": SNAPSHOT_PATH,
        "snapshot_blob_sha": bundle.snapshot_blob_sha,
        "snapshot_sha256": bundle.snapshot_sha256,
        "proof_path": PROOF_PATH,
        "proof_blob_sha": bundle.proof_blob_sha,
        "proof_sha256": bundle.proof_sha256,
        "bindings_path": BINDINGS_PATH,
        "bindings_blob_sha": bundle.bindings_blob_sha,
        "bindings_sha256": bundle.bindings_sha256,
        "runner_blob_sha": bundle.runner_blob_sha,
        "generated_at_utc": generated,
        "proof_generated_at_utc": bundle.proof["generated_at_utc"],
        "source_mode": bundle.snapshot["source_mode"],
        "schema_version": bundle.snapshot["schema_version"],
        "acceptance_status": "ACCEPTED",
    }


LOCKED_CONTENT_KEYS = (
    "snapshot_blob_sha", "snapshot_sha256", "proof_blob_sha", "proof_sha256",
    "bindings_blob_sha", "bindings_sha256", "generated_at_utc",
    "proof_generated_at_utc", "source_mode", "schema_version", "acceptance_status",
)


def _sha(value: Any, label: str, reason: str) -> str:
    text = str(value or "")
    if len(text) != 40 or any(ch not in "0123456789abcdef" for ch in text):
        raise ContractError(reason, label)
    return text


def bundle_from_entry(repo: Path, role: str, locked: dict[str, Any]) -> SnapshotBundle:
    """Load and verify the immutable provenance commit recorded in the registry."""
    commit_sha = _sha(locked.get("commit_sha"), f"{role} commit", "PROVENANCE_COMMIT_MISSING")
    data_origin = _sha(
        locked.get("data_origin_commit_sha"),
        f"{role} data origin",
        "TRANSACTION_ANCESTRY_INVALID",
    )
    resolve_ref(repo, commit_sha, "PROVENANCE_COMMIT_MISSING")
    resolve_ref(repo, data_origin, "TRANSACTION_ANCESTRY_INVALID")
    if not is_ancestor(repo, data_origin, commit_sha):
        raise ContractError("TRANSACTION_ANCESTRY_INVALID", f"{role} data origin")

    snapshot = git_show(repo, commit_sha, SNAPSHOT_PATH, "PROVENANCE_COMMIT_MISSING")
    proof = git_show(repo, commit_sha, PROOF_PATH, "PROVENANCE_COMMIT_MISSING")
    bindings = git_show(repo, commit_sha, BINDINGS_PATH, "PROVENANCE_COMMIT_MISSING")
    runner = git_show(repo, commit_sha, RUNNER_PATH, "PROVENANCE_COMMIT_MISSING")
    bundle = make_bundle(
        role=role,
        commit_sha=commit_sha,
        data_origin_commit_sha=data_origin,
        runner_blob_sha=git_blob_sha(runner),
        snapshot_bytes=snapshot,
        proof_bytes=proof,
        bindings_bytes=bindings,
    )
    observed = entry(bundle)
    for key in (*LOCKED_CONTENT_KEYS, "runner_blob_sha"):
        if locked.get(key) != observed.get(key):
            raise ContractError("PROVENANCE_HASH_MISMATCH", f"{role} {key}")
    return bundle


def materialized_bundle_from_ref(
    repo: Path,
    role: str,
    ref: str,
    locked: dict[str, Any],
    provenance: SnapshotBundle,
) -> SnapshotBundle:
    """Load accepted bytes from a main-line materialization and hash-lock them."""
    materialization = resolve_ref(repo, ref, "BASE_MATERIALIZATION_HASH_MISMATCH")
    bundle = make_bundle(
        role=role,
        commit_sha=provenance.commit_sha,
        data_origin_commit_sha=provenance.data_origin_commit_sha,
        runner_blob_sha=provenance.runner_blob_sha,
        snapshot_bytes=git_show(
            repo, materialization, SNAPSHOT_PATH, "BASE_MATERIALIZATION_HASH_MISMATCH"
        ),
        proof_bytes=git_show(
            repo, materialization, PROOF_PATH, "BASE_MATERIALIZATION_HASH_MISMATCH"
        ),
        bindings_bytes=git_show(
            repo, materialization, BINDINGS_PATH, "BASE_MATERIALIZATION_HASH_MISMATCH"
        ),
    )
    observed = entry(bundle)
    for key in LOCKED_CONTENT_KEYS:
        if locked.get(key) != observed.get(key):
            raise ContractError("BASE_MATERIALIZATION_HASH_MISMATCH", f"{role} {key}")
    return bundle


def bundle_from_ref(
    repo: Path,
    role: str,
    ref: str,
    *,
    data_origin_ref: str | None = None,
) -> SnapshotBundle:
    commit_sha = resolve_ref(repo, ref)
    data_origin = resolve_ref(repo, data_origin_ref or ref, "TRANSACTION_ANCESTRY_INVALID")
    if not is_ancestor(repo, data_origin, commit_sha):
        raise ContractError("TRANSACTION_ANCESTRY_INVALID", f"{role} data origin")
    return make_bundle(
        role=role,
        commit_sha=commit_sha,
        data_origin_commit_sha=data_origin,
        runner_blob_sha=git_blob_sha(
            git_show(repo, commit_sha, RUNNER_PATH, "PROVENANCE_COMMIT_MISSING")
        ),
        snapshot_bytes=git_show(repo, commit_sha, SNAPSHOT_PATH, "CURRENT_MISSING"),
        proof_bytes=git_show(repo, commit_sha, PROOF_PATH, "CURRENT_MISSING"),
        bindings_bytes=git_show(repo, commit_sha, BINDINGS_PATH, "CURRENT_MISSING"),
    )


def load_registry_at_ref(repo: Path, ref: str) -> dict[str, Any]:
    return parse_json(
        git_show(repo, ref, REGISTRY_PATH, "BASE_MATERIALIZATION_HASH_MISMATCH"),
        f"registry at {ref}",
    )


def load_pair(
    repo: Path,
    *,
    base_ref: str | None = None,
    current_ref: str | None = None,
) -> tuple[SnapshotBundle, SnapshotBundle, dict[str, Any]]:
    if bool(base_ref) != bool(current_ref):
        raise ContractError("SCHEMA_MISMATCH", "base-ref and current-ref must be supplied together")

    if base_ref and current_ref:
        base_sha = resolve_ref(repo, base_ref, "TRANSACTION_ANCESTRY_INVALID")
        current_sha = resolve_ref(repo, current_ref)
        if not is_ancestor(repo, base_sha, current_sha):
            raise ContractError("TRANSACTION_ANCESTRY_INVALID", "base is not ancestor of current")
        base_registry = load_registry_at_ref(repo, base_sha)
        locked_previous = base_registry.get("current") or {}
        provenance_previous = bundle_from_entry(repo, "previous", locked_previous)
        previous = materialized_bundle_from_ref(
            repo, "previous", base_sha, locked_previous, provenance_previous
        )
        current = bundle_from_ref(
            repo, "current", current_sha, data_origin_ref=base_sha
        )
        mode = "BUILD_FROM_ACCEPTED_BASE"
    else:
        registry = parse_json((repo / REGISTRY_PATH).read_bytes(), "committed registry")
        locked_current = registry.get("current") or {}
        locked_previous = registry.get("previous") or {}
        current = bundle_from_entry(repo, "current", locked_current)
        previous = bundle_from_entry(repo, "previous", locked_previous)
        materialized_bundle_from_ref(
            repo,
            "previous",
            current.data_origin_commit_sha,
            locked_previous,
            previous,
        )
        mode = "VERIFY_COMMITTED_ACCEPTED_PAIR"

    evidence = {
        "mode": mode,
        "provenance_hashes": "PASS",
        "base_materialization_hashes": "PASS",
        "transaction_base_ancestry": "PASS",
    }
    return current, previous, evidence


def unavailable(
    path: str,
    reason: str,
    previous_method: str,
    current_method: str,
    *,
    dependency: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "UNAVAILABLE",
        "path": path,
        "reason_code": reason,
        "previous_methodology_id": previous_method,
        "current_methodology_id": current_method,
        "delta_value": None,
    }
    if dependency:
        result["dependency"] = dependency
    return result


def numeric_metric(
    metric_id: str,
    path: str,
    unit: str,
    delta_unit: str,
    precision: int,
    method: str,
    sources: list[str],
    current: SnapshotBundle,
    previous: SnapshotBundle,
) -> dict[str, Any]:
    current_value = number(at(current, path), metric_id)
    previous_value = number(at(previous, path), metric_id)
    delta = current_value - previous_value
    return {
        "status": "COMPARABLE",
        "type": "NUMERIC",
        "path": path,
        "unit": unit,
        "delta_unit": delta_unit,
        "methodology_id": method,
        "proof_sources": sources,
        "previous_value": format(previous_value, "f"),
        "current_value": format(current_value, "f"),
        "raw_delta": format(delta, "f"),
        "display_precision": precision,
        "display_delta": display_delta(delta, precision),
        "direction": direction(delta),
    }


def categorical_metric(
    path: str,
    unit: str,
    method: str,
    sources: list[str],
    current: SnapshotBundle,
    previous: SnapshotBundle,
) -> dict[str, Any]:
    current_value = at(current, path)
    previous_value = at(previous, path)
    if not isinstance(current_value, str) or not isinstance(previous_value, str):
        raise ContractError("SCHEMA_MISMATCH", path)
    return {
        "status": "COMPARABLE",
        "type": "CATEGORICAL",
        "path": path,
        "unit": unit,
        "methodology_id": method,
        "proof_sources": sources,
        "previous_value": previous_value,
        "current_value": current_value,
        "transition": "UNCHANGED" if current_value == previous_value else "CHANGED",
    }


def defi_method(bundle: SnapshotBundle) -> str:
    liquidity = bundle.snapshot.get("liquidity_tvl") or {}
    direct = liquidity.get("defi_tvl_methodology_id")
    if isinstance(direct, str) and direct:
        return direct
    for item in source_map(bundle).values():
        url = item.get("url")
        for method, expected in DEFI_METHOD_URLS.items():
            if url == expected:
                return method
    return "unknown_defi_tvl_methodology"


def liquidity_method(defi_methodology: str) -> str:
    mapping = {
        "defillama_historical_chain_tvl_ex_double_count_v0_1":
            "liquidity_context_state_with_global_ex_double_count_tvl_v0_1",
        "defillama_protocols_sum_v0_1":
            "liquidity_context_state_with_protocol_sum_tvl_v0_1",
    }
    return mapping.get(defi_methodology, f"liquidity_context_state_with_{defi_methodology}")


def validate_defi_source(bundle: SnapshotBundle, methodology: str) -> None:
    expected = DEFI_METHOD_URLS.get(methodology)
    if not expected:
        raise ContractError("METHODOLOGY_MISMATCH", methodology)
    candidates = [item for item in source_map(bundle).values() if item.get("url") == expected]
    if len(candidates) != 1 or candidates[0].get("status") != "PASS":
        raise ContractError("PROOF_NOT_PASS", f"{bundle.role} defi tvl")


def build_documents(
    current: SnapshotBundle,
    previous: SnapshotBundle,
) -> tuple[dict[str, Any], dict[str, Any]]:
    for bundle in (current, previous):
        validate_shape(bundle)
    if timestamp(current.snapshot["generated_at_utc"], "current") <= timestamp(
        previous.snapshot["generated_at_utc"], "previous"
    ):
        raise ContractError("TIMESTAMP_ORDER_INVALID", "current must be later")

    metrics: dict[str, Any] = {}
    unavailable_metrics: dict[str, Any] = {}
    methods: dict[str, Any] = {}

    for metric_id, spec in STATIC_METRICS.items():
        method = spec["methodology_id"]
        reason = None
        try:
            for bundle in (current, previous):
                validate_sources(bundle, spec["sources"])
                validate_binding(bundle, spec["binding"])
            universe = spec.get("universe")
            if universe and at(current, universe) != at(previous, universe):
                raise ContractError("UNIVERSE_MISMATCH", metric_id)
            if spec["kind"] == "numeric":
                metrics[metric_id] = numeric_metric(
                    metric_id,
                    spec["path"],
                    spec["unit"],
                    spec["delta_unit"],
                    spec["precision"],
                    method,
                    spec["sources"],
                    current,
                    previous,
                )
            else:
                metrics[metric_id] = categorical_metric(
                    spec["path"],
                    spec["unit"],
                    method,
                    spec["sources"],
                    current,
                    previous,
                )
        except ContractError as exc:
            reason = exc.reason_code
            unavailable_metrics[metric_id] = unavailable(
                spec["path"], reason, method, method
            )
        methods[metric_id] = {
            "current_methodology_id": method,
            "previous_methodology_id": method,
            "comparable": reason is None,
            "current_runner_blob_sha": current.runner_blob_sha,
            "previous_runner_blob_sha": previous.runner_blob_sha,
        }

    current_defi = defi_method(current)
    previous_defi = defi_method(previous)
    defi_reason = None
    try:
        if (
            current_defi != previous_defi
            or "unknown" in current_defi
            or "unknown" in previous_defi
        ):
            raise ContractError("METHODOLOGY_MISMATCH", "defi_tvl_usd")
        validate_defi_source(current, current_defi)
        validate_defi_source(previous, previous_defi)
        metrics["defi_tvl_usd"] = numeric_metric(
            "defi_tvl_usd",
            "liquidity_tvl.defi_tvl_usd",
            "usd",
            "usd",
            0,
            current_defi,
            ["defillama_tvl_methodology_source"],
            current,
            previous,
        )
    except ContractError as exc:
        defi_reason = exc.reason_code
        unavailable_metrics["defi_tvl_usd"] = unavailable(
            "liquidity_tvl.defi_tvl_usd",
            defi_reason,
            previous_defi,
            current_defi,
        )
    methods["defi_tvl_usd"] = {
        "current_methodology_id": current_defi,
        "previous_methodology_id": previous_defi,
        "comparable": defi_reason is None,
        "current_runner_blob_sha": current.runner_blob_sha,
        "previous_runner_blob_sha": previous.runner_blob_sha,
    }

    current_liquidity = liquidity_method(current_defi)
    previous_liquidity = liquidity_method(previous_defi)
    liquidity_reason = None
    try:
        if defi_reason is not None:
            code = (
                "DEPENDENCY_METHODOLOGY_MISMATCH"
                if defi_reason == "METHODOLOGY_MISMATCH"
                else "DEPENDENCY_UNAVAILABLE"
            )
            raise ContractError(code, "liquidity_context_state")
        if current_liquidity != previous_liquidity:
            raise ContractError("METHODOLOGY_MISMATCH", "liquidity_context_state")
        metrics["liquidity_context_state"] = categorical_metric(
            "liquidity_tvl.liquidity_context_state",
            "state",
            current_liquidity,
            ["defi_tvl_usd"],
            current,
            previous,
        )
    except ContractError as exc:
        liquidity_reason = exc.reason_code
        unavailable_metrics["liquidity_context_state"] = unavailable(
            "liquidity_tvl.liquidity_context_state",
            liquidity_reason,
            previous_liquidity,
            current_liquidity,
            dependency="defi_tvl_usd",
        )
    methods["liquidity_context_state"] = {
        "current_methodology_id": current_liquidity,
        "previous_methodology_id": previous_liquidity,
        "comparable": liquidity_reason is None,
        "current_runner_blob_sha": current.runner_blob_sha,
        "previous_runner_blob_sha": previous.runner_blob_sha,
    }

    if (
        set(metrics) | set(unavailable_metrics) != set(TRACKED_METRICS)
        or set(metrics) & set(unavailable_metrics)
    ):
        raise ContractError("SCHEMA_MISMATCH", "metric partition")

    status = (
        "FULL_COMPARABLE"
        if len(metrics) == len(TRACKED_METRICS)
        else "PARTIAL_COMPARABLE"
        if metrics
        else "UNAVAILABLE"
    )
    current_entry = entry(current)
    previous_entry = entry(previous)
    registry = {
        "schema_version": "crypto_astro_snapshot_registry_public_v0_2",
        "registry_generated_at_utc": current.snapshot["generated_at_utc"],
        "selection_policy": "EXPLICIT_ACCEPTED_PAIR",
        "current": current_entry,
        "previous": previous_entry,
        "metric_methodologies": methods,
        "boundary": deepcopy(BOUNDARY),
    }
    delta = {
        "schema_version": "crypto_astro_snapshot_delta_public_v0_2",
        "generated_at_utc": current.snapshot["generated_at_utc"],
        "current_snapshot_id": current_entry["snapshot_id"],
        "previous_snapshot_id": previous_entry["snapshot_id"],
        "comparison_status": status,
        "metrics": metrics,
        "unavailable_metrics": unavailable_metrics,
        "boundary": deepcopy(BOUNDARY),
    }
    return registry, delta


def json_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def write_documents(out_dir: Path, registry: dict[str, Any], delta: dict[str, Any]) -> None:
    for relative, document in ((REGISTRY_PATH, registry), (DELTA_PATH, delta)):
        path = out_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(document))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--base-ref")
    parser.add_argument("--current-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    current, previous, evidence = load_pair(
        repo, base_ref=args.base_ref, current_ref=args.current_ref
    )
    registry, delta = build_documents(current, previous)
    write_documents(args.out_dir.resolve(), registry, delta)
    print(json.dumps({
        "status": "PASS",
        "registry_path": REGISTRY_PATH,
        "delta_path": DELTA_PATH,
        "current_snapshot_id": registry["current"]["snapshot_id"],
        "previous_snapshot_id": registry["previous"]["snapshot_id"],
        "comparison_status": delta["comparison_status"],
        "comparable_metrics": sorted(delta["metrics"]),
        "unavailable_metrics": sorted(delta["unavailable_metrics"]),
        "provenance_hashes": evidence["provenance_hashes"],
        "base_materialization_hashes": evidence["base_materialization_hashes"],
        "transaction_base_ancestry": evidence["transaction_base_ancestry"],
        "network_requests": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
