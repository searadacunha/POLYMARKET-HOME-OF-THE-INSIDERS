"""Offline tests of the weekly ChangeNOW flow collector: windows, pagination, deduplication, attribution bounds,
tracing with a fake chain, report arithmetic and the freeze. Run from the monitoring folder:
    python3 -m unittest tests.test_changenow_weekly -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_monitor import net                                                                    # noqa: E402
from changenow_weekly import analyse, chainio as io, collect, reconcile, registry, report, trace  # noqa: E402
from changenow_weekly import polymarket as pm                                                  # noqa: E402

FIX = Path(__file__).resolve().parents[1] / "fixtures"
RELAY_DEPOSITS = json.loads((FIX / "relay_erc20_deposits_2026_W46.json").read_text())["cases"]
A, B, C, W, Q = ("0x" + c * 40 for c in "abcde")
SOURCE = "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423"
SOLVER = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
TX = lambda n: "0x" + f"{n:064x}"                                                              # noqa: E731


def row(src, dst, raw, block, index=0, token=pm.USDC_E, chain=137, tx=None, ts=None):
    return dict(chain=chain, block=block, block_hash="0x" + "b" * 64, tx=tx or TX(block * 1000 + index), log_index=index, ts=ts or 1794182400 + block,
                token=token, src=src, dst=dst, raw=raw)


def log(token, src, dst, raw, block, index, tx):
    return dict(address=token, topics=[io.TRANSFER, io.pad(src), io.pad(dst)], data="0x" + f"{raw:064x}", blockNumber=hex(block), blockHash="0x" + "b" * 64,
                blockTimestamp=hex(1794182400 + block), transactionHash=tx, logIndex=hex(index), removed=False)


def context(payouts=(), ledgers=None, wallets=None):
    blocks = {137: dict(first=100, last=10_000, head=10_000, head_ts=1794182400 + 10_000, week="2026-W46"), 1: dict(first=100, last=10_000, head=10_000, head_ts=1794182400 + 10_000, week="2026-W46")}
    ctx = trace.Context(blocks, {137: {SOURCE}, 1: set()}, list(payouts))
    for (chain, address), rows in (ledgers or {}).items():
        ctx.ledgers[(chain, address)] = dict(rows=sorted(rows, key=trace.position), first=1, last=10_000, native="logs")
    ctx.wallets.update(wallets or {})
    return ctx


class Windows(unittest.TestCase):
    def test_iso_week_is_monday_to_monday_utc(self):
        start, end = io.week_bounds("2026-W46")
        self.assertEqual((io.iso(start), io.iso(end)), ("2026-11-09 00:00:00", "2026-11-16 00:00:00"))
        self.assertEqual(io.week_of(start), "2026-W46")
        self.assertEqual(io.week_of(end - 1), "2026-W46")
        self.assertEqual(io.week_of(end), "2026-W47")                    # the end is excluded
        self.assertEqual(io.next_week("2026-W53"), "2027-W01")           # 2026 has 53 ISO weeks

    def test_first_block_at_is_the_first_block_at_or_after_the_time(self):
        with mock.patch.object(io, "block_time", lambda chain, n: 1000 + 2 * n):
            self.assertEqual(io.first_block_at(137, 1100, 500), 50)
            self.assertEqual(io.first_block_at(137, 1101, 500), 51)


class Decoding(unittest.TestCase):
    def test_transfer_shapes(self):
        good = io.decode_transfer(log(pm.USDC_E, A, B, 5, 10, 3, TX(1)), 137)
        self.assertEqual((good["src"], good["dst"], good["raw"], good["block"], good["log_index"], good["ts"]), (A, B, 5, 10, 3, 1794182410))
        nft = dict(log(pm.USDC_E, A, B, 5, 10, 3, TX(1)), topics=[io.TRANSFER, io.pad(A), io.pad(B), "0x" + "0" * 64], data="0x")
        self.assertIsNone(io.decode_transfer(nft, 137))                  # ERC-721: four topics, never read as an amount
        self.assertIsNone(io.decode_transfer(dict(nft, topics=[]), 137))  # anonymous log
        native = dict(address=io.POL_SYSTEM, topics=[io.POL_LOG_TRANSFER, io.pad(io.POL_SYSTEM), io.pad(A), io.pad(B)], data="0x" + f"{7:064x}" + "0" * 256,
                      blockNumber="0xa", blockHash="0x" + "b" * 64, transactionHash=TX(2), logIndex="0x1")
        self.assertEqual((io.decode_transfer(native, 137)["token"], io.decode_transfer(native, 137)["raw"]), ("native", 7))

    def test_multicall_decoding_keeps_call_order_and_empty_answers(self):
        answers = [(True, bytes(12) + bytes.fromhex(A[2:])), (True, b""), (False, bytes.fromhex("3c10b94e"))]
        head = (32).to_bytes(32, "big") + len(answers).to_bytes(32, "big")
        offsets, bodies, cursor = b"", b"", 32 * len(answers)
        for ok, data in answers:
            body = int(ok).to_bytes(32, "big") + (64).to_bytes(32, "big") + len(data).to_bytes(32, "big") + data + bytes((32 - len(data) % 32) % 32)
            offsets += cursor.to_bytes(32, "big")
            bodies += body
            cursor += len(body)
        with mock.patch.object(io, "rpc", lambda *a, **k: "0x" + (head + offsets + bodies).hex()):
            got = io.aggregate3(137, [(A, "8da5cb5b")] * 3)
        self.assertEqual(got, [(True, "0" * 24 + A[2:]), (True, ""), (False, "3c10b94e")])


class LogWindows(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(io, "PACE", 0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_window_halves_on_refusal_and_coverage_has_no_hole(self):
        asked = []

        def node(chain, method, params, state=False):
            a, b = int(params[0]["fromBlock"], 16), int(params[0]["toBlock"], 16)
            if b - a + 1 > 3000:
                raise net.SourceError("query returned more than 10000 results")
            asked.append((a, b))
            return [log(pm.USDC_E, A, B, 1, n, 0, TX(n)) for n in range(a, b + 1) if n % 1000 == 0]

        with mock.patch.object(io, "rpc", node):
            logs, windows = io.get_logs(137, 1, 40_000, [io.TRANSFER])
        self.assertEqual([int(l["blockNumber"], 16) for l in logs], list(range(1000, 40_001, 1000)))
        self.assertEqual(windows[0][0], 1)
        self.assertEqual(windows[-1][1], 40_000)
        self.assertTrue(all(windows[i][1] + 1 == windows[i + 1][0] for i in range(len(windows) - 1)))

    def test_a_refusal_at_the_smallest_window_is_raised_not_swallowed(self):
        def node(*a, **k):
            raise net.SourceError("limit exceeded")
        with mock.patch.object(io, "rpc", node), self.assertRaises(net.SourceError):
            io.get_logs(137, 1, 500, [io.TRANSFER])

    def test_a_filter_naming_few_token_contracts_is_read_from_the_node_that_serves_wide_ranges(self):
        asked = []

        def node(chain, method, params, state=False, urls=None):
            asked.append((int(params[0]["toBlock"], 16) - int(params[0]["fromBlock"], 16) + 1, urls))
            return []

        wide = io.CHAINS[8453]["by_contract"]
        with mock.patch.object(io, "rpc", node):
            io.get_logs(8453, 1, 120_000, [io.TRANSFER], [pm.USDC])                          # one contract named: wide windows, the other node
            io.get_logs(8453, 1, 2_000, [io.TRANSFER])                                       # no contract named: the chain's own node and window
            io.get_logs(8453, 1, 2_000, [io.TRANSFER], ["0x" + f"{n:040x}" for n in range(wide["contracts"] + 1)])   # too many contracts for that node
            io.get_logs(137, 1, 60_000, [io.TRANSFER], [pm.USDC])                            # a chain without such a node is not affected
        self.assertEqual(asked[:3], [(50_000, [wide["url"]]), (50_000, [wide["url"]]), (20_000, [wide["url"]])])
        self.assertEqual(asked[3:7], [(1_000, None)] * 4)
        self.assertEqual(asked[7:], [(50_000, None), (10_000, None)])

    def test_a_removed_log_stops_the_read(self):
        with mock.patch.object(io, "rpc", lambda *a, **k: [dict(log(pm.USDC_E, A, B, 1, 5, 0, TX(5)), removed=True)]), self.assertRaises(net.SourceError):
            io.get_logs(137, 1, 10, [io.TRANSFER])


def etherscan_server(rows, short=996):
    """The list service as observed on 2026-11-14: 1,000 rows a page, sometimes fewer in the middle of a list."""
    def serve(chain, **p):
        hits = [r for r in rows if int(p["startblock"]) <= int(r["blockNumber"]) <= int(p["endblock"])]
        page = hits[(p["page"] - 1) * 1000:p["page"] * 1000]
        return page[:short] if p["page"] == 1 and len(hits) > 1000 and len({r["blockNumber"] for r in page}) > 1 else page
    return serve


class EtherscanPaging(unittest.TestCase):
    def rows(self, counts):
        out, n = [], 0
        for block, count in counts:
            for _ in range(count):
                n += 1
                out.append(dict(hash=TX(n), blockNumber=str(block), value="1", to=B, isError="0", timeStamp="1"))
        for r in out:
            r["from"] = A
        return out

    def test_a_short_page_in_the_middle_is_not_the_end(self):
        rows = self.rows([(b, 7) for b in range(100, 600)])              # 3,500 rows, short pages of 996
        with mock.patch.object(io, "etherscan", etherscan_server(rows)):
            got = io.etherscan_rows(1, "txlist", A, 100, 599)
        self.assertEqual(sorted(r["hash"] for r in got), sorted(r["hash"] for r in rows))
        self.assertEqual(len(got), len({r["hash"] for r in got}))        # boundary blocks are read twice and kept once

    def test_a_block_that_fills_a_page_is_paged_from_inside(self):
        rows = self.rows([(100, 40), (101, 2500), (102, 30)])
        with mock.patch.object(io, "etherscan", etherscan_server(rows)):
            got = io.etherscan_rows(1, "txlist", A, 100, 102)
        self.assertEqual(len(got), 2570)

    def test_a_block_too_large_to_prove_complete_raises(self):
        rows = self.rows([(100, 10_500)])
        with mock.patch.object(io, "etherscan", etherscan_server(rows)), self.assertRaises(net.SourceError):
            io.etherscan_rows(1, "txlist", A, 100, 100)

    def test_native_list_must_hold_every_signed_transaction(self):
        rows = self.rows([(100, 3)])
        store = collect.Store(tempfile.mkdtemp(), "2026-W46", 1)
        blocks = dict(first=100, last=100)
        with mock.patch.object(io, "etherscan_rows", lambda chain, action, a, f, l: rows if action == "txlist" else []):
            self.assertEqual(collect.native_lists(store, 1, blocks, {A: 3}, say=lambda m: None)["rows"], 3)
            with self.assertRaises(net.SourceError):                     # the nonce says five were signed: the list is short
                collect.native_lists(store, 1, blocks, {A: 5}, say=lambda m: None)


class Checkpoints(unittest.TestCase):
    def test_ranges_resume_and_a_hole_is_an_error(self):
        store = collect.Store(tempfile.mkdtemp(), "2026-W46", 137)
        self.assertEqual(store.next_block("reg_out", 100), 100)
        store.write("reg_out", 100, 199, [row(A, B, 1, 150)])
        store.write("reg_out", 200, 250, [row(A, B, 2, 220)])
        self.assertEqual(store.next_block("reg_out", 100), 251)
        self.assertEqual([r["raw"] for r in store.rows("reg_out")], [1, 2])
        store.write("reg_out", 300, 400, [])
        with self.assertRaises(RuntimeError):
            store.next_block("reg_out", 100)

    def test_incremental_stream_reads_only_new_blocks(self):
        store = collect.Store(tempfile.mkdtemp(), "2026-W46", 137)
        seen = []

        def logs(chain, first, last, topics, address=None):
            seen.append((first, last))
            return [log(pm.USDC_E, A, B, 1, first, 0, TX(first))], [(first, last, 1)]

        with mock.patch.object(io, "get_logs", logs):
            collect.log_stream(store, 137, "reg_out", 1, 30_000, [io.TRANSFER], say=lambda m: None)
            first_pass = list(seen)
            collect.log_stream(store, 137, "reg_out", 1, 45_000, [io.TRANSFER], say=lambda m: None)
        self.assertEqual(first_pass, [(1, 20_000), (20_001, 30_000)])
        self.assertEqual(seen[len(first_pass):], [(30_001, 45_000)])
        self.assertEqual(len(list(store.rows("reg_out"))), 3)

    def test_on_a_narrow_chain_the_token_list_is_cut_into_groups_and_rows_are_merged_in_chain_order(self):
        store = collect.Store(tempfile.mkdtemp(), "2026-W46", 8453)
        tokens = ["0x" + f"{n:040x}" for n in range(1, 13)]                                  # twelve tokens: two groups of at most ten
        asked = []

        def logs(chain, first, last, topics, address=None):
            asked.append((len(address), len(topics[-1])))
            return [log(address[0], A, B, 1, 500 if len(address) == 10 else 400, 0, TX(len(address)))], [(first, last, 1)]

        with mock.patch.object(io, "get_logs", logs):
            stats = collect.dependent_stream(store, 8453, "dep_in", dict(first=1, last=1000), ["0x" + f"{n:040x}" for n in range(100, 2100)], "dst", tokens=tokens, say=lambda m: None)
        self.assertEqual(sorted(asked), [(2, 500), (2, 1500), (10, 500), (10, 1500)])        # 2,000 addresses: lists of 1,500 at most, for each token group
        self.assertEqual([r["block"] for r in store.rows("dep_in")], [400, 400, 500, 500])
        self.assertEqual((stats["rows"], stats["heavy"]), (4, []))

    def test_a_changed_register_reads_the_week_again_from_its_first_block(self):
        store = collect.Store(tempfile.mkdtemp(), "2026-W46", 1)
        seen = []

        def logs(chain, first, last, topics, address=None):
            seen.append((first, last, len(topics[-1])))
            return [], [(first, last, 0)]

        with mock.patch.object(io, "get_logs", logs):
            collect.registry_streams(store, 1, dict(first=1, last=15_000), [A], say=lambda m: None)
            collect.registry_streams(store, 1, dict(first=1, last=18_000), [A], say=lambda m: None)        # same register: only the new blocks
            collect.registry_streams(store, 1, dict(first=1, last=18_000), [A, B], say=lambda m: None)     # one address more: the whole week again
        self.assertEqual(seen[4:6], [(15_001, 18_000, 1)] * 2)
        self.assertEqual(seen[6:], [(1, 10_000, 2), (10_001, 18_000, 2)] * 2)                              # an added address must not miss its earlier transfers


class Register(unittest.TestCase):
    def test_tiers_of_the_committed_register(self):
        reg = registry.load()
        self.assertEqual(reg[SOURCE]["tier"], "B_STRUCTURAL")
        self.assertEqual(reg["0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b"]["tier"], "A_LABELLED")
        self.assertEqual(reg["0x19f00b3a7b6f55c9da966fe3723251784a797fa7"]["tier"], "X_NOT_SERVICE")   # a deposit address at an exchange
        self.assertEqual(reg["0x0e2ea4d1ae07cf636e6fdde4ac89891f9dd63e2b"]["tier"], "C_SUSPECTED")      # behaviour only
        self.assertNotIn("0x0e2ea4d1ae07cf636e6fdde4ac89891f9dd63e2b", registry.usable(reg))
        self.assertNotIn("0x19f00b3a7b6f55c9da966fe3723251784a797fa7", registry.usable(reg))

    def test_every_structural_tier_rests_on_a_recorded_transaction(self):
        reg, evidence = registry.load(), json.loads(registry.EVIDENCE.read_text())
        structural = [a for a, r in reg.items() if r["tier"] == "B_STRUCTURAL"]
        self.assertTrue(structural)
        for a in structural:
            seeds = [r for r in evidence[a]["early_ties"] if r["direction"] == "in" and r["counterparty_tier_a"]]
            self.assertTrue(seeds, a)
            self.assertIn(seeds[0]["tx"], reg[a]["basis"])
            self.assertEqual(reg[seeds[0]["counterparty"]]["tier"], "A_LABELLED")

    def test_roles_follow_the_written_rules(self):
        reg = {A: {}, B: {}, C: {}, Q: {}}
        hot = [row(A, "0x" + f"{n:040x}", 10, n) for n in range(1, 121)]
        gas = [row(B, "0x" + f"{n:040x}", 1, n, token="native") for n in range(1000, 1150)]
        sweeps = [row("0x" + f"{n:040x}", A, 50, n + 5) for n in range(1000, 1150)]         # the gas recipients sweep a token into the service
        dust = [row("0x" + f"{n:040x}", B, 1, n + 9, token="native") for n in range(1000, 1150)]   # and send their leftover gas back
        native_payer = [row(Q, "0x" + f"{n:040x}", 7, n, token="native") for n in range(5000, 5150)]   # pays native coin to customers, who sweep nothing
        treasury = [row(C, W, 5, n) for n in range(1, 31)]
        roles = registry.roles(hot + gas + sweeps + dust + native_payer + treasury + [row(A, B, 0, 5)], reg)
        self.assertEqual((roles[A]["role"], roles[B]["role"], roles[C]["role"], roles[Q]["role"]), ("PAYOUT_HOT", "GAS_FUNDER", "CONSOLIDATION", "PAYOUT_HOT"))
        self.assertEqual(roles[A]["sends"], 120)                         # the zero-value row is not a transfer


class Attribution(unittest.TestCase):
    def bound(self, out_raw, before, payouts, others=()):
        pays = [row(SOURCE, A, raw, block) for raw, block in payouts]
        ledger = pays + [row(B, A, raw, block) for raw, block in others]
        ctx = context(pays, {(137, A): ledger})
        out = row(A, W, out_raw, 900)
        with mock.patch.object(trace, "balance_before", lambda *a: before):
            parts, detail = trace.attribute(ctx, 137, A, out, trace.tracked_inflows(ctx, trace.FUNDING, 137, A, pm.USDC_E, trace.position(out)))
        return [take for _, take in parts], detail

    def test_clean_address_passes_the_whole_amount(self):
        self.assertEqual(self.bound(100, 0, [(100, 500)])[0], [100])

    def test_only_what_other_money_cannot_cover_is_attributed(self):
        self.assertEqual(self.bound(100, 30, [(100, 500)])[0], [70])                       # 30 was already there
        self.assertEqual(self.bound(100, 0, [(100, 500)], others=[(45, 600)])[0], [55])    # 45 arrived from elsewhere in between
        self.assertEqual(self.bound(100, 80, [(100, 500)], others=[(20, 600)])[0], [])     # other money covers it all

    def test_first_in_first_out_and_never_more_than_was_paid(self):
        self.assertEqual(self.bound(150, 0, [(100, 500), (80, 600)])[0], [100, 50])
        self.assertEqual(self.bound(500, 0, [(100, 500), (80, 600)])[0], [100, 80])

    def test_a_payout_after_the_outflow_is_not_tracked(self):
        ctx = context([row(SOURCE, A, 100, 950)])
        self.assertEqual(trace.tracked_inflows(ctx, trace.FUNDING, 137, A, pm.USDC_E, (900, 0)), [])

    def test_a_payout_is_attributed_once_across_walks(self):
        pay = row(SOURCE, A, 100, 500)
        ctx = context([pay], {(137, A): [pay]})
        with mock.patch.object(trace, "balance_before", lambda *a: 0):
            first = trace.explain(ctx, trace.FUNDING, row(A, W, 100, 600))
            trace.commit(ctx, first)
            second = trace.explain(ctx, trace.FUNDING, row(A, W, 100, 700))
        self.assertEqual(first["status"], "CONFIRMED")
        self.assertEqual(sum(raw for _, raw, _ in first["parts"]), 100)
        self.assertEqual(second["status"], "UNRESOLVED")                 # nothing is left of that payout


class Walks(unittest.TestCase):
    def test_payout_straight_into_a_wallet(self):
        got = trace.explain(context(), trace.FUNDING, row(SOURCE, W, 250, 500))
        self.assertEqual((got["status"], got["parts"][0][1], got["hops"][0]["kind"]), ("CONFIRMED", 250, "CHANGENOW_PAYOUT"))

    def test_wrap_then_relay_swap_then_payout_all_same_amount(self):
        """USDC paid to Q, swapped to USDC.e by a Relay order on the same chain, wrapped into pUSD minted to W."""
        order = "ab" * 32
        pay = row(SOURCE, Q, 99_681_696, 1000, token=pm.USDC)
        deposit = row(Q, trace.DEPOSITORY, 99_681_696, 1003, token=pm.USDC)
        fill = row(SOLVER, Q, 99_681_696, 1004, token=pm.USDC_E, tx=TX(77))
        wrap_tx = TX(88)
        receipt = dict(transactionHash=wrap_tx, blockNumber=hex(1006), status="0x1", logs=[
            log(pm.USDC_E, Q, pm.PUSD, 99_681_696, 1006, 10, wrap_tx), log(pm.PUSD, io.ZERO, W, 99_681_696, 1006, 12, wrap_tx)])
        ctx = context([pay], {(137, Q): [pay, deposit, fill, row(Q, pm.PUSD, 99_681_696, 1006, 10, tx=wrap_tx)]})
        ctx.receipts[(137, wrap_tx)] = receipt
        ctx.txs[(137, TX(77))] = dict(to=pm.USDC_E, input="0xa9059cbb" + "0" * 128 + order)
        origin = dict(deposit, log_index=5)
        mint = row(io.ZERO, W, 99_681_696, 1006, 12, token=pm.PUSD, tx=wrap_tx)
        with mock.patch.object(trace, "balance_before", lambda *a: 0), mock.patch.object(trace, "relay_origin", lambda c, o, ts: origin if o == order else None):
            got = trace.explain(ctx, trace.FUNDING, mint)
        self.assertEqual(got["status"], "CONFIRMED", got["detail"])
        self.assertEqual([h["kind"] for h in got["hops"]], ["CONVERSION_1_TO_1", "TRANSFER", "RELAY_ORDER", "CHANGENOW_PAYOUT"])
        self.assertEqual(got["parts"][0][1:], (99_681_696, 99_681_696))
        self.assertEqual(got["hops"][2]["order"], "0x" + order)

    def test_relay_escrow_log_is_decoded_for_tokens_and_native(self):
        order = "cd" * 32
        erc20 = dict(address=trace.DEPOSITORY, topics=[trace.ERC20_DEPOSIT], blockNumber=hex(5000), transactionHash=TX(9), logIndex="0x4", blockTimestamp=hex(1794182400 + 5000),
                     data="0x" + "0" * 24 + Q[2:] + "0" * 24 + pm.USDC[2:] + f"{150_000_000:064x}" + order)
        native = dict(erc20, topics=[trace.NATIVE_DEPOSIT], data="0x" + "0" * 24 + Q[2:] + f"{10 ** 17:064x}" + order)
        call_log = dict(erc20, topics=["0x4be109453ef7e895dc7215c929fff9b76b51483d56a4d04548b4866e9aa7c5ea"], data="0x" + order + "0" * 64 * 6)   # RelayCallExecuted: id first
        other = dict(erc20, data=erc20["data"][:-64] + "ee" * 32)                                              # a deposit for another order
        ctx = context()
        for entry, token, raw in ((erc20, pm.USDC, 150_000_000), (native, "native", 10 ** 17)):
            with mock.patch.object(io, "get_logs", lambda *a, **k: ([call_log, other, entry], [])):        # other events and orders come first
                got = trace.relay_origin(ctx, order, 1794182400 + 5000)
            self.assertEqual((got["src"], got["token"], got["raw"], got["tx"]), (Q, token, raw, TX(9)))
        with mock.patch.object(io, "get_logs", lambda *a, **k: ([call_log, other], [])):
            self.assertIsNone(trace.relay_origin(ctx, order, 1794182400 + 5000))
        with mock.patch.object(io, "get_logs", lambda *a, **k: ([], [])):
            self.assertIsNone(trace.relay_origin(ctx, order, 1794182400 + 5000))        # not found is said, never guessed

    def test_mixed_funds_stop_the_walk(self):
        other = row(B, Q, 500, 400)
        late = row(B, Q, 100, 800)
        ctx = context([], {(137, Q): [other, late]})
        with mock.patch.object(trace, "balance_before", lambda *a: 500):               # Q already held five times the inflow
            got = trace.explain(ctx, trace.FUNDING, row(Q, W, 100, 900))
        self.assertEqual(got["status"], "UNRESOLVED")
        self.assertIn("mixed", got["detail"]["reason"])

    def test_a_credit_paid_by_the_exchange_is_not_a_funding(self):
        exchange = "0xe111180000d2663c0091e4f400237545b87b996b"
        got = trace.explain(context(), trace.FUNDING, row(exchange, W, 100, 900, token=pm.PUSD))
        self.assertEqual(got["status"], "NOT_ORIGIN")

    def test_a_wallet_wrapping_its_own_balance_is_not_a_second_funding(self):
        """Seen on chain on 2026-11-13: a key forwards a payout to its wallet, then the wallet wraps the same USDC.e
        into pUSD. The first movement is the funding. The wrap is the wallet's own money and must add nothing."""
        pay = row(SOURCE, A, 9_737_192, 500)
        forward = row(A, W, 9_810_000, 520)
        wrap_tx = TX(66)
        receipt = dict(transactionHash=wrap_tx, blockNumber=hex(540), status="0x1", logs=[log(pm.USDC_E, W, pm.PUSD, 9_810_000, 540, 2, wrap_tx), log(pm.PUSD, io.ZERO, W, 9_810_000, 540, 4, wrap_tx)])
        ctx = context([pay], {(137, A): [pay, forward], (137, W): [forward]}, wallets={W: dict(type="DEPOSIT_WALLET", owners=[A], evidence=[])})
        ctx.receipts[(137, wrap_tx)] = receipt
        with mock.patch.object(trace, "balance_before", lambda *a: 1_167_400):          # the key already held 1.1674 USDC.e
            first = trace.explain(ctx, trace.FUNDING, forward)
            trace.commit(ctx, first)
            again = trace.explain(ctx, trace.FUNDING, forward)
            second = trace.explain(ctx, trace.FUNDING, row(io.ZERO, W, 9_810_000, 540, 4, token=pm.PUSD, tx=wrap_tx))
        self.assertEqual(sum(raw for _, raw, _ in first["parts"]), 9_810_000 - 1_167_400)     # the lower bound, 8.6426
        self.assertEqual(again["status"], "UNRESOLVED")                                   # the bound of that outflow is spent
        self.assertEqual(second["status"], "NOT_ORIGIN")
        self.assertIn("own balance", second["detail"]["reason"])

    def test_an_address_that_passes_on_part_of_an_inflow_may_have_passed_the_other_money_first(self):
        """The key receives 100 from ChangeNOW on top of 30 it held, sends 100 to Q, and Q sends 60 on to the wallet."""
        pay, to_q, to_w = row(SOURCE, A, 100, 500), row(A, Q, 100, 520), row(Q, W, 60, 540)
        ctx = context([pay], {(137, A): [pay, to_q], (137, Q): [to_q, to_w]})
        with mock.patch.object(trace, "balance_before", lambda chain, address, token, block: 30 if address == A else 0):
            got = trace.explain(ctx, trace.FUNDING, to_w)
        self.assertEqual(got["status"], "CONFIRMED", got["detail"])
        self.assertEqual(sum(raw for _, raw, _ in got["parts"]), 30)     # 70 tracked in the 100; 40 left Q elsewhere: max(0, 60 - 30)

    def test_only_a_plain_solver_payment_ties_its_calldata_tail_to_an_order(self):
        order = "ab" * 32
        ctx = context()
        cases = {TX(71): (dict(to=pm.USDC_E, input="0x23b872dd" + "0" * 192 + order), order),                 # transferFrom on the token, id appended
                 TX(72): (dict(to=pm.USDC_E, input="0xa9059cbb" + "0" * 128 + order), order),                 # transfer on the token, id appended
                 TX(73): (dict(to=pm.USDC_E, input="0xa9059cbb" + "0" * 128), None),                          # the solver's own payment, no id
                 TX(74): (dict(to=Q, input="0x" + order), order)}                                              # native send straight to the recipient
        for tx, (body, want) in cases.items():
            ctx.txs[(137, tx)] = body
            token = "native" if tx == TX(74) else pm.USDC_E
            self.assertEqual(trace.relay_order(ctx, 137, row(SOLVER, Q, 5, 900, token=token, tx=tx)), want, tx)
        ctx.txs[(137, TX(75))] = dict(to=B, input="0x12345678" + "0" * 256 + order)                            # a batch contract: several orders possible
        with self.assertRaises(trace.Unresolved):
            trace.relay_order(ctx, 137, row(SOLVER, Q, 5, 900, tx=TX(75)))
        self.assertIsNone(trace.relay_order(ctx, 137, row(A, Q, 5, 900, tx=TX(75))))                            # not a solver: not a Relay fill

    def test_a_balance_held_before_a_pass_through_is_other_money(self):
        """The key receives 100 from ChangeNOW and sends 100 to Q, which held 1 already, and Q sends 100 to the wallet."""
        pay, to_q, to_w = row(SOURCE, A, 100, 500), row(A, Q, 100, 520), row(Q, W, 100, 540)
        ctx = context([pay], {(137, A): [pay, to_q], (137, Q): [to_q, to_w]})
        with mock.patch.object(trace, "balance_before", lambda chain, address, token, block: 1 if address == Q else 0):
            got = trace.explain(ctx, trace.FUNDING, to_w)
        self.assertEqual(got["status"], "CONFIRMED", got["detail"])
        self.assertEqual(sum(raw for _, raw, _ in got["parts"]), 99)    # the 1 Q held could have been passed on first

    def test_a_relay_order_scales_the_amount_with_its_rate(self):
        """0.2 ETH paid on Ethereum, deposited whole into the escrow, 400 USDC.e paid out on Polygon and wrapped."""
        order = "ef" * 32
        pay = row(SOURCE, Q, 2 * 10 ** 17, 300, token="native", chain=1)
        fill = row(SOLVER, Q, 400_000_000, 1004, tx=TX(77))
        wrap_tx = TX(88)
        receipt = dict(transactionHash=wrap_tx, blockNumber=hex(1006), status="0x1", logs=[log(pm.USDC_E, Q, pm.PUSD, 400_000_000, 1006, 10, wrap_tx), log(pm.PUSD, io.ZERO, W, 400_000_000, 1006, 12, wrap_tx)])
        ctx = context([pay], {(137, Q): [fill, row(Q, pm.PUSD, 400_000_000, 1006, 10, tx=wrap_tx)], (1, Q): [pay]})
        ctx.sources[1] = {SOURCE}
        ctx.receipts[(137, wrap_tx)] = receipt
        ctx.txs[(137, TX(77))] = dict(to=pm.USDC_E, input="0x23b872dd" + "0" * 192 + order)          # transferFrom, as the solver pays on Polygon
        origin = row(Q, trace.DEPOSITORY, 2 * 10 ** 17, 305, 7, token="native", chain=1)
        with mock.patch.object(trace, "balance_before", lambda *a: 0), mock.patch.object(trace, "relay_origin", lambda c, o, ts: origin):
            got = trace.explain(ctx, trace.FUNDING, row(io.ZERO, W, 400_000_000, 1006, 12, token=pm.PUSD, tx=wrap_tx))
        self.assertEqual(got["status"], "CONFIRMED", got["detail"])
        self.assertEqual(got["parts"][0][1:], (2 * 10 ** 17, 400_000_000))               # ETH wei at the payout, pUSD units at the wallet

    def test_money_paid_by_a_registered_address_is_not_an_outside_origin(self):
        ctx = context()
        ctx.service = {B}
        self.assertEqual(trace.explain(ctx, trace.WITHDRAWAL, row(B, C, 100, 900))["status"], "NOT_ORIGIN")

    def test_only_wallet_shaped_bytecode_reaches_the_classifier(self):
        ctx = context()
        ctx.codes.update({(137, A): "0x6080604052348015600f57600080fd5b50", (137, B): "0x", (137, C): "0xef0100" + "1" * 40})
        with mock.patch.object(pm, "classify", side_effect=AssertionError("classifier called for a non-wallet shape")):
            self.assertEqual([ctx.wallet(x) for x in (A, B, C)], [None, None, None])

    def test_unwrap_paid_by_the_collateral_reserve_is_walked_to_the_wallet(self):
        """The wallet burns pUSD and the reserve pays the same amount of USDC.e straight to a ChangeNOW deposit address."""
        reserve, tx = "0xc417fd8e9661c0d2120b64a04bb3278c17e99db1", TX(55)
        receipt = dict(transactionHash=tx, blockNumber=hex(700), status="0x1", logs=[log(pm.PUSD, W, pm.PUSD, 1_002_000_000, 700, 3, tx), log(pm.USDC_E, reserve, C, 1_002_000_000, 700, 5, tx)])
        ctx = context(wallets={W: dict(type="DEPOSIT_WALLET", owners=[A], evidence=[])})
        ctx.receipts[(137, tx)] = receipt
        got = trace.explain(ctx, trace.WITHDRAWAL, row(reserve, C, 1_002_000_000, 700, 5, tx=tx))
        self.assertEqual((got["status"], [h["kind"] for h in got["hops"]]), ("CONFIRMED", ["CONVERSION_1_TO_1", "POLYMARKET_WALLET_DEBIT"]))
        self.assertEqual(got["parts"][0][0]["src"], W)

    def test_withdrawal_is_walked_back_to_the_wallet_first_in_first_out(self):
        """The wallet sends 200 then 12 USDC.e to its key, which sends 212 to a ChangeNOW deposit address."""
        first, second = row(W, A, 200_000_000, 500), row(W, A, 12_000_000, 520)
        deposit = row(A, C, 212_000_000, 560)
        ctx = context([], {(137, A): [first, second, deposit]}, wallets={W: dict(type="DEPOSIT_WALLET", owners=[A], evidence=[])})
        ctx.codes.update({(137, W): "0x363d"})
        with mock.patch.object(trace, "balance_before", lambda *a: 0):
            got = trace.explain(ctx, trace.WITHDRAWAL, deposit)
        self.assertEqual(got["status"], "CONFIRMED", got["detail"])
        self.assertEqual([(o["raw"], raw) for o, raw, _ in got["parts"]], [(200_000_000, 200_000_000), (12_000_000, 12_000_000)])


class WithdrawalSenders(unittest.TestCase):
    def test_a_sender_is_fed_by_its_first_wallet_and_the_search_stops_there(self):
        wallet = "0x" + "0" * 39 + "7"
        crowd = ["0x" + f"{n:040x}" for n in range(100, 200)]               # 100 payers of one router: the wallet is among the first 40
        ctx = context()
        asked = []
        ctx.preload_codes = lambda part: asked.append(len(part))
        ctx.wallet = lambda a: a == wallet or None
        got = analyse.fed_senders(ctx, {A: set(crowd) | {wallet}, B: {pm.PUSD}, C: set(crowd), Q: {wallet}}, [A, B, C])
        self.assertEqual(got, {A, B})                                        # B: paid by a collateral ramp; C: no wallet among its payers
        self.assertEqual(asked, [40, 40, 40, 20])                            # A stops at its first batch; C reads all 100 of its payers; Q is not a sender
        self.assertEqual(analyse.fed_senders(ctx, {A: {io.ZERO}}, [A]), set())      # a mint from nowhere feeds nobody


class SecondReading(unittest.TestCase):
    def test_a_published_transfer_must_still_be_in_its_receipt(self):
        tx = TX(5)
        receipt = dict(transactionHash=tx, status="0x1", blockNumber=hex(700), blockHash="0x" + "b" * 64, logs=[log(pm.USDC_E, A, B, 250, 700, 3, tx)])
        ref = dict(chain=137, tx=tx, log_index=3, block=700, block_hash="0x" + "b" * 64, src=A, dst=B, token=pm.USDC_E, raw="250")
        self.assertEqual(reconcile.check_transfer(ref, {(137, tx): receipt}), "ok")
        self.assertIn("MISMATCH", reconcile.check_transfer(dict(ref, raw="251"), {(137, tx): receipt}))                 # another amount
        self.assertIn("MISMATCH", reconcile.check_transfer(dict(ref, block_hash="0x" + "c" * 64), {(137, tx): receipt}))  # another block: a reorganisation
        self.assertIn("MISMATCH", reconcile.check_transfer(dict(ref, log_index=9), {(137, tx): receipt}))
        self.assertIn("MISMATCH", reconcile.check_transfer(ref, {(137, tx): dict(receipt, status="0x0")}))
        self.assertIn("not checked", reconcile.check_transfer(dict(ref, log_index=-2), {}))


class RelayDeposits(unittest.TestCase):
    """The 27 withdrawals of 2026-W46 enter Relay's shared escrow with RelayErc20Deposit(address,address,uint256,bytes32),
    not with an ERC-20 Transfer. The fixture keeps the two real logs of each receipt: the deposit event and the token
    movement that corroborates it. Altered copies use those same shapes."""

    def cache(self, case, receipt=None):
        return {(case["ref"]["chain"], case["ref"]["tx"]): receipt or case["receipt"]}

    @staticmethod
    def logs(case, mutate):
        return [mutate(dict(one)) for one in case["receipt"]["logs"]]

    def test_all_27_real_deposits_verify_by_their_own_abi(self):
        self.assertEqual(len(RELAY_DEPOSITS), 27)
        for case in RELAY_DEPOSITS:
            self.assertEqual(reconcile.check_transfer(case["ref"], self.cache(case), (case["order"],)), "ok", case["event_id"])

    def test_the_deposit_log_is_not_an_erc20_transfer(self):
        case = RELAY_DEPOSITS[0]
        deposit = next(one for one in case["receipt"]["logs"] if int(one["logIndex"], 16) == case["ref"]["log_index"])
        self.assertIsNone(io.decode_transfer(deposit, 137))                          # the old check could only say "not a transfer"
        decoded = io.decode_relay_deposit(deposit)
        self.assertEqual((decoded["depositor"], decoded["token"], decoded["raw"], decoded["order"]),
                         (case["ref"]["src"], case["ref"]["token"], int(case["ref"]["raw"]), case["order"]))

    def test_a_deposit_without_a_correlated_order_is_a_mismatch(self):
        case = RELAY_DEPOSITS[0]
        self.assertIn("correlated Relay order", reconcile.check_transfer(case["ref"], self.cache(case)))

    def test_an_altered_order_id_is_a_mismatch(self):
        case = RELAY_DEPOSITS[0]
        got = reconcile.check_transfer(case["ref"], self.cache(case), ("0x" + "f" * 64,))
        self.assertIn("order", got)

    def test_an_altered_deposit_amount_is_a_mismatch(self):
        case = RELAY_DEPOSITS[0]

        def bump(one):
            if int(one["logIndex"], 16) == case["ref"]["log_index"]:
                words = [one["data"][2:][i:i + 64] for i in range(0, len(one["data"][2:]), 64)]
                words[2] = f"{int(words[2], 16) + 1:064x}"
                one["data"] = "0x" + "".join(words)
            return one

        got = reconcile.check_transfer(case["ref"], self.cache(case, dict(case["receipt"], logs=self.logs(case, bump))), (case["order"],))
        self.assertIn("Relay deposit differs", got)
        self.assertIn("raw", got)

    def test_an_altered_token_movement_no_longer_corroborates_the_deposit(self):
        case = RELAY_DEPOSITS[0]

        def bump(one):
            if int(one["logIndex"], 16) != case["ref"]["log_index"]:
                one["data"] = hex(int(one["data"], 16) + 1)
            return one

        got = reconcile.check_transfer(case["ref"], self.cache(case, dict(case["receipt"], logs=self.logs(case, bump))), (case["order"],))
        self.assertIn("no matching token transfer", got)

    def test_a_deposit_without_its_token_movement_is_a_mismatch(self):
        case = RELAY_DEPOSITS[0]
        only_deposit = [one for one in case["receipt"]["logs"] if int(one["logIndex"], 16) == case["ref"]["log_index"]]
        got = reconcile.check_transfer(case["ref"], self.cache(case, dict(case["receipt"], logs=only_deposit)), (case["order"],))
        self.assertIn("no matching token transfer", got)

    def test_two_matching_token_movements_are_ambiguous(self):
        case = RELAY_DEPOSITS[0]
        move = next(one for one in case["receipt"]["logs"] if int(one["logIndex"], 16) != case["ref"]["log_index"])
        duplicate = dict(move, logIndex=hex(int(move["logIndex"], 16) + 1000))
        got = reconcile.check_transfer(case["ref"], self.cache(case, dict(case["receipt"], logs=case["receipt"]["logs"] + [duplicate])), (case["order"],))
        self.assertIn("ambiguous Relay deposit", got)

    def test_a_failed_transaction_is_a_mismatch(self):
        case = RELAY_DEPOSITS[0]
        got = reconcile.check_transfer(case["ref"], self.cache(case, dict(case["receipt"], status="0x0")), (case["order"],))
        self.assertIn("transaction failed", got)

    def test_a_receipt_of_another_transaction_is_a_mismatch(self):
        case = RELAY_DEPOSITS[0]
        got = reconcile.check_transfer(case["ref"], self.cache(case, dict(case["receipt"], transactionHash="0x" + "1" * 64)), (case["order"],))
        self.assertIn("another transaction", got)

    def test_a_receipt_of_another_chain_is_a_mismatch(self):
        case = RELAY_DEPOSITS[0]
        got = reconcile.check_transfer(case["ref"], self.cache(case, dict(case["receipt"], chainId="0x1")), (case["order"],))
        self.assertIn("receipt chain", got)

    def test_a_missing_receipt_is_unavailable_not_a_pass(self):
        case = RELAY_DEPOSITS[0]
        with mock.patch.object(io, "rpc", side_effect=net.SourceError("receipt not served")), mock.patch.object(reconcile.time, "sleep", lambda *_: None):
            got = reconcile._safe_check(reconcile.check_transfer, case["ref"], {}, (case["order"],))
        self.assertTrue(got.startswith("UNAVAILABLE"), got)

    def test_the_escrow_log_must_be_a_relay_deposit_of_that_order(self):
        case = RELAY_DEPOSITS[0]
        hop = dict(case["ref"], kind="RELAY_ORDER", order=case["order"], fill_chain=1, fill_tx=TX(77),
                   fill_raw=case["ref"]["raw"], fill_token=case["ref"]["token"])
        paid = dict(hash=hop["fill_tx"], input="0x" + "0" * 8 + case["order"][2:], chainId="0x1")
        with mock.patch.object(io, "rpc", lambda *a, **k: paid):
            self.assertEqual(reconcile.check_relay(hop, self.cache(case)), "ok")
            self.assertIn("order", reconcile.check_relay(dict(hop, order="0x" + "f" * 64), self.cache(case)))

        def retarget(one):
            if int(one["logIndex"], 16) == case["ref"]["log_index"]:
                one["address"] = A                                          # a look-alike event outside the escrow
            return one

        got = reconcile.check_relay(hop, self.cache(case, dict(case["receipt"], logs=self.logs(case, retarget))))
        self.assertIn("not a Relay deposit", got)

    def test_a_native_escrow_log_is_read_by_its_own_abi(self):
        order, depositor, raw = "0x" + "a" * 64, A, 10 ** 18
        escrow = dict(address=io.RELAY_DEPOSITORY, topics=[io.RELAY_NATIVE_DEPOSIT], data="0x" + "0" * 24 + depositor[2:] + f"{raw:064x}" + order[2:],
                      logIndex="0x5", blockNumber=hex(700), blockHash="0x" + "b" * 64, transactionHash=TX(9), removed=False)
        receipt = dict(transactionHash=TX(9), status="0x1", blockNumber=hex(700), blockHash="0x" + "b" * 64, logs=[escrow])
        hop = dict(chain=1, tx=TX(9), log_index=5, block=700, block_hash="0x" + "b" * 64, src=depositor, dst=io.RELAY_DEPOSITORY,
                   token="native", raw=str(raw), order=order, fill_chain=1, fill_tx=TX(10))
        paid = dict(hash=TX(10), input="0x" + "0" * 8 + order[2:], chainId="0x1")
        with mock.patch.object(io, "rpc", lambda *a, **k: paid):
            self.assertEqual(reconcile.check_relay(hop, {(1, TX(9)): receipt}), "ok")


class Derivation(unittest.TestCase):
    def test_importing_the_archived_tools_leaves_no_cache_file_in_evidence_folders(self):
        for folder in ("investigations/polysentinel/sources/signal_engine/fund_flow", "investigations/changenow-outflows/sources/tools"):
            self.assertFalse((report.REPO / folder / "__pycache__").exists(), folder)     # validate_evidence.py refuses any file outside the manifest

    def test_deposit_wallet_addresses_match_wallets_seen_on_chain(self):
        self.assertEqual(pm.kk.deposit_wallet("0xf8442eb119ca4d29cd5bcce4e28aedffa9db1827", pm.kk.TEMPLATE), "0x9e7ca29f605c6570cf2959ca5579ff21cd112d36")
        self.assertEqual(pm.kk.deposit_wallet("0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d"), "0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5")


def analysis(closed=False):
    def event(n, direction, account, usd, cn_tx, cn_index, pm_index, ts):
        cn = dict(chain=137, tx=cn_tx, log_index=cn_index, block=1000 + n, block_hash="0x" + "b" * 64, ts=ts, src=SOURCE if direction == "FUNDING" else A,
                  dst=A if direction == "FUNDING" else C, token=pm.USDC_E, raw=str(int(usd * 1e6)))
        money = dict(chain=137, tx=TX(900 + n), log_index=pm_index, block=1001 + n, block_hash="0x" + "b" * 64, ts=ts + 6, src=A, dst=account, token=pm.PUSD, raw=str(int(usd * 1e6)))
        return dict(event_id=f"e{n}", week="2026-W46", direction=direction, level="CONFIRMED", account=account, cn=cn, cn_address=SOURCE if direction == "FUNDING" else C,
                    cn_counterparty=A, cn_raw=str(int(usd * 1e6)), pm=money, pm_raw=str(int(usd * 1e6)), hops=[dict(kind="CHANGENOW_PAYOUT", chain=137, tx=cn_tx, log_index=cn_index,
                    block=1000 + n, ts=ts, src=SOURCE, dst=A, token=pm.USDC_E, raw=str(int(usd * 1e6)))], bound=dict(direct=True), symbol="USDC", decimals=6, amount=usd, price_usd=1.0,
                    price_ts=ts, usd=usd, cn_role="PAYOUT_HOT", cn_attribution=["B_STRUCTURAL"], cn_service_wallets=[SOURCE])
    summary = dict(first_trade_ts=1794182500, last_trade_ts=1794182900, week_trades=3, week_trade_usd=40.0, week_complete=True, markets=[], cash_rows=[])
    near = dict(after_funding=[dict(ts=1794182506, day_over=True, trades=2, usd=30.0, first_trade_ts=1794182806, largest_market="Will it rain?", largest_market_usd=20.0)],
                before_withdrawal=[dict(ts=1794182706, redemptions=1, usd=80.0, largest_market="Did it rain?", largest_market_usd=80.0)], complete=True)
    account = lambda name: dict(wallet="", type="DEPOSIT_WALLET", owners=[A], evidence=["owner() read on-chain."], profile=dict(name=name, pseudonym=None), summary=summary,   # noqa: E731
                                around=near if name else dict(after_funding=[], before_withdrawal=[], complete=True))
    events = [event(1, "FUNDING", W, 60.0, TX(1), 3, 5, 1794182500), event(2, "FUNDING", W, 40.0, TX(1), 3, 9, 1794182600),    # one payout, two credits
              event(3, "WITHDRAWAL", W, 25.0, TX(2), 1, 2, 1794182700), event(4, "FUNDING", Q, 500.0, TX(3), 0, 1, 1794182800)]
    block = dict(first=100, last=10_000, closed=closed, head=10_000, head_ts=1794182400 + 20_000, rule="finalized", week="2026-W46")
    stats = dict(payouts=10, payout_recipients=8, unrecognised_token_rows=1, deposit_addresses_gas_funded=4, deposit_addresses_single_use=1, other_senders_into_sources=0)
    return dict(week="2026-W46", start=1794182400, end=1794787200, generated_ts=1794700000, closed=closed, blocks={"137": block}, active={"137": {SOURCE: 12}},
                stage1={"137": dict(reg_out=dict(rows=10, windows=2, other_shapes=0), native=None)},
                population={"137": dict(stats=stats, sources=[SOURCE], funders=[], roles={SOURCE: dict(role="PAYOUT_HOT", sends=10, recipients=8, once_share=0.9, top_share=0.1, receives=5, senders=5)},
                                        deposits=dict(customer_deposits=5, senders=4, deposit_addresses_without_customer_row=0, native_read=True))},
                dependent={k: dict(rows=1, addresses=1, heavy=[]) for k in ("rcp_out", "own_in", "snd_in")},
                linking=dict(counterparties=12, trading_wallets_among_counterparties=1, keys_owning_a_wallet=2), events=events, accounts={W: account("alpha"), Q: account(None)},
                candidates=[dict(week="2026-W46", direction="FUNDING", level="PROBABLE", account=B, wallet_kind="DEPOSIT_WALLET", owner=C, ownership_proof="owner()", changenow_transfers=2,
                                 usd_upper_bound=900.0, unpriced_transfers=0, chains=[137], first_ts=1794182400, last_ts=1794182500, transfers=[], missing=["funds are mixed"])],
                totals={"137:payouts": dict(transfers=10, addresses=8, usd=1000.0, unvalued_transfers=0, by_token={})}, other_chains={},
                walks=dict(counts={"FUNDING:CONFIRMED": 3}, unresolved=[]), requests=dict(io_counts={"gateway.tenderly.co:200": 5}))


class Reports(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.raw = Path(tempfile.mkdtemp())
        for patcher in (mock.patch.object(report, "OUT", self.out), mock.patch("builtins.print")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, closed=False):
        (self.raw / "2026-W46").mkdir(exist_ok=True)
        (self.raw / "2026-W46" / "analysis.json").write_text(json.dumps(analysis(closed)))
        return report.write(self.raw, "2026-W46")

    def test_ranking_counts_each_changenow_transfer_once(self):
        rows = report.leaderboard(analysis())
        self.assertEqual([r["account"] for r in rows], [Q, W])            # by gross volume, largest first
        alpha = rows[1]
        self.assertEqual(alpha["inflow_transactions"], 1)                 # one payout split over two credits is one transaction
        self.assertEqual((alpha["inflow_usd"], alpha["outflow_usd"], alpha["gross_usd"], alpha["net_usd"]), (100.0, 25.0, 125.0, 75.0))
        self.assertEqual(sum(r["gross_usd"] for r in rows), sum(e["usd"] for e in analysis()["events"]))

    def test_probable_candidates_never_enter_the_confirmed_table(self):
        self.write()
        board = (self.out / "WEEKLY_LEADERBOARD.md").read_text()
        confirmed, probable = board.split("## Probable flows")
        self.assertNotIn(B, confirmed)
        self.assertIn(B, probable)
        self.assertIn("Provisional", board)
        data = json.loads((self.out / "weekly_leaderboard.json").read_text())
        self.assertEqual([r["account"] for r in data["accounts"]], [Q, W])
        self.assertEqual(data["status"]["state"], "PROVISIONAL")
        self.assertFalse(report.freeze("2026-W46"))                      # an open week cannot be sealed

    def test_every_deliverable_is_written_and_rows_match(self):
        self.write()
        week = self.out / "weeks" / "2026-W46"
        for name in ("WEEKLY_LEADERBOARD.md", "weekly_leaderboard.csv", "weekly_leaderboard.json", "transactions.csv", "transactions.json", "candidates.csv", "COVERAGE.md", "PATTERNS.md", "STATUS.json"):
            self.assertTrue((week / name).stat().st_size > 0, name)
        self.assertEqual(len((week / "transactions.csv").read_text().splitlines()), 1 + 4)       # one line per economic event
        self.assertTrue((self.out / "accounts" / f"{W}.md").exists())
        self.assertFalse((week / "SHA256SUMS").exists())                  # an open week is not frozen

    def test_patterns_show_trading_after_a_funding_and_redemptions_before_a_withdrawal(self):
        self.write()
        text = (self.out / "PATTERNS.md").read_text()
        after = text.split("## Trading in the day after a confirmed funding")[1].split("##")[0]
        self.assertIn("| 60.00 | 5 | 2 | 30.00 | Will it rain? (20.00 USD) | yes |", after)      # the credit of 60 USD, first trade five minutes later
        self.assertIn("1 of 1 fundings were followed by at least one trade", after)
        before = text.split("## Redemptions in the day before a confirmed withdrawal")[1].split("##")[0]
        self.assertIn("| 25.00 | 1 | 80.00 | Did it rain? (80.00 USD) |", before)
        old = analysis()
        for account in old["accounts"].values():
            del account["around"]                                        # an analysis file written before this measure existed
        (self.raw / "2026-W46" / "analysis.json").write_text(json.dumps(old))
        report.write(self.raw, "2026-W46")
        self.assertIn("Not measured for this analysis file.", (self.out / "PATTERNS.md").read_text())

    def test_the_day_after_a_funding_and_the_day_before_a_withdrawal_are_read_from_the_feed(self):
        asked = []

        def feed(wallet, kind=None, start=None, end=None, **k):
            asked.append((kind, start, end))
            rows = dict(TRADE=[dict(timestamp=1000 + 60, usdc_size=5, title="M1"), dict(timestamp=1000 + 7200, usdc_size=9, title="M2"), dict(timestamp=1000 + 90000, usdc_size=50, title="M3")],
                        REDEEM=[dict(timestamp=200_000 - 100, usdc_size=70, title="R1"), dict(timestamp=200_000 - 90_000, usdc_size=999, title="R0")])[kind]
            return [r for r in rows if start <= r["timestamp"] <= end], True

        with mock.patch.object(pm, "activity", feed):
            got = pm.around(W, [("FUNDING", 1000), ("WITHDRAWAL", 200_000)], horizon=50_000)
        self.assertEqual(asked, [("TRADE", 1000, 50_000), ("REDEEM", 200_000 - 86400, 200_000)])
        self.assertEqual(got["after_funding"], [dict(ts=1000, day_over=False, trades=2, usd=14.0, first_trade_ts=1060, largest_market="M2", largest_market_usd=9.0)])
        self.assertEqual(got["before_withdrawal"], [dict(ts=200_000, redemptions=1, usd=70.0, largest_market="R1", largest_market_usd=70.0)])

    def test_the_same_analysis_gives_the_same_bytes(self):
        self.write()
        first = {p.name: p.read_bytes() for p in (self.out / "weeks" / "2026-W46").iterdir()}
        self.write()
        self.assertEqual(first, {p.name: p.read_bytes() for p in (self.out / "weeks" / "2026-W46").iterdir()})

    def test_a_closed_week_is_frozen_and_any_change_is_caught(self):
        self.write(closed=True)
        week = self.out / "weeks" / "2026-W46"
        self.assertFalse(report.freeze("2026-W46"))                      # closed, but not read a second time yet
        (week / "RECONCILIATION.json").write_text(json.dumps(dict(mismatches=[["e1", "changenow side", 137, TX(1), "MISMATCH: log differs"]])))
        self.assertFalse(report.freeze("2026-W46"))                      # a mismatch keeps the week open
        (week / "RECONCILIATION.json").write_text(json.dumps(dict(mismatches=[])))
        self.assertTrue(report.freeze("2026-W46"))
        self.assertTrue((week / "SHA256SUMS").exists())
        self.assertIn("FROZEN", (self.out / "WEEKLY_LEADERBOARD.md").read_text())
        self.assertEqual(report.verify(self.out), 0)
        with self.assertRaises(SystemExit):                              # a frozen week is never written again
            self.write(closed=True)
        (week / "transactions.csv").write_text((week / "transactions.csv").read_text() + "x\n")
        self.assertEqual(report.verify(self.out), 1)
        (week / "extra.txt").write_text("added")
        self.assertEqual(report.verify(self.out), 1)

    def test_published_frozen_weeks_of_this_repository_are_intact(self):
        with mock.patch.object(report, "OUT", report.REPO / "reports/changenow"):
            self.assertEqual(report.verify(), 0)


if __name__ == "__main__":
    unittest.main()
