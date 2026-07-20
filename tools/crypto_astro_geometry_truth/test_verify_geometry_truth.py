from __future__ import annotations

import unittest

from verify_geometry_truth import scan_html


class GeometryTruthScanTests(unittest.TestCase):
    def valid_html(self) -> str:
        return "\n".join(
            [
                'class="metric-context-mark" data-geometry-truth="decorative"',
                'class="metric-context-mark" data-geometry-truth="decorative"',
                'class="metric-rail dominance" data-geometry-truth="data-bound"',
                'class="metric-rail stable" data-geometry-truth="data-bound"',
                'class="composition-screen" data-geometry-truth="semantic"',
                'class="composition-semantic-field"',
                'class="barometer-visual" data-geometry-truth="semantic"',
                'class="barometer-semantic-frame"',
                'class="score-orb field-gauge" data-geometry-truth="data-bound"',
                'class="astromodule-polish-rails astromodule-semantic-bands" data-geometry-truth="semantic"',
                'class="astromodule-right-balance__band"',
                'class="distributed-row-v0-1 distributed-row-text-v0-1"',
                'class="distributed-row-v0-1 distributed-row-text-v0-1"',
                'class="distributed-row-v0-1 distributed-row-text-v0-1"',
                'class="distributed-row-v0-1 distributed-row-text-v0-1"',
                'class="distributed-row-v0-1 distributed-row-text-v0-1"',
                'class="distributed-row-v0-1 distributed-row-text-v0-1"',
                'data-geometry-truth="data-bound"><span>Score</span>',
                'data-geometry-truth="data-bound"><span>Score</span>',
                'class="sample-context-status-v0-1"',
                'class="sample-context-status-v0-1"',
                'class="trend-memory-unavailable" data-geometry-truth="semantic"',
                'BTC Dominance 56.5%',
                'Stablecoin Share 13.5%',
                'Market Field Score 61 out of 100',
                'style="width:53.0%" >53.01<',
                'style="width:52.5%" >52.46<',
                '>-2.67%<',
                '>-9.93%<',
                '>-1.01%<',
                '>-4.63%<',
                'Previous verified snapshot is not available.',
            ]
        )

    def test_valid_geometry_contract_passes_scan(self) -> None:
        checks, _ = scan_html(self.valid_html())
        self.assertTrue(all(checks.values()), [name for name, passed in checks.items() if not passed])

    def test_forbidden_unbound_rail_fails(self) -> None:
        checks, _ = scan_html(self.valid_html() + '\nclass="metric-rail cap"')
        self.assertFalse(checks["forbidden_absent:market_cap_unbound_rail"])

    def test_missing_categorical_rows_fails(self) -> None:
        html = self.valid_html().replace(
            'class="distributed-row-v0-1 distributed-row-text-v0-1"',
            "removed",
            1,
        )
        checks, _ = scan_html(html)
        self.assertFalse(checks["required_count:text_only_sample_rows"])

    def test_unsupported_component_value_fails(self) -> None:
        checks, _ = scan_html(self.valid_html() + "\n>49.83<")
        self.assertFalse(checks["forbidden_absent:sample_temporal_unsupported"])


if __name__ == "__main__":
    unittest.main()
