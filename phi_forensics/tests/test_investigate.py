"""The investigative questions end to end: the real readers, ledger, funding and cluster code against tests/world.py.

Every expected figure is worked out by hand from the scenario of world.py in the comments; none is read back from the
code under test. Block b has the time 1 600 000 000 + 2 b and the head is block 90 000 000.
"""
import functools
import unittest
import urllib.request
from fractions import Fraction
from unittest import mock

from phi_forensics import investigate, ledger, sources
from phi_forensics.tests import world
from phi_forensics.tests.world import C1, C2, C3, C4, D, E, F, K, P, S, T2N, T2Y, USDC, USDC_E, V, W, tx

MARK = "an open position is valued at a mark, which is not a price at which its size could be sold"
CONVERTED = ("this wallet converted neg-risk shares: without exact amounts the markets of those events are not valued and shares received "
             "by conversion do not appear")
NOW_UTC = "2026-05-28T20:27:40Z"  # 1 780 000 060


class Case(unittest.TestCase):
    def setUp(self):
        self.world = world.World()
        world.offline(self, self.world)
        self.src = self.world.sources()

    def markets(self, book):
        return {m["condition_id"]: m for m in book["markets"]}


class Ledger(Case):
    def test_api_amounts(self):
        # C1: buy 200 Yes for 60 (tx 7), redeem 200 (tx 12): cash 140, realised 140, flat.
        # C2: buy 100 Yes for 40 (API size, tx 8), split 50 (tx 9), sell 50 No for 22.5 (tx 10): cash -67.5; at the marks 0.55 / 0.45
        #     the inventory is 50 sets + 100 x 0.55 - 50 x 0.45 = 82.5, net 15, unrealised 82.5 - 50 - (40 - 22.5) = 15.
        # C3: buy 50 No for 30 (tx 14), then converted (tx 15): an event the API rows cannot place, so not valued.
        # E: the conversion row itself, no cash. Totals: cash 140 - 67.5 - 30 = 42.5, known inventory 82.5, net not stated.
        book = investigate.wallet_ledger(self.src, W)
        self.assertEqual(book["totals"], {"markets": 4, "trading_cash": "42.500000", "realised": "140.000000",
                                          "unrealised_on_valued_inventory": "15.000000", "inventory_value_known": "82.500000",
                                          "markets_not_valued": 1, "net_trading_result": None, "net_is_complete": False, "other_income": {}})
        got = self.markets(book)
        self.assertEqual([m["condition_id"] for m in book["markets"]], [C1, C2, C3, E])
        self.assertEqual((got[C1]["cash"], got[C1]["net"], got[C1]["status"]), ("140.000000", "140.000000", "FLAT"))
        self.assertEqual((got[C2]["cash"], got[C2]["inventory_value"], got[C2]["net"], got[C2]["unrealised"], got[C2]["valuation"]),
                         ("-67.500000", "82.500000", "15.000000", "15.000000", f"MARK (catalogue, {NOW_UTC})"))
        self.assertEqual(got[C2]["shares"], [
            {"token_id": T2Y, "outcome": "Yes", "outcome_index": 0, "signed_shares": "100.000000", "held_with_sets": "150.000000"},
            {"token_id": T2N, "outcome": "No", "outcome_index": 1, "signed_shares": "-50.000000", "held_with_sets": "0.000000"}])
        self.assertEqual((got[C3]["cash"], got[C3]["net"], got[C3]["status"], got[C3]["flags"]),
                         ("-30.000000", None, "INVENTORY_NOT_VALUED", ["IN_A_CONVERTED_NEG_RISK_EVENT"]))
        self.assertEqual(got[E]["flags"], ["CONVERSION_INVENTORY_NOT_RECONSTRUCTED"])
        # Transactions 7 and 8 are before 2026-04-28T11:00:40Z, the first trades of C3 and V's markets after it.
        self.assertEqual((got[C1]["flags"], got[C2]["flags"]), ([ledger.GROSS], [ledger.GROSS]))
        self.assertEqual((book["amounts"], book["chain"], book["activity_rows"], book["history_complete"], book["conversions"]),
                         ("API", None, 7, True, 1))
        self.assertEqual(len(book["limits"]), 3)
        self.assertIn(ledger.GROSS, book["limits"][0])
        self.assertEqual(book["limits"][1:], [CONVERTED, MARK])
        # The platform lists 158 of token 201 (98 + 50 + 10) and 50 of token 401; the rows show 150 of 201 and 50 of 302.
        check = book["platform_positions_check"]
        self.assertEqual((check["tokens_compared"], check["agree"], check["differ"], check["platform_list_complete"]), (4, 1, 3, True))
        self.assertEqual(check["differences"], [{"token_id": "201", "rebuilt": "150.000000", "platform": "158.000000"},
                                                {"token_id": "302", "rebuilt": "50.000000", "platform": "0.000000"},
                                                {"token_id": "401", "rebuilt": "0.000000", "platform": "50.000000"}])

    def test_exact_amounts(self):
        # From the chain: tx 8 delivered 98 shares, tx 15 moves 50 No of C3 out and 50 Yes of C4 in, tx 16 brings 10 Yes of C2 that
        # the API does not list. C2: 50 sets + 108 x 0.55 - 50 x 0.45 = 86.9, cash -67.5, net 19.4. C3: cost 30 leaves, net -30.
        # C4: 50 Yes at 0.6 = 30 with the cost 30 carried over: net 30, unrealised 0. Net 140 + 19.4 - 30 + 30 + 0 = 159.4.
        book = investigate.wallet_ledger(self.src, W, exact=True, block_at=self.world.block_at)
        self.assertEqual(book["totals"], {"markets": 5, "trading_cash": "42.500000", "realised": "140.000000",
                                          "unrealised_on_valued_inventory": "19.400000", "inventory_value_known": "116.900000",
                                          "markets_not_valued": 0, "net_trading_result": "159.400000", "net_is_complete": True, "other_income": {}})
        got = self.markets(book)
        self.assertEqual([m["condition_id"] for m in book["markets"]], [C1, C2, C3, C4, E])
        self.assertEqual([(got[c]["cash"], got[c]["net"], got[c]["realised"]) for c in (C1, C2, C3, C4, E)],
                         [("140.000000", "140.000000", "140.000000"), ("-67.500000", "19.400000", "0.000000"),
                          ("-30.000000", "-30.000000", "-30.000000"), ("0.000000", "30.000000", "30.000000"), ("0.000000", "0.000000", "0.000000")])
        self.assertEqual(got[C2]["flags"], [ledger.CHAIN_ONLY])
        self.assertEqual(got[C2]["rows"], {"BUY": 1, "CHAIN_ONLY": 1, "SELL": 1, "SPLIT": 1})
        self.assertEqual((got[C3]["flags"], got[C4]["flags"], got[E]["flags"]), (["CONVERSION"], ["CONVERSION"], ["CONVERSION"]))
        # Window: block_at(first row) - 10 = 88 199 990 to the head; in it, tx 16 (tokens) and tx 17 (cash only) have no API row.
        self.assertEqual(book["chain"], {"rows_checked": 7, "cash_rows_corrected": 0, "share_rows_corrected": 1, "cash_correction_abs": "0.000000",
                                         "rows_without_chain_record": 0, "transactions_with_mixed_directions": 0,
                                         "transactions_cash_direction_differs": 0, "conversions_placed": 1, "conversion_tokens_not_in_catalogue": 0,
                                         "chain_transactions_without_api_row": 2, "of_which_moving_outcome_tokens": 1,
                                         "chain_only_transactions_placed": 1, "chain_only_transactions_not_placed": 0})
        self.assertEqual(book["limits"], [MARK])
        self.assertEqual({k: book["platform_positions_check"][k] for k in ("tokens_compared", "agree", "differ")},
                         {"tokens_compared": 3, "agree": 3, "differ": 0})

    def test_exact_amounts_correct_an_api_row_that_contradicts_the_chain(self):
        self.world.row(W, 10)["usdc_size"] = 25  # the chain paid 22.5 for this sale
        api = self.markets(investigate.wallet_ledger(self.world.sources(), W))
        self.assertEqual(api[C2]["cash"], "-65.000000")  # -40 - 50 + 25
        book = investigate.wallet_ledger(self.src, W, exact=True, block_at=self.world.block_at)
        self.assertEqual(self.markets(book)[C2]["cash"], "-67.500000")
        self.assertEqual((book["chain"]["cash_rows_corrected"], book["chain"]["cash_correction_abs"]), (1, "2.500000"))

    def test_as_of_reads_only_what_was_known_then(self):
        # 2026-05-08T14:20:00Z = 1 778 250 000, after tx 10 and before the redemption of tx 12. Last prices at or before it:
        # 201 at 0.52, 202 at 0.47, 101 at 0.90 (the 0.95 of 1 778 260 000 is later). C1: 200 x 0.9 - 60 = 120.
        # C2: 50 + 100 x 0.52 - 50 x 0.47 = 78.5, cash -67.5, net 11. Total cash -127.5, net 131.
        book = investigate.wallet_ledger(self.src, W, as_of=1_778_250_000)
        self.assertEqual((book["totals"]["trading_cash"], book["totals"]["net_trading_result"], book["totals"]["inventory_value_known"]),
                         ("-127.500000", "131.000000", "258.500000"))
        got = self.markets(book)
        self.assertEqual((got[C1]["net"], got[C2]["net"]), ("120.000000", "11.000000"))
        self.assertEqual(got[C1]["valuation"], "MARK (price history at or before 2026-05-08T14:20:00Z)")
        self.assertEqual((book["as_of_utc"], book["activity_rows"]), ("2026-05-08T14:20:00Z", 4))
        self.assertNotIn("platform_positions_check", book)
        self.assertEqual(book["limits"][1:], [MARK])
        for url in self.world.urls:
            if "end=" in url or "endTs=" in url:
                self.assertTrue(url.endswith("1778250000") or "1778250000&" in url, url)

    def test_a_cut_history_says_its_totals_are_partial(self):
        # Pages of three rows: max_rows=3 stops after tx 7, 8 and 9. C1 holds 200 Yes paid 60, valued at its payout 1: net 140.
        # C2 holds 100 Yes and 50 sets for 90: 50 + 100 x 0.55 = 105, net 15. Net 155.
        book = investigate.wallet_ledger(self.src, W, max_rows=3)
        self.assertEqual((book["history_complete"], book["activity_rows"], book["totals"]["net_trading_result"]), (False, 3, "155.000000"))
        self.assertEqual(self.markets(book)[C1]["valuation"], "RESOLUTION (catalogue)")
        self.assertEqual(book["limits"][0], "history cut at 3 rows: totals are partial")

    def test_a_complete_wallet(self):
        # V: buy 100 Yes of C1 for 25 (tx 11), redeem 100 (tx 13): cash and net 75. Both rows after the first generation: no flag.
        book = investigate.wallet_ledger(self.src, V)
        self.assertEqual((book["totals"]["net_trading_result"], book["totals"]["net_is_complete"]), ("75.000000", True))
        self.assertEqual(self.markets(book)[C1]["flags"], [])
        self.assertEqual(book["platform_positions_check"]["tokens_compared"], 0)

    def test_source_failures_raise_instead_of_answering_empty(self):
        for status, body in ((500, b"oops"), (410, b'{"error": "retired"}'), (200, b"<html>wait</html>"),
                             (200, b'{"data": [], "pagination": {"has_more": true}}')):
            w = world.World()
            w.fail_http("/v2/activity", status, body)
            with self.assertRaises(sources.SourceError):
                investigate.wallet_ledger(w.sources(), W)


class Windows(Case):
    def test_block_floor_is_certainly_early_enough(self):
        # 1 776 000 000 is block 88 000 000; 90 000 000 - int(4 000 000 / 1.5) - 500 000 = 86 833 334.
        self.assertEqual(investigate.block_floor(self.src, 1_776_000_000), (86_833_334, 90_000_000))
        self.assertEqual(investigate.block_floor(self.src, 1_790_000_000), (89_500_000, 90_000_000))

    def test_exact_window_stops_soon_after_a_silent_wallet(self):
        rows = [{"timestamp": world.ts(80_000_000)}, {"timestamp": world.ts(80_100_000)}]  # silent for 19.8 million seconds
        self.assertEqual(investigate.exact_window(self.src, rows, self.world.block_at), (79_999_990, 80_500_000))
        rows = [{"timestamp": world.ts(89_000_000)}]  # 2 000 000 seconds before the head: read to the head
        self.assertEqual(investigate.exact_window(self.src, rows, self.world.block_at), (88_999_990, 90_000_000))


class Prices(Case):
    def test_reconcile_positions_with_a_tolerance(self):
        book = investigate.wallet_ledger(self.src, W)
        got = investigate.reconcile_positions(self.src, W, book, tolerance=8 * world.U)  # 158 - 150 = 8 shares is not above it
        self.assertEqual((got["agree"], got["differ"]), (2, 2))

    def test_past_prices_read_nothing_after_the_date(self):
        draft = ledger.build(self.world.activity[W], as_of=1_778_250_000)
        got = investigate.past_prices(self.src, draft, 1_778_250_000)
        self.assertEqual({c: q["prices"] for c, q in got.items()}, {C1: {0: Fraction(9, 10)}, C2: {0: Fraction(13, 25), 1: Fraction(47, 100)}})
        history = [u for u in self.world.urls if "prices-history" in u]
        self.assertEqual(len(history), 3)
        self.assertTrue(all("endTs=1778250000" in u and "startTs=1777645200" in u for u in history))


class Funding(Case):
    def test_deposits_withdrawals_and_a_check_that_does_not_close(self):
        # Scan from block_floor(1 776 400 000 - 180 days) = 90 000 000 - int(19 152 000 / 1.5) - 500 000 = 76 732 000: tx 1 (5 USDC.e
        # at block 70 000 000) is older. Received minus sent since then: 1000 + 500 + 22.5 + 200 - 60 - 40 - 50 - 30 - 300 = 1242.5;
        # held now: 1247.5 (747.5 USDC.e and 500 USDC). The 5 missing are the older deposit.
        flows = investigate.wallet_funding(self.src, W)
        self.assertEqual([(d["tx"], d["counterparty"], d["counterparty_kind"], d["amount"]) for d in flows["deposits"]],
                         [(tx(2), F, "key", "1000.000000"), (tx(6), S, "labelled_service", "500.000000")])
        self.assertEqual([(d["tx"], d["counterparty"], d["amount"]) for d in flows["withdrawals"]], [(tx(17), D, "300.000000")])
        self.assertEqual(flows["totals"], {"deposited": {USDC_E: "1000.000000", USDC: "500.000000"}, "withdrawn": {USDC_E: "300.000000"}})
        self.assertEqual(flows["counterparties"][F], {"address": F, "kind": "key", "nonce": 5, "as_of_block": 88_000_000})
        self.assertEqual(flows["counterparties"][D], {"address": D, "kind": "key", "nonce": 3, "as_of_block": 89_600_000})
        self.assertEqual(flows["counterparties"][S]["label"], "Relay solver")
        self.assertEqual((flows["trading_legs_excluded"], flows["collateral_swap_legs_excluded"]), (6, 0))  # tx 7, 8, 9, 10, 12, 14
        self.assertEqual(flows["scan"], {"from_block": 76_732_000, "to_block": 90_000_000, "calls": 4})
        self.assertEqual(flows["collateral_check"], {"received_minus_sent_since_scan_start": "1242.500000", "balance_now": "1247.500000",
                                                     "difference": "5.000000", "closes": False})
        self.assertEqual((flows["owner_keys"], flows["relayed"], flows["first_trade_utc"]), ([K], [], "2026-04-17T04:26:40Z"))
        self.assertEqual(flows["seconds_from_first_deposit_to_first_trade"], 400_000)  # blocks 88 000 000 to 88 200 000
        self.assertEqual(flows["profile"], {"proxy_wallet": W, "created_at": "2026-04-10T09:00:00Z", "name": "tester-one", "verified": False})
        self.assertEqual(flows["limits"][0], "transfers read from block 76732000: an older deposit would not appear (ask for the full history)")
        self.assertEqual(len(flows["limits"]), 4)

    def test_the_full_history_closes_the_check(self):
        flows = investigate.wallet_funding(self.src, W, full_history=True)
        self.assertEqual([d["tx"] for d in flows["deposits"]], [tx(1), tx(2), tx(6)])
        self.assertEqual(flows["collateral_check"], {"received_minus_sent_since_scan_start": "1247.500000", "balance_now": "1247.500000",
                                                     "difference": "0.000000", "closes": True})
        self.assertEqual(flows["seconds_from_first_deposit_to_first_trade"], 36_400_000)  # 1 776 400 000 - 1 740 000 000
        self.assertEqual(len(flows["limits"]), 3)

    def test_a_plain_key_without_profile(self):
        # V: 200 from F and 50 from the Relay solver, 150 to D; 200 + 50 + 100 - 25 - 150 = 175 = its balance.
        flows = investigate.wallet_funding(self.src, V)
        self.assertEqual([(d["counterparty"], d["amount"]) for d in flows["deposits"]], [(F, "200.000000"), (S, "50.000000")])
        self.assertEqual((flows["owner_keys"], flows["profile"]), (None, None))
        self.assertEqual(flows["collateral_check"]["closes"], True)
        self.assertEqual(flows["collateral_check"]["balance_now"], "175.000000")
        self.assertEqual(flows["scan"]["from_block"], 77_998_667)  # 90 000 000 - int(17 252 000 / 1.5) - 500 000

    def test_a_log_range_refused_as_too_wide_is_narrowed_and_read(self):
        self.world.max_log_range = 3_000_000  # 10 000 000 refused, 2 500 000 accepted: 13 268 000 blocks in 6 calls per direction
        flows = investigate.wallet_funding(self.world.sources(), W)
        self.assertEqual((flows["collateral_check"]["difference"], flows["scan"]["calls"]), ("5.000000", 12))

    def test_a_node_error_object_raises(self):
        self.world.fail_rpc("eth_getLogs")
        with self.assertRaises(sources.SourceError):
            investigate.wallet_funding(self.src, W)


class Links(Case):
    def test_links_among_wallets(self):
        # F pays W and V: COMMON_FUNDER. W and V both pay D: COMMON_DESTINATION (D's ten other payers are outside the set).
        # The Relay solver pays both: a shared service, not a link.
        got = investigate.wallet_links(self.src, [V, W.upper().replace("0X", "0x")])
        self.assertEqual(got["wallets"], [W, V])
        self.assertEqual([(l["a"], l["b"], l["type"], l["grade"], l.get("via")) for l in got["links"]],
                         [(W, V, "COMMON_DESTINATION", "FINANCIAL_RELATION_DEMONSTRATED", D),
                          (W, V, "COMMON_FUNDER", "FINANCIAL_RELATION_DEMONSTRATED", F), (W, V, "SHARED_SERVICE", "NOT_A_LINK", S)])
        self.assertEqual([(c["members"], c["grade"], c["types"]) for c in got["clusters"]],
                         [([W, V], "FINANCIAL_RELATION_DEMONSTRATED", ["COMMON_DESTINATION", "COMMON_FUNDER"])])
        self.assertTrue(got["graph_mermaid"].startswith("graph LR"))
        self.assertEqual(len(got["limits"]), 2)
        with self.assertRaises(ValueError):
            investigate.wallet_links(self.src, [W, W])

    def test_a_personal_funder_gives_candidates_and_a_service_gives_none(self):
        got = investigate.associated_wallets(self.src, W)
        # F paid V (tx 4) and P (tx 3) within 2 000 000 blocks of tx 2. D is paid by 12 addresses: treated as a service.
        self.assertEqual([(c["address"], c["relation"], c["via"], c["grade"]) for c in got["candidates"]],
                         [(V, "PAID_BY_THE_SAME_ADDRESS", F, "FINANCIAL_RELATION_DEMONSTRATED"),
                          (P, "PAID_BY_THE_SAME_ADDRESS", F, "FINANCIAL_RELATION_DEMONSTRATED")])
        self.assertEqual(got["candidates"][0]["evidence"], [{"tx": tx(4), "log_index": 0, "block": 88_050_000, "amount": "200.000000"}])
        self.assertEqual(got["candidates"][1]["evidence"], [{"tx": tx(3), "log_index": 0, "block": 88_010_000, "amount": "70.000000"}])
        self.assertEqual(got["candidates"][0]["own_evidence"], {"tx": tx(2), "log_index": 0})
        self.assertEqual([(s["address"], s["relation"], s["addresses_reached"]) for s in got["shared_services_ignored"]],
                         [(D, "PAYS_THE_SAME_ADDRESS", 12)])
        self.assertNotIn(S, [c["via"] for c in got["candidates"]])
        self.assertEqual((got["owner_keys"], len(got["limits"])), ([K], 3))


class Overview(Case):
    def test_wallet_overview(self):
        got = investigate.wallet_overview(self.src, W)
        self.assertEqual(got["trading"]["trading_cash"], "42.500000")
        self.assertEqual((got["trading"]["activity_rows"], got["trading"]["first_trade_utc"], got["trading"]["unknown_row_types"]),
                         (7, "2026-04-17T04:26:40Z", {}))
        # Largest by |net|, or |cash| when not valued: C1 140, C3 30, C2 15, E 0.
        self.assertEqual([m["condition_id"] for m in got["largest_markets"]], [C1, C3, C2, E])
        self.assertEqual(got["funding"]["deposited_by_counterparty_kind"], {"key": "1000.000000", "labelled_service": "500.000000"})
        self.assertEqual((got["funding"]["deposits"], got["funding"]["withdrawals"], got["funding"]["seconds_from_first_deposit_to_first_trade"]),
                         (2, 1, 400_000))
        self.assertEqual(got["owner_keys"], [K])
        self.assertEqual(len(got["limits"]), 7)  # 3 of the ledger and 4 of the funding, none shared
        self.assertEqual(got["limits"], sorted(got["limits"]))


class Transport(Case):
    """The same readers over net.fetch, whose retries are part of what a live read does."""

    def reader(self):
        patch = mock.patch.object(urllib.request, "urlopen", self.world.urlopen)
        patch.start()
        self.addCleanup(patch.stop)
        return sources.Sources(fetch=functools.partial(world.REAL_FETCH, sleep=lambda seconds: None), rpc=self.world.rpc, clock=self.world.clock)

    def test_a_429_is_retried_then_read(self):
        self.world.fail_http("/v2/activity", 429, b'{"error": "slow down"}')
        book = investigate.wallet_ledger(self.reader(), V)
        self.assertEqual(book["totals"]["net_trading_result"], "75.000000")
        self.assertEqual(sum("/v2/activity" in u for u in self.world.urls), 2)

    def test_a_410_is_not_retried_and_raises(self):
        self.world.fail_http("/v2/activity", 410, b'{"error": "Data API v1 has been retired"}')
        with self.assertRaises(sources.SourceError) as caught:
            investigate.wallet_ledger(self.reader(), V)
        self.assertEqual((caught.exception.status, sum("/v2/activity" in u for u in self.world.urls)), (410, 1))


if __name__ == "__main__":
    unittest.main()
