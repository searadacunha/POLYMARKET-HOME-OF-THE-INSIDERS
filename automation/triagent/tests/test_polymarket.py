"""Collector and receipts, tested on real API payload shapes (addresses replaced, see fixtures/README.md)."""
import json

from tests.base import Case, fixture
from triagent import polymarket
from triagent.store import MIGRATIONS, now
from triagent.util import ProviderError

EXP = fixture("expected.json")


def rpc_post(receipts: dict, head: int = 10**9):
    def post(url, method="POST", body=None, **kw):
        if body["method"] == "eth_blockNumber":
            return 200, json.dumps({"jsonrpc": "2.0", "id": 1, "result": hex(head)}).encode()
        result = receipts.get(body["params"][0])
        return 200, json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()
    return post


class PayloadShapeTests(Case):
    def test_real_trade_feed_rows_parse(self):
        page = fixture("trades_v2_cash5000.json")
        self.assertTrue(all(polymarket.well_formed(r) for r in page["data"]))
        self.assertTrue(all(r["size"] * r["price"] >= 4999 for r in page["data"]))  # filter_type=CASH works
        self.assertNotIn("usdc_size", page["data"][0])  # /v2/trades has no usdc_size: computed size*price

    def test_real_activity_fields(self):
        rows = fixture("activity_v2_deposit_withdrawal.json")["data"] + fixture("activity_v2_trade_redeem.json")["data"]
        for r in rows:
            for k in ("proxy_wallet", "timestamp", "type", "usdc_size", "transaction_hash"):
                self.assertIn(k, r)
        self.assertEqual({r["type"] for r in rows} >= {"DEPOSIT", "WITHDRAWAL", "TRADE", "REDEEM"}, True)
        self.assertEqual(polymarket.strip({"name": "x", "bio": "y", "type": "TRADE"}), {"type": "TRADE"})

    def test_deposit_funder_from_real_receipt(self):
        receipt = fixture("receipt_deposit.json")["result"]
        found = polymarket.deposit_source(receipt, EXP["proxy"])
        self.assertEqual((found["funder"], found["via"], found["token"]), (EXP["funder"], "wrapped", polymarket.USDC_E))

    def test_deposit_walks_back_through_relay_contracts(self):
        payer, wallet, onramp, proxy = ("0x" + c * 40 for c in "1234")
        word = lambda a: "0x" + "0" * 24 + a[2:]  # noqa: E731
        log = lambda tok, a, b, v: {"address": tok, "topics": [polymarket.TRANSFER, word(a), word(b)], "data": hex(v)}  # noqa: E731
        receipt = {"logs": [log(polymarket.USDC_E, payer, wallet, 5), log(polymarket.USDC_E, wallet, wallet, 5),
                            log(polymarket.USDC_E, wallet, onramp, 5), log(polymarket.USDC_E, onramp, polymarket.COLLATERAL, 5),
                            log(polymarket.COLLATERAL, polymarket.ZERO, proxy, 5)]}
        found = polymarket.deposit_source(receipt, proxy)
        self.assertEqual((found["funder"], found["path"]), (payer, [onramp, wallet]))

    def test_withdrawal_destination_from_real_receipt(self):
        receipt = fixture("receipt_withdrawal.json")["result"]
        found = polymarket.withdrawal_destination(receipt, EXP["proxy"])
        self.assertEqual(found["destination"], EXP["destination"])
        self.assertIsNone(polymarket.deposit_source(receipt, EXP["proxy"]))  # a withdrawal is not a funding


class CollectorTests(Case):
    def row(self, i, ts, **kw):
        base = {"proxy_wallet": f"0x{i:040x}", "side": "BUY", "token_id": "1", "condition_id": "0xc1",
                "size": 20000.0, "price": 0.5, "timestamp": ts, "transaction_hash": f"0x{i:064x}",
                "title": "Market", "outcome": "Yes", "name": "PRIVATE", "bio": "PRIVATE"}
        return base | kw

    def test_checkpoint_pagination_dedup_and_malformed(self):
        t = now()
        pages = {None: {"data": [self.row(1, t), self.row(2, t - 10), {"broken": True},
                                 self.row(3, t, size="12")],
                        "pagination": {"next_cursor": "c2"}},
                 "c2": {"data": [self.row(4, t - 20)], "pagination": {"next_cursor": None}}}
        calls = []

        def fetch(url):
            cursor = url.split("cursor=")[1] if "cursor=" in url else None
            calls.append(cursor)
            return pages[cursor]
        first = polymarket.collect_trades(self.cfg, self.store, fetch)
        self.assertEqual((first["pages"], first["inserted"], first["malformed"]), (1, 2, 2))  # bootstrap: 1 page
        self.assertEqual(self.store.query("SELECT count(*) n FROM trades")[0]["n"], 2)
        self.assertNotIn("PRIVATE", json.dumps(self.store.query("SELECT * FROM trades")))
        second = polymarket.collect_trades(self.cfg, self.store, fetch)
        self.assertEqual(second["inserted"], 1)  # page 2 reached, page 1 rows deduplicated
        self.assertEqual(int(self.store.get_kv("trades_checkpoint_ts")), t)

    def test_gap_is_logged_when_backfill_limit_hit(self):
        self.store.set_kv("trades_checkpoint_ts", now() - 10**6)
        self.cfg.values["BACKFILL_MAX_PAGES"] = "2"
        fetch = lambda url: {"data": [self.row(5, now())], "pagination": {"next_cursor": "more"}}  # noqa: E731
        polymarket.collect_trades(self.cfg, self.store, fetch)
        self.assertTrue(self.store.query("SELECT * FROM events WHERE message LIKE '%gap may exist%'"))

    def test_bad_payload_raises(self):
        with self.assertRaises(ProviderError):
            polymarket.collect_trades(self.cfg, self.store, lambda url: {"unexpected": 1})
        with self.assertRaises(ProviderError):
            polymarket.activity("0x" + "1" * 40, lambda url: [])

    def test_alert_creates_one_mission_for_confirmed_trade(self):
        t = now() - 3600
        wallet, tx = "0x" + "a" * 40, "0x" + "b" * 64
        self.store.execute("""INSERT INTO trades(tx_hash,proxy_wallet,condition_id,token_id,side,size,price,usdc,ts,
                              title,outcome,seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (tx, wallet, "0xc1", "1", "BUY", 40000, 0.5, 20000, t, "Market", "Yes", now()))
        activity = {"addresses": {}, "data": [
            {"type": "DEPOSIT", "timestamp": t - 7200, "usdc_size": 20000, "transaction_hash": "0x" + "d" * 64},
            {"type": "TRADE", "timestamp": t, "usdc_size": 20000, "condition_id": "0xc1", "transaction_hash": tx},
            {"type": "TRADE", "timestamp": t + 999, "usdc_size": 1, "condition_id": "0xc2", "transaction_hash": tx},
        ], "pagination": {"next_cursor": None}}
        trade_receipt = {"status": "0x1", "blockNumber": hex(100), "logs": []}
        post = rpc_post({tx: trade_receipt, "0x" + "d" * 64: None}, head=1000)
        result = polymarket.scan(self.cfg, self.store, fetch=lambda url: activity, post=post)
        self.assertEqual(result["alerts"], 1)
        alert = self.store.query("SELECT * FROM alerts")[0]
        flags = json.loads(alert["flags_json"])
        self.assertTrue({"NEW_WALLET", "FRESH_FUNDING", "FEW_PRIOR_TRADES", "CONCENTRATED"} <= set(flags))
        features = json.loads(alert["features_json"])["features"]
        self.assertEqual(features["n_trades_before"], 0)  # the later trade (t+999) is not visible at t
        job = self.store.jobs("origin='collector'")[0]
        self.assertIn("NOT evidence", job["task"])
        self.assertEqual(polymarket.scan(self.cfg, self.store, fetch=lambda url: activity, post=post)["alerts"], 0)

    def test_reorged_trade_is_ignored(self):
        tx = "0x" + "e" * 64
        self.store.execute("""INSERT INTO trades(tx_hash,proxy_wallet,condition_id,token_id,side,size,price,usdc,ts,
                              title,outcome,seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (tx, "0x" + "f" * 40, "0xc1", "1", "BUY", 40000, 0.5, 20000, now() - 600, "M", "Yes", now()))
        polymarket.scan(self.cfg, self.store, fetch=lambda url: {"data": []}, post=rpc_post({tx: None}))
        self.assertEqual(self.store.query("SELECT onchain FROM trades")[0]["onchain"], "missing")
        self.assertEqual(self.store.query("SELECT count(*) n FROM alerts")[0]["n"], 0)

    def test_agent_reported_edge_needs_matching_receipt_log(self):
        receipt = fixture("receipt_deposit.json")["result"]
        tx = receipt["transactionHash"]
        post = rpc_post({tx: receipt})
        good = {"src": EXP["funder"], "dst": polymarket.COLLATERAL, "kind": "DIRECT_TRANSFER", "chain": "polygon",
                "tx_hash": tx, "token": "usdc.e", "amount": "1", "timestamp": 1, "method": "m"}
        wrong = dict(good, src="0x" + "9" * 40)
        levels = [r["level"] for r in polymarket.verify_reported_edges(self.cfg, self.store, "job", [good, wrong], post)]
        self.assertEqual(levels, ["receipt_verified", "agent_reported"])
        edge = self.store.query("SELECT * FROM edges WHERE level='receipt_verified'")[0]
        self.assertTrue((self.cfg.evidence_dir / f"{edge['evidence_sha256']}.json").is_file())

    def test_shared_funder_needs_low_fanout(self):
        funder = "0x" + "c" * 40
        for i in range(3):
            self.store.add_edge(funder, f"0x{i:040x}", "DIRECT_TRANSFER", method="t", level="receipt_verified",
                                chain="polygon", tx_hash=f"0x{i:064x}", ts=100)
        self.assertEqual(polymarket.fanout(self.store, funder, 200, as_source=True), 3)
        self.assertEqual(polymarket.fanout(self.store, funder, 50, as_source=True), 0)  # as-of: later edges unseen


class ServiceLabelTests(Case):
    def test_labelled_service_is_never_a_shared_funder(self):
        solver, user_funder = "0x" + "5" * 40, "0x" + "6" * 40
        page = {"addresses": {solver: {"tags": [{"name": "Relay: Solver"}]}}}
        tags = polymarket.labels(self.store, [solver, user_funder], lambda url: page)
        self.assertEqual(tags, {solver: ["Relay: Solver"], user_funder: []})
        self.assertEqual(polymarket.labels(self.store, [solver], lambda url: 1 / 0), {solver: ["Relay: Solver"]})  # cache

    def test_unavailable_labels_suppress_link_flags(self):
        def down(url):
            raise ProviderError("transient", "down")
        self.assertIsNone(polymarket.labels(self.store, ["0x" + "7" * 40], down))
        self.assertEqual(self.store.schema_version(), len(MIGRATIONS))
