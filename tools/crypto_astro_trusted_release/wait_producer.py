#!/usr/bin/env python3
"""Bounded wait for the exact scheduler-dispatched refresh producer to finish."""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from typing import Any, Callable

MANUAL_PATH = ".github/workflows/crypto-astro-static-refresh-manual.yml"
BOT_ACTOR = "github-actions[bot]"
PENDING_STATES = {"queued", "in_progress", "waiting", "requested", "pending"}


class ProducerWaitError(RuntimeError):
    pass


def wait_for_producer(
    fetch_run: Callable[[int], dict[str, Any]],
    run_id: int,
    *,
    timeout: float = 120.0,
    poll_interval: float = 2.0,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Wait until the exact bot producer reaches terminal success, or fail closed."""
    deadline = clock() + timeout
    while True:
        run = fetch_run(run_id)
        if run.get("path") != MANUAL_PATH or run.get("event") != "workflow_dispatch":
            raise ProducerWaitError("MANUAL_TRIGGER_INVALID")
        if run.get("actor", {}).get("login") != BOT_ACTOR:
            raise ProducerWaitError("MANUAL_TRIGGER_ACTOR_INVALID")

        status = run.get("status")
        conclusion = run.get("conclusion")
        if status == "completed":
            if conclusion != "success":
                raise ProducerWaitError(f"MANUAL_TRIGGER_NOT_SUCCESS:{conclusion}")
            return run
        if status not in PENDING_STATES:
            raise ProducerWaitError(f"MANUAL_TRIGGER_STATE_INVALID:{status}:{conclusion}")
        if clock() >= deadline:
            raise ProducerWaitError("MANUAL_TRIGGER_TIMEOUT")
        sleeper(poll_interval)


def github_fetcher(repo: str, token: str) -> Callable[[int], dict[str, Any]]:
    def fetch(run_id: int) -> dict[str, Any]:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/runs/{run_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "crypto-astro-trusted-release",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    return fetch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()

    wait_for_producer(
        github_fetcher(args.repo, args.token),
        args.run_id,
        timeout=args.timeout,
    )
    print("PRODUCER_TERMINAL_SUCCESS=PASS")


if __name__ == "__main__":
    main()
