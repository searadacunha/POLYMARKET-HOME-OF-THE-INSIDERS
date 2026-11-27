"""The wallet ledger on hand-computed cases, and its accounting identity on random histories."""
import random
import unittest
from fractions import Fraction

from phi_forensics import ledger

C1, C2 = "0x" + "c1" * 32, "0x" + "c2" * 32
YES, NO = "111", "222"


def row(ts, kind, size=0.0, cash=0.0, side="", token="", index=None, condition=C1, outcome=None):
    return {"timestamp": ts, "type": kind, "side": side, "condition_id": condition, "token_id": token, "size": size, "usdc_size": cash,
            "outcome_index": index, "outcome": outcome or {0: "Yes", 1: "No"}.get(index), "title": "Will X happen?", "slug": "will-x"}


def buy(ts, token, size, cash, **kw):
    return row(ts, "TRADE", size, cash, "BUY", token, 0 if token == YES else 1, **kw)


def sell(ts, token, size, cash, **kw):
    return row(ts, "TRADE", size, cash, "SELL", token, 0 if token == YES else 1, **kw)


def paid(yes, no=None):
    return {C1: {"prices": {0: yes, 1: 1 - yes if no is None else no}, "source": "RESOLUTION_PAYOUT"}}


def one(rows, prices=None, **kw):
    built = ledger.build(rows, prices, **kw)
    return built["markets"][0], built["totals"]


class Trades(unittest.TestCase):
    def test_a_winning_position_held_to_resolution(self):
        market, totals = one([buy(1, YES, 100, 40)], paid(1))
        self.assertEqual((market["cash"], market["inventory_value"], market["net"]), ("-40.000000", "100.000000", "60.000000"))
        self.assertEqual((market["realised"], market["unrealised"], market["status"], market["valuation"]),
                         ("0.000000", "60.000000", "INVENTORY_VALUED", "RESOLUTION_PAYOUT"))
        self.assertEqual((totals["net_trading_result"], totals["net_is_complete"]), ("60.000000", True))

    def test_a_losing_position_is_worth_nothing(self):
        market, _ = one([buy(1, YES, 100, 40)], paid(0))
        self.assertEqual((market["net"], market["unrealised"]), ("-40.000000", "-40.000000"))

    def test_selling_realises_at_average_cost(self):
        market, _ = one([buy(1, YES, 100, 40), buy(2, YES, 100, 60), sell(3, YES, 50, 35)], paid(1))
        self.assertEqual(market["realised"], "10.000000")       # 35 received for 50 shares that cost 0.50 each
        self.assertEqual(market["unrealised"], "75.000000")     # 150 shares worth 150, cost 75
        self.assertEqual(market["net"], "85.000000")
        self.assertEqual(market["shares"][0]["signed_shares"], "150.000000")

    def test_a_closed_round_trip_is_flat_and_needs_no_price(self):
        market, totals = one([buy(1, YES, 100, 40), sell(2, YES, 100, 55)])
        self.assertEqual((market["status"], market["net"], market["realised"], market["shares"]), ("FLAT", "15.000000", "15.000000", []))
        self.assertEqual(totals["net_trading_result"], "15.000000")

    def test_redeem_settles_everything_even_when_api_sizes_are_gross_of_fees(self):
        # Bought 100 on paper, 98.5 after a fee taken in shares: the redemption pays 98.5 and the position is closed.
        market, _ = one([buy(1, YES, 100, 40), row(9, "REDEEM", 98.5, 98.5, token=YES, index=0)])
        self.assertEqual((market["status"], market["cash"], market["realised"], market["net"]), ("FLAT", "58.500000", "58.500000", "58.500000"))

    def test_a_losing_redeem_pays_nothing_and_closes_the_position(self):
        market, _ = one([buy(1, NO, 10, 6), row(9, "REDEEM", 0, 0, token=NO, index=1)])
        self.assertEqual((market["status"], market["net"]), ("FLAT", "-6.000000"))

    def test_an_open_position_without_a_price_is_not_valued_and_the_total_says_so(self):
        market, totals = one([buy(1, YES, 100, 40)])
        self.assertEqual((market["status"], market["net"], market["inventory_value"], market["valuation"]), ("INVENTORY_NOT_VALUED", None, None, None))
        self.assertEqual((totals["net_trading_result"], totals["net_is_complete"], totals["markets_not_valued"]), (None, False, 1))
        self.assertEqual(totals["trading_cash"], "-40.000000")

    def test_a_mark_values_an_open_position(self):
        market, _ = one([buy(1, YES, 100, 40)], {C1: {"prices": {0: Fraction(55, 100)}, "source": "MARK 2026-11-27T08:00:00Z"}})
        self.assertEqual((market["unrealised"], market["valuation"]), ("15.000000", "MARK 2026-11-27T08:00:00Z"))

    def test_short_against_nothing_is_kept_signed(self):
        market, _ = one([sell(1, YES, 10, 7), buy(2, YES, 4, 2)], paid(0))
        self.assertEqual(market["shares"][0]["signed_shares"], "-6.000000")
        self.assertEqual((market["realised"], market["net"]), ("0.800000", "5.000000"))  # covered 4 at 0.50 after selling at 0.70

    def test_a_trade_that_crosses_zero_closes_then_opens(self):
        market, _ = one([buy(1, YES, 10, 4), sell(2, YES, 15, 9)], paid(1))
        self.assertEqual(market["realised"], "2.000000")        # 10 sold at 0.60 against 0.40
        self.assertEqual(market["shares"][0]["signed_shares"], "-5.000000")
        self.assertEqual(market["net"], "0.000000")             # +5 cash, owes 5 shares that paid 1


class SetsAndConversions(unittest.TestCase):
    def test_a_split_and_a_merge_are_neutral(self):
        market, _ = one([row(1, "SPLIT", 50, 50), row(2, "MERGE", 50, 50)])
        self.assertEqual((market["status"], market["net"], market["cash"], market["complete_sets"]), ("FLAT", "0.000000", "0.000000", "0.000000"))

    def test_selling_one_side_of_a_split_leaves_the_other(self):
        rows = [row(1, "SPLIT", 100, 100), sell(2, YES, 100, 30)]
        for payout, net in ((1, "-70.000000"), (0, "30.000000")):
            market, _ = one(rows, paid(payout))
            self.assertEqual(market["net"], net)
            self.assertEqual((market["shares"][0]["signed_shares"], market["shares"][0]["held_with_sets"]), ("-100.000000", "0.000000"))
            self.assertEqual(market["complete_sets"], "100.000000")

    def test_a_set_is_worth_one_whatever_the_outcome_and_needs_no_price(self):
        market, totals = one([row(1, "SPLIT", 100, 100)])
        self.assertEqual((market["inventory_value"], market["net"], market["status"]), ("100.000000", "0.000000", "INVENTORY_VALUED"))
        self.assertTrue(totals["net_is_complete"])

    def test_merging_both_sides_bought_apart_realises_the_arbitrage(self):
        market, _ = one([buy(1, YES, 10, 4), buy(2, NO, 10, 5), row(3, "MERGE", 10, 10)])
        self.assertEqual((market["status"], market["realised"], market["net"], market["flags"]), ("FLAT", "1.000000", "1.000000", []))

    def test_a_merge_of_shares_the_rows_never_showed_is_flagged_and_still_balances(self):
        market, _ = one([buy(1, YES, 10, 4), row(3, "MERGE", 10, 10)], paid(1))
        self.assertEqual(market["flags"], ["MERGE_OF_SHARES_NOT_SEEN_IN_ROWS"])
        self.assertEqual(market["net"], "6.000000")

    def test_a_conversion_is_flagged_and_its_cash_counted(self):
        market, _ = one([buy(1, NO, 10, 6), row(2, "CONVERSION", 10, 3)], paid(0))
        self.assertEqual(market["flags"], ["CONVERSION_INVENTORY_NOT_RECONSTRUCTED"])
        self.assertEqual(market["cash"], "-3.000000")

    def test_rewards_are_income_not_trading(self):
        built = ledger.build([buy(1, YES, 10, 4), sell(2, YES, 10, 5), row(3, "MAKER_REBATE", 1.25, 1.25, condition=""), row(4, "REWARD", 2, 2, condition="")])
        self.assertEqual(built["totals"]["other_income"], {"MAKER_REBATE": "1.250000", "REWARD": "2.000000"})
        self.assertEqual((built["totals"]["net_trading_result"], built["totals"]["markets"]), ("1.000000", 1))

    def test_an_unknown_row_type_is_counted_never_dropped_in_silence(self):
        built = ledger.build([buy(1, YES, 10, 4), row(2, "AIRDROP", 5, 5), row(3, "TRADE", 1, 1, side="HOLD", token=YES)])
        self.assertEqual(built["unknown_row_types"], {"AIRDROP": 1})
        self.assertEqual(built["markets"][0]["flags"], ["TRADE_ROW_WITHOUT_SIDE_OR_TOKEN"])
        self.assertEqual(built["markets"][0]["cash"], "-4.000000")


def tx(n):
    return "0x" + f"{n:064x}"


def on(n, r):
    return {**r, "transaction_hash": tx(n)}


class ChainAmounts(unittest.TestCase):
    """What the repository measured on the 2026 fee schedules: the API shows gross sizes and gross proceeds."""

    def test_deltas_net_what_the_wallet_received_and_sent(self):
        deltas = ledger.chain_deltas(
            [{"tx": tx(1).upper().replace("0X", "0x"), "amount_raw": 5}, {"tx": tx(2), "amount_raw": 9}], [{"tx": tx(1), "amount_raw": 2_001_000}],
            [{"tx": tx(1), "token_id": YES, "amount_raw": 7_735_360}, {"tx": tx(3), "token_id": NO, "amount_raw": 4}],
            [{"tx": tx(3), "token_id": NO, "amount_raw": 4}])
        self.assertEqual((deltas[tx(1)]["cash"], dict(deltas[tx(1)]["tokens"])), (-2_000_995, {YES: 7_735_360}))
        self.assertEqual((deltas[tx(2)]["cash"], dict(deltas[tx(3)]["tokens"])), (9, {NO: 0}))

    def test_a_fee_taken_in_shares_and_a_fee_taken_on_proceeds_are_both_restored(self):
        rows = [on(1, buy(1, YES, 8.7, 2.001)), on(2, sell(2, YES, 7.73536, 2.165901))]
        deltas = {tx(1): {"cash": -2_001_000, "tokens": {YES: 7_735_360}}, tx(2): {"cash": 2_050_000, "tokens": {YES: -7_735_360}}}
        api_only, _ = one(rows)
        self.assertEqual((api_only["status"], api_only["shares"][0]["signed_shares"]), ("INVENTORY_NOT_VALUED", "0.964640"))
        built = ledger.build(rows, chain=deltas)
        market = built["markets"][0]
        self.assertEqual((market["status"], market["net"], market["cash"]), ("FLAT", "0.049000", "0.049000"))
        self.assertEqual(built["amounts"], "CHAIN")
        self.assertEqual((built["chain"]["cash_rows_corrected"], built["chain"]["share_rows_corrected"], built["chain"]["cash_correction_abs"]),
                         (1, 1, "0.115901"))
        self.assertEqual(ledger.build(rows)["amounts"], "API")

    def test_several_fills_of_one_transaction_share_the_chain_total_exactly(self):
        rows = [on(1, buy(1, YES, 3, 1.0)), on(1, buy(1, YES, 6, 2.0)), on(1, buy(1, YES, 1, 0.3))]
        built = ledger.build(rows, chain={tx(1): {"cash": -3_300_001, "tokens": {YES: 9_500_000}}})
        market = built["markets"][0]
        self.assertEqual((market["cash"], market["shares"][0]["signed_shares"]), ("-3.300001", "9.500000"))

    def test_rows_the_chain_does_not_show_keep_their_api_amounts_and_are_counted(self):
        built = ledger.build([on(1, buy(1, YES, 10, 4)), on(2, sell(2, YES, 10, 5))], chain={tx(1): {"cash": -4_000_000, "tokens": {YES: 10_000_000}}})
        self.assertEqual((built["chain"]["rows_without_chain_record"], built["chain"]["rows_checked"], built["markets"][0]["net"]), (1, 2, "1.000000"))

    def test_cash_moving_the_wrong_way_is_reported_not_applied(self):
        built = ledger.build([on(1, buy(1, YES, 10, 4))], chain={tx(1): {"cash": 3_000_000, "tokens": {YES: 10_000_000}}})
        self.assertEqual((built["chain"]["transactions_cash_direction_differs"], built["markets"][0]["cash"]), (1, "-4.000000"))
        mixed = ledger.build([on(1, buy(1, YES, 10, 4)), on(1, sell(1, NO, 5, 2))], chain={tx(1): {"cash": -1_900_000, "tokens": {}}})
        self.assertEqual((mixed["chain"]["transactions_with_mixed_directions"], mixed["markets"][0]["cash"]), (1, "-2.000000"))

    def test_redemptions_and_splits_take_their_cash_from_the_chain(self):
        rows = [on(1, row(1, "SPLIT", 10, 10)), on(2, sell(2, YES, 10, 3)), on(3, row(3, "REDEEM", 10, 10, token=NO, index=1))]
        deltas = {tx(1): {"cash": -10_000_000, "tokens": {YES: 10_000_000, NO: 10_000_000}}, tx(2): {"cash": 2_900_000, "tokens": {YES: -10_000_000}},
                  tx(3): {"cash": 9_990_000, "tokens": {NO: -10_000_000}}, tx(9): {"cash": 50_000_000, "tokens": {}}, tx(8): {"cash": 0, "tokens": {YES: 5}}}
        built = ledger.build(rows, chain=deltas)
        self.assertEqual((built["markets"][0]["net"], built["markets"][0]["status"]), ("2.890000", "FLAT"))
        self.assertEqual((built["chain"]["chain_transactions_without_api_row"], built["chain"]["of_which_moving_outcome_tokens"]), (2, 1))

    def test_a_conversion_is_placed_market_by_market_from_the_chain(self):
        # 100 NO of market C1 bought for 90, converted into 100 YES of market C2 plus nothing in cash; C2 then wins.
        c2_yes = "333"
        rows = [on(1, buy(1, NO, 100, 90)), on(2, row(2, "CONVERSION", 100, 0, condition="0x" + "ee" * 32))]
        deltas = {tx(1): {"cash": -90_000_000, "tokens": {NO: 100_000_000}}, tx(2): {"cash": 0, "tokens": {NO: -100_000_000, c2_yes: 100_000_000}}}
        homes = {NO: {"condition_id": C1, "outcome_index": 1, "outcome": "No", "title": "Will X happen?"},
                 c2_yes: {"condition_id": C2, "outcome_index": 0, "outcome": "Yes", "title": "Will Y happen?"}}
        prices = {C1: {"prices": {0: 0, 1: 1}, "source": "RESOLUTION_PAYOUT"}, C2: {"prices": {0: 1, 1: 0}, "source": "RESOLUTION_PAYOUT"}}
        built = ledger.build(rows, prices, chain=deltas, token_markets=homes)
        by = {m["condition_id"]: m for m in built["markets"]}
        self.assertEqual((by[C1]["status"], by[C1]["shares"], by[C1]["net"], by[C1]["flags"]), ("FLAT", [], "-90.000000", ["CONVERSION"]))
        self.assertEqual((by[C2]["shares"][0]["signed_shares"], by[C2]["net"], by[C2]["rows"]), ("100.000000", "100.000000", {"CONVERT_IN": 1}))
        self.assertEqual((by[C2]["realised"], by[C2]["unrealised"]), ("90.000000", "10.000000"))   # arrives carrying the 90 paid
        self.assertEqual(built["totals"]["net_trading_result"], "10.000000")
        self.assertEqual((built["chain"]["conversions_placed"], built["chain"]["conversion_tokens_not_in_catalogue"]), (1, 0))
        self.assertEqual(by["0x" + "ee" * 32]["flags"], ["CONVERSION"])

    def test_a_conversion_that_pays_cash_passes_on_what_is_left_of_the_cost(self):
        rows = [on(1, buy(1, NO, 100, 90)), on(2, row(2, "CONVERSION", 100, 30, condition="0x" + "ee" * 32))]
        deltas = {tx(1): {"cash": -90_000_000, "tokens": {NO: 100_000_000}}, tx(2): {"cash": 30_000_000, "tokens": {NO: -100_000_000, "333": 60_000_000, "444": 40_000_000}}}
        homes = {NO: {"condition_id": C1, "outcome_index": 1}, "333": {"condition_id": C2, "outcome_index": 0}, "444": {"condition_id": C2, "outcome_index": 1}}
        built = ledger.build(rows, {C2: {"prices": {0: 1, 1: 0}, "source": "RESOLUTION_PAYOUT"}}, chain=deltas, token_markets=homes)
        self.assertEqual(built["totals"]["net_trading_result"], "0.000000")          # paid 90, got 30 in cash and 60 winning shares
        self.assertEqual(sum(float(m["realised"]) + float(m["unrealised"] or 0) for m in built["markets"]), 0.0)

    def test_an_outcome_the_catalogue_does_not_list_gets_its_own_market_and_no_value_by_default(self):
        event = "0x" + "ee" * 32
        rows = [on(1, buy(1, NO, 100, 90)), on(2, row(2, "CONVERSION", 100, 0, condition=event))]
        deltas = {tx(1): {"cash": -90_000_000, "tokens": {NO: 100_000_000}}, tx(2): {"cash": 0, "tokens": {NO: -100_000_000, "333": 100_000_000}}}
        homes = {NO: {"condition_id": C1, "outcome_index": 1}}
        built = ledger.build(rows, chain=deltas, token_markets=homes)
        spare = next(m for m in built["markets"] if m["condition_id"] == ledger.UNLISTED + "333")
        self.assertEqual((spare["status"], spare["flags"], spare["shares"][0]["signed_shares"]),
                         ("INVENTORY_NOT_VALUED", ["CONVERSION", "OUTCOME_NOT_IN_CATALOGUE"], "100.000000"))
        self.assertIn(event, spare["title"])
        self.assertEqual((built["chain"]["conversions_placed"], built["chain"]["conversion_tokens_not_in_catalogue"]), (1, 1))
        self.assertIsNone(built["totals"]["net_trading_result"])
        settled = ledger.build(rows, {ledger.UNLISTED + "333": {"prices": {0: 0}, "source": "NEG_RISK_EVENT_SETTLED_ON_ANOTHER_OUTCOME"}},
                               chain=deltas, token_markets=homes)
        self.assertEqual(settled["totals"]["net_trading_result"], "-90.000000")

    def test_without_the_token_map_a_conversion_stays_flagged_as_not_reconstructed(self):
        rows = [on(1, buy(1, NO, 100, 90)), on(2, row(2, "CONVERSION", 100, 0, condition="0x" + "ee" * 32))]
        deltas = {tx(1): {"cash": -90_000_000, "tokens": {NO: 100_000_000}}, tx(2): {"cash": 0, "tokens": {NO: -100_000_000, "333": 100_000_000}}}
        built = ledger.build(rows, chain=deltas)
        self.assertEqual(built["chain"]["conversions_placed"], 0)
        self.assertIn("CONVERSION_INVENTORY_NOT_RECONSTRUCTED", {f for m in built["markets"] for f in m["flags"]})

    def test_a_market_named_unreliable_is_not_valued_and_the_total_is_incomplete(self):
        built = ledger.build([buy(1, NO, 100, 90), buy(2, YES, 5, 1, condition=C2), sell(3, YES, 5, 2, condition=C2)],
                             {C1: {"prices": {0: 0, 1: 1}, "source": "RESOLUTION_PAYOUT"}},
                             unreliable={C1: "IN_A_CONVERTED_NEG_RISK_EVENT", C2: "IN_A_CONVERTED_NEG_RISK_EVENT"})
        by = {m["condition_id"]: m for m in built["markets"]}
        self.assertEqual((by[C1]["status"], by[C1]["net"], by[C1]["flags"]), ("INVENTORY_NOT_VALUED", None, ["IN_A_CONVERTED_NEG_RISK_EVENT"]))
        self.assertEqual((by[C2]["status"], by[C2]["flags"]), ("FLAT", []))            # nothing held there: nothing in doubt
        self.assertEqual((built["totals"]["net_trading_result"], built["totals"]["markets_not_valued"]), (None, 1))

    def test_allocation_is_exact(self):
        rng = random.Random(3)
        for _ in range(300):
            weights = [rng.randrange(0, 10_000) for _ in range(rng.randrange(1, 9))]
            total = rng.randrange(0, 10 ** 9)
            parts = ledger._allocate(total, weights)
            self.assertEqual(sum(parts), total)
            self.assertTrue(all(part >= 0 for part in parts))
        self.assertEqual(ledger._allocate(10, [0, 0]), [5, 5])
        self.assertEqual(ledger._allocate(7, [1, 1, 1]), [3, 2, 2])


class PointInTime(unittest.TestCase):
    ROWS = [buy(10, YES, 100, 40), buy(20, YES, 100, 60), sell(30, YES, 200, 150), buy(40, NO, 5, 1, condition=C2)]

    def test_the_position_as_it_was(self):
        early = ledger.build(self.ROWS, as_of=20)
        self.assertEqual((early["rows_counted"], early["markets"][0]["shares"][0]["signed_shares"], len(early["markets"])), (2, "200.000000", 1))
        self.assertEqual(ledger.build(self.ROWS, as_of=9)["markets"], [])
        self.assertEqual(ledger.build(self.ROWS, as_of=30)["markets"][0]["status"], "FLAT")
        self.assertEqual(len(ledger.build(self.ROWS)["markets"]), 2)

    def test_rows_are_applied_in_time_order_whatever_the_input_order(self):
        self.assertEqual(ledger.build(self.ROWS), ledger.build(list(reversed(self.ROWS))))


class Identity(unittest.TestCase):
    def test_realised_plus_unrealised_equals_cash_plus_inventory_on_random_histories(self):
        rng = random.Random(20261127)
        for trial in range(300):
            rows, t = [], 0
            for _ in range(rng.randrange(1, 40)):
                t += rng.randrange(1, 100)
                kind = rng.choice(["BUY", "BUY", "SELL", "SELL", "SPLIT", "MERGE", "REDEEM"])
                size = rng.randrange(1, 5_000_000) / 1_000_000
                if kind in ("BUY", "SELL"):
                    token = rng.choice([YES, NO])
                    maker = buy if kind == "BUY" else sell
                    rows.append(maker(t, token, size, round(size * rng.randrange(1, 99) / 100, 6)))
                elif kind == "REDEEM":
                    rows.append(row(t, "REDEEM", size, round(size * rng.choice([0, 1]), 6), token=YES, index=0))
                else:
                    rows.append(row(t, kind, size, size))
            yes = rng.choice([0, 1, Fraction(37, 100)])
            market, totals = one(rows, paid(yes))      # summary() raises if the identity fails
            cash = sum((r["usdc_size"] if (r["side"] == "SELL" or r["type"] in ("MERGE", "REDEEM")) else -r["usdc_size"]) for r in rows)
            self.assertAlmostEqual(float(market["cash"]), cash, places=5, msg=trial)
            self.assertAlmostEqual(float(market["realised"]) + float(market["unrealised"]), float(market["net"]), places=5, msg=trial)

    def test_amounts_are_exact_strings(self):
        self.assertEqual(ledger.amount(1), "0.000001")
        self.assertEqual(ledger.amount(-1), "-0.000001")
        self.assertEqual(ledger.amount(0), "0.000000")
        self.assertEqual(ledger.amount(Fraction(-1, 3)), "0.000000")
        self.assertEqual(ledger.amount(Fraction(5, 2)), "0.000003")
        self.assertEqual(ledger.amount(80_439_745_603), "80439.745603")
        self.assertEqual(ledger.units(80439.745603), 80_439_745_603)
        self.assertEqual(ledger.units("0.1"), 100_000)


if __name__ == "__main__":
    unittest.main()
