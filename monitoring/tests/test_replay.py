"""Replay of a real evening (Machado market, 9 October 2025) from a stored fixture, offline and deterministic.
The fixture holds public trades, 10-minute prices and the as-of history of one account; see tests/make_fixtures.py."""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_monitor import detect, store   # noqa: E402

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures", "nobel_machado_20251009.json")
ACCOUNT = "0xa430506774f9efaf39903ee7e0db1351f66891ca"     # the proxy published as "6741" in investigations/followup-20261113
T_FIRST, T_ALERT = 1760049777, 1760050815                  # 2025-10-09 22:42:57 and 23:00:15 UTC
ANNOUNCEMENT = 1760086800                                  # 2025-10-10 09:00:00 UTC


def load():
    with open(FIX) as f:
        fx = json.load(f)
    con = store.connect(os.path.join(tempfile.mkdtemp(), "replay.sqlite"))
    with con:
        store.put_market(con, dict(fx["market"], tags=json.loads(fx["market"]["tags"])))
        con.executemany("insert into prices values(?,?,?)", [(fx["market"]["yes_token"], t, p) for t, p in fx["prices"]])
        store.add_fills(con, fx["fills"], "api")
        con.executemany("insert into baselines values(:wallet,:as_of,:body,0)", fx["baselines"])
        con.executemany("insert into funding values(:tx,:log_index,:block,:ts,:proxy,:payer,:token,:amount,:payer_kind,:payer_nonce)", fx["funding"])
    return con, fx


class NobelEvening(unittest.TestCase):
    def setUp(self):
        self.con, self.fx = load(); self.addCleanup(self.con.close)
        self.cid = self.fx["market"]["condition_id"]

    def test_replay_raises_one_alert_ten_hours_before_the_announcement(self):
        out = [r for r in detect.replay(self.con) if r.get("level")]
        self.assertEqual(len(out), 1)
        a = out[0]
        self.assertEqual((a["level"], a["side"], a["features"]["initiator"]), ("LONELY_THIN", "YES", ACCOUNT))
        self.assertEqual((a["t_first"], a["t_alert"]), (T_FIRST, T_ALERT))
        self.assertGreater(a["features"]["share15"], 0.9)
        self.assertEqual(a["initiator_history"]["prior_markets"], 0)
        self.assertGreater((ANNOUNCEMENT - a["replay_as_of"]) / 3600, 9.5)
        self.assertTrue(all(tx.startswith("0x") and len(tx) == 66 for tx in a["evidence_tx"]))
        self.assertIn("says nothing about identity", a["reading"])

    def test_nothing_before_the_alert_time(self):
        self.assertEqual(detect.evaluate(self.con, self.cid, "YES", T_FIRST - 60)[0], "none")       # the price has not moved yet
        status, why = detect.evaluate(self.con, self.cid, "YES", T_ALERT - 1)
        self.assertNotEqual(status, "alert", why)
        self.assertEqual(detect.evaluate(self.con, self.cid, "YES", T_ALERT)[0], "alert")
        self.assertEqual(detect.evaluate(self.con, self.cid, "NO", ANNOUNCEMENT)[0], "none")

    def test_later_rows_cannot_change_an_alert(self):
        before = detect.evaluate(self.con, self.cid, "YES", T_ALERT)[1]
        tok = self.fx["market"]["yes_token"]
        store.add_fills(self.con, [{"tx": "0xfuture", "log_index": -1, "ts": T_ALERT + 30, "wallet": "0xlate", "token_id": tok, "side": "BUY",
                                    "shares": 9e6, "cash": 8.1e6, "price": 0.9}], "api")
        self.con.execute("insert into prices values(?,?,?)", (tok, T_ALERT + 600, 0.99))
        self.assertEqual(detect.evaluate(self.con, self.cid, "YES", T_ALERT)[1], before)

    def test_the_funder_is_a_plain_key_and_services_are_not_links(self):
        a = detect.evaluate(self.con, self.cid, "YES", T_ALERT)[1]
        kinds = {x["payer_kind"] for x in a["funding"]}
        self.assertIn("key", kinds)
        self.assertEqual(a["cluster"], [])                    # no second wallet of the event is funded yet at that time
        # a second account paid by the same key and buying the same event becomes a cluster member, a contract payer never does
        key = next(x["payer"] for x in a["funding"] if x["payer_kind"] == "key")
        tok = self.fx["market"]["yes_token"]
        store.add_fills(self.con, [{"tx": "0xb1", "log_index": -1, "ts": T_ALERT - 100, "wallet": "0xsecond", "token_id": tok, "side": "BUY",
                                    "shares": 10.0, "cash": 3.0, "price": 0.3},
                                   {"tx": "0xb2", "log_index": -1, "ts": T_ALERT - 90, "wallet": "0xthird", "token_id": tok, "side": "BUY",
                                    "shares": 10.0, "cash": 3.0, "price": 0.3}], "api")
        self.con.executemany("insert into funding values(?,?,?,?,?,?,?,?,?,?)",
                             [("0xf1", 0, 1, T_ALERT - 200, "0xsecond", key, "t", 100.0, "key", 1),
                              ("0xf2", 0, 1, T_ALERT - 200, "0xthird", "0xbridge", "t", 100.0, "contract", 0),
                              ("0xf3", 0, 1, T_ALERT - 200, ACCOUNT, "0xbridge", "t", 100.0, "contract", 0)])
        b = detect.evaluate(self.con, self.cid, "YES", T_ALERT)[1]
        self.assertEqual(b["cluster"], [{"wallet": "0xsecond", "shared_payer": key}])

    def test_a_group_reached_through_brand_new_keys_is_found_two_hops_up(self):
        tok = self.fx["market"]["yes_token"]; t = T_ALERT + 3600
        store.add_fills(self.con, [{"tx": f"0xg{i}", "log_index": -1, "ts": t, "wallet": w, "token_id": tok, "side": "BUY", "shares": 10.0, "cash": 7.0, "price": 0.7}
                                   for i, w in enumerate(("0xnew1", "0xnew2", "0xnew3"))], "api")
        self.con.executemany("insert into funding values(?,?,?,?,?,?,?,?,?,?)", [
            ("0xh1", 0, 1, t - 60, "0xnew1", "0xkey1", "t", 500.0, "key", 1), ("0xh2", 0, 1, t - 120, "0xkey1", "0xhub", "t", 500.0, "key", 240),
            ("0xh3", 0, 1, t - 60, "0xnew2", "0xkey2", "t", 500.0, "key", 1), ("0xh4", 0, 1, t - 120, "0xkey2", "0xhub", "t", 500.0, "key", 241),
            ("0xh5", 0, 1, t - 60, "0xnew3", "0xkey3", "t", 500.0, "key", 1), ("0xh6", 0, 1, t - 120, "0xkey3", "0xrouter", "t", 500.0, "contract", 1)])
        groups = detect.clusters(self.con, self.fx["market"]["event_slug"], t)
        self.assertIn({"shared_payer": "0xhub", "wallets": ["0xnew1", "0xnew2"]}, groups)
        self.assertFalse(any("0xnew3" in g["wallets"] for g in groups))          # paid through a contract: no link
        self.assertEqual(detect.clusters(self.con, self.fx["market"]["event_slug"], t - 90), [])   # not yet funded at that time

    def test_alert_is_recorded_once_and_journaled(self):
        a = detect.evaluate(self.con, self.cid, "YES", T_ALERT)[1]
        self.assertTrue(detect.record(self.con, a)); self.assertFalse(detect.record(self.con, a))
        self.assertEqual(store.verify_journal(self.con), (1, None))
        self.assertEqual({r["id"] for r in detect.replay(self.con) if r.get("level")}, {a["id"]})   # replay reproduces the journaled alert


if __name__ == "__main__":
    unittest.main()
