from __future__ import annotations

import unittest

from verify_editorial_composition import verify


class EditorialCompositionVerifierTests(unittest.TestCase):
    def sample(self) -> str:
        values = "$2.287T $40.71B 56.5% 13.5% 34.5% 39.9% 9.8% 66.3% $75.55B"
        filler = " ".join(["context"] * 680)
        return f'''<main>
<nav class="crypto-astro-primary-nav"><a href="#surface">Current</a><a href="#what-changed">What Changed</a><a href="#btc-phi-cycle-hub">BTC</a><a href="#market">Market</a><a href="#trust-access">Trust &amp; Access</a></nav>
<section id="surface" data-editorial-chapter="orientation"><a href="https://www.bhrigu.io/crypto-astro/btc">Ask one BTC field question</a></section>
<section id="what-changed" data-editorial-chapter="what-changed">Previous verified snapshot is not yet available.</section>
<section id="btc-phi-cycle-hub" data-editorial-chapter="btc-field"><a href="https://www.bhrigu.io/crypto-astro/btc">Ask one BTC field question</a></section>
<section id="market" data-editorial-chapter="wider-market">{values} {filler}</section>
<section id="trust-access" data-editorial-chapter="trust-access"><a href="#proof">View source proof</a><a href="https://www.bhrigu.io/access">Research access</a>Research context only. No trading signal, forecast, price target, or investment advice.</section>
<details id="proof"><summary>Proof</summary></details>
</main>'''

    def test_accepts_canonical_shape(self) -> None:
        report = verify(self.sample())
        self.assertEqual(report["status"], "PASS", report["failures"])

    def test_accepts_separate_brand_anchor(self) -> None:
        value = self.sample().replace(
            '<nav class="crypto-astro-primary-nav">',
            '<nav class="crypto-astro-primary-nav"><a class="crypto-astro-primary-nav__brand" href="#surface">Crypto-Astro</a>',
            1,
        )
        report = verify(value)
        self.assertEqual(report["status"], "PASS", report["failures"])

    def test_rejects_duplicate_chapter_id(self) -> None:
        value = self.sample().replace(
            '<details id="proof">',
            '<span id="market"></span><details id="proof">',
            1,
        )
        report = verify(value)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(item.startswith("duplicate_ids") for item in report["failures"]))

    def test_rejects_competing_primary_cta(self) -> None:
        value = self.sample().replace("</section>\n<section id=\"what-changed\"", '<a href="https://www.bhrigu.io/crypto-astro/btc">Ask one BTC field question</a></section>\n<section id="what-changed"', 1)
        report = verify(value)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("primary_cta_two_consistent_placements", report["failures"])

    def test_rejects_old_internal_first_level_copy(self) -> None:
        report = verify(self.sample().replace("context", "A/E · prepared field membranes", 1))
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(item.startswith("forbidden_first_level") for item in report["failures"]))

    def test_rejects_missing_previous_snapshot_fallback(self) -> None:
        report = verify(self.sample().replace("Previous verified snapshot is not yet available.", ""))
        self.assertIn("what_changed_fail_closed_fallback", report["failures"])


if __name__ == "__main__":
    unittest.main()
