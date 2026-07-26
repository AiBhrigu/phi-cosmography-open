#!/usr/bin/env python3
"""Bounded external HTTP proof for the Crypto-Astro public surfaces.

Read-only verifier:
- no repository writes
- no deployment
- no backend/API/payment activation
- no forecast, trading signal, or price target

Failure evidence is always materialized before the process exits. The report
retains the failing stage, target, URL, HTTP status, redirects, retry history,
and exception details whenever those values are available.
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
from typing import Any, Callable
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
    """Fail-closed proof exception with serializable diagnostic context."""

    def __init__(
        self,
        reason_code: str,
        *,
        stage: str = "",
        target: str = "",
        url: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.reason_code = reason_code
        self.stage = stage
        self.target = target
        self.url = url
        self.details = details or {}
        super().__init__(reason_code)


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
            raise ProofFailure(
                "REDIRECT_LIMIT_EXCEEDED",
                stage="external_fetch",
                url=req.full_url,
                details={"redirects": list(self.redirects), "redirect_limit": self.max_redirects},
            )
        if not newurl.startswith("https://"):
            raise ProofFailure(
                "REDIRECT_NOT_HTTPS",
                stage="external_fetch",
                url=req.full_url,
                details={"redirects": list(self.redirects), "redirect_target": newurl},
            )
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
        raise ProofFailure(
            "EXPECTED_MAIN_SHA_MUST_BE_40_HEX",
            stage="input_validation",
            details={"expected_main_sha": value},
        )


def _exception_record(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ProofFailure):
        return {
            "exception_type": type(exc).__name__,
            "reason_code": exc.reason_code,
            "message": str(exc),
            "stage": exc.stage,
            "target": exc.target,
            "url": exc.url,
            "details": exc.details,
        }
    return {
        "exception_type": type(exc).__name__,
        "reason_code": "UNEXPECTED_EXCEPTION",
        "message": str(exc),
        "stage": "",
        "target": "",
        "url": "",
        "details": {},
    }


def fetch_once(url: str, *, timeout: float, max_redirects: int = 5) -> FetchResult:
    if not url.startswith("https://"):
        raise ProofFailure(
            "TARGET_NOT_HTTPS",
            stage="external_fetch",
            url=url,
            details={"requested_url": url},
        )
    redirects = RecordingRedirectHandler(max_redirects=max_redirects)
    opener = build_opener(redirects)
    request = Request(
        url,
        headers={
            "User-Agent": "Crypto-Astro-Public-HTTP-Proof/0.2",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.1",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read()
            status = int(getattr(response, "status", response.getcode()))
            final_url = response.geturl()
            if status != 200:
                raise ProofFailure(
                    "HTTP_STATUS_NOT_200",
                    stage="external_fetch",
                    url=url,
                    details={
                        "requested_url": url,
                        "final_url": final_url,
                        "http_status": status,
                        "redirects": list(redirects.redirects),
                    },
                )
            if not final_url.startswith("https://"):
                raise ProofFailure(
                    "FINAL_URL_NOT_HTTPS",
                    stage="external_fetch",
                    url=url,
                    details={
                        "requested_url": url,
                        "final_url": final_url,
                        "http_status": status,
                        "redirects": list(redirects.redirects),
                    },
                )
            return FetchResult(
                requested_url=url,
                final_url=final_url,
                status=status,
                redirects=list(redirects.redirects),
                content_type=normalized_content_type(response.headers.get("Content-Type")),
                body=body,
                headers={key.lower(): value for key, value in response.headers.items()},
            )
    except HTTPError as exc:
        raise ProofFailure(
            "HTTP_ERROR",
            stage="external_fetch",
            url=url,
            details={
                "requested_url": url,
                "final_url": exc.geturl() or url,
                "http_status": int(exc.code),
                "redirects": list(redirects.redirects),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        ) from exc
    except URLError as exc:
        raise ProofFailure(
            "URL_ERROR",
            stage="external_fetch",
            url=url,
            details={
                "requested_url": url,
                "http_status": None,
                "redirects": list(redirects.redirects),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        ) from exc
    except TimeoutError as exc:
        raise ProofFailure(
            "FETCH_TIMEOUT",
            stage="external_fetch",
            url=url,
            details={
                "requested_url": url,
                "http_status": None,
                "redirects": list(redirects.redirects),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        ) from exc
    except OSError as exc:
        raise ProofFailure(
            "FETCH_OS_ERROR",
            stage="external_fetch",
            url=url,
            details={
                "requested_url": url,
                "http_status": None,
                "redirects": list(redirects.redirects),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            },
        ) from exc


def fetch_with_retry(
    url: str,
    *,
    timeout: float,
    attempts: int,
    retry_delay: float,
    fetcher: Callable[..., FetchResult] = fetch_once,
) -> FetchResult:
    if attempts < 1:
        raise ProofFailure(
            "ATTEMPTS_MUST_BE_POSITIVE",
            stage="input_validation",
            url=url,
            details={"attempts": attempts},
        )
    attempt_records: list[dict[str, Any]] = []
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetcher(url, timeout=timeout)
        except (ProofFailure, HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            record = _exception_record(exc)
            record["attempt"] = attempt
            attempt_records.append(record)
            if attempt < attempts:
                time.sleep(retry_delay)
    last_record = attempt_records[-1] if attempt_records else {}
    details = dict(last_record.get("details") or {})
    details.update(
        {
            "attempt_count": attempts,
            "attempts": attempt_records,
            "last_exception_type": type(last_error).__name__ if last_error else "",
            "last_exception_message": str(last_error) if last_error else "",
        }
    )
    raise ProofFailure(
        "FETCH_FAILED",
        stage="external_fetch",
        url=url,
        details=details,
    )


def read_local_bytes(repo: Path, relative_path: str) -> bytes:
    path = repo / relative_path
    if not path.is_file():
        raise ProofFailure(
            "LOCAL_SOURCE_MISSING",
            stage="local_source_validation",
            target=relative_path,
            url=relative_path,
            details={"relative_path": relative_path},
        )
    return path.read_bytes()


def read_local_json(repo: Path, relative_path: str) -> dict[str, Any]:
    try:
        value = json.loads(read_local_bytes(repo, relative_path))
    except json.JSONDecodeError as exc:
        raise ProofFailure(
            "LOCAL_JSON_INVALID",
            stage="local_source_validation",
            target=relative_path,
            url=relative_path,
            details={"relative_path": relative_path, "exception_message": str(exc)},
        ) from exc
    if not isinstance(value, dict):
        raise ProofFailure(
            "LOCAL_JSON_ROOT_NOT_OBJECT",
            stage="local_source_validation",
            target=relative_path,
            url=relative_path,
            details={"relative_path": relative_path},
        )
    return value


def assert_content_type(actual: str, allowed: set[str], target: str) -> None:
    if actual not in allowed:
        raise ProofFailure(
            "CONTENT_TYPE_INVALID",
            stage="external_assertion",
            target=target,
            url=TARGETS.get(target, ""),
            details={"actual": actual or "missing", "allowed": sorted(allowed)},
        )


def assert_exact_bytes(live: bytes, expected: bytes, target: str) -> None:
    if live != expected:
        raise ProofFailure(
            "PUBLIC_BYTES_MISMATCH",
            stage="external_assertion",
            target=target,
            url=TARGETS.get(target, ""),
            details={
                "live_sha256": sha256_bytes(live),
                "expected_sha256": sha256_bytes(expected),
            },
        )


def decode_utf8(data: bytes, target: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProofFailure(
            "UTF8_DECODE_FAILED",
            stage="external_assertion",
            target=target,
            url=TARGETS.get(target, ""),
            details={"exception_message": str(exc)},
        ) from exc


def verify_bhrigu_form(result: FetchResult) -> dict[str, bool]:
    assert_content_type(result.content_type, {"text/html"}, "bhrigu_form")
    text = decode_utf8(result.body, "bhrigu_form")
    assertions = {
        "title_present": "BTC Field Read" in text,
        "question_form_present": "Ask one BTC field question" in text,
        "failure_absent": "BTC Field Read unavailable" not in text,
    }
    if not all(assertions.values()):
        raise ProofFailure(
            "BHRIGU_FORM_ASSERTION_FAILED",
            stage="external_assertion",
            target="bhrigu_form",
            url=TARGETS["bhrigu_form"],
            details={"assertions": assertions},
        )
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
        raise ProofFailure(
            "BHRIGU_READ_ASSERTION_FAILED",
            stage="external_assertion",
            target="bhrigu_read",
            url=TARGETS["bhrigu_read"],
            details={"assertions": assertions, "expected_timestamp": expected_timestamp},
        )
    return assertions


def result_record(
    result: FetchResult, *, assertions: dict[str, Any]
) -> dict[str, Any]:
    return {
        "status": "PASS",
        "requested_url": result.requested_url,
        "final_url": result.final_url,
        "http_status": result.status,
        "redirect_count": len(result.redirects),
        "redirects": result.redirects,
        "content_type": result.content_type,
        "bytes": len(result.body),
        "sha256": sha256_bytes(result.body),
        "assertions": assertions,
    }


def failure_target_record(
    *,
    target: str,
    url: str,
    exc: Exception,
    result: FetchResult | None = None,
) -> dict[str, Any]:
    exc_record = _exception_record(exc)
    details = exc_record.get("details") or {}
    redirects = list(result.redirects) if result else list(details.get("redirects") or [])
    requested_url = result.requested_url if result else details.get("requested_url", url)
    final_url = result.final_url if result else details.get("final_url", "")
    http_status = result.status if result else details.get("http_status")
    return {
        "status": "FAIL",
        "requested_url": requested_url,
        "final_url": final_url,
        "http_status": http_status,
        "redirect_count": len(redirects),
        "redirects": redirects,
        "content_type": result.content_type if result else "",
        "bytes": len(result.body) if result else 0,
        "sha256": sha256_bytes(result.body) if result else "",
        "failure": exc_record,
    }


def _new_report(expected_main_sha: str) -> dict[str, Any]:
    return {
        "schema_version": "crypto_astro_public_http_proof_v0_1",
        "diagnostic_contract": "failure_evidence_retention_v0_1",
        "status": "RUNNING",
        "verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "expected_main_sha": expected_main_sha,
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "canonical_snapshot_timestamp": "",
        "current_stage": "initialization",
        "current_target": "",
        "local_source_validation": {
            "status": "PENDING",
            "snapshot_timestamp": "",
            "proof_timestamp": "",
            "market_field_timestamp": "",
        },
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


def write_report(report_path: Path, report: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = report_path.with_suffix(report_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary_path.replace(report_path)


def run_proof(
    *,
    repo: Path,
    report_path: Path,
    expected_main_sha: str,
    timeout: float,
    attempts: int,
    retry_delay: float,
) -> dict[str, Any]:
    report = _new_report(expected_main_sha)
    active_result: FetchResult | None = None
    try:
        report["current_stage"] = "input_validation"
        validate_sha(expected_main_sha)

        report["current_stage"] = "local_source_validation"
        report["current_target"] = "snapshot_json"
        snapshot = read_local_json(repo, LOCAL_FILES["snapshot_json"])
        report["current_target"] = "proof_json"
        proof = read_local_json(repo, LOCAL_FILES["proof_json"])
        report["current_target"] = "market_field_json"
        market_field = read_local_json(repo, LOCAL_FILES["market_field_json"])

        snapshot_timestamp = str(snapshot.get("generated_at_utc", ""))
        proof_timestamp = str(proof.get("generated_at_utc", ""))
        market_field_timestamp = str(market_field.get("updated_at_utc", ""))
        report["canonical_snapshot_timestamp"] = snapshot_timestamp
        report["local_source_validation"].update(
            {
                "snapshot_timestamp": snapshot_timestamp,
                "proof_timestamp": proof_timestamp,
                "market_field_timestamp": market_field_timestamp,
            }
        )
        if not snapshot_timestamp:
            raise ProofFailure(
                "LOCAL_SNAPSHOT_TIMESTAMP_MISSING",
                stage="local_source_validation",
                target="snapshot_json",
                url=LOCAL_FILES["snapshot_json"],
            )
        if proof_timestamp != snapshot_timestamp:
            raise ProofFailure(
                "LOCAL_PROOF_TIMESTAMP_MISMATCH",
                stage="local_source_validation",
                target="proof_json",
                url=LOCAL_FILES["proof_json"],
                details={
                    "expected_timestamp": snapshot_timestamp,
                    "actual_timestamp": proof_timestamp,
                },
            )
        if market_field_timestamp != snapshot_timestamp:
            raise ProofFailure(
                "LOCAL_MARKET_FIELD_TIMESTAMP_MISMATCH",
                stage="local_source_validation",
                target="market_field_json",
                url=LOCAL_FILES["market_field_json"],
                details={
                    "expected_timestamp": snapshot_timestamp,
                    "actual_timestamp": market_field_timestamp,
                },
            )
        report["local_source_validation"]["status"] = "PASS"

        for name in (
            "pages_html",
            "snapshot_json",
            "proof_json",
            "market_field_json",
        ):
            report["current_stage"] = "external_fetch"
            report["current_target"] = name
            active_result = None
            try:
                active_result = fetch_with_retry(
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
                report["current_stage"] = "external_assertion"
                assert_content_type(active_result.content_type, allowed, name)
                assert_exact_bytes(active_result.body, expected, name)
                report["targets"][name] = result_record(
                    active_result,
                    assertions={
                        "http_200": True,
                        "https_final_url": True,
                        "content_type_valid": True,
                        "exact_bytes_match_main_source": True,
                        "expected_sha256": sha256_bytes(expected),
                    },
                )
            except Exception as exc:
                report["targets"][name] = failure_target_record(
                    target=name,
                    url=TARGETS[name],
                    exc=exc,
                    result=active_result,
                )
                raise

        report["current_stage"] = "external_fetch"
        report["current_target"] = "bhrigu_form"
        active_result = None
        try:
            active_result = fetch_with_retry(
                TARGETS["bhrigu_form"],
                timeout=timeout,
                attempts=attempts,
                retry_delay=retry_delay,
            )
            report["current_stage"] = "external_assertion"
            report["targets"]["bhrigu_form"] = result_record(
                active_result, assertions=verify_bhrigu_form(active_result)
            )
        except Exception as exc:
            report["targets"]["bhrigu_form"] = failure_target_record(
                target="bhrigu_form",
                url=TARGETS["bhrigu_form"],
                exc=exc,
                result=active_result,
            )
            raise

        report["current_stage"] = "external_fetch"
        report["current_target"] = "bhrigu_read"
        active_result = None
        try:
            active_result = fetch_with_retry(
                TARGETS["bhrigu_read"],
                timeout=timeout,
                attempts=attempts,
                retry_delay=retry_delay,
            )
            report["current_stage"] = "external_assertion"
            report["targets"]["bhrigu_read"] = result_record(
                active_result,
                assertions=verify_bhrigu_read(
                    active_result, expected_timestamp=snapshot_timestamp
                ),
            )
        except Exception as exc:
            report["targets"]["bhrigu_read"] = failure_target_record(
                target="bhrigu_read",
                url=TARGETS["bhrigu_read"],
                exc=exc,
                result=active_result,
            )
            raise

        report["status"] = "PASS"
        report["current_stage"] = "complete"
        report["current_target"] = ""
    except Exception as exc:
        report["status"] = "FAIL"
        record = _exception_record(exc)
        if not record["stage"]:
            record["stage"] = report.get("current_stage", "")
        if not record["target"]:
            record["target"] = report.get("current_target", "")
        if not record["url"] and record["target"] in TARGETS:
            record["url"] = TARGETS[record["target"]]
        report["failure"] = record
        raise
    finally:
        write_report(report_path, report)
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
        reason_code = exc.reason_code if isinstance(exc, ProofFailure) else type(exc).__name__
        print(f"CRYPTO_ASTRO_PUBLIC_HTTP_PROOF=FAIL:{reason_code}:{exc}")
        print(f"REPORT_PATH={args.report}")
        return 1
    print("CRYPTO_ASTRO_PUBLIC_HTTP_PROOF=PASS")
    print(f"EXPECTED_MAIN_SHA={report['expected_main_sha']}")
    print(f"SNAPSHOT_TIMESTAMP={report['canonical_snapshot_timestamp']}")
    print(f"TARGET_COUNT={len(report['targets'])}")
    print(f"REPORT_PATH={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
