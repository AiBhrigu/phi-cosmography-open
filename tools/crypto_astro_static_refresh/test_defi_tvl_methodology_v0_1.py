#!/usr/bin/env python3
"""Deterministic contract test for the non-double-counted DeFi TVL lane."""

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


primary = load_module(
    "crypto_astro_primary",
    ROOT / "crypto_astro_all_module_static_refresh_source_v0_1.py",
)
wrapper = load_module(
    "crypto_astro_wrapper",
    ROOT / "crypto_astro_static_refresh_hardened_v0_5.py",
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_fixture(repo):
    tvl = 75_551_199_898.0
    liquidity = {
        "defi_tvl_usd": tvl,
        "defi_tvl_source_label": wrapper.DEFI_TVL_SOURCE_LABEL,
        "defi_tvl_source_url": wrapper.DEFI_TVL_SOURCE_URL,
        "defi_tvl_source_timestamp_utc": "2026-07-19T00:00:00Z",
        "defi_tvl_methodology_id": wrapper.DEFI_TVL_METHODOLOGY_ID,
        "defi_tvl_methodology": wrapper.DEFI_TVL_METHODOLOGY,
        "defi_tvl_excludes_liquid_staking": True,
        "defi_tvl_excludes_double_counted": True,
    }
    write_json(
        repo / "site/crypto-astro/data/crypto_astro_snapshot.public.json",
        {"liquidity_tvl": liquidity},
    )
    write_json(
        repo / "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json",
        {
            "sources": [
                {
                    "label": wrapper.DEFI_TVL_SOURCE_LABEL,
                    "url": wrapper.DEFI_TVL_SOURCE_URL,
                    "status": "PASS",
                    "sha256": "a" * 64,
                    "fetched_at_utc": "2026-07-19T00:00:00Z",
                    "bytes": 100,
                },
                {
                    "label": wrapper.DEFI_TVL_COMPATIBILITY_LABEL,
                    "url": wrapper.DEFI_TVL_SOURCE_URL,
                    "status": "PASS",
                    "sha256": "a" * 64,
                    "fetched_at_utc": "2026-07-19T00:00:00Z",
                    "bytes": 100,
                    "compatibility_alias_of": wrapper.DEFI_TVL_SOURCE_LABEL,
                    "methodology_id": wrapper.DEFI_TVL_METHODOLOGY_ID,
                }
            ]
        },
    )
    write_json(
        repo / "site/crypto-astro/data/crypto_astro_module_bindings.public.json",
        {
            "modules": {
                "liquidity_tvl": {
                    "methodology_id": wrapper.DEFI_TVL_METHODOLOGY_ID,
                    "proof_source": wrapper.DEFI_TVL_SOURCE_LABEL,
                }
            }
        },
    )
    write_json(
        repo / "site/crypto-astro/data/market_field_snapshot.public.v0_1.json",
        {
            "vectors": {
                "M_market": {
                    "defi_tvl_usd": tvl,
                    "defi_tvl_methodology_id": wrapper.DEFI_TVL_METHODOLOGY_ID,
                    "defi_tvl_excludes_double_counted": True,
                }
            }
        },
    )
    index = repo / "site/crypto-astro/index.html"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(wrapper.DEFI_TVL_PUBLIC_COPY, encoding="utf-8")


def main():
    assert primary.DEFI_TVL_SOURCE_URL == "https://api.llama.fi/v2/historicalChainTvl"
    assert primary.DEFI_TVL_SOURCE_LABEL == wrapper.DEFI_TVL_SOURCE_LABEL
    assert primary.DEFI_TVL_COMPATIBILITY_LABEL == wrapper.DEFI_TVL_COMPATIBILITY_LABEL
    assert primary.DEFI_TVL_METHODOLOGY_ID == wrapper.DEFI_TVL_METHODOLOGY_ID

    value, timestamp = primary.latest_non_double_counted_tvl(
        [
            {"date": 200, "tvl": 20},
            {"date": 100, "tvl": 10},
            {"date": "bad", "tvl": 999},
        ]
    )
    assert value == 20.0
    assert timestamp == "1970-01-01T00:03:20Z"

    try:
        primary.latest_non_double_counted_tvl([{"date": 1, "tvl": 0}])
    except ValueError:
        pass
    else:
        raise AssertionError("non-positive TVL must fail closed")

    primary_source = (
        ROOT / "crypto_astro_all_module_static_refresh_source_v0_1.py"
    ).read_text(encoding="utf-8")
    assert 'safe_fetch("defillama_protocols"' not in primary_source
    assert "safe_fetch(DEFI_TVL_COMPATIBILITY_LABEL" not in primary_source
    assert "fetch_json(LEGACY_DEFI_TVL_SOURCE_URL" not in primary_source

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        build_fixture(repo)
        report = {}
        assert wrapper.validate_defi_tvl_methodology(repo, report)
        assert report["validation"]["defi_tvl_methodology"] == "PASS"

        proof_path = repo / "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json"
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        compatibility = next(
            source for source in proof["sources"]
            if source["label"] == wrapper.DEFI_TVL_COMPATIBILITY_LABEL
        )
        compatibility["url"] = wrapper.LEGACY_DEFI_TVL_SOURCE_URL
        write_json(proof_path, proof)
        report = {}
        assert not wrapper.validate_defi_tvl_methodology(repo, report)
        assert "proof:legacy_protocol_sum_url_present" in report["validation"][
            "defi_tvl_methodology_errors"
        ]

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        for rel in wrapper.AFFECTED_FILES:
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}" if path.suffix == ".json" else "", encoding="utf-8")

        html = repo / "site/crypto-astro/index.html"
        html.write_text(
            "No live adapter is active. This is not a live adapter.", encoding="utf-8"
        )
        report = {}
        assert wrapper.validate_active_outputs(repo, report)

        html.write_text("The live adapter is active.", encoding="utf-8")
        report = {}
        assert not wrapper.validate_active_outputs(repo, report)
        assert report["validation"]["forbidden_positive_claim_hits"]

    print("DEFI_TVL_METHODOLOGY_TEST=PASS")


if __name__ == "__main__":
    main()
