from __future__ import annotations

import unittest

from tools.crypto_astro_trusted_release.wait_producer import (
    MANUAL_PATH,
    ProducerWaitError,
    wait_for_producer,
)


def run_state(
    status="completed",
    conclusion="success",
    *,
    path=MANUAL_PATH,
    event="workflow_dispatch",
    actor="github-actions[bot]",
):
    return {
        "path": path,
        "event": event,
        "actor": {"login": actor},
        "status": status,
        "conclusion": conclusion,
    }


class FetchSequence:
    def __init__(self, values):
        self.values = list(values)
        self.calls = 0

    def __call__(self, run_id):
        self.calls += 1
        return self.values[min(self.calls - 1, len(self.values) - 1)]


class ProducerTerminalWaitTest(unittest.TestCase):
    def test_in_progress_then_success(self):
        fetch = FetchSequence([
            run_state(status="in_progress", conclusion=None),
            run_state(status="completed", conclusion="success"),
        ])
        ticks = iter([0.0, 0.1, 0.2])
        out = wait_for_producer(
            fetch,
            123,
            timeout=1,
            poll_interval=0,
            clock=lambda: next(ticks),
            sleeper=lambda _: None,
        )
        self.assertEqual(out["conclusion"], "success")
        self.assertEqual(fetch.calls, 2)

    def test_terminal_failure_fails_closed(self):
        fetch = FetchSequence([run_state(status="completed", conclusion="failure")])
        with self.assertRaisesRegex(ProducerWaitError, "MANUAL_TRIGGER_NOT_SUCCESS:failure"):
            wait_for_producer(fetch, 123, timeout=1, poll_interval=0)

    def test_wrong_actor_fails_closed_before_wait(self):
        fetch = FetchSequence([run_state(status="in_progress", conclusion=None, actor="AiBhrigu")])
        with self.assertRaisesRegex(ProducerWaitError, "MANUAL_TRIGGER_ACTOR_INVALID"):
            wait_for_producer(fetch, 123, timeout=1, poll_interval=0)

    def test_wrong_path_or_event_fails_closed(self):
        fetch = FetchSequence([run_state(path=".github/workflows/other.yml")])
        with self.assertRaisesRegex(ProducerWaitError, "MANUAL_TRIGGER_INVALID"):
            wait_for_producer(fetch, 123, timeout=1, poll_interval=0)

    def test_pending_timeout_fails_closed(self):
        fetch = FetchSequence([run_state(status="in_progress", conclusion=None)])
        with self.assertRaisesRegex(ProducerWaitError, "MANUAL_TRIGGER_TIMEOUT"):
            wait_for_producer(
                fetch,
                123,
                timeout=0,
                poll_interval=0,
                clock=lambda: 0.0,
                sleeper=lambda _: None,
            )


if __name__ == "__main__":
    unittest.main()
