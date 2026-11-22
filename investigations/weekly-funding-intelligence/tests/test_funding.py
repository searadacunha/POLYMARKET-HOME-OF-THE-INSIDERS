import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from weekly_funding import accounts, collect
from weekly_funding.common import (
    ETH_POOLS,
    F2020,
    POOLS,
    TOKENS,
    TRANSFER,
    WITHDRAWAL,
    ZERO,
    addr_topic,
    bounds,
    network_query,
    save,
    week_of,
    weeks,
)
from weekly_funding.events import decode, verified_pack
from weekly_funding.report import Group, Quotes, classify, post
from weekly_funding.routes import guaranteed
from weekly_funding.statistics import analyze
from weekly_funding.token_routes import amount_onward
from decimal import Decimal as D

A = "0x" + "a" * 40
B = "0x" + "b" * 40
TX = "0x" + "a" * 64
BH = "0x" + "b" * 64
TOKEN = next(iter(TOKENS))
POOL = next(iter(POOLS))
W = "2026-W39"
START, END = bounds(W)


def transfer(to=A, idx=2):
    return [
        80,
        START + 1,
        BH,
        TX,
        idx,
        TOKEN,
        [TRANSFER, addr_topic(F2020), addr_topic(to)],
        "0x" + f"{500000:064x}",
    ]


def pack(rows):
    return dict(
        chain=137,
        stream="changenow",
        week=W,
        query=network_query(137, "changenow"),
        boundaries=[[[79, START - 1, BH], [80, START, BH]], [[89, END - 1, BH], [90, END, BH]]],
        logs=rows,
        ranges=[[80, 89, "rpc", len(rows)]],
        gaps=[],
    )


def withdraw(chain=137, pool=POOL, fee=12):
    return [
        80,
        START + 1,
        BH,
        TX,
        7,
        pool,
        [WITHDRAWAL, addr_topic(B)],
        "0x" + addr_topic(A)[2:] + "0" * 64 + f"{fee:064x}",
    ]


class Evidence(unittest.TestCase):
    def test_iso_utc(self):
        self.assertEqual(week_of(START - 1), "2026-W38")
        self.assertEqual(week_of(END), "2026-W40")
        self.assertEqual(list(weeks("2020-W53", "2021-W01")), ["2020-W53", "2021-W01"])

    def test_tornado_recipient_not_relayer_net_fee(self):
        e = decode(137, "tornado", withdraw())
        self.assertEqual((e.recipient, e.sender, e.units), (A, POOL, 100 * 10**18 - 12))
        with self.assertRaises(ValueError):
            decode(137, "tornado", withdraw(fee=100 * 10**18 + 1))
        pool = next(k for k, v in ETH_POOLS.items() if v[0] != "native")
        e = decode(1, "tornado", withdraw(1, pool, 1000))
        self.assertEqual(e.amount, D("99.999"))
        with self.assertRaises(ValueError):
            decode(1, "tornado", withdraw())

    def test_fee_only_zero_fake_token_bad_padding(self):
        self.assertIsNone(decode(137, "tornado", withdraw(fee=100 * 10**18)))
        self.assertIsNone(decode(137, "changenow", transfer(ZERO)))
        r = transfer()
        r[5] = A
        with self.assertRaises(ValueError):
            decode(137, "changenow", r)
        r = withdraw()
        r[7] = "0x1" + r[7][3:]
        with self.assertRaises(ValueError):
            decode(137, "tornado", r)

    def test_tx_plus_log_not_tx_only(self):
        r = transfer()
        self.assertEqual(len(verified_pack(pack([r, r, transfer(B, 3)]), W, 137, "changenow")), 2)
        with self.assertRaises(ValueError):
            verified_pack(pack([r, transfer(B)]), W, 137, "changenow")

    def test_missing_overlap_time_and_count_fail_closed(self):
        for mut in (
            lambda p: p["ranges"].append([89, 89, "rpc", 0]),
            lambda p: p["ranges"][0].__setitem__(0, 81),
            lambda p: p["logs"][0].__setitem__(1, END),
            lambda p: p["ranges"][0].__setitem__(3, 2),
        ):
            p = pack([transfer()])
            mut(p)
            with self.assertRaises(ValueError):
                verified_pack(p, W, 137, "changenow")

    def test_failed_range_can_recover_without_overwriting_success(self):
        p = pack([transfer()])
        p["ranges"] = [[80, 84, "rpc", 1]]
        p["gaps"] = [[85, 89, ["unavailable"]]]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / W / "changenow.json.gz"
            save(path, p)
            with (
                patch.object(collect, "boundary", side_effect=p["boundaries"]),
                patch.object(collect, "ranges", return_value=([[85, 89, "rpc", 0]], [], [])) as query,
            ):
                collect.collect_week(W, "changenow", root)
                self.assertEqual(query.call_args.args[2:4], (85, 89))
            finished = path.read_bytes()
            with (
                patch.object(collect, "boundary", side_effect=p["boundaries"]),
                patch.object(collect, "ranges", return_value=([[80, 89, "rpc", 0]], [], [])),
            ):
                with self.assertRaises(ValueError):
                    collect.collect_week(W, "changenow", root, True)
            self.assertEqual(path.read_bytes(), finished)

    def test_label_and_economic_identity(self):
        e = decode(137, "changenow", transfer())
        self.assertEqual(classify(e, {A: "fill"}, {}, {})[0], "POSSIBLE")
        self.assertEqual(classify(e, {B: "fill"}, {A: B}, {})[2], "signer_only_no_final_transfer")
        self.assertEqual(classify(e, {A: "fill"}, {}, {(137, A): "bridge"})[0], "REFUTED")
        e = decode(1, "tornado", withdraw(1, next(iter(ETH_POOLS))))
        self.assertEqual(classify(e, {A: "fill"}, {}, {})[2], "same_address_on_other_chain")
        self.assertEqual(
            classify(decode(137, "tornado", withdraw()), {A: "fill"}, {}, {})[0], "CONFIRMED_DIRECT"
        )

    def test_sums_before_threshold_and_frame_intersection(self):
        e = decode(137, "tornado", withdraw())
        g = Group()
        for _ in range(2):
            g.record(
                e, "CONFIRMED_DIRECT", A, "exact_trading_address", D("501"), "UNKNOWN", "TRADE_OBSERVED"
            )
        r = g.row(W, "Tornado Cash", "ALL", set(), {B})
        self.assertEqual(
            (r["funded_distinct"], r["funding_usd"], r["funded_ge_1000_observed"]), (1, "1002.00", 1)
        )
        self.assertEqual((r["funded_in_frame"], r["rate_in_covered_active_pm"]), (0, "0.00000000"))
        self.assertEqual(
            g.row(W, "Tornado Cash", "ALL", {A}, set())["rate_in_covered_active_pm"], "UNKNOWN"
        )
        self.assertEqual(
            g.row(W, "Tornado Cash", "ALL", set(), set(), False)["confirmed_direct"], "UNKNOWN"
        )

    def test_missing_price_has_no_peg_fallback(self):
        e = decode(137, "changenow", transfer())
        q = Quotes(
            {
                "ids": {"137:" + TOKEN: "coin"},
                "series": {"coin": {"confidence": 1, "prices": [{"price": 1, "timestamp": e.ts + 1}]}},
            }
        )
        self.assertEqual(q.quote(e), (None, None))
        g = Group()
        g.record(e, "CONFIRMED_DIRECT", A, "exact_trading_address", None, "YES", "TRADE_OBSERVED")
        self.assertEqual(g.row(W, "ChangeNOW", "ALL", set(), {A})["funding_usd"], "UNKNOWN")

    def test_first_strict_buy_and_right_censor(self):
        row = [START + 2, TX, "BUY", BH, "42", "19", "market"]
        r = {"buys": [row, row], "intervals": [[START + 1, START + 2, False]]}
        self.assertEqual(post(r, START)[1], tuple(row))
        self.assertEqual(post(r, START + 2)[:2], ("UNKNOWN", None))

    def test_malformed_or_ignored_api_filter_not_no_trade(self):
        reply = {"data": [], "pagination": {"has_more": True, "next_cursor": None}}
        with patch.object(accounts.net, "get_json", return_value=reply):
            self.assertEqual(accounts.profile(A, [START], END)["status"], "UNKNOWN")
        reply = {
            "data": [{"proxy_wallet": A, "timestamp": END + 5, "type": "TRADE", "side": "BUY"}],
            "pagination": {"has_more": False, "next_cursor": None},
        }
        with patch.object(accounts.net, "get_json", return_value=reply):
            with self.assertRaises(ValueError):
                accounts.activity_page(A, START, END)

    def test_distinct_roots_cannot_fund_a_route_by_amount_alone(self):
        seed = decode(137, "changenow", transfer())

        def raw(frm, to, idx, tx):
            return dict(
                address=TOKEN,
                topics=[TRANSFER, addr_topic(frm), addr_topic(to)],
                data=hex(seed.units),
                blockNumber=hex(80 + idx),
                logIndex=hex(idx),
                transactionHash=tx,
                removed=False,
            )

        s = raw(F2020, A, 2, TX)
        s["blockNumber"] = hex(seed.block)
        out = raw(A, B, 3, BH)
        self.assertEqual(amount_onward(seed, out, [s, out], "0x0"), seed.units)
        self.assertEqual(amount_onward(seed, out, [s, out], "0x1"), 0)
        extra = dict(s, transactionHash=BH, logIndex="0x1")
        self.assertEqual(amount_onward(seed, out, [extra, s, out], "0x0"), 0)

    def test_native_lower_bound_accounts_for_gas_balance_and_nonce(self):
        e = decode(137, "tornado", withdraw(fee=0))
        tx = dict(
            hash=TX,
            blockHash=BH,
            blockNumber="0x60",
            type="0x2",
            nonce="0xa",
            value=hex(e.units),
            input="0x",
            to=B,
        )
        tx["from"] = A
        receipt = dict(
            transactionHash=TX,
            blockHash=BH,
            blockNumber="0x60",
            gasUsed="0x5208",
            effectiveGasPrice="0x2",
            status="0x1",
            to=B,
        )
        receipt["from"] = A
        proof = dict(
            tx=tx,
            receipt=receipt,
            header=dict(number="0x60", timestamp=hex(e.ts + 10), hash=BH),
            code_before="0x",
            code_after="0x",
            nonce_before="0xa",
            nonce_after="0xb",
            balance_after="0x8",
        )
        self.assertEqual(guaranteed(e, proof), e.units - 42008)
        self.assertEqual(guaranteed(e, dict(proof, nonce_after="0xc")), 0)
        self.assertEqual(guaranteed(e, dict(proof, code_before="0xabcdef")), 0)


class Statistics(unittest.TestCase):
    def test_no_eligible_matches_no_p_values(self):
        r = analyze([], {"ChangeNOW": 4, "Tornado Cash": 0})
        self.assertEqual(len(r), 10)
        self.assertTrue(all(x["status"] == "NOT_TESTABLE" and x["p_holm"] is None for x in r))

    def test_positive_control_and_fixed_family(self):
        # Fixtures only. Planted concentration differences should be detectable at fixed n=20.
        rows = []
        for i in range(20):
            for grp, stakes in [("CONTROL", [1, 1]), ("ChangeNOW", [2])]:
                rows.append(
                    dict(
                        wallet=grp + str(i),
                        service=grp,
                        week="2026-W46",
                        ascertainment_complete=True,
                        liquidity_quintile=2,
                        prior_volume=1000,
                        age_days=10,
                        funding_usd=100,
                        market_buys=stakes,
                        dependency_group=str(i),
                        complete={"concentration": True},
                    )
                )
        r = analyze(rows, {"ChangeNOW": 20, "Tornado Cash": 0})[0]
        self.assertEqual((r["eligible_pairs"], r["effect"]), (20, 0.5))
        self.assertAlmostEqual(r["p_holm"], 10 * r["p"])
        for row in rows:
            if row["service"] == "CONTROL":
                row["funding_usd"] = 1000
        self.assertEqual(
            analyze(rows, {"ChangeNOW": 20, "Tornado Cash": 0})[0]["status"], "NOT_TESTABLE"
        )


if __name__ == "__main__":
    unittest.main()
