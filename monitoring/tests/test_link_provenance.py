"""Offline regression for legacy-link quarantine in the active Polymarket engine.

This does not delete historical records. It prevents links produced before
historical-state + receipt-path checks from generating NEW C4/C5 claims.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_engine import chainfund, enrich, store

W1 = "0x" + "11" * 20
W2 = "0x" + "22" * 20
ROOT = "0x" + "aa" * 20
TX1 = "0x" + "ab" * 32
TX2 = "0x" + "bc" * 32
T0 = 1_800_000_000
VER = "receipt_guard_v1"


def create_db(case):
    con = store.connect(":memory:")
    case.addCleanup(con.close)
    return con


def add_link(con, wallet, tx, ts, certified=False, root=ROOT):
    with con:
        con.execute("insert into links values(?,?,?,?,?)", (wallet, root, 0, tx, ts))
        if certified:
            con.execute("insert into link_provenance values(?,?,?,?,?,?)",
                        (wallet, root, tx, VER, "a" * 64, 1.0))


def setup_events(con, t1=T0, t2=T0 + 3600, same=True):
    with con:
        con.execute("insert into markets(condition_id,event_slug) values(?,?)", ("m1", "event-a"))
        if not same:
            con.execute("insert into markets(condition_id,event_slug) values(?,?)", ("m2", "event-b"))
        con.execute("insert into entries(wallet,condition_id,oi,t,state) values(?,?,?,?,?)",
                    (W1, "m1", 0, t1, "watching"))
        con.execute("insert into entries(wallet,condition_id,oi,t,state) values(?,?,?,?,?)",
                    (W2, "m1" if same else "m2", 0, t2, "watching"))


class LegacyQuarantine(unittest.TestCase):
    def test_old_cached_links_are_preserved_but_cannot_trigger_c4(self):
        con = create_db(self)
        setup_events(con)
        add_link(con, W1, TX1, T0 - 100, certified=False)
        add_link(con, W2, TX2, T0 + 3500, certified=False)
        e2 = {"wallet": W2, "t": T0 + 3600}
        self.assertEqual(enrich.group_classes(con, e2, "event-a"), {})
        self.assertEqual(con.execute("select count(*) from links").fetchone()[0], 2)

        # A newly validated wallet is NOT enough: the other source remains legacy.
        with con:
            con.execute("insert into link_provenance values(?,?,?,?,?,?)",
                        (W2, ROOT, TX2, VER, "a" * 64, 1.0))
        self.assertEqual(enrich.group_classes(con, e2, "event-a"), {})
        # Only after both are processed under the new evidence gates can C4 fire.
        with con:
            con.execute("insert into link_provenance values(?,?,?,?,?,?)",
                        (W1, ROOT, TX1, VER, "b" * 64, 1.0))
        c4 = enrich.group_classes(con, e2, "event-a")
        self.assertEqual(c4["C4_COFUNDED_GROUP"]["other_wallet"], W1)
        self.assertEqual(c4["C4_COFUNDED_GROUP"]["root"], ROOT)

    def test_legacy_fanout_does_not_silence_currently_validated_link(self):
        con = create_db(self)
        setup_events(con)
        add_link(con, W1, TX1, T0 - 100, certified=True)
        add_link(con, W2, TX2, T0 + 3500, certified=True)
        with con:
            for i in range(11):
                con.execute("insert into links values(?,?,?,?,?)",
                            (f"old_{i}", ROOT, 0, f"legacy_{i}", T0 - 100))
        out = enrich.group_classes(con, {"wallet": W2, "t": T0 + 3600}, "event-a")
        self.assertIn("C4_COFUNDED_GROUP", out)

    def test_legacy_recurrent_funder_does_not_trigger_c5(self):
        con = create_db(self)
        t2 = T0 + 8 * 86400
        setup_events(con, T0, t2, same=False)
        add_link(con, W1, TX1, T0 - 100, certified=False)
        add_link(con, W2, TX2, t2 - 100, certified=True)
        self.assertEqual(enrich.group_classes(con, {"wallet": W2, "t": t2}, "event-b"), {})
        with con:
            con.execute("insert into link_provenance values(?,?,?,?,?,?)",
                        (W1, ROOT, TX1, VER, "b" * 64, 1.0))
        out = enrich.group_classes(con, {"wallet": W2, "t": t2}, "event-b")
        self.assertEqual(out["C5_RECURRENT_FUNDER"]["other_wallet"], W1)

    def test_old_or_unknown_validator_versions_are_not_eligible(self):
        con = create_db(self)
        setup_events(con)
        add_link(con, W1, TX1, T0 - 100, certified=True)
        add_link(con, W2, TX2, T0 + 3500, certified=True)
        with con:
            con.execute("update link_provenance set validator='legacy' where wallet=?", (W1,))
        self.assertEqual(enrich.group_classes(con, {"wallet": W2, "t": T0 + 3600}, "event-a"), {})

    def test_new_guarded_receipt_records_provenance_with_hash(self):
        con = create_db(self)
        receipt = {"blockNumber": "0x64",
                   "logs": [chainfund._log(chainfund.USDC_E, ROOT, W2, 5_000_000, 0)]}

        def rpc(method, params, urls=None):
            if method == "eth_getTransactionReceipt":
                return receipt
            if method == "eth_getCode":
                return "0x"
            if method == "eth_getTransactionCount":
                return "0xa"
            raise AssertionError(method)

        def labels(url):
            address = url.split("addresses=")[1]
            return {"addresses": {address: {"tags": []}}}

        enrich.trace_funding(con, W2, [(T0, 5.0, TX2)], rpc=rpc, get_json=labels)
        rows = con.execute("select wallet,root,tx,validator,receipt_sha256 "
                           "from link_provenance").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(tuple(rows[0][:4]), (W2, ROOT, TX2, VER))
        self.assertEqual(len(rows[0][4]), 64)
        self.assertEqual(con.execute("select count(*) from links").fetchone()[0], 1)

    def test_existing_receipt_is_not_silently_certified(self):
        con = create_db(self)
        with con:
            con.execute("insert into deposits values(?,?,?,?,?,?,?,?,?)",
                        (W1, TX1, T0, 5.0, "ok", ROOT, "direct", 100, "0" * 64))
            con.execute("insert into links values(?,?,?,?,?)",
                        (W1, ROOT, 0, TX1, T0))
        def no_rpc(*args, **kwargs):
            raise AssertionError("must not touch existing archival receipt")
        enrich.trace_funding(con, W1, [(T0, 5.0, TX1)], rpc=no_rpc)
        self.assertEqual(con.execute("select count(*) from link_provenance").fetchone()[0], 0)
        self.assertEqual(con.execute("select count(*) from links").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
