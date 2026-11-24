"""Synthetic regression fixtures for the cohort ledger (no network). Run: python3 -m unittest discover -s tests"""
import gzip
import hashlib
import json
import sys
import tempfile
import threading
import unittest
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import ledger_build as B  # noqa: E402
import ledger_collect as C  # noqa: E402

ACC = "0x" + "a1" * 20
OTHER = "0x" + "b2" * 20
SIGNER = "0x" + "c3" * 20
EX_V2 = "0xe111180000d2663c0091e4f400237545b87b996b"
EX_V1 = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"
YES, NO = 1111, 2222
COND = "0x" + "77" * 32


def t(a):
    return "0x" + "0" * 24 + a[2:]


def word(n):
    return "%064x" % n


def log(tx, li, address, topics, data_words, block=100, bhash=None, ts=1_000_000):
    return {"address": address, "topics": topics, "data": "0x" + "".join(word(w) for w in data_words),
            "block": block, "block_hash": bhash or ("0x" + "%064x" % block), "ts": ts, "tx": tx, "log_index": li,
            "removed": False}


def erc20(tx, li, frm, to, v, token=B.PUSD, **kw):
    return log(tx, li, token, [B.TRANSFER, t(frm), t(to)], [v], **kw)


def single(tx, li, frm, to, tid, v, **kw):
    return log(tx, li, B.CTF, [B.TRANSFER_SINGLE, t(EX_V2), t(frm), t(to)], [tid, v], **kw)


def fill_v2(tx, li, maker, side, tid, mamt, tamt, fee, taker=OTHER, **kw):
    return log(tx, li, EX_V2, [B.V2_FILL, "0x" + "11" * 32, t(maker), t(taker)], [side, tid, mamt, tamt, fee, 0, 0], **kw)


def as_dict(logs):
    return {(x["tx"], x["log_index"]): x for x in logs}


def run_book(logs, payout=None, accounts=(ACC,)):
    recs, _ = B.account_txs(as_dict(logs), list(accounts))
    cond_of = {(B.CTF, YES): (COND, 0, "Yes"), (B.CTF, NO): (COND, 1, "No")}
    pos, cash, flags, fills, wallet, ledger = B.book(recs, cond_of, payout or {}, {})
    return recs, pos, cash, flags, wallet, cond_of


def net_of(pos, cash, cond_of, payout, key=(ACC, COND)):
    v, src = B.value_inventory(pos[key], cond_of, payout, {})
    return (None if v is None else cash[key] + v), v, src


class Accounting(unittest.TestCase):
    def test_buy_with_fee_then_win_counts_fee_once(self):
        # BUY 10 YES at 0.40: pays 4.000000 + fee 0.100000 = 4.100000 pUSD; YES wins
        logs = [fill_v2("0x01", 1, ACC, 0, YES, 4_000_000, 10_000_000, 100_000),
                erc20("0x01", 2, ACC, EX_V2, 4_100_000), single("0x01", 3, EX_V2, ACC, YES, 10_000_000)]
        payout = {COND: ([1, 0], 1)}
        recs, pos, cash, *_rest = run_book(logs, payout)
        cond_of = _rest[-1]
        net, value, src = net_of(pos, cash, cond_of, payout)
        self.assertEqual(net, Fraction(10_000_000 - 4_100_000))  # 5.900000, fee inside the cash, not again
        self.assertEqual(src, "RESOLUTION_PAYOUT")

    def test_partial_sale_average_cost_and_identity(self):
        logs = [fill_v2("0x01", 1, ACC, 0, YES, 4_000_000, 10_000_000, 0), erc20("0x01", 2, ACC, EX_V2, 4_000_000),
                single("0x01", 3, EX_V2, ACC, YES, 10_000_000),
                fill_v2("0x02", 1, ACC, 1, YES, 4_000_000, 2_400_000, 0, block=101),
                erc20("0x02", 2, EX_V2, ACC, 2_400_000, block=101), single("0x02", 3, ACC, EX_V2, YES, 4_000_000, block=101)]
        payout = {COND: ([0, 1], 1)}  # YES loses
        _, pos, cash, *_r = run_book(logs, payout)
        p = pos[(ACC, COND)][(B.CTF, YES)]
        self.assertEqual(p.qty, 6_000_000)
        self.assertEqual(p.realized, Fraction(2_400_000 - 1_600_000))   # sold 4 of 10 at cost 0.40
        net, value, _ = net_of(pos, cash, _r[-1], payout)
        self.assertEqual(net, Fraction(-4_000_000 + 2_400_000))
        self.assertEqual(p.realized + (value - p.cost) - p.transfer_out_cost, net)

    def test_split_merge_redeem(self):
        # split 10 -> 10 YES + 10 NO, merge 4 sets, redeem 6 YES winning
        logs = [erc20("0x01", 1, ACC, B.CTF, 10_000_000, token=B.USDC_E),
                single("0x01", 2, "0x" + "0" * 40, ACC, YES, 10_000_000), single("0x01", 3, "0x" + "0" * 40, ACC, NO, 10_000_000),
                log("0x01", 4, B.CTF, [list(B.EVENTS)[0], t(ACC), "0x" + "0" * 64, COND], [int(B.USDC_E, 16), 64, 10_000_000, 2, 1, 2]),
                single("0x02", 1, ACC, "0x" + "0" * 40, YES, 4_000_000, block=101),
                single("0x02", 2, ACC, "0x" + "0" * 40, NO, 4_000_000, block=101),
                erc20("0x02", 3, B.CTF, ACC, 4_000_000, token=B.USDC_E, block=101),
                log("0x02", 4, B.CTF, [list(B.EVENTS)[1], t(ACC), "0x" + "0" * 64, COND], [int(B.USDC_E, 16), 64, 4_000_000, 2, 1, 2], block=101),
                single("0x03", 1, ACC, "0x" + "0" * 40, YES, 6_000_000, block=102),
                single("0x03", 2, ACC, "0x" + "0" * 40, NO, 6_000_000, block=102),
                erc20("0x03", 3, B.CTF, ACC, 6_000_000, token=B.USDC_E, block=102),
                log("0x03", 4, B.CTF, [list(B.EVENTS)[2], t(ACC), t(B.USDC_E), "0x" + "0" * 64], [int(COND, 16), 64, 6_000_000, 2, 1, 2], block=102)]
        payout = {COND: ([1, 0], 1)}
        recs, pos, cash, *_r = run_book(logs, payout)
        self.assertEqual({k for r in recs.values() for k in r["kinds"]}, {"SPLIT", "MERGE", "REDEEM"})
        net, value, _ = net_of(pos, cash, _r[-1], payout)
        self.assertEqual(net, 0)                      # a complete set is always worth one unit of collateral
        for p in pos[(ACC, COND)].values():
            self.assertEqual(p.qty, 0)
        total = sum((p.realized for p in pos[(ACC, COND)].values()), Fraction(0))
        self.assertEqual(total, net)

    def test_multiple_fills_one_transaction(self):
        logs = [fill_v2("0x01", 1, ACC, 0, YES, 1_000_000, 2_000_000, 0), fill_v2("0x01", 2, ACC, 0, YES, 3_000_000, 5_000_000, 0),
                erc20("0x01", 3, ACC, EX_V2, 4_000_000), single("0x01", 4, EX_V2, ACC, YES, 7_000_000)]
        recs, pos, cash, flags, *_ = run_book(logs)
        p = pos[(ACC, COND)][(B.CTF, YES)]
        self.assertEqual((p.qty, p.cost, len(recs[(ACC, "0x01")]["fills"])), (7_000_000, Fraction(4_000_000), 2))
        self.assertNotIn("TRADE_CASH_RESIDUAL", flags.get((ACC, COND), {}))

    def test_counterparty_and_signer_are_not_the_account(self):
        # the account appears only as the taker field of someone else's fill, and a signer EOA owns another fill
        logs = [fill_v2("0x01", 1, OTHER, 0, YES, 1_000_000, 2_000_000, 0, taker=ACC),
                fill_v2("0x01", 2, SIGNER, 0, YES, 1_000_000, 2_000_000, 0)]
        recs, *_ = run_book(logs, accounts=(ACC,))
        self.assertEqual(recs, {})

    def test_non_collateral_token_and_wrong_decimals_are_not_cash(self):
        fake = "0x" + "de" * 20  # an 18-decimal look-alike must never be valued as collateral
        logs = [erc20("0x01", 1, OTHER, ACC, 5 * 10**18, token=fake)]
        recs, *_ = run_book(logs)
        r = recs[(ACC, "0x01")]
        self.assertEqual((r["cash"], r["kinds"]), ({}, ["NO_NET_CHANGE"]))
        self.assertEqual(r["other_tokens"][fake], 5 * 10**18)

    def test_deposit_is_not_trading_pnl(self):
        logs = [erc20("0x01", 1, OTHER, ACC, 50_000_000)]
        recs, pos, cash, flags, wallet, _ = run_book(logs)
        self.assertEqual((dict(pos), wallet[ACC]["non_trading_cash_in"]), ({}, 50_000_000))

    def test_share_transfer_in_is_flagged_zero_cost(self):
        logs = [single("0x01", 1, OTHER, ACC, YES, 3_000_000)]
        recs, pos, cash, *_ = run_book(logs)
        p = pos[(ACC, COND)][(B.CTF, YES)]
        self.assertEqual((recs[(ACC, "0x01")]["kinds"], p.transfer_in, p.cost), (["SHARE_TRANSFER"], 3_000_000, 0))

    def test_out_of_order_input_gives_same_book(self):
        logs = [fill_v2("0x01", 1, ACC, 0, YES, 4_000_000, 10_000_000, 0), erc20("0x01", 2, ACC, EX_V2, 4_000_000),
                single("0x01", 3, EX_V2, ACC, YES, 10_000_000),
                fill_v2("0x02", 1, ACC, 1, YES, 4_000_000, 2_400_000, 0, block=101),
                erc20("0x02", 2, EX_V2, ACC, 2_400_000, block=101), single("0x02", 3, ACC, EX_V2, YES, 4_000_000, block=101)]
        a = run_book(logs)[1][(ACC, COND)][(B.CTF, YES)]
        b = run_book(list(reversed(logs)))[1][(ACC, COND)][(B.CTF, YES)]
        self.assertEqual((a.qty, a.cost, a.realized), (b.qty, b.cost, b.realized))

    def test_same_block_follows_log_order_not_hash_order(self):
        # buy in tx 0xff (logs 1-3) then sell in tx 0x01 (logs 10-12), same block: the hash order would sell first
        logs = [fill_v2("0xff", 1, ACC, 0, YES, 4_000_000, 10_000_000, 0), erc20("0xff", 2, ACC, EX_V2, 4_000_000),
                single("0xff", 3, EX_V2, ACC, YES, 10_000_000),
                fill_v2("0x01", 10, ACC, 1, YES, 4_000_000, 2_400_000, 0), erc20("0x01", 11, EX_V2, ACC, 2_400_000),
                single("0x01", 12, ACC, EX_V2, YES, 4_000_000)]
        _, pos, *_ = run_book(logs)
        p = pos[(ACC, COND)][(B.CTF, YES)]
        self.assertFalse(p.negative_inventory)
        self.assertEqual(p.realized, Fraction(2_400_000 - 1_600_000))

    def test_shares_sent_to_a_burn_sink_are_a_disposal_not_a_transfer(self):
        dead = "0x000000000000000000000000000000000000dead"
        logs = [fill_v2("0x01", 1, ACC, 0, YES, 4_000_000, 10_000_000, 0), erc20("0x01", 2, ACC, EX_V2, 4_000_000),
                single("0x01", 3, EX_V2, ACC, YES, 10_000_000), single("0x02", 1, ACC, dead, YES, 10_000_000, block=101)]
        recs, pos, *_ = run_book(logs)
        self.assertEqual(recs[(ACC, "0x02")]["kinds"], ["BURN_FOR_COLLATERAL"])
        p = pos[(ACC, COND)][(B.CTF, YES)]
        self.assertEqual((p.realized, p.transfer_out_cost, p.qty), (Fraction(-4_000_000), 0, 0))

    def test_shares_sent_to_another_wallet_stay_a_transfer(self):
        logs = [single("0x01", 1, OTHER, ACC, YES, 1), single("0x02", 1, ACC, OTHER, YES, 1, block=101)]
        recs, *_ = run_book(logs)
        self.assertEqual(recs[(ACC, "0x02")]["kinds"], ["SHARE_TRANSFER"])

    def test_missing_price_point_is_unknown_not_zero(self):
        logs = [fill_v2("0x01", 1, ACC, 0, YES, 4_000_000, 10_000_000, 0), erc20("0x01", 2, ACC, EX_V2, 4_000_000),
                single("0x01", 3, EX_V2, ACC, YES, 10_000_000)]
        _, pos, cash, *_r = run_book(logs, payout={})
        net, value, src = net_of(pos, cash, _r[-1], {})
        self.assertEqual((net, value, src), (None, None, "UNKNOWN"))

    def test_batched_burn_across_markets_follows_official_payouts(self):
        # one transaction burns 10 losing shares of market A and 10 winning shares of market B for 10 collateral,
        # through a contract that emits no event naming the user
        cond_b, win_b = "0x" + "88" * 32, 3333
        logs = [single("0x01", 1, ACC, "0x" + "0" * 40, YES, 10_000_000), single("0x01", 2, ACC, "0x" + "0" * 40, win_b, 10_000_000),
                erc20("0x01", 3, "0x" + "0" * 40, ACC, 10_000_000)]
        recs, _ = B.account_txs(as_dict(logs), [ACC])
        self.assertEqual(recs[(ACC, "0x01")]["kinds"], ["BURN_FOR_COLLATERAL"])
        cond_of = {(B.CTF, YES): (COND, 0, "Yes"), (B.CTF, win_b): (cond_b, 1, "No")}
        payout = {COND: ([0, 1], 1), cond_b: ([0, 1], 1)}
        pos, cash, *_ = B.book(recs, cond_of, payout, {})
        self.assertEqual((cash[(ACC, COND)], cash[(ACC, cond_b)]), (0, 10_000_000))

    def test_split_payout_is_rounded_down_like_the_contract(self):
        # a 50/50 resolution pays floor(shares / 2): 3 units of a 7-unit position, never 3.5
        self.assertEqual(B.payout_units(7, ([1, 1], 2), 0), 3)
        logs = [single("0x01", 1, OTHER, ACC, YES, 7), single("0x02", 1, ACC, "0x" + "0" * 40, YES, 7, block=101),
                erc20("0x02", 2, "0x" + "0" * 40, ACC, 3, block=101)]
        recs, _ = B.account_txs(as_dict(logs), [ACC])
        cond_of = {(B.CTF, YES): (COND, 0, "Yes")}
        pos, cash, flags, *_ = B.book(recs, cond_of, {COND: ([1, 1], 2)}, {})
        self.assertNotIn("BURN_CASH_NOT_PAYOUT", flags.get((ACC, COND), {}))
        self.assertEqual(cash[(ACC, COND)], 3)

    def test_v1_fee_withheld_and_refunded_uses_actual_shares(self):
        # V1 BUY: OrderFilled says 10 shares and fee 0.1 share; the account receives 9.9 then a 0.1 refund
        module = "0xe3f18acc55091e2c48d883fc8c8413319d4ab7b0"
        logs = [log("0x01", 1, EX_V1, [B.V1_FILL, "0x" + "11" * 32, t(ACC), t(OTHER)], [0, YES, 4_000_000, 10_000_000, 100_000]),
                erc20("0x01", 2, ACC, EX_V1, 4_000_000, token=B.USDC_E), single("0x01", 3, EX_V1, ACC, YES, 9_900_000),
                single("0x01", 4, module, ACC, YES, 100_000)]
        _, pos, *_ = run_book(logs)
        p = pos[(ACC, COND)][(B.CTF, YES)]
        self.assertEqual((p.qty, p.cost, p.fees), (10_000_000, Fraction(4_000_000), 0))


class Marks(unittest.TestCase):
    def test_future_price_point_is_never_used(self):
        pts = [{"t": 100, "p": 0.4}, {"t": 200, "p": 0.5}, {"t": 301, "p": 0.99}]
        self.assertEqual(B.select_mark(pts, 300), (200, 0.5))
        self.assertIsNone(B.select_mark([{"t": 301, "p": 0.9}], 300))

    def test_open_inventory_uses_a_timestamped_mark(self):
        logs = [fill_v2("0x01", 1, ACC, 0, YES, 4_000_000, 10_000_000, 0), erc20("0x01", 2, ACC, EX_V2, 4_000_000),
                single("0x01", 3, EX_V2, ACC, YES, 10_000_000)]
        _, pos, cash, *_r = run_book(logs)
        marks = {(B.CTF, YES): {"price": 0.55, "source": "CLOB prices-history", "time_utc": "2026-11-23T18:00:00Z"}}
        v, src = B.value_inventory(pos[(ACC, COND)], _r[-1], {}, marks)
        self.assertEqual((v, src), (Fraction(5_500_000), "MARK:CLOB prices-history@2026-11-23T18:00:00Z"))


class Loading(unittest.TestCase):
    def _raw(self, d, ranges, end=200):
        plan = {"start_block": 1, "end_block": end, "provider": "test", "accounts": [ACC], "chunk_size": 80}
        (d / "plan.json").write_text(json.dumps(plan))
        cks = []
        for i, (lo, hi, logs) in enumerate(ranges):
            rec = {"logs": logs}
            blob = gzip.compress(json.dumps(rec).encode(), mtime=0)
            rel = f"raw/f/c0/{i}.json.gz"
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_bytes(blob)
            cks.append({"filter": "fills", "chunk": "c0", "from": lo, "to": hi, "n": len(logs), "file": rel,
                        "sha256": hashlib.sha256(blob).hexdigest()})
        (d / "checkpoint.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cks))

    @staticmethod
    def raw_log(tx, li, block, bhash, data="0x01"):
        return {"transactionHash": tx, "logIndex": hex(li), "address": B.PUSD, "topics": [B.TRANSFER],
                "data": data, "blockNumber": hex(block), "blockHash": bhash, "blockTimestamp": hex(5), "removed": False}

    def test_duplicate_log_ids_are_merged_and_conflicts_reported(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            a = self.raw_log("0xaa", 1, 10, "0xh1")
            self._raw(d, [(1, 100, [a, a]), (101, 200, [self.raw_log("0xaa", 1, 10, "0xh1", data="0x02")])])
            plan, cov, logs, problems = B.load(d)
            self.assertEqual(len(logs), 1)
            self.assertEqual([p["kind"] for p in problems], ["DUPLICATE_DIFFERS"])
            self.assertTrue(cov["fills/c0"]["complete"])

    def test_reorged_block_is_detected_and_orphan_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self._raw(d, [(1, 200, [self.raw_log("0xaa", 1, 10, "0xh1"), self.raw_log("0xbb", 1, 10, "0xh2")])])
            _, _, logs, problems = B.load(d)
            self.assertIn("BLOCK_HASH_CONFLICT", [p["kind"] for p in problems])
            kept, dropped = B.canonical(logs, {10: "0xh2"})
            self.assertEqual((list(kept), dropped), ([("0xbb", 1)], [("0xaa", 1)]))

    def test_gap_in_ranges_is_not_complete(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self._raw(d, [(1, 100, []), (150, 200, [])])
            _, cov, _, _ = B.load(d)
            self.assertFalse(cov["fills/c0"]["complete"])


class Collector(unittest.TestCase):
    def test_cap_halves_and_rate_limit_is_never_empty(self):
        calls = []

        def fetch(url, flt, lo, hi):
            calls.append((lo, hi))
            if hi - lo + 1 > 50:
                raise C.TooMany("Query returned more than 20000 results")
            if lo == 151:
                raise C.net.SourceError("HTTP 429", 429)
            return [], "sha"

        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            plan = {"start_block": 1, "end_block": 200, "provider": "x"}
            with self.assertRaises(C.net.SourceError):
                C.run_stream(d, plan, "fills", "c0", {"topics": [None]}, threading.Lock(), lambda m: None,
                             fetch=fetch, sleep=lambda s: None)
            ck = [json.loads(x) for x in (d / "checkpoint.jsonl").read_text().splitlines()]
            self.assertEqual(ck[-1]["to"], 150)          # accepted up to the failure, nothing beyond
            calls.clear()
            ok = lambda url, flt, lo, hi: ([], "sha") if hi - lo < 50 else (_ for _ in ()).throw(C.TooMany("more than results"))
            C.run_stream(d, plan, "fills", "c0", {"topics": [None]}, threading.Lock(), lambda m: None, fetch=ok,
                         sleep=lambda s: None)
            ck = [json.loads(x) for x in (d / "checkpoint.jsonl").read_text().splitlines()]
            self.assertEqual((ck[0]["from"], ck[-1]["to"]), (1, 200))   # resumed at 151, finished, contiguous

    def test_provider_extra_log_is_refused(self):
        bad = {"address": EX_V2, "topics": [B.V1_FILL], "blockNumber": hex(5), "removed": False}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                C.run_stream(Path(d), {"start_block": 1, "end_block": 10, "provider": "x"}, "fills", "c0",
                             {"address": [EX_V2], "topics": [[B.V2_FILL]]}, threading.Lock(), lambda m: None,
                             fetch=lambda *a: ([bad], "sha"), sleep=lambda s: None)


class Formatting(unittest.TestCase):
    def test_fmt_exact(self):
        self.assertEqual(B.fmt(Fraction(-2_407_870)), "-2.407870")
        self.assertEqual(B.fmt(Fraction(1, 3)), "0.000000")
        self.assertEqual(B.fmt(None), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
