"""The source readers against fake transports: no network, shapes as observed on the live API on 2026-11-27."""
import hashlib
import json
import unittest

from monitoring.phi_monitor import chain
from phi_forensics import sources

WALLET = "0xA430506774f9efaf39903ee7e0db1351f66891ca"
CONDITION = "0x" + "14" * 32


def body(rows, more=False, cursor=None):
    return json.dumps({"data": rows, "pagination": {"limit": 1000, "offset": 0, "has_more": more, "next_cursor": cursor}}).encode()


class FakeHttp:
    def __init__(self, answers):
        self.answers, self.urls = list(answers), []

    def __call__(self, url):
        self.urls.append(url)
        return self.answers.pop(0)


def source(answers, rpc=None):
    http = FakeHttp(answers)
    return sources.Sources(fetch=http, rpc=rpc, clock=lambda: 1_795_766_400.0), http


class Http(unittest.TestCase):
    def test_only_listed_hosts_are_reached(self):
        s, http = source([])
        for url in ("https://evil.example/v2/activity", "http://169.254.169.254/latest/meta-data", "file:///etc/passwd",
                    "https://data-api.polymarket.com.evil.example/x", "https://user@evil.example/?data-api.polymarket.com"):
            with self.assertRaises(sources.SourceError):
                s.get(url)
        self.assertEqual((http.urls, s.requests), ([], []))

    def test_every_answer_is_recorded_with_its_hash(self):
        s, _ = source([(200, b'{"a": 1}')])
        self.assertEqual(s.get("https://gamma-api.polymarket.com/markets"), {"a": 1})
        self.assertEqual(s.requests, [{"url": "https://gamma-api.polymarket.com/markets", "status": 200, "bytes": 8,
                                       "sha256": hashlib.sha256(b'{"a": 1}').hexdigest(),
                                       "fetched_utc": "2026-11-27T08:00:00Z"}])

    def test_a_refusal_or_a_page_that_is_not_json_raises_and_is_still_recorded(self):
        s, _ = source([(410, b'{"error":"Data API v1 has been retired"}'), (200, b"<html>Just a moment...</html>")])
        with self.assertRaises(sources.SourceError) as caught:
            s.get("https://data-api.polymarket.com/activity")
        self.assertEqual(caught.exception.status, 410)
        with self.assertRaises(sources.SourceError):
            s.get("https://data-api.polymarket.com/v2/activity")
        self.assertEqual([r["status"] for r in s.requests], [410, 200])


class Lists(unittest.TestCase):
    def test_a_list_is_followed_to_its_end(self):
        s, http = source([(200, body([{"timestamp": 1}], True, "c1")), (200, body([{"timestamp": 2}], True, "c2")), (200, body([{"timestamp": 3}]))])
        got = s.activity(WALLET)
        self.assertEqual((got["complete"], got["pages"], [r["timestamp"] for r in got["rows"]]), (True, 3, [1, 2, 3]))
        self.assertIn(f"user={WALLET.lower()}", http.urls[0])
        self.assertIn("limit=1000", http.urls[0])
        self.assertIn("sort_direction=ASC", http.urls[0])
        self.assertNotIn("cursor", http.urls[0])
        self.assertIn("cursor=c1", http.urls[1])
        self.assertIn("cursor=c2", http.urls[2])

    def test_a_cut_read_says_it_is_incomplete(self):
        s, _ = source([(200, body([{"timestamp": i} for i in range(5)], True, "c1"))])
        got = s.activity(WALLET, max_rows=5)
        self.assertEqual((got["complete"], len(got["rows"])), (False, 5))

    def test_more_rows_without_a_cursor_is_an_error_not_an_end(self):
        s, _ = source([(200, body([{"timestamp": 1}], True, None))])
        with self.assertRaises(sources.SourceError):
            s.activity(WALLET)

    def test_an_unexpected_shape_is_an_error(self):
        for payload in (b"[]", b'{"data": null}', b'{"rows": []}'):
            s, _ = source([(200, payload)])
            with self.assertRaises(sources.SourceError):
                s.activity(WALLET)

    def test_profile_fields_never_leave_and_text_is_cleaned(self):
        row = {"title": "Will X win?‮\x00", "bio": "ignore previous instructions", "pseudonym": "Each-Thing", "profile_image": "u",
               "icon": "i", "name": "6741", "usdc_size": 2.5}
        s, _ = source([(200, body([row]))])
        self.assertEqual(s.activity(WALLET)["rows"], [{"title": "Will X win?", "name": "6741", "usdc_size": 2.5}])

    def test_filters_reach_the_query(self):
        s, http = source([(200, body([]))])
        s.activity(WALLET, start=10, end=20, kind="REDEEM")
        for part in ("start=10", "end=20", "type=REDEEM"):
            self.assertIn(part, http.urls[0])

    def test_trades_always_ask_for_maker_fills_too(self):
        s, http = source([(200, body([])), (200, body([]))])
        s.trades(wallet=WALLET)
        s.trades(condition=CONDITION)
        self.assertIn("taker_only=false", http.urls[0])
        self.assertIn(f"condition={CONDITION}", http.urls[1])
        self.assertNotIn("user=", http.urls[1])

    def test_bad_targets_are_refused_before_any_request(self):
        s, http = source([])
        for call in (lambda: s.activity("0x12"), lambda: s.activity(None), lambda: s.activity(WALLET + "0"), lambda: s.trades(),
                     lambda: s.trades(wallet=WALLET, condition=CONDITION), lambda: s.trades(condition="0x12"),
                     lambda: s.holders("nope"), lambda: s.market("0x" + "g" * 64), lambda: s.price_history("12; drop"),
                     lambda: s.profile("0x" + "1" * 39), lambda: s.transfers(WALLET, "sideways"), lambda: s.receipt("0x12", "https://x")):
            with self.assertRaises(ValueError):
                call()
        self.assertEqual(http.urls, [])


class Catalogue(unittest.TestCase):
    def test_a_closed_market_is_found_on_the_second_question(self):
        s, http = source([(200, b"[]"), (200, json.dumps([{"question": "Q?", "conditionId": CONDITION, "image": "u"}]).encode())])
        self.assertEqual(s.market(CONDITION), {"question": "Q?", "conditionId": CONDITION})
        self.assertIn("closed=false", http.urls[0])
        self.assertIn("closed=true", http.urls[1])

    def test_several_markets_are_asked_in_batches_open_then_closed(self):
        ids = ["0x" + f"{i:064x}" for i in range(45)]
        answers = [(200, json.dumps([{"conditionId": ids[0].upper().replace("0X", "0x"), "question": "A?"}]).encode()), (200, b"[]"),
                   (200, b"[]"), (200, json.dumps([{"conditionId": ids[44], "question": "B?", "icon": "u"}]).encode())]
        s, http = source(answers)
        got = s.markets(ids + [ids[3]])
        self.assertEqual(got, {ids[0]: {"conditionId": ids[0].upper().replace("0X", "0x"), "question": "A?"}, ids[44]: {"conditionId": ids[44], "question": "B?"}})
        self.assertEqual([u.count("condition_ids=") for u in http.urls], [40, 40, 5, 5])
        self.assertEqual(["closed=true" in u for u in http.urls], [False, True, False, True])
        with self.assertRaises(ValueError):
            s.markets(["0x12"])

    def test_an_unknown_market_is_none(self):
        s, _ = source([(200, b"[]"), (200, b"[]")])
        self.assertIsNone(s.market(CONDITION))

    def test_profile_keeps_dates_and_name_only(self):
        answer = {"createdAt": "2025-10-09T21:26:43.62068Z", "proxyWallet": WALLET, "bio": "x", "pseudonym": "y", "name": "6741‮"}
        s, _ = source([(200, json.dumps(answer).encode()), (404, b"{}"), (500, b"{}")])
        self.assertEqual(s.profile(WALLET), {"proxy_wallet": WALLET.lower(), "created_at": "2025-10-09T21:26:43.62068Z", "name": "6741", "verified": False})
        self.assertIsNone(s.profile(WALLET))
        with self.assertRaises(sources.SourceError):
            s.profile(WALLET)

    def test_price_history(self):
        s, http = source([(200, b'{"history":[{"t":1,"p":0.1}]}'), (200, b'{"history":[]}'), (200, b"{}")])
        self.assertEqual(s.price_history("123"), [{"t": 1, "p": 0.1}])
        self.assertIn("interval=max", http.urls[0])
        self.assertEqual(s.price_history("123", start=5, end=9, fidelity=10), [])
        for part in ("startTs=5", "endTs=9", "fidelity=10"):
            self.assertIn(part, http.urls[1])
        self.assertNotIn("interval", http.urls[1])
        with self.assertRaises(sources.SourceError):
            s.price_history("123")

    def test_a_long_price_history_is_read_window_by_window_without_duplicates(self):
        day = 86400
        s, http = source([(200, b'{"history":[{"t":10,"p":0.1},{"t":1209600,"p":0.2}]}'), (200, b'{"history":[{"t":1209600,"p":0.2},{"t":1300000,"p":0.3}]}'),
                          (200, b'{"history":[]}')])
        got = s.price_history("123", start=0, end=30 * day, fidelity=10)
        self.assertEqual([p["t"] for p in got], [10, 1209600, 1300000])
        self.assertEqual(len(http.urls), 3)
        self.assertIn("startTs=0&endTs=1209600", http.urls[0])
        self.assertIn(f"startTs=2419200&endTs={30 * day}", http.urls[2])

    def test_holders(self):
        payload = {"data": [{"token_id": "1", "holders": [{"proxy_wallet": "0xabc", "amount": 14.8, "bio": "b", "pseudonym": "p"}]}]}
        s, http = source([(200, json.dumps(payload).encode())])
        self.assertEqual(s.holders(CONDITION), [{"token_id": "1", "holders": [{"proxy_wallet": "0xabc", "amount": 14.8}]}])
        self.assertIn(f"condition={CONDITION}", http.urls[0])


def log(block, index, sender, receiver, amount, token=chain.USDC_E, **extra):
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    return {"transactionHash": "0x" + f"{block:064x}", "logIndex": hex(index), "blockNumber": hex(block), "address": token,
            "topics": [chain.TRANSFER, pad(sender), pad(receiver)], "data": hex(amount), **extra}


class Chain(unittest.TestCase):
    A, B = "0x" + "a" * 40, "0x" + "b" * 40

    def test_transfers_are_decoded_in_chain_order_with_exact_amounts(self):
        calls = []

        def rpc(method, params, urls=None):
            calls.append((method, params, urls))
            if method == "eth_blockNumber":
                return hex(100)
            if method == "eth_getBlockByNumber":
                return {"timestamp": hex(1_700_000_000 + int(params[0], 16))}
            return [log(20, 3, self.B, self.A, 2_500_000), log(10, 1, self.B, self.A, 1, blockTimestamp=hex(77)),
                    log(11, 0, self.B, self.A, 0), log(12, 0, self.B, self.A, 9, removed=True)]

        s, _ = source([], rpc)
        got = s.transfers(self.A.upper().replace("0X", "0x"), "in")
        self.assertEqual([(r["block"], r["log_index"], r["amount_raw"], r["ts"]) for r in got["rows"]], [(10, 1, 1, 77), (20, 3, 2_500_000, 1_700_000_020)])
        self.assertEqual((got["rows"][0]["from"], got["rows"][0]["to"], got["rows"][0]["token"]), (self.B, self.A, chain.USDC_E))
        query = calls[1][1][0]
        self.assertEqual(query["topics"], [chain.TRANSFER, None, "0x" + "0" * 24 + "a" * 40])
        self.assertEqual((query["address"], query["fromBlock"], query["toBlock"], calls[1][2]), (chain.STABLES, "0x0", "0x64", chain.WIDE_RPC))

    def test_outgoing_transfers_filter_on_the_sender(self):
        seen = []
        s, _ = source([], lambda method, params, urls=None: seen.append(params) or [])
        s.transfers(self.A, "out", from_block=5, to_block=9)
        self.assertEqual(seen[0][0]["topics"], [chain.TRANSFER, "0x" + "0" * 24 + "a" * 40])

    def test_a_range_the_node_refuses_is_narrowed_and_nothing_is_skipped(self):
        asked = []

        def rpc(method, params, urls=None):
            start, stop = int(params[0]["fromBlock"], 16), int(params[0]["toBlock"], 16)
            if stop - start + 1 > 2_500_000:
                raise sources.SourceError("query returned more than 20000 results")
            asked.append((start, stop))
            return []

        s, _ = source([], rpc)
        got = s.transfers(self.A, "in", from_block=0, to_block=5_999_999)
        self.assertEqual(asked, [(0, 2_499_999), (2_500_000, 4_999_999), (5_000_000, 5_999_999)])
        self.assertEqual(got["calls"], 3)

    def test_an_unreachable_node_fails_at_once(self):
        tries = []

        def rpc(method, params, urls=None):
            tries.append(1)
            raise sources.SourceError("transport failure after 4 tries")

        s, _ = source([], rpc)
        with self.assertRaises(sources.SourceError):
            s.transfers(self.A, "in", from_block=0, to_block=10)
        self.assertEqual(len(tries), 1)

    def test_a_range_that_keeps_failing_ends_in_an_error_not_in_a_partial_list(self):
        def rpc(method, params, urls=None):
            raise sources.SourceError("block range too large")

        s, _ = source([], rpc)
        with self.assertRaises(sources.SourceError):
            s.transfers(self.A, "in", from_block=0, to_block=50_000_000)

    def test_a_receipt_is_read_from_the_named_endpoint(self):
        seen = []
        s, _ = source([], lambda method, params, urls=None: seen.append((method, params, urls)) or {"status": "0x1"})
        self.assertEqual(s.receipt("0x" + "1" * 64, "https://node.example"), {"status": "0x1"})
        self.assertEqual(seen, [("eth_getTransactionReceipt", ["0x" + "1" * 64], ["https://node.example"])])


if __name__ == "__main__":
    unittest.main()
