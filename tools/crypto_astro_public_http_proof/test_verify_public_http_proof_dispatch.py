#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("verify_public_http_proof_dispatch.py")
SPEC = importlib.util.spec_from_file_location(
    "verify_public_http_proof_dispatch", MODULE_PATH
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

MAIN_SHA = "4fc4d460587ef434563b0b17b05c68f9caf0ced0"
GOOD_BODY = "\n".join(
    [
        "SCHEMA=crypto_astro_public_http_proof_dispatch_request_v0_1",
        "REQUEST_ID=CA-HTTP-20260722-01",
        "OPERATOR_REF=COSMOGRAPHER-HTTP-20260722-01",
        f"EXPECTED_MAIN_SHA={MAIN_SHA}",
    ]
)


class PublicHttpProofDispatchTests(unittest.TestCase):
    def parse(self, body: str = GOOD_BODY, **overrides):
        values = {
            "title": mod.ISSUE_TITLE,
            "actor_login": mod.OWNER_LOGIN,
            "author_login": mod.OWNER_LOGIN,
            "author_association": "OWNER",
            "current_main_sha": MAIN_SHA,
        }
        values.update(overrides)
        return mod.parse_request(body, **values)

    def test_valid_request(self) -> None:
        request = self.parse()
        self.assertEqual(request.request_id, "CA-HTTP-20260722-01")
        self.assertEqual(request.operator_ref, "COSMOGRAPHER-HTTP-20260722-01")
        self.assertEqual(request.expected_main_sha, MAIN_SHA)

    def test_stale_sha_fails_closed(self) -> None:
        with self.assertRaisesRegex(mod.DispatchValidationError, "EXPECTED_MAIN_SHA_STALE"):
            self.parse(current_main_sha="a" * 40)

    def test_non_owner_actor_fails_closed(self) -> None:
        with self.assertRaisesRegex(mod.DispatchValidationError, "ACTOR_NOT_OWNER"):
            self.parse(actor_login="someone-else")

    def test_wrong_title_fails_closed(self) -> None:
        with self.assertRaisesRegex(mod.DispatchValidationError, "WRONG_TITLE"):
            self.parse(title="Crypto-Astro assistant dispatch request")

    def test_unknown_key_or_order_fails_closed(self) -> None:
        lines = GOOD_BODY.splitlines()
        lines[1] = "OPERATOR_REF=COSMOGRAPHER-HTTP-20260722-01"
        lines[2] = "REQUEST_ID=CA-HTTP-20260722-01"
        with self.assertRaisesRegex(
            mod.DispatchValidationError, "KEY_ORDER_OR_SET_INVALID"
        ):
            self.parse("\n".join(lines))

    def test_url_and_shell_tokens_fail_closed(self) -> None:
        for token in ("https://example.test", "${VALUE}", "$(whoami)", "```"):
            body = GOOD_BODY.replace(
                "COSMOGRAPHER-HTTP-20260722-01", token
            )
            with self.subTest(token=token):
                with self.assertRaisesRegex(
                    mod.DispatchValidationError, "FORBIDDEN_TOKEN"
                ):
                    self.parse(body)

    def test_policy_contract(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        policy = mod.load_policy(repo / mod.POLICY_PATH)
        self.assertEqual(mod.validate_policy(policy), [])

    def test_repository_contract(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        report = mod.verify_repository(repo)
        self.assertEqual(report["status"], "PASS", report["failures"])
        self.assertEqual(
            set(report["exact_implementation_scope"]), mod.EXACT_IMPLEMENTATION_SCOPE
        )


if __name__ == "__main__":
    unittest.main()
