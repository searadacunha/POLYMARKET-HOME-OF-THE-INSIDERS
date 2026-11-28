"""Receipt checks against fake nodes, and fill checks against real archived OrderFilled logs."""
import json
import unittest
from pathlib import Path

from monitoring.phi_monitor import chain
from phi_forensics import evidence, sources

TX = "0x" + "7" * 64
A, B, C = "0x" + "a" * 40, "0x" + "b" * 40, "0x" + "c" * 40
N1, N2 = evidence.ENDPOINTS
FIXTURE = Path(__file__).resolve().parents[2] / "monitoring" / "fixtures" / "orderfilled_20261113.json"


def transfer(index, sender, recipient, amount, token=chain.USDC_E):
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    return {"address": token, "topics": [chain.TRANSFER, pad(sender), pad(recipient)], "data": hex(amount), "logIndex": hex(index)}


def receipt(logs, status="0x1", **extra):
    return {"blockNumber": hex(500), "blockHash": "0x" + "9" * 64, "status": status, "logs": logs, **extra}


class Nodes:
    """Each endpoint answers a receipt, None (unknown transaction) or an exception (unreachable)."""

    def __init__(self, first, second):
        self.answers = {N1: first, N2: second}

    def receipt(self, tx, endpoint):
        answer = self.answers[endpoint]
        if isinstance(answer, Exception):
            raise answer
        return answer

    def block_time(self, number):
        return 1_760_000_000


DOWN = sources.SourceError("transport failure")
PAID = receipt([transfer(4, A, B, 5_170_000_000), transfer(9, B, C, 1)])


class Transfers(unittest.TestCase):
    def check(self, nodes, **claim):
        return evidence.verify_transfer(nodes, TX, **claim)

    def test_confirmed_needs_two_agreeing_nodes_and_one_matching_log(self):
        got = self.check(Nodes(PAID, dict(PAID, effectiveGasPrice="0x1")), sender=A.upper().replace("0X", "0x"), recipient=B, amount_raw=5_170_000_000)
        self.assertEqual((got["verdict"], got["nodes_agreeing"], got["block"], got["time_utc"]), ("CONFIRMED", 2, 500, "2025-10-09T08:53:20Z"))
        self.assertEqual(got["matching_logs"], [{"token": chain.USDC_E, "from": A, "to": B, "amount": "5170000000", "log_index": 4}])
        self.assertEqual(got["claim"], {"from": A, "to": B, "amount": "5170000000"})
        self.assertEqual(len(got["receipt_sha256"]), 64)
        self.assertNotIn("receipt", json.dumps(got["nodes"]))

    def test_one_node_alone_is_not_a_confirmation(self):
        for other in (DOWN, None):
            got = self.check(Nodes(PAID, other), sender=A, recipient=B)
            self.assertEqual((got["verdict"], got["nodes_agreeing"]), ("SEEN_ON_ONE_NODE", 1))

    def test_a_single_unit_of_difference_is_not_the_claimed_transfer(self):
        got = self.check(Nodes(PAID, PAID), sender=A, recipient=B, amount_raw=5_170_000_001)
        self.assertEqual((got["verdict"], got["matching_logs"], got["transfers_in_receipt"]), ("NOT_IN_RECEIPT", [], 2))
        self.assertEqual(self.check(Nodes(PAID, PAID), sender=A, recipient=C)["verdict"], "NOT_IN_RECEIPT")
        self.assertEqual(self.check(Nodes(PAID, PAID), sender=A, token=chain.USDC)["verdict"], "NOT_IN_RECEIPT")

    def test_two_identical_transfers_need_a_log_index(self):
        twice = receipt([transfer(1, A, B, 700), transfer(2, A, B, 700)])
        got = self.check(Nodes(twice, twice), sender=A, recipient=B, amount_raw=700)
        self.assertEqual((got["verdict"], len(got["matching_logs"])), ("AMBIGUOUS", 2))
        self.assertEqual(self.check(Nodes(twice, twice), sender=A, recipient=B, amount_raw=700, log_index=2)["verdict"], "CONFIRMED")
        self.assertEqual(self.check(Nodes(twice, twice), sender=A, log_index=3)["verdict"], "NOT_IN_RECEIPT")

    def test_absent_unreachable_reverted_and_disagreeing(self):
        self.assertEqual(self.check(Nodes(None, None), sender=A)["verdict"], "NOT_FOUND")
        self.assertEqual(self.check(Nodes(None, DOWN), sender=A)["verdict"], "NOT_FOUND")
        both_down = self.check(Nodes(DOWN, DOWN), sender=A)
        self.assertEqual((both_down["verdict"], both_down["nodes_agreeing"]), ("UNREACHABLE", 0))
        self.assertNotIn("block", both_down)
        reverted = self.check(Nodes(receipt([], status="0x0"), receipt([], status="0x0")), sender=A)
        self.assertEqual((reverted["verdict"], reverted["block"]), ("REVERTED", 500))
        other = receipt([transfer(4, A, B, 5_170_000_000)])
        self.assertEqual(self.check(Nodes(PAID, other), sender=A, recipient=B)["verdict"], "ENDPOINTS_DISAGREE")

    def test_without_a_claim_the_receipt_is_only_decoded(self):
        got = self.check(Nodes(PAID, PAID))
        self.assertEqual((got["verdict"], len(got["transfers"]), got["claim"]), ("DECODED", 2, {}))

    def test_the_digest_ignores_formatting_and_sees_any_change_in_a_log(self):
        shuffled = receipt(list(reversed(PAID["logs"])), gasUsed="0x5")
        upper = receipt([dict(log, data=log["data"].upper().replace("0X", "0x")) for log in PAID["logs"]])
        self.assertEqual(evidence.receipt_digest(PAID), evidence.receipt_digest(shuffled))
        self.assertEqual(evidence.receipt_digest(PAID), evidence.receipt_digest(upper))
        self.assertNotEqual(evidence.receipt_digest(PAID), evidence.receipt_digest(receipt([transfer(4, A, B, 5_170_000_001), transfer(9, B, C, 1)])))
        self.assertNotEqual(evidence.receipt_digest(PAID), evidence.receipt_digest(receipt(PAID["logs"], status="0x0")))


@unittest.skipUnless(FIXTURE.exists(), "archived logs not present")
class Fills(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logs = json.loads(FIXTURE.read_text(encoding="utf-8"))["logs"]
        cls.tx = "0x75694957f0f178df48a1d85609e89246620b1b29e3ac27273511653c30055252"
        cls.receipt = receipt([log for log in logs if log["transactionHash"] == cls.tx])
        cls.buyer = "0xabe5de1162afa37223e3fae15f268a7842c5d99a"
        cls.token = "15035195039196635574169602968791196891740860668126783008232581544203600495657"

    def test_a_real_fill_is_confirmed_with_exact_amounts(self):
        got = evidence.verify_fill(Nodes(self.receipt, self.receipt), self.tx, self.buyer.upper().replace("0X", "0x"), token_id=self.token, side="BUY")
        self.assertEqual((got["verdict"], got["fills_in_receipt"]), ("CONFIRMED", 2))
        fill = got["matching_logs"][0]
        self.assertEqual((fill["shares_raw"], fill["cash_raw"], fill["version"], fill["log_index"]), ("5096154", "2446154", "v2", 97))
        self.assertEqual(fill["exchange"], "0xe111180000d2663c0091e4f400237545b87b996b")

    def test_the_wrong_side_or_wallet_is_not_in_the_receipt(self):
        nodes = Nodes(self.receipt, self.receipt)
        self.assertEqual(evidence.verify_fill(nodes, self.tx, self.buyer, side="SELL")["verdict"], "NOT_IN_RECEIPT")
        self.assertEqual(evidence.verify_fill(nodes, self.tx, A)["verdict"], "NOT_IN_RECEIPT")
        self.assertEqual(evidence.verify_fill(Nodes(None, None), self.tx, self.buyer)["verdict"], "NOT_FOUND")

    def test_the_counterparty_log_of_the_same_match_is_a_distinct_fill(self):
        fills = evidence.verify_fill(Nodes(self.receipt, self.receipt), self.tx, self.buyer)["fills_in_receipt"]
        other = [log for log in self.receipt["logs"] if self.buyer[2:] not in log["topics"][2]]
        self.assertEqual((fills, len(other)), (2, 1))


if __name__ == "__main__":
    unittest.main()
