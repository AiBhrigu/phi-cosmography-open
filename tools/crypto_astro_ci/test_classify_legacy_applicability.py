import unittest

from classify_legacy_applicability import (
    CURRENT_SURFACE_CHANGE,
    GENERATED_REFRESH,
    HISTORICAL_EXACT,
    NON_APPLICABLE,
    HISTORICAL_HEADS,
    classify,
)


class ApplicabilityClassifierTests(unittest.TestCase):
    def test_exact_historical_branch_has_priority(self):
        for workflow, head_ref in HISTORICAL_HEADS.items():
            with self.subTest(workflow=workflow):
                result = classify(workflow, head_ref, ["README.md"])
                self.assertEqual(result.mode, HISTORICAL_EXACT)

    def test_generated_refresh_is_explicitly_not_legacy(self):
        result = classify(
            "geometry-truth",
            "automation/crypto-astro-static-refresh-12345",
            ["site/crypto-astro/index.html"],
        )
        self.assertEqual(result.mode, GENERATED_REFRESH)

    def test_current_surface_change_runs_reusable_current_checks(self):
        result = classify(
            "editorial-composition",
            "agent/crypto-astro-first-screens-phi-refinement-v0-1",
            ["site/theme/crypto_astro/extensions/12_first_screens_phi.css"],
        )
        self.assertEqual(result.mode, CURRENT_SURFACE_CHANGE)

    def test_current_validator_change_is_current_surface_change(self):
        result = classify(
            "css-modules",
            "agent/crypto-astro-gate3-legacy-ci-applicability-repair-v0-1",
            ["tools/crypto_astro_ci/classify_legacy_applicability.py"],
        )
        self.assertEqual(result.mode, CURRENT_SURFACE_CHANGE)

    def test_unrelated_change_is_explicit_non_applicable(self):
        result = classify("lt1-import-normalization", "docs/update", ["README.md"])
        self.assertEqual(result.mode, NON_APPLICABLE)

    def test_unknown_workflow_fails_closed(self):
        with self.assertRaises(ValueError):
            classify("unknown", "branch", [])


if __name__ == "__main__":
    unittest.main()
