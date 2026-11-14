"""Offline tests of phi_engine: decoder, registry, journal, catch-up without a hole, entries, evaluation of an entry with
a fake network, the group classes, the alert text. Run from the monitoring folder:
    python3 -m unittest discover -s tests -v"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_monitor import chain, net                                                     # noqa: E402
from phi_engine import asof, chainfund, contracts, enrich, feed, models, report, store   # noqa: E402

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures")
T0 = 1_800_000_000
W1, W2, FUNDER, POOL, RELAY = ("0x" + c * 40 for c in "1234a")
COND, TOK_YES, TOK_NO = "0xc0", "111", "222"


def db(case):
    path = os.path.join(tempfile.mkdtemp(), "e.sqlite")
    con = store.connect(path); case.addCleanup(con.close)
    return con, path


def log(wallet, token, cash, shares, block, index, exchange="0xe111180000d2663c0091e4f400237545b87b996b", side=0, ts=None, fee=0):
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    w = lambda n: f"{n:064x}"
    a, b = (cash, shares) if side == 0 else (shares, cash)
    return {"address": exchange, "topics": [contracts.ORDER_FILLED, "0x" + "ab" * 32, pad(wallet), pad(exchange)],
            "data": "0x" + w(side) + w(int(token)) + w(int(a * 1e6)) + w(int(b * 1e6)) + w(int(fee * 1e6)) + "00" * 64,
            "transactionHash": "0x" + f"{block:060x}" + f"{index:04x}", "logIndex": hex(index), "blockNumber": hex(block),
            "blockTimestamp": hex(ts if ts is not None else T0 + block)}


class FakeChain:
    """eth_blockNumber and eth_getLogs over a list of logs; counts calls; can fail for a while."""
    def __init__(self, logs, head):
        self.logs, self.head, self.calls = logs, head, 0

    def __call__(self, method, params, urls=None):
        self.calls += 1
        if method == "eth_blockNumber":
            return hex(self.head)
        if method == "eth_getLogs":
            q = params[0]; lo, hi = int(q["fromBlock"], 16), int(q["toBlock"], 16); addrs = q.get("address")
            return [l for l in self.logs if lo <= int(l["blockNumber"], 16) <= hi and (addrs is None or l["address"] in addrs)]
        raise AssertionError(method)


def gamma(tags=("politics",), end="2030-01-01T00:00:00Z", known=True):
    def get_json(url):
        if "markets?clob_token_ids" in url:
            return [{"conditionId": COND, "clobTokenIds": json.dumps([TOK_YES, TOK_NO]), "outcomes": '["Yes", "No"]', "question": "Will X happen?",
                     "events": [{"slug": "event-x"}], "negRisk": False, "endDate": end, "version": "v1"}] if known else []
        if "/events/slug/" in url:
            return {"tags": [{"slug": t} for t in tags]}
        raise AssertionError(url)
    return get_json


class Decoder(unittest.TestCase):
    def test_same_reading_as_the_monitor_on_real_logs_and_the_fee_is_kept(self):
        with open(os.path.join(FIX, "orderfilled_20261113.json")) as f:
            logs = json.load(f)["logs"]
        for l in logs:
            a, b = feed.decode(l), chain.decode_fill(l)
            self.assertEqual({k: a[k] for k in b}, b)
            self.assertIsNotNone(a["fee"])
        f = feed.decode(log(W1, TOK_YES, 2000.0, 10000.0, 5, 1, fee=12.5))
        self.assertEqual((f["side"], f["cash"], f["shares"], f["price"], f["fee"], f["wallet"]), ("BUY", 2000.0, 10000.0, 0.2, 12.5, W1))

    def test_registry_and_unknown_emitters(self):
        self.assertIn("0xe3333700ca9d93003f00f0f71f8515005f6c00aa", contracts.EXCHANGES)        # Protocol V2 exchange
        stranger = log(W1, TOK_YES, 5.0, 10.0, 1, 0, exchange="0x" + "ee" * 20)
        self.assertEqual(contracts.unknown_emitters([log(W1, TOK_YES, 5.0, 10.0, 1, 0), stranger, stranger]), {"0x" + "ee" * 20: 2})
        self.assertEqual((contracts.family(["games", "politics"]), contracts.family(["sports"]), contracts.family(["politics"])),
                         ("EXCLUDED", "PUBLIC_PROCESS", "INFO"))


class Journal(unittest.TestCase):
    def test_edit_of_time_or_body_and_deletion_are_all_seen(self):
        con, _ = db(self)
        with con:
            for i in range(4):
                store.journal(con, "note", {"i": i}, now=1000.0 + i)
        self.assertEqual(store.verify_journal(con), (4, None))
        con.execute("update journal set t=5.0 where seq=2"); self.assertEqual(store.verify_journal(con)[1], 2)
        con.rollback()
        con.execute("delete from journal where seq=3"); self.assertEqual(store.verify_journal(con)[1], 4)      # a hole in the sequence
        con.rollback()
        con.execute("update journal set body='{\"i\": 9}' where seq=4"); self.assertEqual(store.verify_journal(con)[1], 4)


class Feed(unittest.TestCase):
    def test_a_long_outage_is_caught_up_without_a_hole(self):
        con, _ = db(self)
        logs = [log(W1, TOK_YES, 50.0, 100.0, b, 0) for b in range(1000, 6000, 7)]
        rpc = FakeChain(logs, head=1003)
        feed.watch(con, rpc=rpc)                                         # first start at block 1000
        rpc.head = 6003                                                  # then the machine was off for 5,000 blocks
        seen = 0
        for _ in range(40):
            out = feed.watch(con, max_chunks=30, rpc=rpc); seen += out["fills"]
            if out["behind"] == 0:
                break
        expected = sum(1 for l in logs if 1001 <= int(l["blockNumber"], 16) <= 6000)
        self.assertEqual((seen, out["behind"]), (expected, 0))
        self.assertEqual(con.execute("select sum(fills) from coverage").fetchone()[0], expected + 1)  # every fill is counted (one more: the block read at the start)
        self.assertEqual(con.execute("select count(*) from fills").fetchone()[0], 0)                  # small fills of unwatched wallets are not kept as rows
        self.assertEqual(store.checkpoint(con, "chain")["block"], 6000)
        kinds = [r[0] for r in con.execute("select kind from journal")]
        self.assertIn("catching_up", kinds)                              # the lag was written down while it lasted

    def test_a_strange_log_is_journaled_and_the_feed_goes_on(self):
        con, _ = db(self)
        bad = log(W1, TOK_YES, 50.0, 100.0, 12, 0); bad["data"] = "0x" + "00" * 64          # too short to be a fill
        rpc = FakeChain([log(W1, TOK_YES, 50.0, 100.0, 11, 0), bad, log(W1, TOK_YES, 50.0, 100.0, 13, 0)], head=13)
        store.checkpoint(con, "chain", {"block": 10, "t": 0}); con.commit()
        self.assertEqual(feed.watch(con, rpc=rpc)["fills"], 0)           # three confirmations: blocks 11 to 13 are not read yet
        rpc.head = 16; out = feed.watch(con, rpc=rpc)
        self.assertEqual((out["fills"], store.checkpoint(con, "chain")["block"]), (2, 13))   # the two good fills are read, the feed went past the bad one
        self.assertEqual(con.execute("select count(*) from journal where kind='undecodable_log'").fetchone()[0], 1)

    def test_reading_the_same_blocks_twice_stores_nothing_twice(self):
        con, _ = db(self)
        rpc = FakeChain([log(W1, TOK_YES, 5000.0, 10000.0, 11, 0), log(W2, TOK_YES, 6000.0, 10000.0, 11, 1), log(W2, TOK_YES, 60.0, 100.0, 11, 2)], head=14)
        for _ in range(2):
            store.checkpoint(con, "chain", {"block": 10, "t": 0}); con.commit(); feed.watch(con, rpc=rpc)
        self.assertEqual(con.execute("select count(*) from fills").fetchone()[0], 2)                  # the two large fills, once each

    def test_every_fill_of_a_watched_wallet_is_kept(self):
        con, _ = db(self)
        con.execute("insert into entries(wallet, condition_id, oi, t, state) values(?,?,?,?,?)", (W2, COND, 0, T0, "watching")); con.commit()
        rpc = FakeChain([log(W1, TOK_YES, 60.0, 100.0, 11, 0), log(W2, TOK_YES, 60.0, 100.0, 11, 1)], head=14)
        store.checkpoint(con, "chain", {"block": 10, "t": 0}); con.commit(); out = feed.watch(con, rpc=rpc)
        self.assertEqual((out["fills"], out["stored"], [r[0] for r in con.execute("select wallet from fills")]), (2, 1, [W2]))

    def test_sentinel_names_an_exchange_the_registry_does_not_know(self):
        con, _ = db(self)
        rpc = FakeChain([log(W1, TOK_YES, 50.0, 100.0, 97, 0, exchange="0x" + "ee" * 20), log(W1, TOK_YES, 50.0, 100.0, 97, 1)], head=100)
        self.assertEqual(feed.sentinel(con, rpc=rpc), {"0x" + "ee" * 20: 1})
        self.assertEqual(con.execute("select count(*) from journal where kind='unknown_exchange'").fetchone()[0], 1)


class Entries(unittest.TestCase):
    def fill(self, con, wallet, token, cash, price, ts, n):
        con.execute("insert into fills values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (f"0xt{n}", n, n, ts, "0xe111180000d2663c0091e4f400237545b87b996b", wallet, "0x0", token, "BUY",
                                                                         cash / price, cash, 0.0, price, ts + 5.0)); con.commit()

    def test_first_large_buy_is_an_entry_once(self):
        con, _ = db(self)
        self.fill(con, W1, TOK_YES, 1500.0, 0.2, T0, 1); self.fill(con, W1, TOK_YES, 3000.0, 0.25, T0 + 60, 2)
        self.fill(con, W1, TOK_YES, 900.0, 0.2, T0 + 70, 3); self.fill(con, W2, TOK_NO, 5000.0, 0.95, T0 + 80, 4)       # too small; price above 0.90
        new, last, c = feed.open_entries(con, 0, get_json=gamma())
        self.assertEqual((new, c["not_first"], c["large_buys"]), (1, 1, 2))
        e = con.execute("select wallet, oi, t, cash, state from entries").fetchall()
        self.assertEqual([tuple(x) for x in e], [(W1, 0, T0, 1500.0, "new")])

    def test_excluded_tags_are_checked_at_every_fill_not_only_the_first(self):
        con, _ = db(self)
        self.fill(con, W1, TOK_YES, 1500.0, 0.2, T0, 1)
        self.assertEqual(feed.open_entries(con, 0, get_json=gamma(tags=("games",)))[0], 0)
        self.fill(con, W2, TOK_YES, 2500.0, 0.3, T0 + 10, 2)                                # the market is known now: still no entry
        new, _, c = feed.open_entries(con, 1, get_json=gamma(tags=("games",)))
        self.assertEqual((new, c["excluded_family"]), (0, 1))

    def test_a_token_unknown_to_the_catalogue_is_asked_again_later(self):
        con, _ = db(self)
        self.fill(con, W1, TOK_YES, 1500.0, 0.2, T0, 1)
        self.fill(con, W2, TOK_NO, 2500.0, 0.3, T0 + 5, 2)
        new, last, c = feed.open_entries(con, 0, get_json=gamma(known=False))
        self.assertEqual((new, last, c["unknown_token"]), (0, 2, 2))                         # put aside; the cursor moves on, nothing is held back
        self.assertEqual(feed.open_entries(con, last, get_json=gamma())[0], 0)               # asked again only after the retry delay
        con.execute("update tokens set checked=0"); con.commit()                             # the delay has passed and the catalogue knows the market
        new, last2, c = feed.open_entries(con, last, get_json=gamma())
        self.assertEqual((new, last2, con.execute("select count(*) from pending_fills").fetchone()[0]), (2, 2, 0))
        # a token that never appears in the catalogue is journaled after two hours, once
        con3, _ = db(self); self.fill(con3, W1, TOK_YES, 1500.0, 0.2, T0, 1)
        feed.open_entries(con3, 0, get_json=gamma(known=False), now=lambda: 1000.0)
        c = feed.open_entries(con3, 1, get_json=gamma(known=False), now=lambda: 1000.0 + 3 * 3600)[2]
        self.assertEqual((c["given_up"], con3.execute("select count(*) from journal where kind='token_never_resolved'").fetchone()[0]), (1, 1))

    def test_a_combinatorial_position_is_counted_apart_and_never_asked_to_the_catalogue(self):
        con, _ = db(self); combo = str((3 << 248) + 12345)
        con.execute("insert into fills values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("0xtc", 1, 1, T0, contracts.EXCHANGE_V3, W1, "0x0", combo, "BUY", 10000.0, 2000.0, 0.0, 0.2, T0 + 5.0)); con.commit()
        self.fill(con, W2, TOK_YES, 1500.0, 0.2, T0 + 1, 2)
        def no_combo(url):
            self.assertNotIn(combo, url); return gamma()(url)
        new, last, c = feed.open_entries(con, 0, get_json=no_combo)
        self.assertEqual((new, last, c["combo"], c["unknown_token"]), (1, 2, 1, 0))            # the fill behind it became an entry
        self.assertFalse(contracts.is_combo(contracts.EXCHANGE_V3, str((1 << 248) + 5)))      # a binary Protocol V2 position is a market side

    def test_no_entry_after_the_scheduled_end(self):
        con, _ = db(self)
        self.fill(con, W1, TOK_YES, 1500.0, 0.2, T0, 1)
        self.assertEqual(feed.open_entries(con, 0, get_json=gamma(end="2020-01-01T00:00:00Z"))[2]["after_scheduled_end"], 1)


def activity(rows):
    """Data API answer for slim rows [ts, type, cond, side, usdc, price, oi, tx], newest first as the API serves them."""
    name = {"T": "TRADE", "D": "DEPOSIT", "W": "WITHDRAWAL"}
    def get_json(url):
        if "/v2/activity" in url:
            w = url.split("user=")[1].split("&")[0]
            return {"data": [{"proxy_wallet": w, "timestamp": r[0], "type": name[r[1]], "condition_id": r[2], "side": r[3], "usdc_size": r[4], "price": r[5],
                              "outcome_index": r[6], "transaction_hash": r[7]} for r in reversed(rows.get(w, []))], "pagination": {"has_more": False}}
        if "metadata.services.blockscout.com" in url:
            a = url.split("addresses=")[1]
            return {"addresses": {a.upper().replace("0X", "0x"): {"tags": [{"name": "Service"}] if a in (POOL, RELAY) else []}}}   # checksummed-like key
        return gamma()(url)
    return get_json


CHAIN_T0 = T0 - 1_900              # fake chain: block b is mined at CHAIN_T0 + 2 b (block 900 = the deposit at T0 - 100); the head is past every entry
CHAIN_HEAD = 1_100_000


def chain_rpc(receipts, inflow, code=None, nonce=None, head=CHAIN_HEAD):
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    def rpc(method, params, urls=None):
        if method == "eth_getTransactionReceipt":
            return receipts.get(params[0])
        if method == "eth_getCode":
            return "0x60" if params[0] in (code or {POOL}) else "0x"
        if method == "eth_getTransactionCount":
            return hex((nonce or {}).get(params[0], 40))
        if method == "eth_getLogs" and int(params[0]["toBlock"], 16) - int(params[0]["fromBlock"], 16) >= 10000 and urls == enrich.SLICE_RPC:
            raise AssertionError("a capped endpoint was asked for more than 10,000 blocks")
        if method == "eth_getLogs":
            to = "0x" + params[0]["topics"][2][-40:]; lo, hi = int(params[0]["fromBlock"], 16), int(params[0]["toBlock"], 16)
            return [{"topics": [chainfund.TRANSFER, pad(s), pad(to)], "address": chainfund.USDC, "data": hex(v), "blockNumber": hex(b), "transactionHash": tx,
                     "blockTimestamp": hex(CHAIN_T0 + 2 * b)} for (dst, s, v, b, tx) in inflow if dst == to and lo <= b <= hi]
        if method == "eth_blockNumber":
            return hex(head)
        if method == "eth_getBlockByNumber":
            return {"timestamp": hex(CHAIN_T0 + 2 * int(params[0], 16))}
        raise AssertionError(method)
    return rpc


def swap_receipt(wallet, value, block):
    """A deposit that is the wallet's own money swapped by a pool: the pool pays the collateral to the wallet."""
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    return {"blockNumber": hex(block), "logs": [{"address": chainfund.USDC_E, "topics": [chainfund.TRANSFER, pad(POOL), pad(wallet)], "data": hex(value), "logIndex": "0x1"}]}


class Evaluation(unittest.TestCase):
    def setup(self, con, wallet, t, cash=2000.0, price=0.06):
        gamma_json = gamma()
        con.execute("insert into fills values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("0xentry" + wallet[-2:], 1, 500, t, "0xe111180000d2663c0091e4f400237545b87b996b", wallet, "0x0",
                                                                         TOK_YES, "BUY", cash / price, cash, 0.0, price, t + 6.0)); con.commit()
        feed.open_entries(con, 0, get_json=gamma_json)
        return dict(con.execute("select * from entries where wallet=?", (wallet,)).fetchone())

    def test_an_answer_without_the_entry_is_not_a_new_wallet(self):
        con, _ = db(self); e = self.setup(con, W1, T0)
        with self.assertRaises(enrich.NotReady):                       # the data API has not caught up: nothing is concluded
            enrich.evaluate(con, e, rpc=chain_rpc({}, []), get_json=activity({W1: []}))
        alerts, counts = enrich.work(con, rpc=chain_rpc({}, []), get_json=activity({W1: []}), now=lambda: T0 + 30)
        self.assertEqual((alerts, counts["not_ready"]), ([], 1))
        self.assertEqual(con.execute("select state, tries from entries").fetchone()[:], ("new", 1))

    def test_money_received_on_the_chain_without_a_deposit_row_is_fresh(self):
        pad = lambda a: "0x" + "0" * 24 + a[2:]
        rows = {W1: [[T0, "T", COND, "BUY", 2000.0, 0.06, 0, None]]}            # no deposit row at all, as for a quarter of 2026 wallets
        rec = {"blockNumber": hex(450), "logs": [{"address": chainfund.USDC, "topics": [chainfund.TRANSFER, pad(FUNDER), pad(W1)],
                                                  "data": hex(5_000_000_000), "logIndex": "0x0"}]}
        con, _ = db(self); e = self.setup(con, W1, T0)
        alerts, _ = enrich.evaluate(con, e, rpc=chain_rpc({"0xchain1": rec}, [(W1, FUNDER, 5_000_000_000, 450, "0xchain1")]),   # block 450 = T0 - 1000
                                    get_json=activity(rows), now=lambda: T0 + 400)
        self.assertIn("C1_FRESH_FUNDED_BET", {a["class"] for a in alerts})
        self.assertEqual(con.execute("select payer from deposits where tx='0xchain1'").fetchone()[0], FUNDER)    # the transfer is traced like a deposit
        got = enrich.chain_inflows(W1, T0 - 86400, T0, rpc=chain_rpc({}, [(W1, FUNDER, 7, 450, "0xa"), (W1, FUNDER, 9, 951, "0xlate")], head=1000))
        self.assertEqual([g["tx"] for g in got], ["0xa"])           # a day is read in slices; a transfer at or after the entry is left out
        con2, _ = db(self); e2 = self.setup(con2, W1, T0)
        alerts2, _ = enrich.evaluate(con2, e2, rpc=chain_rpc({}, []), get_json=activity(rows), now=lambda: T0 + 400)
        self.assertNotIn("C1_FRESH_FUNDED_BET", {a["class"] for a in alerts2})                          # nothing received: not fresh

    def test_fresh_funded_bet_fires_at_the_entry_names_the_real_funder_and_turns_heavy_at_10000(self):
        con, path = db(self); e = self.setup(con, W1, T0)
        rows = {W1: [[T0 - 100, "D", None, None, 40000.0, None, None, "0xdep1"], [T0, "T", COND, "BUY", 2000.0, 0.06, 0, None],
                     [T0 + 60, "T", COND, "BUY", 5000.0, 0.10, 0, None], [T0 + 300, "T", COND, "BUY", 4000.0, 0.30, 0, None]]}
        rpc = chain_rpc({"0xdep1": swap_receipt(W1, 39_991_000_000, 900)}, [(W1, FUNDER, 40_000_000_000, 880, "0xfund1"), (W1, POOL, 39_991_000_000, 900, "0xdep1")])
        alerts, _ = enrich.evaluate(con, e, rpc=rpc, get_json=activity(rows), now=lambda: T0 + 400)
        by = {a["class"]: a for a in alerts}
        self.assertEqual(sorted(by), ["C1_FRESH_FUNDED_BET", "C6_QUIET_FRESH_LOW", "C7_HEAVY_NEWCOMER", "R1_S_FRESH_REPLICATION"])
        a = by["C1_FRESH_FUNDED_BET"]; heavy = by["C7_HEAVY_NEWCOMER"]
        self.assertEqual((a["t_alert"], a["market"]["price_at_alert"]), (T0, 0.06))                    # the entry itself
        self.assertEqual((heavy["t_alert"], heavy["market"]["price_at_alert"], heavy["wallets"]["net_bought_usd"]), (T0 + 300, 0.30, 11000.0))
        self.assertEqual(a["wallets"]["deposits"][0]["payer_kind"], "contract")               # the pool is a service
        self.assertEqual([(l["key"], l["how"]) for l in a["wallets"]["plain_keys_behind_deposits"]], [(FUNDER, "sent the money that was swapped into the deposit")])
        self.assertEqual(a["validation"]["status"], "EXPLORATORY" if not os.path.exists(os.path.join(os.path.dirname(report.__file__), "reference", "validation_status.json"))
                         else a["validation"]["status"])
        text = report.render(a)
        for part in ("MARKET", "WALLETS", "ANOMALY", "EVIDENCE", "VALIDATION"):
            self.assertIn(part, text)
        # the same history cut before the third buy: the entry class is there, the heavy one is not yet. Nothing after a moment is used
        con2, _ = db(self); e2 = self.setup(con2, W1, T0)
        early, _ = enrich.evaluate(con2, e2, rpc=rpc, get_json=activity({W1: rows[W1][:3]}), now=lambda: T0 + 100)
        self.assertEqual((("C1_FRESH_FUNDED_BET" in {x["class"] for x in early}), ("C7_HEAVY_NEWCOMER" in {x["class"] for x in early})), (True, False))

    def test_second_wallet_of_the_same_key_completes_a_group_and_a_service_never_does(self):
        con, _ = db(self)
        rows = lambda t: [[t - 100, "D", None, None, 5000.0, None, None, f"0xdep{t}"], [t, "T", COND, "BUY", 3000.0, 0.2, 0, None]]
        rec = lambda w, t: {f"0xdep{t}": swap_receipt(w, 4_990_000_000, 900 + t - T0)}
        e1 = self.setup(con, W1, T0, cash=3000.0, price=0.2)
        a1, _ = enrich.evaluate(con, e1, rpc=chain_rpc(rec(W1, T0), [(W1, FUNDER, 5_000_000_000, 890, "0xf1")]), get_json=activity({W1: rows(T0)}), now=lambda: T0 + 50)
        self.assertNotIn("C4_COFUNDED_GROUP", {x["class"] for x in a1})                         # the first wallet alone is not a group
        t2 = T0 + 3600
        con.execute("insert into fills values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("0xentry2", 2, 600, t2, "0xe111180000d2663c0091e4f400237545b87b996b", W2, "0x0", TOK_YES, "BUY",
                                                                         15000.0, 3000.0, 0.0, 0.2, t2 + 6.0)); con.commit()
        feed.open_entries(con, 1, get_json=gamma())
        e2 = dict(con.execute("select * from entries where wallet=?", (W2,)).fetchone())
        a2, _ = enrich.evaluate(con, e2, rpc=chain_rpc(rec(W2, t2), [(W2, FUNDER, 5_000_000_000, 4480, "0xf2")]), get_json=activity({W2: rows(t2)}), now=lambda: t2 + 50)
        g = {x["class"]: x for x in a2}["C4_COFUNDED_GROUP"]
        self.assertEqual((g["wallets"]["linked_wallet"]["other_wallet"], g["wallets"]["linked_wallet"]["root"]), (W1, FUNDER))
        # same story when the common payer carries a public tag (the tag service answers with another letter case): no link
        con4, _ = db(self)
        e1 = self.setup(con4, W1, T0, cash=3000.0, price=0.2)
        enrich.evaluate(con4, e1, rpc=chain_rpc(rec(W1, T0), [(W1, RELAY, 5_000_000_000, 890, "0xf1")]), get_json=activity({W1: rows(T0)}), now=lambda: T0 + 50)
        self.assertEqual((con4.execute("select tags from addresses where address=?", (RELAY,)).fetchone()[0], con4.execute("select count(*) from links").fetchone()[0]),
                         ('["Service"]', 0))
        # same story when the common payer is a busy key: no link
        con3, _ = db(self); busy = {FUNDER: 5000}
        e1 = self.setup(con3, W1, T0, cash=3000.0, price=0.2)
        enrich.evaluate(con3, e1, rpc=chain_rpc(rec(W1, T0), [(W1, FUNDER, 5_000_000_000, 890, "0xf1")], nonce=busy), get_json=activity({W1: rows(T0)}), now=lambda: T0 + 50)
        self.assertEqual(con3.execute("select count(*) from links").fetchone()[0], 0)

    def test_a_missing_receipt_postpones_the_entry(self):
        con, _ = db(self); e = self.setup(con, W1, T0)
        rows = {W1: [[T0 - 100, "D", None, None, 4000.0, None, None, "0xdep1"], [T0, "T", COND, "BUY", 2000.0, 0.06, 0, None]]}
        with self.assertRaises(enrich.NotReady):
            enrich.evaluate(con, e, rpc=chain_rpc({}, []), get_json=activity(rows))
        self.assertEqual(con.execute("select count(*) from alerts").fetchone()[0], 0)


class SharedCode(unittest.TestCase):
    def test_selftests_of_the_code_shared_with_the_study(self):
        asof._selftest(); chainfund._selftest(); models._selftest()


if __name__ == "__main__":
    unittest.main()
