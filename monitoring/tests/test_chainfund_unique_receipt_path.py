"""Receipt-join ambiguity tests: an amount match is not proof of funds flow.

All inputs are synthetic Transfer logs. No network and no wallet secrets.
Run: cd monitoring && python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_engine import chainfund as c, receipt_link_guard as guard

W = "0x" + "11" * 20
A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
R = "0x" + "cc" * 20
ONRAMP = "0x93070a847efef7f70739046a929d47a521f5b8ee"


class ReceiptPathTests(unittest.TestCase):
    def test_normal_one_hop_remains_identifiable(self):
        logs = [c._log(c.USDC_E, A, R, 12, 0), c._log(c.USDC_E, R, W, 12, 1)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["via"], got["path"]), (A, "direct", [R]))

    def test_an_after_the_fact_transfer_cannot_be_upstream(self):
        logs = [c._log(c.USDC_E, R, W, 12, 0), c._log(c.USDC_E, A, R, 12, 1)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["path"]), (R, []))

    def test_equal_amount_but_different_tokens_is_not_one_transfer(self):
        logs = [c._log(c.USDC, A, R, 12, 0), c._log(c.USDC_E, R, W, 12, 1)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["token"], got["path"]), (R, c.USDC_E, []))

    def test_two_indistinguishable_upstream_sources_are_not_arbitrarily_selected(self):
        logs = [c._log(c.USDC_E, A, R, 12, 0), c._log(c.USDC_E, B, R, 12, 1),
                c._log(c.USDC_E, R, W, 12, 2)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["path"]), (R, []))
        self.assertEqual(got["unresolved"], "ambiguous_upstream_equal_value_candidates")

    def test_only_one_source_before_credit_is_usable(self):
        logs = [c._log(c.USDC_E, A, R, 12, 0), c._log(c.USDC_E, R, W, 12, 1),
                c._log(c.USDC_E, B, R, 12, 2)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["path"]), (A, [R]))

    def test_wrapped_payer_requires_unique_earlier_collateral_inflow(self):
        logs = [c._log(c.USDC, A, ONRAMP, 9, 0), c._log(c.USDC, B, ONRAMP, 9, 1),
                c._log(c.PUSD, c.ZERO, W, 9, 2)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["via"], got["unresolved"]),
                         (None, "wrapped_ambiguous", "multiple_equal_value_sources"))

    def test_later_collateral_inflow_cannot_prove_prior_mint(self):
        logs = [c._log(c.PUSD, c.ZERO, W, 9, 0), c._log(c.USDC, A, ONRAMP, 9, 1)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["via"]), (None, "wrapped_unmatched"))

    def test_unique_wrapped_payin_is_kept(self):
        logs = [c._log(c.USDC, A, ONRAMP, 9, 0), c._log(c.PUSD, c.ZERO, W, 9, 1)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["via"], got["token"], got["path"]),
                         (A, "wrapped", c.USDC, []))

    def test_tied_largest_credits_do_not_choose_first_sender(self):
        logs = [c._log(c.USDC_E, A, W, 9, 0), c._log(c.USDC_E, B, W, 9, 1)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["via"], got["value"]),
                         (None, "ambiguous_credit", 9))

    def test_smaller_credit_does_not_override_unique_largest(self):
        logs = [c._log(c.USDC_E, B, W, 8, 0), c._log(c.USDC_E, A, W, 9, 1)]
        got = guard.payer_of_deposit(logs, W)
        self.assertEqual((got["payer"], got["value"]), (A, 9))

    def test_missing_log_index_never_generates_a_secondary_payer(self):
        a = c._log(c.USDC_E, A, R, 9, 0)
        b = c._log(c.USDC_E, R, W, 9, 1)
        a.pop("logIndex")
        got = guard.payer_of_deposit([a, b], W)
        self.assertEqual((got["payer"], got["path"]), (R, []))

    def test_removed_transfers_do_not_enter_a_join(self):
        a = c._log(c.USDC_E, A, R, 9, 0)
        a["removed"] = True
        got = guard.payer_of_deposit([a, c._log(c.USDC_E, R, W, 9, 1)], W)
        self.assertEqual((got["payer"], got["path"]), (R, []))


if __name__ == "__main__":
    unittest.main()
