"""Offline unit tests: decoder, pure detection functions, storage, collection logic with a fake network.
Run from the monitoring folder:  python3 -m unittest discover -s tests -v"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_monitor import chain, collect, ignition, net, store, tapefeat, ws   # noqa: E402

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures")


def fixture(name):
    with open(os.path.join(FIX, name)) as f:
        return json.load(f)


def db(case):
    con = store.connect(os.path.join(tempfile.mkdtemp(), "t.sqlite")); case.addCleanup(con.close)
    return con


class PureFunctions(unittest.TestCase):
    def test_selftests_of_the_frozen_functions(self):
        ignition._selftest(); tapefeat._selftest()

    def test_ignition_never_reads_points_after_its_time(self):
        quiet = [(i * 600, 0.03) for i in range(60)]
        jump = quiet + [(60 * 600, 0.05), (61 * 600, 0.11), (62 * 600, 0.31)]
        ig = ignition.first_ignition(jump, "YES")
        self.assertEqual(ig, ignition.first_ignition(jump + [(63 * 600, 0.99), (64 * 600, 0.01)], "YES"))
        self.assertIsNone(ignition.first_ignition(jump[:-1], "YES"))


class Decoder(unittest.TestCase):
    def test_real_logs_equal_the_data_api_rows(self):
        fx = fixture("orderfilled_20261113.json")
        got = {}
        for log in fx["logs"]:
            f = chain.decode_fill(log)
            got.setdefault(f["tx"], []).append((f["wallet"], f["token_id"], f["side"], round(f["shares"], 4), round(f["price"], 4), f["ts"]))
        self.assertEqual(set(got), set(fx["data_api_rows"]))
        for tx, rows in fx["data_api_rows"].items():
            want = sorted((r["wallet"], r["token_id"], r["side"], round(r["size"], 4), round(r["price"], 4), r["timestamp"]) for r in rows)
            self.assertEqual(sorted(got[tx]), want, tx)

    def test_removed_and_malformed_logs(self):
        log = dict(fixture("orderfilled_20261113.json")["logs"][0])
        self.assertIsNone(chain.decode_fill(dict(log, removed=True)))
        with self.assertRaises(ValueError):
            chain.decode_fill(dict(log, topics=log["topics"][:3]))
        with self.assertRaises(ValueError):
            chain.decode_fill(dict(log, data="0x" + "0" * 63 + "7" + log["data"][66:]))    # side 7 does not exist


class WebSocket(unittest.TestCase):
    def test_recorded_frames_fragments_ping_and_close(self):
        self.assertGreaterEqual(ws._selftest(), 2)

    def test_trade_prints_are_kept_and_nothing_else(self):
        msg = json.dumps([{"event_type": "last_trade_price", "asset_id": "1", "timestamp": "1794577264007", "price": "0.31", "size": "12",
                           "side": "BUY", "transaction_hash": "0xabc"}, {"event_type": "price_change", "market": "0xc"}]).encode()
        self.assertEqual(collect._ws_rows(msg, 5.0), [("1", 1794577264007, 0.31, 12.0, "BUY", "0xabc", 5.0)])
        self.assertEqual(collect._ws_rows(b"PONG", 5.0), [])


class Storage(unittest.TestCase):
    def test_fills_are_idempotent_and_journal_is_chained(self):
        con = db(self)
        f = {"tx": "0xa", "log_index": 1, "block": 5, "ts": 100, "wallet": "0xw", "counterparty": "0xc", "token_id": "1", "side": "BUY",
             "shares": 10.0, "cash": 3.0, "price": 0.3}
        self.assertEqual(store.add_fills(con, [f, dict(f, log_index=2)], "chain"), 2)
        self.assertEqual(store.add_fills(con, [f], "chain"), 0)
        store.journal(con, "alert", {"a": 1}); store.journal(con, "alert", {"a": 2})
        self.assertEqual(store.verify_journal(con), (2, None))
        con.execute("update journal set body='{\"a\": 9}' where seq=1")
        self.assertEqual(store.verify_journal(con), (0, 1))


class FakeNet:
    """Serves canned pages and counts calls; anything unexpected raises, so no test touches the network."""
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def get_json(self, url, **kw):
        self.calls.append(url)
        for key, body in self.pages:
            if key in url:
                if isinstance(body, Exception):
                    raise body
                return body
        raise AssertionError("unexpected url " + url)


def trade(ts, wallet="0xw", side="BUY", token="1", size=10.0, price=0.3, tx=None):
    return {"timestamp": ts, "proxy_wallet": wallet, "side": side, "token_id": token, "size": size, "price": price,
            "transaction_hash": tx or f"0x{ts:x}", "name": "must never be stored", "bio": "must never be stored"}


class Collection(unittest.TestCase):
    def setUp(self):
        self.con = db(self); self.real = collect.net.get_json
        store.put_market(self.con, {"condition_id": "0xc1", "yes_token": "1", "no_token": "2"})

    def tearDown(self):
        collect.net.get_json = self.real

    def test_tape_follows_the_cursor_and_a_second_read_does_not_double_rows(self):
        p1 = {"data": [trade(500), trade(400)], "pagination": {"has_more": True, "next_cursor": "C2"}}
        p2 = {"data": [trade(300), trade(90)], "pagination": {"has_more": True, "next_cursor": "C3"}}
        fake = FakeNet([("cursor=C2", p2), ("condition=0xc1", p1)]); collect.net.get_json = fake.get_json
        r = collect.fetch_tape(self.con, "0xc1", 100)
        self.assertEqual((r["rows"], r["pages"], r["complete"]), (3, 2, True))          # the row at 90 is below the window
        collect.fetch_tape(self.con, "0xc1", 100)
        self.assertEqual(self.con.execute("select count(*) from fills").fetchone()[0], 3)
        self.assertEqual([x[0] for x in store.tape(self.con, "0xc1", 0, 999)], [300, 400, 500])
        cols = [d[1] for d in self.con.execute("pragma table_info(fills)")]
        self.assertFalse({"name", "bio", "pseudonym"} & set(cols))

    def test_tape_refuses_a_stream_that_is_not_newest_first(self):
        bad = {"data": [trade(400), trade(500)], "pagination": {}}
        collect.net.get_json = FakeNet([("condition=0xc1", bad)]).get_json
        with self.assertRaises(net.SourceError):
            collect.fetch_tape(self.con, "0xc1", 100)

    def test_tape_too_deep_stores_nothing(self):
        page = {"data": [trade(500)], "pagination": {"has_more": True, "next_cursor": "C"}}
        collect.net.get_json = FakeNet([("condition=0xc1", page)]).get_json
        self.assertEqual(collect.fetch_tape(self.con, "0xc1", 100, max_pages=3), {"rows": 0, "pages": 3, "complete": False})
        self.assertEqual(self.con.execute("select count(*) from fills").fetchone()[0], 0)

    def test_an_http_error_is_never_an_empty_tape(self):
        collect.net.get_json = FakeNet([("condition=0xc1", net.SourceError("HTTP 500", 500))]).get_json
        with self.assertRaises(net.SourceError):
            collect.fetch_tape(self.con, "0xc1", 100)


class ChainWatch(unittest.TestCase):
    def setUp(self):
        self.con = db(self); self.real = (chain.fills, chain.head)
        self.asked = []

        def fills(a, b):
            self.asked.append((a, b))
            return [{"tx": f"0x{n:x}", "log_index": 0, "block": n, "ts": 1000 + 2 * n, "wallet": "0xw", "counterparty": "0xe", "token_id": "9",
                     "side": "BUY", "shares": 100.0, "cash": 2.0, "price": 0.02} for n in range(a, b + 1)]
        chain.fills = fills

    def tearDown(self):
        chain.fills, chain.head = self.real

    def test_resume_from_checkpoint_without_gap_or_duplicate(self):
        r1 = collect.watch_chain(self.con, head=1000)                      # first start: one block, no history claimed
        self.assertEqual((r1["from"], r1["to"]), (997, 997))
        r2 = collect.watch_chain(self.con, head=1050)
        self.assertEqual((r2["from"], r2["to"], r2["fills"]), (998, 1047, 50))
        self.assertEqual(collect.watch_chain(self.con, head=1050)["fills"], 0)
        blocks = [r[0] for r in self.con.execute("select block from fills order by block")]
        self.assertEqual(blocks, list(range(997, 1048)))

    def test_a_long_outage_is_journaled_as_a_gap(self):
        collect.watch_chain(self.con, head=1000)
        collect.watch_chain(self.con, head=1000 + collect.MAX_CATCHUP + 500)
        gaps = [json.loads(r[0]) for r in self.con.execute("select body from journal where kind='gap'")]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["from_block"], 998)

    def test_trigger_needs_a_real_jump_over_a_low_reference(self):
        base = {"tx": "0x1", "log_index": 0, "block": 1, "wallet": "0xw", "counterparty": "0xe", "token_id": "7", "side": "BUY", "shares": 5000.0}
        t = 100000
        store.add_fills(self.con, [dict(base, tx=f"0xr{i}", ts=t - 5 * 3600 + i, cash=150.0, price=0.03) for i in range(6)], "chain")
        self.assertEqual(collect._trigger(self.con, dict(base, ts=t, cash=250.0, price=0.05)), 0)     # under 3x and under +0.10
        self.assertEqual(collect._trigger(self.con, dict(base, ts=t, cash=50.0, price=0.40)), 0)      # too small
        self.assertEqual(collect._trigger(self.con, dict(base, ts=t, cash=250.0, price=0.95)), 0)     # looks like a resolution
        self.assertEqual(collect._trigger(self.con, dict(base, ts=t, cash=250.0, price=0.14, side="SELL")), 0)
        self.assertEqual(collect._trigger(self.con, dict(base, ts=t, cash=250.0, price=0.14)), 1)
        self.assertEqual(collect._trigger(self.con, dict(base, ts=t + 5, cash=250.0, price=0.20)), 0)  # already a candidate


if __name__ == "__main__":
    unittest.main()
