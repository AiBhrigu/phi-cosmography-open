#!/usr/bin/env python3
"""Classify historical Crypto-Astro CI gates without weakening current truth checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

HISTORICAL_EXACT = "HISTORICAL_EXACT"
GENERATED_REFRESH = "GENERATED_REFRESH"
CURRENT_SURFACE_CHANGE = "CURRENT_SURFACE_CHANGE"
NON_APPLICABLE = "NON_APPLICABLE"

HISTORICAL_HEADS = {
    "css-extraction": "feature/crypto-astro-mechanical-inline-css-extraction-v0-1",
    "css-modules": "feature/crypto-astro-deterministic-css-modules-v0-1",
    "lt1-import-normalization": "feature/crypto-astro-lt1-import-normalization-v0-1",
    "geometry-truth": "feature/crypto-astro-geometry-truth-repair-v0-1",
    "editorial-composition": "feature/crypto-astro-editorial-composition-and-cta-v0-1",
}

REFRESH_PREFIX = "automation/crypto-astro-static-refresh-"
CURRENT_PREFIXES = (
    "site/crypto-astro/",
    "site/theme/crypto_astro",
    "tools/crypto_astro_",
    ".github/workflows/crypto-astro-",
)


@dataclass(frozen=True)
class Classification:
    mode: str
    reason: str
    changed_files: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "crypto_astro_legacy_ci_applicability_v0_1",
            "mode": self.mode,
            "reason": self.reason,
            "changed_files": list(self.changed_files),
        }


def normalize_paths(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({path.strip() for path in paths if path.strip()}))


def classify(workflow: str, head_ref: str, changed_files: Sequence[str]) -> Classification:
    if workflow not in HISTORICAL_HEADS:
        raise ValueError(f"unknown workflow: {workflow}")

    changed = normalize_paths(changed_files)
    historical_head = HISTORICAL_HEADS[workflow]

    if head_ref == historical_head:
        return Classification(
            HISTORICAL_EXACT,
            f"exact historical implementation branch for {workflow}",
            changed,
        )

    if head_ref.startswith(REFRESH_PREFIX):
        return Classification(
            GENERATED_REFRESH,
            "generated static refresh is governed by current refresh, memory, visual and BHRIGU consumer gates",
            changed,
        )

    if any(path.startswith(CURRENT_PREFIXES) for path in changed):
        return Classification(
            CURRENT_SURFACE_CHANGE,
            "current Crypto-Astro surface or validation infrastructure changed",
            changed,
        )

    return Classification(
        NON_APPLICABLE,
        "no current or historical Crypto-Astro surface path changed",
        changed,
    )


def git_changed_files(base_sha: str, head_sha: str) -> tuple[str, ...]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", base_sha, head_sha],
        text=True,
    )
    return normalize_paths(output.splitlines())


def write_github_output(path: str, result: Classification) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(f"mode={result.mode}\n")
        handle.write(f"reason={result.reason}\n")
        handle.write(f"changed_count={len(result.changed_files)}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", required=True, choices=sorted(HISTORICAL_HEADS))
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--out")
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changed = tuple(args.changed_file)
    if args.base_sha or args.head_sha:
        if not (args.base_sha and args.head_sha):
            raise SystemExit("--base-sha and --head-sha must be supplied together")
        changed = git_changed_files(args.base_sha, args.head_sha)

    result = classify(args.workflow, args.head_ref, changed)
    payload = result.as_dict()
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(rendered, end="")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(rendered, encoding="utf-8")
    write_github_output(args.github_output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
