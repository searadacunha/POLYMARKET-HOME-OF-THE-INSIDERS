"""Offline tests: evidence classes, deduplication, weekly counting, rankings and the bets accounting before a withdrawal.
No network: every input below is written in the test."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "scripts"))

import build  # noqa: E402
import pnl  # noqa: E402

WALLET = "0x" + "a1" * 20
WALLET2 = "0x" + "a2" * 20
KEY = "0x" + "b1" * 20
DEP = "0x" + "d1" * 20
DEP2 = "0x" + "d2" * 20
SINK_A = "0x" + "c1" * 20
SINK_B = "0x" + "c2" * 20
SOLVER = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
SINK_C = "0x" + "c3" * 20
REG = {SINK_A: dict(tier="A_LABELLED"), SINK_B: dict(tier="B_STRUCTURAL"), SINK_C: dict(tier="B_STRUCTURAL")}
build.GRADES.update({SINK_A: "A", SINK_C: "C"})          # graded rows win over the register's tier
build.RAMP_ADDRESSES.update({"0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"})


def row(chain, tx, log, ts, src, dst, raw=1_000_000, token=USDC_E, block=100):
    return dict(chain=chain, tx=tx, log_index=log, block=block, block_hash="", ts=ts, src=src, dst=dst, token=token, raw=str(raw))


def hop(kind, r, **extra):
    return dict(kind=kind, **r, **extra)


def value(usd):
    return dict(symbol="USDC.e", decimals=6, amount=usd, price_usd=1.0, price_ts=0, usd=usd)


def week(name, walks, parts, candidates=(), endpoints=(), fed_payers=None):
    return dict(week=name, walks=list(walks), parts=list(parts), candidates=list(candidates), endpoints=list(endpoints),
                fed_payers=fed_payers or {}, blocks={"137": dict(first=1, last=2, closed=True)}, totals={},
                linking=dict(polygon_senders=0, heavy_keys=0))


def endpoint(dep, sink):
    return dict(chain=137, address=dep, rule="GAS_FUNDED", sinks=[sink], sweep=dict(tx="0xsweep"), sweeps=1, gas=dict(tx="0xgas"))


class Classes(unittest.TestCase):
    def test_direct_wallet_transfer_is_confirmed_direct(self):
        s = row(137, "0x01", 5, 1000, WALLET, DEP)
        w = dict(category="WALLET", status="CONFIRMED", start=s, hops=[hop("POLYMARKET_WALLET_DEBIT", s)], detail=dict(direct=True))
        p = dict(start=s, origin=s, origin_raw="1000000", start_raw="1000000", account=WALLET, value=value(1.0))
        rows, _ = build.rows_from({"2026-W01": week("2026-W01", [w], [p], endpoints=[endpoint(DEP, SINK_B)])}, REG)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["evidence_class"], "CONFIRMED_DIRECT")
        self.assertEqual(r["intermediary_count"], 0)
        self.assertEqual(r["changenow_endpoint_grade"], "B")
        self.assertEqual(r["delay_seconds"], 0)

    def test_unwrap_in_the_same_transaction_is_direct(self):
        s = row(137, "0x02", 9, 1000, "0x" + "e1" * 20, DEP)
        leg = row(137, "0x02", 4, 1000, WALLET, "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb", token="0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb")
        w = dict(category="COLLATERAL_RAMP", status="CONFIRMED", start=s, hops=[hop("CONVERSION_1_TO_1", leg), hop("POLYMARKET_WALLET_DEBIT", leg)], detail={})
        p = dict(start=s, origin=leg, origin_raw="1000000", start_raw="1000000", account=WALLET, value=value(1.0))
        rows, _ = build.rows_from({"2026-W01": week("2026-W01", [w], [p], endpoints=[endpoint(DEP, SINK_A)])}, REG)
        self.assertEqual(rows[0]["evidence_class"], "CONFIRMED_DIRECT")
        self.assertEqual(rows[0]["intermediary_count"], 0)
        self.assertEqual(rows[0]["changenow_endpoint_grade"], "A")

    def test_a_proven_path_to_a_wallet_graded_c_stays_possible(self):
        s = row(137, "0x0c", 5, 1000, WALLET, DEP)
        w = dict(category="WALLET", status="CONFIRMED", start=s, hops=[hop("POLYMARKET_WALLET_DEBIT", s)], detail={})
        p = dict(start=s, origin=s, origin_raw="1000000", start_raw="1000000", account=WALLET, value=value(1.0))
        rows, stats = build.rows_from({"2026-W01": week("2026-W01", [w], [p], endpoints=[endpoint(DEP, SINK_C)])}, REG)
        self.assertEqual((rows[0]["evidence_class"], rows[0]["changenow_endpoint_grade"]), ("POSSIBLE", "C"))
        self.assertIn("graded C", rows[0]["note"])
        self.assertEqual(stats["established_path_weak_endpoint"], 1)

    def test_key_in_between_is_supported_indirect_with_one_intermediary(self):
        s = row(137, "0x03", 2, 5000, KEY, DEP)
        o = row(137, "0x00", 7, 4000, WALLET, KEY)
        w = dict(category="OWNER_KEY", status="CONFIRMED", start=s, hops=[hop("POLYMARKET_WALLET_DEBIT", o, attributed_raw="1000000")], detail={})
        p = dict(start=s, origin=o, origin_raw="1000000", start_raw="1000000", account=WALLET, value=value(1.0))
        cand = dict(owner=KEY, wallets=[dict(wallet=WALLET, kind="DEPOSIT_WALLET", proof="owner()")], deposits=[dict(s, value=value(1.0))], wallet_paid_key=[4000])
        rows, _ = build.rows_from({"2026-W01": week("2026-W01", [w], [p], [cand], endpoints=[endpoint(DEP, SINK_B)])}, REG)
        self.assertEqual([r["evidence_class"] for r in rows], ["SUPPORTED_INDIRECT"])     # the candidate row is not added twice
        self.assertEqual(rows[0]["intermediaries"], KEY)
        self.assertEqual(rows[0]["delay_seconds"], 1000)

    def test_relay_bridge_is_supported_indirect(self):
        s = row(1, "0x04", 3, 6000, SOLVER, DEP)
        o = row(137, "0x05", 1, 5900, WALLET, build.DEPOSITORY)
        w = dict(category="RELAY_SOLVER", status="CONFIRMED", start=s,
                 hops=[hop("RELAY_ORDER", o, order="0x" + "ab" * 32, fill_tx="0x04", fill_chain=1), hop("POLYMARKET_WALLET_DEBIT", o)], detail={})
        p = dict(start=s, origin=o, origin_raw="1000000", start_raw="1000000", account=WALLET, value=value(1.0))
        rows, _ = build.rows_from({"2026-W01": week("2026-W01", [w], [p])}, REG)
        self.assertEqual(rows[0]["evidence_class"], "SUPPORTED_INDIRECT")
        self.assertEqual(rows[0]["intermediary_count"], 1)
        self.assertTrue(rows[0]["intermediaries"].startswith("Relay order"))
        self.assertIn("137:0x05", rows[0]["underlying_transactions"])

    def test_owned_key_without_proof_is_possible_and_fed_sender_unresolved(self):
        d1 = row(137, "0x06", 1, 7000, KEY, DEP)
        cand = dict(owner=KEY, wallets=[dict(wallet=WALLET, kind="DEPOSIT_WALLET", proof="owner()")], deposits=[dict(d1, value=value(5.0))], wallet_paid_key=[])
        fed = "0x" + "f1" * 20
        d2 = row(137, "0x07", 1, 7100, fed, DEP2)
        w2 = dict(category="FED_BY_WALLET", status="UNRESOLVED", start=d2, hops=[], detail=dict(reason="funds are mixed"))
        relay = dict(category="RELAY_SOLVER", status="UNRESOLVED", start=row(1, "0x08", 1, 7200, SOLVER, DEP2), hops=[], detail=dict(reason="escrow log not found"))
        rows, stats = build.rows_from({"2026-W01": week("2026-W01", [w2, relay], [], [cand], fed_payers={fed: [WALLET2]})}, REG)
        by = {r["evidence_class"]: r for r in rows}
        self.assertEqual(set(by), {"POSSIBLE", "UNRESOLVED"})
        self.assertEqual(by["POSSIBLE"]["polymarket_wallet"], WALLET)
        self.assertIn("no transfer between them", by["POSSIBLE"]["note"])
        self.assertEqual(by["UNRESOLVED"]["polymarket_wallet"], WALLET2)
        self.assertEqual(stats["relay_fill_not_tied_to_polymarket"], 1)

    def test_relay_record_counts_only_after_the_chain_check(self):
        s = row(1, "0x09", 3, 6000, SOLVER, DEP)
        w = dict(category="RELAY_SOLVER", status="UNRESOLVED", start=s, hops=[], detail=dict(reason="not one plain payment"))
        o = row(137, "0x0a", 2, 5950, WALLET, build.DEPOSITORY)
        checked = {"0x09": dict(verdict="WALLET_DEBIT_VERIFIED", origin=o, value=value(2.0))}
        rows, _ = build.rows_from({"2026-W01": week("2026-W01", [w], [])}, REG, checked=checked)
        self.assertEqual(rows[0]["evidence_class"], "SUPPORTED_INDIRECT")
        self.assertEqual(rows[0]["link_source"], "relay_api")
        rows, stats = build.rows_from({"2026-W01": week("2026-W01", [w], [])}, REG, checked={"0x09": dict(verdict="ORIGIN_NOT_POLYMARKET")})
        self.assertEqual(rows, [])


class AcrossWeeks(unittest.TestCase):
    def test_a_debit_reached_from_two_weeks_is_never_attributed_beyond_its_amount(self):
        o = row(137, "0x50", 1, 1000, WALLET, KEY, raw=100_000_000)                 # the wallet pays its key 100
        s1 = row(137, "0x51", 1, 2000, KEY, DEP, raw=60_000_000)                     # the key pays 60 on Sunday
        s2 = row(137, "0x52", 1, 9000, KEY, DEP2, raw=60_000_000)                    # and 60 on Monday: only 40 can still be the wallet's
        def week_of_part(name, s):
            w = dict(category="OWNER_KEY", status="CONFIRMED", start=s, hops=[hop("POLYMARKET_WALLET_DEBIT", o, attributed_raw="60000000")], detail={})
            p = dict(start=s, origin=o, origin_raw="60000000", start_raw="60000000", account=WALLET, value=value(60.0))
            return week(name, [w], [p])
        rows, stats = build.rows_from({"2026-W01": week_of_part("2026-W01", s1), "2026-W02": week_of_part("2026-W02", s2)}, REG)
        self.assertEqual([r["usd"] for r in rows], ["60.00", "40.00"])
        self.assertEqual([r["polymarket_debit_amount"] for r in rows], ["60.000000", "40.000000"])
        self.assertEqual(stats["part_capped_by_earlier_attribution"], 1)
        same = week_of_part("2026-W02", s1)                                          # the same deposit seen again: listed once
        rows, stats = build.rows_from({"2026-W01": week_of_part("2026-W01", s1), "2026-W02": same}, REG)
        self.assertEqual(len(rows), 1)
        self.assertEqual(stats["part_seen_in_an_earlier_week"], 1)


class Weekly(unittest.TestCase):
    def test_twenty_withdrawals_count_one_wallet_and_recurring_next_week(self):
        walks, parts = [], []
        for i in range(20):
            s = row(137, f"0x1{i:02d}", i, 1000 + i, WALLET, DEP)
            walks.append(dict(category="WALLET", status="CONFIRMED", start=s, hops=[hop("POLYMARKET_WALLET_DEBIT", s)], detail={}))
            parts.append(dict(start=s, origin=s, origin_raw="1000000", start_raw="1000000", account=WALLET, value=value(1.0)))
        s2 = row(137, "0x200", 1, 9000, WALLET, DEP)
        w2 = dict(category="WALLET", status="CONFIRMED", start=s2, hops=[hop("POLYMARKET_WALLET_DEBIT", s2)], detail={})
        p2 = dict(start=s2, origin=s2, origin_raw="1000000", start_raw="1000000", account=WALLET, value=value(3.0))
        weeks = {"2026-W01": week("2026-W01", walks, parts), "2026-W02": week("2026-W02", [w2], [p2])}
        rows, _ = build.rows_from(weeks, REG)
        wk = {r["week"]: r for r in build.weekly(rows, weeks)}
        self.assertEqual(wk["2026-W01"]["wallets_established"], 1)
        self.assertEqual(wk["2026-W01"]["transfers_established"], 20)
        self.assertEqual(wk["2026-W01"]["usd_established"], 20.0)
        self.assertEqual((wk["2026-W01"]["new_wallets"], wk["2026-W02"]["new_wallets"], wk["2026-W02"]["recurring_wallets"]), (1, 0, 1))
        rk = build.rankings(rows, {})
        self.assertEqual((rk[0]["wallet"], rk[0]["withdrawals_established"], rk[0]["changenow_usd_established"]), (WALLET, 21, 23.0))


def act(ts, kind, cid, side="", size=0, usdc=0, price=0, token="1"):
    return dict(timestamp=ts, type=kind, condition_id=cid, side=side, size=size, usdc_size=usdc, price=price, token_id=token, transaction_hash=f"0x{ts}")


def market(cid, closed_iso, outcome_prices='["1", "0"]'):
    return dict(conditionId=cid, outcomes='["Yes", "No"]', clobTokenIds='["1", "2"]', outcomePrices=outcome_prices, closed=True,
                umaResolutionStatus="resolved", closedTime=closed_iso, question=cid, slug=cid)


class Bets(unittest.TestCase):
    def test_realized_before_a_withdrawal(self):
        rows = [act(100, "TRADE", "0xm1", "BUY", 10, 4, 0.4), act(200, "REDEEM", "0xm1", size=10, usdc=10),     # +6, closed at 200
                act(300, "TRADE", "0xm2", "BUY", 10, 5, 0.5),                                                     # open at T=400
                act(310, "TRADE", "0xm3", "BUY", 10, 2, 0.2)]                                                     # resolved Yes at 350, unredeemed: +8
        mk = {"0xm1": market("0xm1", "1970-01-01T00:03:00Z"), "0xm3": market("0xm3", "1970-01-01T00:05:50Z")}
        b = pnl.before(rows, mk, 400, day=86400)
        self.assertEqual(b["markets_closed"], 2)
        self.assertEqual(b["markets_open"], 1)
        self.assertEqual(Decimal(b["realized_before"]), Decimal("14"))
        self.assertEqual(b["best"]["condition_id"], "0xm3")
        self.assertEqual(Decimal(b["capital_open"]), Decimal("5"))
        before_resolution = pnl.before(rows, mk, 340)
        self.assertEqual(Decimal(before_resolution["realized_before"]), Decimal("6"))      # 0xm3 not resolved yet at 340
        self.assertEqual(before_resolution["seconds_since_last_gain"], 140)


if __name__ == "__main__":
    unittest.main()
