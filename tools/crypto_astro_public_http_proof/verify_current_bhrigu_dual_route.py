#!/usr/bin/env python3
"""Current BHRIGU entry/live assertions for the Crypto-Astro public HTTP proof.

This overlay preserves the existing Pages byte-proof and failure-retention
implementation while binding the BHRIGU checks to the accepted current routes:

- /crypto-astro/btc?lang=ru
- /crypto-astro/btc/live?lang=ru

No product, deployment, scheduler, source, or Snapshot mutation is performed.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).with_name("verify_public_http_proof.py")
SPEC = importlib.util.spec_from_file_location("verify_public_http_proof_legacy", MODULE_PATH)
assert SPEC and SPEC.loader
base = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = base
SPEC.loader.exec_module(base)

ENTRY_TARGET = f"{base.BHRIGU_ROOT}?lang=ru"
LIVE_TARGET = f"{base.BHRIGU_ROOT}/live?lang=ru"
CURRENT_PRIMARY_CTA_MARKER = 'data-primary-btc-change-question="true"'
LEGACY_CTA = "Start free dialogue"
LIVE_CONTRACT_META = 'name="btc-live-dialogue" content="semantic-route-graph-v0-1"'
LIVE_SHELL_MARKER = 'data-live-dialogue="btc-cosmographer-route-v0-1"'
ENTRY_TIMESTAMP_PATTERN = re.compile(
    r'data-source-generated-at="(?P<timestamp>\d{4}-\d{2}-\d{2}T'
    r'\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z)"'
)

_entry_snapshot_timestamp: str | None = None


def verify_current_bhrigu_entry(result: Any) -> dict[str, bool]:
    """Verify the accepted RU product entry and retain its Snapshot timestamp."""

    global _entry_snapshot_timestamp

    base.assert_content_type(result.content_type, {"text/html"}, "bhrigu_form")
    text = base.decode_utf8(result.body, "bhrigu_form")
    timestamp_match = ENTRY_TIMESTAMP_PATTERN.search(text)
    _entry_snapshot_timestamp = (
        timestamp_match.group("timestamp") if timestamp_match else None
    )

    assertions = {
        "title_present": "BTC Field Read" in text,
        "current_primary_cta_present": CURRENT_PRIMARY_CTA_MARKER in text,
        "legacy_cta_absent": LEGACY_CTA not in text,
        "live_route_present": "/crypto-astro/btc/live?lang=ru" in text,
        "entry_snapshot_timestamp_present": _entry_snapshot_timestamp is not None,
        "failure_absent": "BTC Field Read unavailable" not in text,
    }
    if not all(assertions.values()):
        raise base.ProofFailure(
            "BHRIGU_ENTRY_ASSERTION_FAILED",
            stage="external_assertion",
            target="bhrigu_form",
            url=base.TARGETS["bhrigu_form"],
            details={
                "assertions": assertions,
                "entry_snapshot_timestamp": _entry_snapshot_timestamp or "",
            },
        )
    return assertions


def verify_current_bhrigu_live(
    result: Any, *, expected_timestamp: str
) -> dict[str, bool]:
    """Verify the accepted RU live route and dual-route Snapshot identity."""

    text = base.decode_utf8(result.body, "bhrigu_read")
    base.assert_content_type(result.content_type, {"text/html"}, "bhrigu_read")

    assertions = {
        "live_contract_meta_present": LIVE_CONTRACT_META in text,
        "live_shell_present": LIVE_SHELL_MARKER in text,
        "live_snapshot_marker_present": "data-market-snapshot-generated-at" in text,
        "live_snapshot_timestamp_present": expected_timestamp in text,
        "entry_snapshot_matches_expected": _entry_snapshot_timestamp
        == expected_timestamp,
        "entry_and_live_snapshot_identity_match": _entry_snapshot_timestamp
        == expected_timestamp,
        "source_failure_absent": "Source-bound failure" not in text,
        "unavailable_absent": "BTC Field Read unavailable" not in text,
    }
    if not all(assertions.values()):
        raise base.ProofFailure(
            "BHRIGU_LIVE_ASSERTION_FAILED",
            stage="external_assertion",
            target="bhrigu_read",
            url=base.TARGETS["bhrigu_read"],
            details={
                "assertions": assertions,
                "expected_timestamp": expected_timestamp,
                "entry_snapshot_timestamp": _entry_snapshot_timestamp or "",
            },
        )
    return assertions


def install_current_surface_contract() -> None:
    """Bind the retained proof engine to the accepted current BHRIGU surface."""

    global _entry_snapshot_timestamp
    _entry_snapshot_timestamp = None
    base.TARGETS["bhrigu_form"] = ENTRY_TARGET
    base.TARGETS["bhrigu_read"] = LIVE_TARGET
    base.verify_bhrigu_form = verify_current_bhrigu_entry
    base.verify_bhrigu_read = verify_current_bhrigu_live


def main() -> int:
    install_current_surface_contract()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
