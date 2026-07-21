#!/usr/bin/env python3
"""Deterministic producer-side proof for the BHRIGU BTC Field Read contract."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
COMPAT_PATH = HERE / "crypto_astro_static_refresh_bhrigu_compat_v0_1.py"


def load_compat():
    spec = importlib.util.spec_from_file_location("crypto_astro_static_refresh_bhrigu_compat_v0_1", COMPAT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load BHRIGU compatibility layer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    compat = load_compat()
    errors = compat.validate_bhrigu_consumer_bundle(REPO)
    if errors:
        raise RuntimeError(f"current producer bundle failed BHRIGU contract: {errors}")

    snapshot = compat.core.load_json(REPO / "site/crypto-astro/data/crypto_astro_snapshot.public.json")
    with tempfile.TemporaryDirectory(prefix="crypto-astro-bhrigu-contract-") as tmp:
        temp_repo = Path(tmp)
        generated = compat.update_market_field(temp_repo, snapshot)
        if generated.get("schema_version") != compat.BHRIGU_MARKET_FIELD_SCHEMA:
            raise RuntimeError("regenerated Market Field did not preserve v0.2")
        generated_errors = compat.validate_bhrigu_market_field(generated)
        if generated_errors:
            raise RuntimeError(f"regenerated Market Field failed contract: {generated_errors}")

        regressed = dict(generated)
        regressed["schema_version"] = "crypto_astro_market_field_public_v0_1"
        if not compat.validate_bhrigu_market_field(regressed):
            raise RuntimeError("v0.1 regression was not rejected")

    print("CRYPTO_ASTRO_BHRIGU_CONSUMER_CONTRACT=PASS")
    print(f"MARKET_FIELD_SCHEMA={compat.BHRIGU_MARKET_FIELD_SCHEMA}")
    print("V0_1_REGRESSION_REJECTED=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
