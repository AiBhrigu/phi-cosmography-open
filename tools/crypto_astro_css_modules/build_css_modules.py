#!/usr/bin/env python3
"""Build and verify the deterministic Crypto-Astro CSS module bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path("site/theme/crypto_astro/css_order_manifest.json")
STYLE_RE = re.compile(rb"<style(?:\s[^>]*)?>(.*?)</style>", re.IGNORECASE | re.DOTALL)


class ModuleBuildError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModuleBuildError(f"Unable to load manifest: {path}") from exc
    if value.get("schema_version") != "crypto_astro_css_order_manifest_v0_1":
        raise ModuleBuildError("Unexpected CSS order manifest schema")
    modules = value.get("modules")
    if not isinstance(modules, list) or not modules:
        raise ModuleBuildError("Manifest must contain ordered modules")
    return value


def join_modules(module_bytes: list[bytes]) -> bytes:
    parts: list[bytes] = []
    for value in module_bytes:
        parts.append(value)
        if value and not value.endswith((b"\n", b"\r")):
            parts.append(b"\n")
    return b"".join(parts)


def read_source_blocks(repo_root: Path, manifest: dict[str, Any]) -> list[bytes]:
    base_sha = str(manifest.get("source_base_sha") or "")
    source_html = str(manifest.get("source_html_path") or "")
    if not base_sha or not source_html:
        raise ModuleBuildError("Source base SHA and HTML path are required")
    try:
        html = subprocess.check_output(
            ["git", "show", f"{base_sha}:{source_html}"],
            cwd=repo_root,
        )
    except subprocess.CalledProcessError as exc:
        raise ModuleBuildError(f"Unable to read source HTML from {base_sha}") from exc
    return STYLE_RE.findall(html)


def build(
    repo_root: Path,
    manifest_path: Path,
    *,
    write: bool,
    verify_source_base: bool,
) -> dict[str, Any]:
    resolved_manifest = repo_root / manifest_path
    manifest = load_manifest(resolved_manifest)
    modules: list[bytes] = []
    source_blocks = read_source_blocks(repo_root, manifest) if verify_source_base else []

    for position, entry in enumerate(manifest["modules"], 1):
        if entry.get("order") != position:
            raise ModuleBuildError(f"Module order mismatch at position {position}")
        module_path = repo_root / str(entry.get("path") or "")
        try:
            value = module_path.read_bytes()
        except OSError as exc:
            raise ModuleBuildError(f"Unable to read module: {module_path}") from exc
        if len(value) != int(entry.get("byte_count", -1)):
            raise ModuleBuildError(f"Module byte count mismatch: {entry['path']}")
        if sha256_bytes(value) != entry.get("sha256"):
            raise ModuleBuildError(f"Module SHA-256 mismatch: {entry['path']}")
        if verify_source_base:
            source_index = int(entry.get("source_style_block_index", 0))
            if source_index < 1 or source_index > len(source_blocks):
                raise ModuleBuildError(f"Invalid source block index: {entry['path']}")
            if value != source_blocks[source_index - 1]:
                raise ModuleBuildError(f"Source style block mismatch: {entry['path']}")
        modules.append(value)

    bundle = join_modules(modules)
    legacy_path = repo_root / str(manifest.get("legacy_source_path") or "")
    output_path = repo_root / str(manifest.get("generated_bundle_path") or "")
    try:
        legacy = legacy_path.read_bytes()
    except OSError as exc:
        raise ModuleBuildError(f"Unable to read legacy source: {legacy_path}") from exc
    if bundle != legacy:
        raise ModuleBuildError("Generated module bundle differs from legacy CSS source")

    if write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(bundle)
    elif not output_path.is_file() or output_path.read_bytes() != bundle:
        raise ModuleBuildError("Generated CSS bundle is missing or stale")

    report = {
        "schema_version": "crypto_astro_css_module_build_report_v0_1",
        "status": "PASS",
        "module_count": len(modules),
        "bundle_byte_count": len(bundle),
        "bundle_sha256": sha256_bytes(bundle),
        "legacy_source_path": str(manifest["legacy_source_path"]),
        "generated_bundle_path": str(manifest["generated_bundle_path"]),
        "source_base_verified": verify_source_base,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify-source-base", action="store_true")
    args = parser.parse_args()
    try:
        report = build(
            args.repo_root.resolve(),
            args.manifest,
            write=args.write,
            verify_source_base=args.verify_source_base,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except ModuleBuildError as exc:
        print(f"CRYPTO_ASTRO_CSS_MODULE_BUILD=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
