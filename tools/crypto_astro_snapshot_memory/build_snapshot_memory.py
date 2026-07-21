#!/usr/bin/env python3
"""Offline, fail-closed Crypto-Astro snapshot-memory builder."""
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

CURRENT_MATERIALIZATION_COMMIT = "8f12ee8e4c8748c362568ada4d79ba16b61adde1"
CURRENT_DATA_ORIGIN_COMMIT = "3520e542f6c554888aeb5e95dde2728dc692d239"
PREVIOUS_COMMIT = "006901742f5656a5b7370f2b1b6e5aa566b865f5"

SNAPSHOT_PATH = "site/crypto-astro/data/crypto_astro_snapshot.public.json"
PROOF_PATH = "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json"
BINDINGS_PATH = "site/crypto-astro/data/crypto_astro_module_bindings.public.json"
REGISTRY_PATH = "site/crypto-astro/data/crypto_astro_snapshot_registry.public.json"
DELTA_PATH = "site/crypto-astro/data/crypto_astro_snapshot_delta.public.json"

EXPECTED_LOCKS = {
    "current": {
        "commit_sha": CURRENT_MATERIALIZATION_COMMIT,
        "data_origin_commit_sha": CURRENT_DATA_ORIGIN_COMMIT,
        "snapshot_blob_sha": "33ded2a6555bdd77549f697d71a0acbfeea3f672",
        "snapshot_sha256": "8fb7e78233ab6ea8fe6b0224cd521fe92e2788c03c44723cd6e1c22e25715b57",
        "proof_blob_sha": "dde4176b6ac7510c0adbd7f785bc3d82aa1607ab",
        "proof_sha256": "4034e9ab3693360652ab6b352b1a0e0547608dd6238f4269c9c3ee78273c653c",
        "bindings_blob_sha": "5b3ddff59fa797e3bb61a2043d344248c2e7e23a",
        "bindings_sha256": "d2f7d6fd7c15e0cf7ff252a7a3634c207e025a326efd45fcc8ab6463e86c89ce",
        "runner_blob_sha": "2754dc348605a2655e26dbc0494d63510ca88843",
    },
    "previous": {
        "commit_sha": PREVIOUS_COMMIT,
        "data_origin_commit_sha": PREVIOUS_COMMIT,
        "snapshot_blob_sha": "318c3d07b077961215d479db4ce5e0a032a1c86a",
        "snapshot_sha256": "f423cf480b1570b8377919421e74bdd47a647cc4773afbaee2845d62bcc54ad8",
        "proof_blob_sha": "d44044b06bf8bf347a39f0058768747e3fa63047",
        "proof_sha256": "203f3e9767311b0a5340f521c84f4f2c61894e69134925422dcf80dbd8c7525c",
        "bindings_blob_sha": "51201acf0738500f0c914ce9b3ed3450ffaf93ad",
        "bindings_sha256": "e4662b9bbaf64c7df43d4489f67f8800afbbfcf8cdb47c8d5239a391c64cd9e1",
        "runner_blob_sha": "086a77f2dd209a061e6b557de0e86a9b7b4f98d9",
    },
}

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
    "ui_binding_opened": False,
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

METRICS = {
    "btc_gravity_pct": ("market_reality.btc_dominance_pct", "numeric", "percent",
                        "percentage_points", 2, "coingecko_global_btc_dominance_direct_v0_1",
                        ["coingecko_global"], "market_reality", None),
    "stablecoin_share_pct": ("market_reality.stablecoin_share_pct", "numeric", "percent",
                             "percentage_points", 2,
                             "stablecoin_share_prefer_llama_then_coingecko_over_total_cap_v0_1",
                             ["defillama_stablecoins", "coingecko_global"], "market_reality", None),
    "alt_breadth_24h_pct": ("altcoin_rotation.alt_breadth_24h_pct", "numeric", "percent",
                            "percentage_points", 1,
                            "top250_nonstable_ex_btc_positive_breadth_24h_v0_1",
                            ["coingecko_top250_markets"], "altcoin_rotation",
                            "altcoin_rotation.universe"),
    "alt_breadth_7d_pct": ("altcoin_rotation.alt_breadth_7d_pct", "numeric", "percent",
                           "percentage_points", 1,
                           "top250_nonstable_ex_btc_positive_breadth_7d_v0_1",
                           ["coingecko_top250_markets"], "altcoin_rotation",
                           "altcoin_rotation.universe"),
    "market_field_score": ("field_output.market_field_score", "numeric", "score_0_100",
                           "score_points", 1, "public_market_field_score_v0_1",
                           ["coingecko_global", "coingecko_top250_markets",
                            "defillama_stablecoins"], "aem_barometer", None),
    "regime_label": ("field_output.regime_label", "categorical", "state", None, None,
                     "public_regime_threshold_58_v0_1",
                     ["coingecko_global", "coingecko_top250_markets",
                      "defillama_stablecoins"], "aem_barometer", None),
}

UNAVAILABLE = {
    "defi_tvl_usd": {
        "path": "liquidity_tvl.defi_tvl_usd",
        "reason_code": "METHODOLOGY_MISMATCH",
        "previous_methodology_id": "defillama_protocols_sum_v0_1",
        "current_methodology_id": "defillama_historical_chain_tvl_ex_double_count_v0_1",
    },
    "liquidity_context_state": {
        "path": "liquidity_tvl.liquidity_context_state",
        "reason_code": "DEPENDENCY_METHODOLOGY_MISMATCH",
        "dependency": "defi_tvl_usd",
        "previous_methodology_id": "liquidity_context_state_with_protocol_sum_tvl_v0_1",
        "current_methodology_id": "liquidity_context_state_with_global_ex_double_count_tvl_v0_1",
    },
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
    def snapshot_sha256(self): return hashlib.sha256(self.snapshot_bytes).hexdigest()
    @property
    def proof_sha256(self): return hashlib.sha256(self.proof_bytes).hexdigest()
    @property
    def bindings_sha256(self): return hashlib.sha256(self.bindings_bytes).hexdigest()
    @property
    def snapshot_blob_sha(self): return git_blob_sha(self.snapshot_bytes)
    @property
    def proof_blob_sha(self): return git_blob_sha(self.proof_bytes)
    @property
    def bindings_blob_sha(self): return git_blob_sha(self.bindings_bytes)


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


def make_bundle(**kwargs) -> SnapshotBundle:
    return SnapshotBundle(
        **kwargs,
        snapshot=parse_json(kwargs["snapshot_bytes"], f'{kwargs["role"]} snapshot'),
        proof=parse_json(kwargs["proof_bytes"], f'{kwargs["role"]} proof'),
        bindings=parse_json(kwargs["bindings_bytes"], f'{kwargs["role"]} bindings'),
    )


def at(document: dict[str, Any], path: str):
    value: Any = document
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            raise ContractError("CURRENT_MISSING", path)
        value = value[key]
    return value


def timestamp(value: Any, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("TIMESTAMP_ORDER_INVALID", label) from exc
    if parsed.tzinfo is None:
        raise ContractError("TIMESTAMP_ORDER_INVALID", label)
    return parsed.astimezone(timezone.utc)


def source_map(bundle: SnapshotBundle):
    items = bundle.proof.get("sources")
    if not isinstance(items, list):
        raise ContractError("SCHEMA_MISMATCH", f"{bundle.role} proof.sources")
    return {item["label"]: item for item in items
            if isinstance(item, dict) and isinstance(item.get("label"), str)}


def validate_boundary(bundle: SnapshotBundle):
    true_keys = [k for k, v in BOUNDARY.items() if v is True
                 and k not in {"crawler_input_forbidden", "html_presentation_input_forbidden"}]
    for name, document in (("snapshot", bundle.snapshot), ("proof", bundle.proof),
                           ("bindings", bundle.bindings)):
        boundary = document.get("boundary")
        if not isinstance(boundary, dict):
            raise ContractError("BOUNDARY_MISMATCH", f"{bundle.role} {name}")
        if any(boundary.get(key) is not True for key in true_keys):
            raise ContractError("BOUNDARY_MISMATCH", f"{bundle.role} {name}")
        if boundary.get("formula_weights_exposed") is not False:
            raise ContractError("BOUNDARY_MISMATCH", f"{bundle.role} {name}")


def validate_shape(bundle: SnapshotBundle):
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
    if bundle.bindings.get("generated_at_utc") != bundle.snapshot.get("generated_at_utc"):
        raise ContractError("SOURCE_BINDING_MISSING", f"{bundle.role} timestamp")
    skew = abs((timestamp(bundle.snapshot["generated_at_utc"], "snapshot") -
                timestamp(bundle.proof["generated_at_utc"], "proof")).total_seconds())
    if skew > 120:
        raise ContractError("TIMESTAMP_ORDER_INVALID", f"{bundle.role} skew")
    validate_boundary(bundle)


def validate_locks(bundle: SnapshotBundle):
    observed = {
        "commit_sha": bundle.commit_sha,
        "data_origin_commit_sha": bundle.data_origin_commit_sha,
        "runner_blob_sha": bundle.runner_blob_sha,
        "snapshot_blob_sha": bundle.snapshot_blob_sha,
        "snapshot_sha256": bundle.snapshot_sha256,
        "proof_blob_sha": bundle.proof_blob_sha,
        "proof_sha256": bundle.proof_sha256,
        "bindings_blob_sha": bundle.bindings_blob_sha,
        "bindings_sha256": bundle.bindings_sha256,
    }
    for key, expected in EXPECTED_LOCKS[bundle.role].items():
        if observed[key] != expected:
            raise ContractError("HASH_MISMATCH", f"{bundle.role} {key}")


def validate_sources(bundle: SnapshotBundle, labels: list[str]):
    sources = source_map(bundle)
    for label in labels:
        item = sources.get(label)
        if not item or item.get("status") != "PASS":
            raise ContractError("PROOF_NOT_PASS", f"{bundle.role} {label}")
        if URLS.get(label) and item.get("url") != URLS[label]:
            raise ContractError("SOURCE_URL_MISMATCH", f"{bundle.role} {label}")


def validate_binding(bundle: SnapshotBundle, module: str):
    required = {"market_reality": "market_reality", "altcoin_rotation": "altcoin_rotation",
                "aem_barometer": "field_output"}[module]
    modules = bundle.bindings.get("modules")
    if not isinstance(modules, dict) or not isinstance(modules.get(module), dict):
        raise ContractError("SOURCE_BINDING_MISSING", f"{bundle.role} {module}")
    if modules[module].get("source") != required:
        raise ContractError("SOURCE_BINDING_MISSING", f"{bundle.role} {module}.source")


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


def entry(bundle: SnapshotBundle):
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


def build_documents(current: SnapshotBundle, previous: SnapshotBundle, *,
                    ancestry_ok: bool, strict_locks: bool = True):
    for bundle in (current, previous):
        validate_shape(bundle)
        if strict_locks:
            validate_locks(bundle)
    if not ancestry_ok:
        raise ContractError("ANCESTRY_INVALID", "previous is not ancestor")
    if timestamp(current.snapshot["generated_at_utc"], "current") <= \
       timestamp(previous.snapshot["generated_at_utc"], "previous"):
        raise ContractError("TIMESTAMP_ORDER_INVALID", "current must be later")

    methods, metrics = {}, {}
    for metric_id, spec in METRICS.items():
        path, kind, unit, delta_unit, precision, method, sources, binding, universe = spec
        methods[metric_id] = {
            "current_methodology_id": method,
            "previous_methodology_id": method,
            "comparable": True,
            "current_runner_blob_sha": current.runner_blob_sha,
            "previous_runner_blob_sha": previous.runner_blob_sha,
        }
        for bundle in (current, previous):
            validate_sources(bundle, sources)
            validate_binding(bundle, binding)
        if universe and at(current.snapshot, universe) != at(previous.snapshot, universe):
            raise ContractError("UNIVERSE_MISMATCH", metric_id)
        current_value, previous_value = at(current.snapshot, path), at(previous.snapshot, path)
        if kind == "numeric":
            c, p = number(current_value, metric_id), number(previous_value, metric_id)
            delta = c - p
            metrics[metric_id] = {
                "status": "COMPARABLE", "type": "NUMERIC", "path": path,
                "unit": unit, "delta_unit": delta_unit, "methodology_id": method,
                "proof_sources": sources, "previous_value": format(p, "f"),
                "current_value": format(c, "f"), "raw_delta": format(delta, "f"),
                "display_precision": precision, "display_delta": display_delta(delta, precision),
                "direction": direction(delta),
            }
        else:
            metrics[metric_id] = {
                "status": "COMPARABLE", "type": "CATEGORICAL", "path": path,
                "unit": unit, "methodology_id": method, "proof_sources": sources,
                "previous_value": previous_value, "current_value": current_value,
                "transition": "UNCHANGED" if current_value == previous_value else "CHANGED",
            }

    unavailable = {}
    for metric_id, spec in UNAVAILABLE.items():
        methods[metric_id] = {
            "current_methodology_id": spec["current_methodology_id"],
            "previous_methodology_id": spec["previous_methodology_id"],
            "comparable": False,
            "current_runner_blob_sha": current.runner_blob_sha,
            "previous_runner_blob_sha": previous.runner_blob_sha,
        }
        unavailable[metric_id] = {
            "status": "UNAVAILABLE", "path": spec["path"],
            "reason_code": spec["reason_code"],
            "previous_methodology_id": spec["previous_methodology_id"],
            "current_methodology_id": spec["current_methodology_id"],
            "delta_value": None,
        }
        if spec.get("dependency"):
            unavailable[metric_id]["dependency"] = spec["dependency"]

    current_entry, previous_entry = entry(current), entry(previous)
    registry = {
        "schema_version": "crypto_astro_snapshot_registry_public_v0_1",
        "registry_generated_at_utc": current.snapshot["generated_at_utc"],
        "selection_policy": "EXPLICIT_ACCEPTED_PAIR",
        "current": current_entry, "previous": previous_entry,
        "metric_methodologies": methods, "boundary": deepcopy(BOUNDARY),
    }
    delta = {
        "schema_version": "crypto_astro_snapshot_delta_public_v0_1",
        "generated_at_utc": current.snapshot["generated_at_utc"],
        "current_snapshot_id": current_entry["snapshot_id"],
        "previous_snapshot_id": previous_entry["snapshot_id"],
        "comparison_status": "PARTIAL_COMPARABLE",
        "metrics": metrics, "unavailable_metrics": unavailable,
        "boundary": deepcopy(BOUNDARY),
    }
    return registry, delta


def json_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def git_show(repo: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=repo,
                            capture_output=True, check=False)
    if result.returncode:
        raise ContractError("PREVIOUS_MISSING", f"{commit}:{path}")
    return result.stdout


def load_from_repo(repo: Path):
    current = make_bundle(
        role="current", commit_sha=CURRENT_MATERIALIZATION_COMMIT,
        data_origin_commit_sha=CURRENT_DATA_ORIGIN_COMMIT,
        runner_blob_sha=EXPECTED_LOCKS["current"]["runner_blob_sha"],
        snapshot_bytes=(repo / SNAPSHOT_PATH).read_bytes(),
        proof_bytes=(repo / PROOF_PATH).read_bytes(),
        bindings_bytes=(repo / BINDINGS_PATH).read_bytes(),
    )
    previous = make_bundle(
        role="previous", commit_sha=PREVIOUS_COMMIT,
        data_origin_commit_sha=PREVIOUS_COMMIT,
        runner_blob_sha=EXPECTED_LOCKS["previous"]["runner_blob_sha"],
        snapshot_bytes=git_show(repo, PREVIOUS_COMMIT, SNAPSHOT_PATH),
        proof_bytes=git_show(repo, PREVIOUS_COMMIT, PROOF_PATH),
        bindings_bytes=git_show(repo, PREVIOUS_COMMIT, BINDINGS_PATH),
    )
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREVIOUS_COMMIT,
         CURRENT_MATERIALIZATION_COMMIT], cwd=repo, check=False
    ).returncode == 0
    return current, previous, ancestry


def write_documents(out_dir: Path, registry: dict[str, Any], delta: dict[str, Any]):
    for relative, document in ((REGISTRY_PATH, registry), (DELTA_PATH, delta)):
        path = out_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(document))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    current, previous, ancestry = load_from_repo(args.repo.resolve())
    registry, delta = build_documents(current, previous, ancestry_ok=ancestry)
    write_documents(args.out_dir.resolve(), registry, delta)
    print(json.dumps({
        "status": "PASS",
        "registry_path": REGISTRY_PATH,
        "delta_path": DELTA_PATH,
        "current_snapshot_id": registry["current"]["snapshot_id"],
        "previous_snapshot_id": registry["previous"]["snapshot_id"],
        "comparable_metrics": sorted(delta["metrics"]),
        "unavailable_metrics": sorted(delta["unavailable_metrics"]),
        "network_requests": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
