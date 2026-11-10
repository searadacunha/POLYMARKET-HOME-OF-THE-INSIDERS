#!/usr/bin/env python3
"""Regression tests for numerical support in finding titles, using synthetic evidence."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_evidence as val  # noqa: E402


class NumericEvidenceTest(unittest.TestCase):
    def finding_errors(self, claim, source):
        with tempfile.TemporaryDirectory() as tmp:
            inv = Path(tmp)
            (inv / 'sources').mkdir()
            (inv / 'sources/proof.txt').write_text(source)
            (inv / 'FINDINGS.md').write_text(
                f'## F-001 | CONFIRMED | {claim}\n'
                '- Sources: sources/proof.txt\n- Method: synthetic check\n'
                '- Limits: numerical support only\n- Links: none\n')
            errors = []
            val.check_findings(inv, errors)
            return errors

    def test_larger_amount_cannot_support_a_suffix(self):
        self.assertTrue(self.finding_errors('Transfer: 1000.50 USDC', 'Transfer: 21000.50 USDC'))

    def test_fractional_amount_cannot_support_an_integer_prefix(self):
        self.assertTrue(self.finding_errors('Transfer: 1000 USDC', 'Transfer: 1000.50 USDC'))

    def test_extra_decimal_digits_cannot_support_a_rounded_claim(self):
        self.assertTrue(self.finding_errors('Transfer: 1000.50 USDC', 'Transfer: 1000.504 USDC'))

    def test_rounded_claim_has_to_be_documented_in_the_source(self):
        self.assertEqual(self.finding_errors('Transfer: 1000.50 USDC',
                                            'Raw: 1000.504 USDC; rounded to cents: 1000.50 USDC.'), [])

    def test_negative_source_cannot_support_positive_claim(self):
        self.assertTrue(self.finding_errors('PnL: 1000.50 USDC', 'PnL: -1000.50 USDC'))
        self.assertTrue(self.finding_errors('PnL: +$1000.50', 'PnL: -$1000.50'))

    def test_positive_source_cannot_support_negative_claim(self):
        self.assertTrue(self.finding_errors('PnL: -$1000.50', 'PnL: +$1000.50'))

    def test_matching_negative_amount_and_unicode_minus(self):
        self.assertEqual(self.finding_errors('PnL: -$1,000.50', 'PnL: −1 000,50.'), [])

    def test_grouping_and_exact_trailing_zeros_are_equivalent(self):
        for source in ('304 137,63', '304\u202f137,63', '304,137.63', '304137.6300'):
            with self.subTest(source=source):
                self.assertEqual(self.finding_errors('Transfer: $304,137.63', source), [])

    def test_terminal_punctuation_is_not_a_fraction(self):
        self.assertEqual(self.finding_errors('Transfer: 1000.50 USDC', 'Transfer: 1000.50.'), [])
        self.assertEqual(self.finding_errors('Transfer: 1000 USDC', '{"amount":1000,"count":2}'), [])

    def test_numeric_fragments_of_addresses_and_identifiers_are_not_evidence(self):
        for source in ('0x' + 'a' * 18 + '1000' + 'b' * 18, 'record_1000', '1000_record', 'v1000.50'):
            with self.subTest(source=source):
                self.assertFalse(val.number_in_text('1000', source))

    def test_display_magnitude_is_not_silently_discarded(self):
        self.assertEqual(self.finding_errors('Staked: $2.05M', 'Staked: 2.05M.'), [])
        self.assertEqual(self.finding_errors('Staked: $2.05M', 'Staked: 2050000.'), [])
        self.assertTrue(self.finding_errors('Staked: $2.05M', 'Staked: 2.05.'))

    def test_scientific_notation_is_read_as_one_complete_value(self):
        self.assertFalse(val.number_in_text('1000.50', '1000.50e2'))
        self.assertTrue(val.number_in_text('1000.50', '1.00050e3'))

    def test_number_in_text_rejects_several_requested_amounts(self):
        self.assertFalse(val.number_in_text('1000 and 2000', '1000 and 2000'))


if __name__ == '__main__':
    unittest.main()
