"""The three OrderFilled decoders read the same real logs the same way: phi_monitor.chain.decode_fill,
phi_engine.feed.decode and livecollect.decode.decode_logs, on fixtures/orderfilled_20261113.json (14 v2 logs).
Where they differ by design the difference is asserted, not hidden. Run from the monitoring folder:
    python3 -m unittest discover -s tests -v"""
import json, os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from livecollect import decode as live   # noqa: E402
from phi_engine import feed               # noqa: E402
from phi_monitor import chain             # noqa: E402

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures", "orderfilled_20261113.json")) as f:
    LOGS = json.load(f)["logs"]


class Conformance(unittest.TestCase):
    def setUp(self):
        self.mon = [chain.decode_fill(l) for l in LOGS]
        self.eng = [feed.decode(l) for l in LOGS]
        out = live.decode_logs(LOGS)
        self.assertEqual((out["families"], len(out["fills"]), out["transfers"]), (["v2_order_filled"], len(LOGS), []))
        self.live = out["fills"]

    def test_shared_fields_agree(self):
        for m, e, v in zip(self.mon, self.eng, self.live):
            same = ("tx", "log_index", "block", "ts", "exchange", "wallet", "counterparty", "token_id", "side", "shares", "cash", "price")
            self.assertEqual({k: e[k] for k in same}, {k: m[k] for k in same})
            # livecollect names the owner of the filled order maker and the other side taker; chain and feed say wallet, counterparty
            self.assertEqual((v["log_index"], v["exchange"], v["maker"], v["taker"], v["token_id"], v["side"]),
                             (m["log_index"], m["exchange"], m["wallet"], m["counterparty"], m["token_id"], m["side"]))

    def test_amounts_differ_only_by_unit_scaling(self):
        # livecollect keeps the raw integer strings of the log; chain and feed divide by 1e6 and order them by side
        for m, v in zip(self.mon, self.live):
            cash, shares = ((v["maker_amount_filled"], v["taker_amount_filled"]) if v["side"] == "BUY"
                            else (v["taker_amount_filled"], v["maker_amount_filled"]))
            self.assertEqual((int(cash) / 1e6, int(shares) / 1e6), (m["cash"], m["shares"]))
            self.assertNotIn("price", v)                           # livecollect does not compute a price

    def test_fee_is_read_by_two_of_three(self):
        for m, e, v in zip(self.mon, self.eng, self.live):
            self.assertNotIn("fee", m)                             # chain.decode_fill drops the fee word
            self.assertEqual(e["fee"], int(v["fee"]) / 1e6)        # feed scales it, livecollect keeps the raw string
        self.assertGreater(len({v["fee"] for v in self.live}), 1)  # real non-zero fees are present in the fixture

    def test_only_chain_and_feed_carry_the_transaction(self):
        # decode_logs is given the logs of one receipt: its fills hold no transaction hash, block or time
        for v in self.live:
            self.assertFalse({"tx", "block", "ts"} & set(v))

    def test_a_removed_log_is_treated_differently(self):
        gone = dict(LOGS[0], removed=True)
        self.assertIsNone(chain.decode_fill(gone))                 # chain: None
        self.assertEqual(live.decode_logs([gone])["fills"], [])    # livecollect: skipped
        self.assertEqual(feed.decode(gone)["tx"], LOGS[0]["transactionHash"])   # feed: decoded; feed.watch checks removed itself


if __name__ == "__main__":
    unittest.main()
