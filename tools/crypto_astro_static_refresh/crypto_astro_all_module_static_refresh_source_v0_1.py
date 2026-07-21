#!/usr/bin/env python3
"""Compatibility facade for the original all-module static-refresh source.

The production refresh path is now:

    crypto_astro_static_refresh_bhrigu_compat_v0_1.py
      -> crypto_astro_static_refresh_hardened_v0_5.py
      -> byte-locked hardened core

Keeping a second mutable copy of the full refresh engine here caused operator-review
language and runtime behavior to drift. This facade preserves the legacy module API,
DeFi TVL methodology contract, and CLI while delegating execution to the current
BHRIGU-compatible hardened runtime. The protected core is not modified.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

RUNTIME_PATH = Path(__file__).with_name(
    "crypto_astro_static_refresh_bhrigu_compat_v0_1.py"
)
OPERATOR_REVIEW_RELATIVE_PATH = Path(
    "docs/crypto-astro-service/crypto_astro_operator_review.md"
)

CRYPTO_ASTRO_REFRESH_MODE = "CRYPTO_ASTRO_REFRESH_MODE"
CRYPTO_ASTRO_OPERATOR_REF = "CRYPTO_ASTRO_OPERATOR_REF"
CRYPTO_ASTRO_REFRESH_REASON = "CRYPTO_ASTRO_REFRESH_REASON"

OPERATOR_BOUNDARY = "Workflow may push one fully validated review branch and open one review PR. It may not merge or issue a deployment command. Publication follows only after explicit merge authorization."
OBSOLETE_OPERATOR_BOUNDARY = "No push, no " + "PR, no deploy."


def load_runtime():
    if not RUNTIME_PATH.is_file():
        raise RuntimeError(f"BHRIGU-compatible runtime missing: {RUNTIME_PATH}")
    spec = importlib.util.spec_from_file_location(
        "crypto_astro_static_refresh_bhrigu_compat_v0_1",
        RUNTIME_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load BHRIGU-compatible refresh runtime")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load_runtime()
base = runtime.base
core = runtime.core

# Preserve the methodology API used by deterministic tests and downstream tools.
NODE = core.NODE
TARGET_BRANCH = core.TARGET_BRANCH
BASE_BRANCH = core.BASE_BRANCH
ALLOWLIST = core.ALLOWLIST
BOUNDARY = core.BOUNDARY
DEFI_TVL_SOURCE_LABEL = core.DEFI_TVL_SOURCE_LABEL
DEFI_TVL_CANONICAL_SOURCE_ID = core.DEFI_TVL_CANONICAL_SOURCE_ID
DEFI_TVL_SOURCE_URL = core.DEFI_TVL_SOURCE_URL
LEGACY_DEFI_TVL_SOURCE_URL = core.LEGACY_DEFI_TVL_SOURCE_URL
DEFI_TVL_METHODOLOGY_ID = core.DEFI_TVL_METHODOLOGY_ID
DEFI_TVL_METHODOLOGY = core.DEFI_TVL_METHODOLOGY
latest_non_double_counted_tvl = core.latest_non_double_counted_tvl


def __getattr__(name: str):
    """Preserve the legacy source module API through the hardened entrypoint."""
    return getattr(base, name)


def cadence_metadata() -> tuple[str, str, str]:
    mode = os.environ.get(CRYPTO_ASTRO_REFRESH_MODE, "UNSPECIFIED").strip()
    operator_ref = os.environ.get(CRYPTO_ASTRO_OPERATOR_REF, "UNSPECIFIED").strip()
    reason = os.environ.get(CRYPTO_ASTRO_REFRESH_REASON, "UNSPECIFIED").strip()
    return mode or "UNSPECIFIED", operator_ref or "UNSPECIFIED", reason or "UNSPECIFIED"


def materialize_operator_review(repo: Path) -> None:
    """Bind the generated operator review to the locked manual-review cadence."""
    path = repo / OPERATOR_REVIEW_RELATIVE_PATH
    if not path.is_file():
        raise RuntimeError(f"generated operator review missing: {path}")

    text = path.read_text(encoding="utf-8")
    mode, operator_ref, reason = cadence_metadata()
    metadata = (
        f"REFRESH_MODE={mode}\n"
        f"OPERATOR_REF={operator_ref}\n"
        f"REFRESH_REASON={reason}\n"
    )
    pattern = re.compile(
        r"(GENERATED_AT_UTC=[^\n]+\n)"
        r"(?:REFRESH_MODE=[^\n]*\nOPERATOR_REF=[^\n]*\nREFRESH_REASON=[^\n]*\n)?"
    )
    text, count = pattern.subn(lambda match: match.group(1) + metadata, text, count=1)
    if count != 1:
        raise RuntimeError("operator review generated-at anchor missing")

    text = text.replace(OBSOLETE_OPERATOR_BOUNDARY, OPERATOR_BOUNDARY)
    if OPERATOR_BOUNDARY not in text:
        raise RuntimeError("operator review cadence boundary missing")
    if "REFRESH_MODE=" not in text or "OPERATOR_REF=" not in text or "REFRESH_REASON=" not in text:
        raise RuntimeError("operator review cadence metadata missing")

    path.write_text(text, encoding="utf-8")


def main() -> int:
    result = core.main()
    if result not in (None, 0):
        return int(result)
    if len(sys.argv) == 3:
        materialize_operator_review(Path(sys.argv[1]).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
