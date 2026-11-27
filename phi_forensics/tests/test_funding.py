"""Funding and withdrawal reading against a fake chain: what is a deposit, where a trace stops and why."""
import unittest

from monitoring.phi_monitor import chain
from phi_forensics import funding

WALLET = "0x" + "aa" * 20
EXCHANGE = "0xe111180000d2663c0091e4f400237545b87b996b"
RELAY = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
P1, P2, P3, BIG, CODE = ("0x" + c * 40 for c in "12345")


def move(n, sender, receiver, amount, block=None):
    return {"tx": "0x" + f"{n:064x}", "log_index": n, "block": block or 1000 + n, "ts": 1_700_000_000 + n * 60, "from": sender, "to": receiver,
            "token": chain.USDC_E, "amount_raw": amount}


class Chain:
    def __init__(self, rows, head=10_000_000):
        self.rows, self.asked, self._head = rows, [], head

    def transfers(self, address, direction, from_block=0, to_block=None, tokens=None):
        self.asked.append((address, direction, from_block, to_block))
        key = "to" if direction == "in" else "from"
        rows = [r for r in self.rows if r[key] == address and from_block <= r["block"] <= (to_block if to_block is not None else 10 ** 12)]
        return {"rows": sorted(rows, key=lambda r: (r["block"], r["log_index"])), "from_block": from_block, "to_block": to_block, "calls": 1}

    def head(self):
        return self._head


KINDS = {P1: "key", P2: "key", P3: "key", BIG: "high_volume_key", CODE: "contract"}


def kinds(address, block):
    return {"address": address, "kind": KINDS.get(address, "unknown"), "nonce": 5, **({} if address in KINDS else {"unresolved": "historical_state_unavailable"})}


class CashFlows(unittest.TestCase):
    def test_deposits_and_withdrawals_exclude_trading_legs_and_protocol_contracts(self):
        rows = [move(1, P1, WALLET, 5_000_000_000), move(2, WALLET, EXCHANGE, 40_000_000), move(3, P2, WALLET, 7_000_000),
                move(4, WALLET, RELAY, 4_900_000_000), move(5, "0x" + "0" * 40, WALLET, 9), move(6, WALLET, WALLET, 3)]
        got = funding.cash_flows(Chain(rows), WALLET.upper().replace("0X", "0x"), trading_txs=[rows[2]["tx"].upper().replace("0X", "0x")], kind_reader=kinds)
        self.assertEqual([(d["counterparty"], d["amount"], d["counterparty_kind"]) for d in got["deposits"]], [(P1, "5000.000000", "key")])
        self.assertEqual([(w["counterparty"], w["counterparty_kind"], w["counterparty_label"]) for w in got["withdrawals"]],
                         [(RELAY, "labelled_service", "Relay solver")])
        self.assertEqual(got["trading_legs_excluded"], 5)       # exchange leg, trade transaction, mint, and the self transfer seen twice
        self.assertEqual(got["totals"], {"deposited": {chain.USDC_E: "5000.000000"}, "withdrawn": {chain.USDC_E: "4900.000000"}})
        self.assertEqual(got["first_deposit"]["tx"], rows[0]["tx"])
        self.assertEqual(got["scan"]["calls"], 2)

    def test_changing_one_stablecoin_for_another_is_neither_a_deposit_nor_a_withdrawal(self):
        swap_out = {**move(7, WALLET, CODE, 121_109_322_288), "token": chain.USDC}
        swap_in = {**move(7, CODE, WALLET, 121_086_855_280), "log_index": 8}
        got = funding.cash_flows(Chain([move(1, P1, WALLET, 121_109_322_288), swap_out, swap_in, move(9, WALLET, P2, 168_236_525_569)]), WALLET, kind_reader=kinds)
        self.assertEqual(([d["counterparty"] for d in got["deposits"]], [w["counterparty"] for w in got["withdrawals"]]), ([P1], [P2]))
        self.assertEqual((got["collateral_swap_legs_excluded"], got["trading_legs_excluded"]), (2, 0))
        self.assertEqual(got["net_collateral_moved_raw"], 121_109_322_288 + 121_086_855_280 - 121_109_322_288 - 168_236_525_569)

    def test_a_counterparty_is_classified_at_the_block_of_its_first_payment(self):
        asked = []

        def reader(address, block):
            asked.append((address, block))
            return {"address": address, "kind": "key", "nonce": 1}

        funding.cash_flows(Chain([move(1, P1, WALLET, 5, block=700), move(2, P1, WALLET, 6, block=900)]), WALLET, kind_reader=reader)
        self.assertEqual(asked, [(P1, 700)])

    def test_an_address_whose_past_state_cannot_be_read_stays_unknown(self):
        got = funding.cash_flows(Chain([move(1, "0x" + "9" * 40, WALLET, 5)]), WALLET, kind_reader=kinds)
        self.assertEqual(got["deposits"][0]["counterparty_kind"], "unknown")
        self.assertEqual(got["counterparties"]["0x" + "9" * 40]["unresolved"], "historical_state_unavailable")

    def test_an_empty_wallet(self):
        got = funding.cash_flows(Chain([]), WALLET, kind_reader=kinds)
        self.assertEqual((got["deposits"], got["withdrawals"], got["first_deposit"], got["totals"]), ([], [], None, {"deposited": {}, "withdrawn": {}}))


class Trace(unittest.TestCase):
    ROWS = [move(10, P1, WALLET, 900_000_000, block=5000), move(8, P2, P1, 950_000_000, block=4000), move(7, BIG, P2, 990_000_000, block=3000),
            move(9, CODE, P1, 5_000_000, block=4500), move(6, P3, P1, 500_000, block=4200), move(5, P3, P2, 77_000_000, block=100)]

    def test_upstream_stops_at_services_and_at_the_hop_limit(self):
        got = funding.trace(Chain(self.ROWS), WALLET, "upstream", at_block=6000, hops=3, look_blocks=3000, kind_reader=kinds)
        self.assertEqual([(e["from"], e["to"], e["hop"]) for e in got["edges"]],
                         [(P1, WALLET, 1), (P2, P1, 2), (CODE, P1, 2), (BIG, P2, 3)])
        self.assertEqual(sorted((s["address"], s["reason"]) for s in got["stops"]), [(BIG, "high_volume_key"), (CODE, "contract")])
        self.assertEqual((got["nodes"][P1]["kind"], got["nodes"][BIG]["kind"]), ("key", "high_volume_key"))
        self.assertIn("does not show", got["limits"]["reading"])

    def test_small_payments_and_payments_outside_the_window_are_not_followed(self):
        got = funding.trace(Chain(self.ROWS), WALLET, "upstream", at_block=6000, hops=3, look_blocks=3000, kind_reader=kinds)
        self.assertNotIn(P3, got["nodes"])                      # 0.50 is under the floor; block 100 is before the window of P2

    def test_the_hop_limit_is_a_stated_stop(self):
        got = funding.trace(Chain(self.ROWS), WALLET, "upstream", at_block=6000, hops=1, look_blocks=3000, kind_reader=kinds)
        self.assertEqual(got["stops"], [{"address": P1, "reason": "hop limit", "hop": 1}])
        self.assertEqual(len(got["edges"]), 1)

    def test_branches_beyond_the_cap_are_counted(self):
        rows = [move(i, "0x" + f"{i:040x}", WALLET, 10_000_000 * i, block=100 + i) for i in range(1, 8)]
        got = funding.trace(Chain(rows), WALLET, "upstream", at_block=500, hops=1, branch=3, look_blocks=1000, kind_reader=lambda a, b: {"address": a, "kind": "key"})
        self.assertEqual(([e["amount"] for e in got["edges"]], got["payments_not_followed"]), (["70.000000", "60.000000", "50.000000"], 4))

    def test_downstream_follows_payees_forward_and_never_asks_past_the_head(self):
        rows = [move(1, WALLET, P1, 800_000_000, block=100), move(2, P1, RELAY, 799_000_000, block=150), move(3, P1, P2, 2_000_000, block=90)]
        fake = Chain(rows, head=160)
        got = funding.trace(fake, WALLET, "downstream", at_block=50, hops=2, look_blocks=1000, kind_reader=kinds)
        self.assertEqual([(e["from"], e["to"]) for e in got["edges"]], [(WALLET, P1), (P1, RELAY)])
        self.assertEqual(got["stops"], [{"address": RELAY, "reason": "Relay solver", "hop": 2}])
        self.assertEqual(fake.asked, [(WALLET, "out", 50, 160), (P1, "out", 100, 160)])

    def test_a_loop_is_walked_once(self):
        rows = [move(1, P1, WALLET, 5_000_000, block=100), move(2, WALLET, P1, 5_000_000, block=90), move(3, P1, P1, 5_000_000, block=80)]
        got = funding.trace(Chain(rows), WALLET, "upstream", at_block=200, hops=4, look_blocks=1000, kind_reader=kinds)
        self.assertEqual(list(got["nodes"]), [P1])

    def test_direction_is_checked(self):
        with self.assertRaises(ValueError):
            funding.trace(Chain([]), WALLET, "sideways", at_block=1)


class PassThrough(unittest.TestCase):
    def test_an_exact_amount_sent_on_within_a_day_is_reported(self):
        deposits = [move(1, P1, WALLET, 9_990_030_000), move(2, P2, WALLET, 5)]
        withdrawals = [move(30, WALLET, P3, 9_990_030_000), move(4000, WALLET, P3, 5)]
        got = funding.pass_throughs(deposits, withdrawals)
        self.assertEqual(got, [{"received": deposits[0]["tx"], "sent": withdrawals[0]["tx"], "amount": "9990.030000", "token": chain.USDC_E,
                                "seconds_between": 29 * 60, "from": P1, "to": P3}])

    def test_a_withdrawal_before_the_deposit_is_not_a_relay(self):
        self.assertEqual(funding.pass_throughs([move(9, P1, WALLET, 7)], [move(3, WALLET, P3, 7)]), [])


if __name__ == "__main__":
    unittest.main()
