#!/usr/bin/env python3
"""Bounded external HTTP proof for the Crypto-Astro public surfaces.

Read-only verifier:
- no repository writes
- no deployment
- no backend/API/payment activation
- no forecast, trading signal, or price target
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

PAGES_ROOT = "https://aibhrigu.github.io/phi-cosmography-open/crypto-astro"
BHRIGU_ROOT = "https://www.bhrigu.io/crypto-astro/btc"
BHRIGU_QUESTION = "What changed in the BTC field and why does it matter?"

TARGETS = {
    "pages_html": f"{PAGES_ROOT}/index.html",
    "snapshot_json": f"{PAGES_ROOT}/data/crypto_astro_snapshot.public.json",
    "proof_json": f"{PAGES_ROOT}/data/crypto_astro_snapshot_proof.public.json",
    "market_field_json": f"{PAGES_ROOT}/data/market_field_snapshot.public.v0_1.json",
    "bhrigu_form": BHRIGU_ROOT,
    "bhrigu_read": f"{BHRIGU_ROOT}?q={quote(BHRIGU_QUESTION)}",
}

LOCAL_FILES = {
    "pages_html": "site/crypto-astro/index.html",
    "snapshot_json": "site/crypto-astro/data/crypto_astro_snapshot.public.json",
    "proof_json": "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json",
    "market_field_json": "site/crypto-astro/data/market_field_snapshot.public.v0_1.json",
}


class ProofFailure(RuntimeError):
    """Raised when an external proof assertion fails."""


@dataclass(frozen=True)
class FetchResult:
    requested_url: str
    final_url: str
    status: int
    redirects: list[dict[str, Any]]
    content_type: str
    body: bytes
    headers: dict[str, str]


class RecordingRedirectHandler(HTTPRedirectHandler):
    def __init__(self, max_redirects: int = 5) -> None:
        super().__init__()
        self.max_redirects = max_redirects
        self.redirects: list[dict[str, Any]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        if len(self.redirects) >= self.max_redirects:
            raise ProofFailure("REDIRECT_LIMIT_EXCEEDED")
        if not newurl.startswith("https://"):
            raise ProofFailure(f"REDIRECT_NOT_HTTPS:{newurl}")
        self.redirects.append(
            {"status": int(code), "from": req.full_url, "to": newurl}
        )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_content_type(value: str | None) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


def validate_sha(value: str) -> None:
    if value and not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ProofFailure("EXPECTED_MAIN_SHA_MUST_BE_40_HEX")


def fetch_once(url: str, *, timeout: float, max_redirects: int = 5) -> FetchResult:
    if not url.startswith("https://"):
        raise ProofFailure(f"TARGET_NOT_HTTPS:{url}")
    redirects = RecordingRedirectHandler(max_redirects=max_redirects)
    opener = build_opener(redirects)
    request = Request(
        url,
        headers={
            "User-Agent": "Crypto-Astro-Public-HTTP-Proof/0.1",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.1",
            "Cache-Control": "no-cache",
        },
    )
    with opener.open(request, timeout=timeout) as response:
        body = response.read()
        status = int(getattr(response, "status", response.getcode()))
        final_url = response.geturl()
        if status != 200:
            raise ProofFailure(f"HTTP_STATUS_NOT_200:{url}:{status}")
        if not final_url.startswith("https://"):
            raise ProofFailure(f"FINAL_URL_NOT_HTTPS:{final_url}")
        return FetchResult(
            requested_url=url,
            final_url=final_url,
            status=status,
            redirects=redirects.redirects,
            content_type=normalized_content_type(response.headers.get("Content-Type")),
            body=body,
            headers={key.lower(): value for key, value in response.headers.items()},
        )


def fetch_with_retry(
    url: str,
    *,
    timeout: float,
    attempts: int,
    retry_delay: float,
) -> FetchResult:
    if attempts < 1:
        raise ProofFailure("ATTEMPTS_MUST_BE_POSITIVE")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetch_once(url, timeout=timeout)
        except (ProofFailure, HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(retry_delay)
    raise ProofFailure(f"FETCH_FAILED:{url}:{type(last_error).__name__}:{last_error}")


def read_local_bytes(repo: Path, relative_path: str) -> bytes:
    path = repo / relative_path
    if not path.is_file():
        raise ProofFailure(f"LOCAL_SOURCE_MISSING:{relative_path}")
    return path.read_bytes()


def read_local_json(repo: Path, relative_path: str) -> dict[str, Any]:
    try:
        value = json.loads(read_local_bytes(repo, relative_path))
    except json.JSONDecodeError as exc:
        raise ProofFailure(f"LOCAL_JSON_INVALID:{relative_path}:{exc}") from exc
    if not isinstance(value, dict):
        raise ProofFailure(f"LOCAL_JSON_ROOT_NOT_OBJECT:{relative_path}")
    return value


def assert_content_type(actual: str, allowed: set[str], target: str) -> None:
    if actual not in allowed:
        raise ProofFailure(
            f"CONTENT_TYPE_INVALID:{target}:{actual or 'missing'}:"
            f"expected={','.join(sorted(allowed))}"
        )


def assert_exact_bytes(live: bytes, expected: bytes, target: str) -> None:
    if live != expected:
        raise ProofFailure(
            f"PUBLIC_BYTES_MISMATCH:{target}:"
            f"live={sha256_bytes(live)}:expected={sha256_bytes(expected)}"
        )


def decode_utf8(data: bytes, target: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProofFailure(f"UTF8_DECODE_FAILED:{target}:{exc}") from exc


def verify_bhrigu_form(result: FetchResult) -> dict[str, bool]:
    assert_content_type(result.content_type, {"text/html"}, "bhrigu_form")
    text = decode_utf8(result.body, "bhrigu_form")
    assertions = {
        "title_present": "BTC Field Read" in text,
        "question_form_present": "Ask one BTC field question" in text,
        "failure_absent": "BTC Field Read unavailable" not in text,
    }
    if not all(assertions.values()):
        raise ProofFailure(f"BHRIGU_FORM_ASSERTION_FAILED:{assertions}")
    return assertions


def verify_bhrigu_read(
    result: FetchResult, *, expected_timestamp: str
) -> dict[str, bool]:
    assert_content_type(result.content_type, {"text/html"}, "bhrigu_read")
    text = decode_utf8(result.body, "bhrigu_read")
    assertions = {
        "result_heading_present": "One coherent Cosmographer read" in text,
        "snapshot_timestamp_present": expected_timestamp in text,
        "source_failure_absent": "Source-bound failure" not in text,
        "unavailable_absent": "BTC Field Read unavailable" not in text,
    }
    if not all(assertions.values()):
        raise ProofFailure(f"BHRIGU_READ_ASSERTION_FAILED:{assertions}")
    return assertions


def result_record(
    result: FetchResult, *, assertions: dict[str, Any]
) -> dict[str, Any]:
    return {
        "requested_url": result.requested_url,
        "final_url": result.final_url,
        "status": result.status,
        "redirect_count": len(result.redirects),
        "redirects": result.redirects,
        "content_type": result.content_type,
        "bytes": len(result.body),
        "sha256": sha256_bytes(result.body),
        "assertions": assertions,
    }


def run_proof(
    *,
    repo: Path,
    report_path: Path,
    expected_main_sha: str,
    timeout: float,
    attempts: int,
    retry_delay: float,
) -> dict[str, Any]:
    validate_sha(expected_main_sha)
    snapshot = read_local_json(
        repo, "site/crypto-astro/data/crypto_astro_snapshot.public.json"
    )
    proof = read_local_json(
        repo, "site/crypto-astro/data/crypto_astro_snapshot_proof.public.json"
    )
    market_field = read_local_json(
        repo, "site/crypto-astro/data/market_field_snapshot.public.v0_1.json"
    )

    expected_timestamp = str(snapshot.get("generated_at_utc", ""))
    if not expected_timestamp:
        raise ProofFailure("LOCAL_SNAPSHOT_TIMESTAMP_MISSING")
    if proof.get("generated_at_utc") != expected_timestamp:
        raise ProofFailure("LOCAL_PROOF_TIMESTAMP_MISMATCH")
    if market_field.get("updated_at_utc") != expected_timestamp:
        raise ProofFailure("LOCAL_MARKET_FIELD_TIMESTAMP_MISMATCH")

    report: dict[str, Any] = {
        "schema_version": "crypto_astro_public_http_proof_v0_1",
        "status": "RUNNING",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "expected_main_sha": expected_main_sha,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "canonical_snapshot_timestamp": expected_timestamp,
        "boundaries": {
            "read_only": True,
            "no_repository_write": True,
            "no_deploy": True,
            "no_schedule": True,
            "no_backend_api_payment_activation": True,
            "no_forecast_trading_signal_price_target": True,
        },
        "targets": {},
    }

    try:
        for name in (
            "pages_html",
            "snapshot_json",
            "proof_json",
            "market_field_json",
        ):
            result = fetch_with_retry(
                TARGETS[name],
                timeout=timeout,
                attempts=attempts,
                retry_delay=retry_delay,
            )
            expected = read_local_bytes(repo, LOCAL_FILES[name])
            allowed = {"text/html"} if name == "pages_html" else {
                "application/json",
                "text/plain",
            }
            assert_content_type(result.content_type, allowed, name)
            assert_exact_bytes(result.body, expected, name)
            report["targets"][name] = result_record(
                result,
                assertions={
                    "http_200": True,
                    "https_final_url": True,
                    "content_type_valid": True,
                    "exact_bytes_match_main_source": True,
                    "expected_sha256": sha256_bytes(expected),
                },
            )

        form_result = fetch_with_retry(
            TARGETS["bhrigu_form"],
            timeout=timeout,
            attempts=attempts,
            retry_delay=retry_delay,
        )
        report["targets"]["bhrigu_form"] = result_record(
            form_result, assertions=verify_bhrigu_form(form_result)
        )

        read_result = fetch_with_retry(
            TARGETS["bhrigu_read"],
            timeout=timeout,
            attempts=attempts,
            retry_delay=retry_delay,
        )
        report["targets"]["bhrigu_read"] = result_record(
            read_result,
            assertions=verify_bhrigu_read(
                read_result, expected_timestamp=expected_timestamp
            ),
        )
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["failure"] = f"{type(exc).__name__}:{exc}"
        raise
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("artifacts/crypto-astro-public-http-proof.json"),
    )
    parser.add_argument("--expected-main-sha", default="")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = run_proof(
            repo=args.repo.resolve(),
            report_path=args.report,
            expected_main_sha=args.expected_main_sha.strip(),
            timeout=args.timeout,
            attempts=args.attempts,
            retry_delay=args.retry_delay,
        )
    except Exception as exc:
        print(f"CRYPTO_ASTRO_PUBLIC_HTTP_PROOF=FAIL:{type(exc).__name__}:{exc}")
        return 1
    print("CRYPTO_ASTRO_PUBLIC_HTTP_PROOF=PASS")
    print(f"EXPECTED_MAIN_SHA={report['expected_main_sha']}")
    print(f"SNAPSHOT_TIMESTAMP={report['canonical_snapshot_timestamp']}")
    print(f"TARGET_COUNT={len(report['targets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
