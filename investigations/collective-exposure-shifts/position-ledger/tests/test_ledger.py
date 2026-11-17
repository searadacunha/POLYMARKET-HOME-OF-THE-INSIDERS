#!/usr/bin/env python3
"""Synthetic tests and edge cases for scripts/ledger.py. Run: python3 -I tests/test_ledger.py (or pytest)."""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import ledger as L  # noqa: E402

A, B, C = "0xaaa", "0xbbb", "0xccc"
M1, M2, M3 = "0xm1", "0xm2", "0xm3"
TAPE = {"history_complete": True, "neg_risk": False, "coverage": L.TAPE_COVERAGE, "fees_enabled": False}
FULL = {"history_complete": True, "neg_risk": False, "coverage": L.FULL_COVERAGE, "fees_enabled": False}


def ev(ts, w, kind, oi=None, qty=0.0, price=None, tx=None, cid=M1, seq=0, usdc=None, seen=None):
    return L.make_event(ts, w, cid, kind, oi=oi, qty=qty, price=price, tx=tx, seq=seq, usdc=usdc, seen_ts=seen,
                        src=f"test#{ts}.{seq}")


def matched(ts, tx, buyer, seller, oi, qty, price, cid=M1):
    """A regular CLOB match: buyer BUY, seller SELL of the same token (balanced)."""
    return [ev(ts, buyer, "BUY", oi, qty, price, tx, cid, 0), ev(ts, seller, "SELL", oi, qty, price, tx, cid, 1)]


def mint(ts, tx, w_yes, w_no, qty, p_yes, cid=M1):
    """A mint match: one buys YES, the other buys NO, new tokens created (balanced: +q, +q)."""
    return [ev(ts, w_yes, "BUY", L.YES, qty, p_yes, tx, cid, 0), ev(ts, w_no, "BUY", L.NO, qty, 1 - p_yes, tx, cid, 1)]


def test_buy_sell_both_sides():
    evs = mint(100, "0x1", A, B, 1000, 0.4) + matched(200, "0x2", C, A, L.YES, 400, 0.5) \
        + matched(300, "0x3", B, C, L.NO, 100, 0.45)
    lg = L.Ledger(evs, {M1: TAPE})
    a = lg.snapshot(A, M1, 1000)
    assert a["observable"]["flow_yes"] == 600 and a["observable"]["x_yes_equiv"] == 600
    assert abs(a["observable"]["cash_flow"] - (-400 + 200)) < 1e-9
    b = lg.snapshot(B, M1, 1000)
    assert b["observable"]["flow_no"] == 1100 and b["observable"]["x_yes_equiv"] == -1100
    c = lg.snapshot(C, M1, 1000)
    assert c["observable"]["flow_yes"] == 400 and c["observable"]["flow_no"] == -100   # sold NO it never bought
    assert c["observable"]["proven_unobserved_inflow"] == [0.0, 100.0]
    assert "UNOBSERVED_INFLOW_PROVEN" in c["reasons"] and c["x_status"] == "OBSERVABLE"
    assert all(v == "BALANCED" for v in lg.tx_verdicts.values())


def test_split_merge_leave_direction_unchanged():
    base = [ev(100, A, "BUY", L.YES, 300, 0.3, "0x1", seq=0), ev(100, B, "SELL", L.YES, 300, 0.3, "0x1", seq=1)]
    proto = [ev(150, A, "SPLIT", qty=1000), ev(250, A, "MERGE", qty=400)]
    full = L.Ledger(base + proto, {M1: FULL})
    s = full.snapshot(A, M1, 300)
    assert s["inventory"]["status"] == "EXACT" and s["inventory"]["lo"] == [900.0, 600.0]
    tape = L.Ledger(base, {M1: TAPE})   # same wallet seen through fills only
    t = tape.snapshot(A, M1, 300)
    assert t["observable"]["x_yes_equiv"] == s["observable"]["x_yes_equiv"] == 300
    assert t["inventory"]["status"] == "BOUNDED" and t["inventory"]["lo"] == [300.0, 0.0] and t["inventory"]["hi"] is None
    assert t["x_status"] == "OBSERVABLE" and "TRANSFERS_NOT_COVERED" in t["reasons"]


def test_negative_inventory_with_full_coverage_is_unknown():
    evs = [ev(100, A, "SELL", L.YES, 50, 0.5, "0x1", seq=0), ev(100, B, "BUY", L.YES, 50, 0.5, "0x1", seq=1)]
    s = L.Ledger(evs, {M1: FULL}).snapshot(A, M1, 200)
    assert s["inventory"]["status"] == "UNKNOWN" and "NEGATIVE_INVENTORY_WITH_FULL_COVERAGE" in s["reasons"]
    assert s["x_status"] == "UNKNOWN"


def test_duplicate_row_is_dropped_only_when_it_breaks_balance():
    evs = matched(100, "0x1", A, B, L.YES, 100, 0.5)
    dup = evs + [ev(100, A, "BUY", L.YES, 100, 0.5, "0x1", seq=2)]   # same fill reported twice
    lg = L.Ledger(dup, {M1: TAPE})
    assert lg.tx_verdicts[("0x1", M1)] == "DUPLICATES_DROPPED"
    assert lg.snapshot(A, M1, 200)["observable"]["flow_yes"] == 100
    assert [r for _, r in lg.quarantine] == ["DUPLICATE_ROW"]
    # two genuine identical fills (taker matched twice at the same size and price): balanced, both kept
    two = [ev(100, A, "BUY", L.YES, 50, 0.5, "0x2", seq=0), ev(100, A, "BUY", L.YES, 50, 0.5, "0x2", seq=1),
           ev(100, B, "SELL", L.YES, 100, 0.5, "0x2", seq=2)]
    lg2 = L.Ledger(two, {M1: TAPE})
    assert lg2.tx_verdicts[("0x2", M1)] == "BALANCED" and lg2.snapshot(A, M1, 200)["observable"]["flow_yes"] == 100


def test_missing_leg_makes_position_unknown_from_that_time():
    evs = matched(100, "0x1", A, B, L.YES, 100, 0.5) + [ev(200, A, "BUY", L.YES, 70, 0.5, "0x2")]  # seller missing
    lg = L.Ledger(evs, {M1: TAPE})
    assert lg.tx_verdicts[("0x2", M1)] == "UNBALANCED"
    assert lg.snapshot(A, M1, 150)["x_status"] == "OBSERVABLE"          # before the broken tx: still readable
    s = lg.snapshot(A, M1, 250)
    assert s["x_status"] == "UNKNOWN" and "TX_UNBALANCED" in s["reasons"] and s["inventory"]["lo"] is None


def test_invalid_chronology_is_refused():
    for bad in (dict(ts=None), dict(ts=-5), dict(ts=float("nan"))):
        try:
            L.make_event(bad["ts"], A, M1, "BUY", oi=0, qty=1, price=0.5)
        except L.ChronologyError:
            continue
        raise AssertionError(f"accepted {bad}")
    try:
        L.make_event(100, A, M1, "BUY", oi=0, qty=1, price=0.5, seen_ts=90)
        raise AssertionError("accepted seen_ts < ts")
    except L.ChronologyError:
        pass
    for kw in (dict(qty=-1, price=0.5), dict(qty=1, price=1.5)):
        try:
            L.make_event(100, A, M1, "BUY", oi=0, **kw)
            raise AssertionError(f"accepted {kw}")
        except ValueError:
            pass


def test_late_observed_event_is_not_used_before_it_is_seen():
    evs = matched(100, "0x1", A, B, L.YES, 100, 0.5)
    late = [ev(150, A, "BUY", L.YES, 40, 0.5, "0x2", seq=0, seen=400), ev(150, C, "SELL", L.YES, 40, 0.5, "0x2", seq=1)]
    lg = L.Ledger(evs + late + matched(200, "0x3", A, B, L.YES, 10, 0.5), {M1: TAPE})
    s = lg.snapshot(A, M1, 300)
    assert s["observable"]["flow_yes"] == 110 and s["x_status"] == "OBSERVABLE"
    # as known at 300, tx 0x2 shows only C's sale: C is flagged, A is not
    assert "TX_UNBALANCED" in lg.snapshot(C, M1, 300)["reasons"]
    s4 = lg.snapshot(A, M1, 400)
    assert s4["observable"]["flow_yes"] == 150 and "TX_UNBALANCED" not in lg.snapshot(C, M1, 400)["reasons"]


def test_tx_check_uses_only_rows_seen_by_T():
    # a counterparty row seen later must neither vouch for nor taint a reading made before it was seen
    one = [ev(100, A, "BUY", L.YES, 100, 0.5, "0x1", seq=0), ev(100, B, "SELL", L.YES, 100, 0.5, "0x1", seq=1, seen=900)]
    assert L.Ledger(one, {M1: TAPE}).snapshot(A, M1, 200)["x_status"] == "UNKNOWN"
    two = [ev(100, B, "SELL", L.YES, 100, 0.5, "0x1", seq=0), ev(100, A, "BUY", L.YES, 100, 0.5, "0x1", seq=1),
           ev(100, A, "BUY", L.YES, 50, 0.5, "0x1", seq=2, seen=900)]
    lg = L.Ledger(two, {M1: TAPE})
    assert lg.snapshot(B, M1, 200)["x_status"] == "OBSERVABLE" and lg.snapshot(B, M1, 1000)["x_status"] == "UNKNOWN"


def test_same_second_order_cannot_create_negative_inventory():
    evs = [ev(100, A, "BUY", L.YES, 1000, 0.5, "0xff", seq=1), ev(100, B, "SELL", L.YES, 1000, 0.5, "0xff", seq=2),
           ev(100, A, "SELL", L.YES, 1000, 0.6, "0x00", seq=3), ev(100, C, "BUY", L.YES, 1000, 0.6, "0x00", seq=4)]
    s = L.Ledger(evs, {M1: FULL}).snapshot(A, M1, 100)
    assert s["observable"]["proven_unobserved_inflow"] == [0.0, 0.0] and s["x_status"] == "EXACT"


def test_bounds_respect_redemption_coverage():
    cov = {**L.FULL_COVERAGE, "redeem": False}
    s = L.Ledger(mint(100, "0x1", A, B, 1000, 0.6), {M1: {**FULL, "coverage": cov}}).snapshot(A, M1, 10 ** 9)
    assert s["x_status"] == "OBSERVABLE" and "REDEMPTIONS_NOT_COVERED" in s["reasons"]
    assert s["inventory"]["status"] == "BOUNDED" and s["inventory"]["lo"] == [0.0, 0.0] and s["inventory"]["hi"] == [1000.0, 0.0]
    neg = [ev(100, A, "SELL", L.YES, 50, 0.5, "0x1", seq=0), ev(100, B, "BUY", L.YES, 50, 0.5, "0x1", seq=1)]
    s2 = L.Ledger(neg, {M1: {**FULL, "coverage": cov}}).snapshot(A, M1, 200)
    assert s2["x_status"] == "UNKNOWN" and "NEGATIVE_INVENTORY_WITH_FULL_COVERAGE" in s2["reasons"]


def test_rows_without_tx_are_flagged():
    lg = L.Ledger([ev(100, A, "BUY", L.YES, 1000, 0.5, None)], {M1: FULL})
    s = lg.snapshot(A, M1, 200)
    assert lg.no_tx_rows[M1] == 1 and "TX_UNCHECKED" in s["reasons"] and s["x_status"] == "OBSERVABLE"


def test_window_index_matches_left_open_windows():
    assert L.window_index(3600) == 0 and L.window_index(3601) == 1 and L.window_index(7200) == 1
    evs = matched(3600, "0x1", A, B, L.YES, 5000, 0.4)
    k = L.window_index(3600)
    assert L.classify(L.Ledger(evs, {M1: TAPE}), A, L.family_binary(M1), k * 3600, (k + 1) * 3600)["class"] == "DIRECTIONAL_ADD"


def test_no_lookahead_random():
    rng = random.Random(7)
    wallets = [f"0xw{i}" for i in range(6)]
    evs = []
    for i in range(400):
        t = 1000 + i * 10
        a, b = rng.sample(wallets, 2)
        oi = rng.randint(0, 1)
        if rng.random() < 0.3:
            evs += mint(t, f"0xt{i}", a, b, rng.randint(1, 50), 0.5)
        else:
            evs += matched(t, f"0xt{i}", a, b, oi, rng.randint(1, 50), round(rng.random(), 2))
    full = L.Ledger(evs, {M1: TAPE})
    for T in (1500, 2500, 4000):
        cut = L.Ledger([e for e in evs if e["ts"] <= T], {M1: TAPE})
        for w in wallets:
            assert full.snapshot(w, M1, T) == cut.snapshot(w, M1, T), (w, T)
    shuffled = evs[:]
    rng.shuffle(shuffled)
    again = L.Ledger(shuffled, {M1: TAPE})
    assert [(e["ts"], e["tx"], e["wallet"]) for e in again.events] == [(e["ts"], e["tx"], e["wallet"]) for e in full.events]
    # conservation: total YES flow equals total NO flow equals net minted supply
    tot = [sum(full.snapshot(w, M1, 10 ** 9)["observable"][k] for w in wallets) for k in ("flow_yes", "flow_no")]
    assert abs(tot[0] - tot[1]) < 1e-6


def test_initial_position_unknown():
    lg = L.Ledger(matched(100, "0x1", A, B, L.YES, 10, 0.5), {M1: {**TAPE, "history_complete": False}})
    s = lg.snapshot(A, M1, 200)
    assert s["x_status"] == "UNKNOWN" and "INITIAL_POSITION_UNKNOWN" in s["reasons"]
    assert L.classify(lg, A, L.family_binary(M1), 0, 200)["class"] == "UNKNOWN"


def test_technical_events_only():
    evs = matched(100, "0x1", A, B, L.YES, 1000, 0.5) + [ev(5000, A, "SPLIT", qty=2000), ev(6000, A, "REWARD", usdc=3)]
    lg = L.Ledger(evs, {M1: FULL})
    assert L.classify(lg, A, L.family_binary(M1), 3600, 7200)["class"] == "C_TECHNICAL"


def test_true_inversion_A():
    evs = matched(100, "0x1", A, B, L.YES, 2000, 0.6) + matched(4000, "0x2", B, A, L.YES, 2000, 0.4) \
        + mint(4100, "0x3", C, A, 1500, 0.4)
    lg = L.Ledger(evs, {M1: TAPE})
    assert lg.snapshot(A, M1, 4200)["observable"]["x_yes_equiv"] == -1500
    assert L.classify(lg, A, L.family_binary(M1), 3600, 7200)["class"] == "A_TRUE_INVERSION"


def test_D_yes_accumulation_keeps_no():
    evs = mint(100, "0x1", A, B, 1000, 0.5) + mint(110, "0x2", C, A, 1000, 0.5) + matched(4000, "0x3", A, B, L.YES, 1000, 0.55)
    lg = L.Ledger(evs, {M1: TAPE})
    r = L.classify(lg, A, L.family_binary(M1), 3600, 7200)
    assert r["class"] == "D_UNVERIFIED_NO_RETENTION", r["class"]
    seen_merges = {**TAPE, "wallet_coverage": {A: {**L.TAPE_COVERAGE, "split_merge": True}}}
    assert L.classify(L.Ledger(evs, {M1: seen_merges}), A, L.family_binary(M1), 3600, 7200)["class"] == "D_YES_ACCUM_KEEP_NO"
    # the activity feed shows a merge that removed the NO: no longer D
    merged = evs + [ev(3700, A, "MERGE", qty=1000)]
    assert L.classify(L.Ledger(merged, {M1: seen_merges}), A, L.family_binary(M1), 3600, 7200)["class"] != "D_YES_ACCUM_KEEP_NO"
    # same YES purchase after the NO was sold is not D
    evs2 = evs[:4] + matched(3700, "0x4", B, A, L.NO, 1000, 0.45) + evs[4:]
    assert L.classify(L.Ledger(evs2, {M1: TAPE}), A, L.family_binary(M1), 3600, 7200)["class"] not in (
        "D_YES_ACCUM_KEEP_NO", "D_UNVERIFIED_NO_RETENTION")


def test_market_making_and_complete_set():
    evs = []
    for i in range(40):
        evs += matched(4000 + i * 10, f"0xa{i}", A, B, L.YES, 500, 0.50)
        evs += matched(4005 + i * 10, f"0xb{i}", C, A, L.YES, 500, 0.51)
    lg = L.Ledger(evs, {M1: TAPE})
    assert L.classify(lg, A, L.family_binary(M1), 3600, 7200)["class"] == "C_MARKET_MAKING"
    arb = matched(4000, "0xc1", A, B, L.YES, 1000, 0.45) + matched(4001, "0xc2", A, C, L.NO, 1000, 0.52)
    assert L.classify(L.Ledger(arb, {M1: TAPE}), A, L.family_binary(M1), 3600, 7200)["class"] == "C_COMPLETE_SET"


def test_hedge_by_selling_is_C():
    evs = matched(100, "0x1", A, B, L.YES, 3000, 0.5) + matched(4000, "0x2", B, A, L.YES, 2000, 0.6)
    assert L.classify(L.Ledger(evs, {M1: TAPE}), A, L.family_binary(M1), 3600, 7200)["class"] == "C_HEDGE_REBALANCE"


def test_ladder_no_d1_then_yes_d2_is_B_not_A():
    info = {M1: TAPE, M2: TAPE}
    fam = L.family_ladder([(M1, "2026-02-28"), (M2, "2026-03-31")], proof="test")
    evs = mint(100, "0x1", B, A, 1000, 0.3, cid=M1) + mint(4000, "0x2", A, C, 1000, 0.5, cid=M2)
    lg = L.Ledger(evs, info)
    v = L.payoff_vector(lg, A, fam, 7200)
    assert v["q_flow"] == [1000.0, 2000.0, 1000.0] and v["shape"] == [0.0, 1000.0, 0.0]
    assert L.classify(lg, A, fam, 3600, 7200)["class"] == "B_INTERVAL_PACKAGE"
    # the same two markets read one at a time would show NO then YES: that per-market reading is not used for B
    ch = L.vector_change(L.payoff_vector(lg, A, fam, 3600), v)
    assert ch["d_q_flow"] == [1000.0, 1000.0, 0.0] and ch["d_shape"] == [0.0, 0.0, -1000.0]


def test_ladder_true_reversal_is_A():
    info = {M1: TAPE, M2: TAPE}
    fam = L.family_ladder([(M1, "2026-02-28"), (M2, "2026-03-31")], proof="test")
    evs = mint(100, "0x1", A, B, 2000, 0.3, cid=M2) + matched(4000, "0x2", B, A, L.YES, 2000, 0.2, cid=M2) \
        + mint(4100, "0x3", C, A, 2000, 0.2, cid=M2)
    assert L.classify(L.Ledger(evs, info), A, fam, 3600, 7200)["class"] == "A_TRUE_INVERSION"


def test_neg_risk_conversion_keeps_family_shape():
    info = {c: {**FULL, "neg_risk": True} for c in (M1, M2, M3)}
    fam = L.family_exclusive([M1, M2, M3], exhaustive=True, proof="test")
    base = [ev(100, A, "BUY", L.NO, 600, 0.7, "0x1", cid=M1, seq=0), ev(100, B, "SELL", L.NO, 600, 0.7, "0x1", cid=M1, seq=1)]
    conv = [ev(200, A, "CONVERT_OUT", qty=600, cid=M1, usdc=0), ev(200, A, "CONVERT_IN", qty=600, cid=M2),
            ev(200, A, "CONVERT_IN", qty=600, cid=M3)]
    lg = L.Ledger(base + conv, info)
    assert L.payoff_vector(lg, A, fam, 150)["shape"] == L.payoff_vector(lg, A, fam, 250)["shape"] == [0.0, 600.0, 600.0]
    assert lg.snapshot(A, M1, 250)["observable"]["x_yes_equiv"] == 0.0     # market-level X moved
    tape_info = {c: {**TAPE, "neg_risk": True} for c in (M1, M2, M3)}
    s = L.Ledger(base, tape_info).snapshot(A, M1, 250)
    assert "CONVERSIONS_NOT_COVERED" in s["reasons"] and s["x_status"] == "OBSERVABLE"
    part = L.family_exclusive([M1, M2], exhaustive=False)
    assert "CONVERSIONS_NOT_COVERED" in L.payoff_vector(L.Ledger(base, tape_info), A, part, 250)["reasons"]


def test_transfer_moves_direction_and_is_flagged_when_not_covered():
    evs = matched(100, "0x1", A, B, L.YES, 100, 0.5) + [ev(200, A, "TRANSFER_OUT", L.YES, 100)]
    assert L.Ledger(evs, {M1: FULL}).snapshot(A, M1, 300)["observable"]["x_yes_equiv"] == 0
    s = L.Ledger(evs[:2], {M1: TAPE}).snapshot(A, M1, 300)
    assert s["x_status"] == "OBSERVABLE" and "TRANSFERS_NOT_COVERED" in s["reasons"]


def test_ladder_proof_is_conservative():
    def m(cid, q, d="Resolves YES if the US strikes Iran by the listed date. Source: news.", nr=False):
        return {"conditionId": cid, "question": q, "description": d, "negRisk": nr}
    ok = L.prove_ladder([m(M2, "US strikes Iran by March 31, 2026?"), m(M1, "US strikes Iran by February 28, 2026?")])
    assert ok["type"] == "ladder" and ok["members"] == [M1, M2]
    assert L.prove_ladder([m(M1, "Will Israel strike Lebanon on November 3, 2025?"),
                           m(M2, "Will Israel strike Lebanon on November 5, 2025?")])["type"] == "unproven"
    assert L.prove_ladder([m(M1, "US strikes Iran by February 28, 2026?"),
                           m(M2, "US strikes Iran by March 31, 2026?", d="Different rules.")])["type"] == "unproven"
    assert L.prove_ladder([m(M1, "X by February 28, 2026?", nr=True), m(M2, "X by March 31, 2026?", nr=True)])["type"] == "unproven"
    assert L.prove_ladder([m(M1, "US strikes Iran by February 28, 2026?"),
                           m(M2, "Israel strikes Iran by March 31, 2026?")])["type"] == "unproven"


def test_partitions_never_put_iran_in_valid_or_test():
    iran = "0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20"
    feb28 = L._epoch("2026-02-28T09:31:17")
    assert L.partition_of(iran, feb28, "us-strikes-iran-by", iran_cids=[iran]) == "EXPLORATORY_IRAN"
    assert L.partition_of("0xother", feb28, "us-strikes-iran-by-march") == "EXPLORATORY_IRAN"
    assert L.partition_of("0xother", feb28, "something-else") == "VALID"
    assert L.partition_of("0xo", L._epoch("2025-12-31T23:59:59")) == "TRAIN"
    assert L.partition_of("0xo", L._epoch("2026-07-01T00:00:00")) == "TEST"
    assert L.partition_of("0xo", L._epoch("2026-11-01T00:00:00")) == "EXCLUDED_PERIOD"
    assert L.partition_of("0xo", None) == "UNKNOWN_CLOSE"
    w = "0xiranwallet"
    assert L.observation_partition(feb28, w, "x", ["0xo"], iran_wallets={w}) == "EXPLORATORY_IRAN"
    assert L.observation_partition(L._epoch("2025-06-01T00:00:00"), w, "x", ["0xo"], iran_wallets={w}) == "EXPLORATORY_IRAN"
    assert L.observation_partition(L._epoch("2025-06-01T00:00:00"), "0xz", "x", ["0xo"], iran_wallets={w}) == "TRAIN"
    assert L.observation_partition(L._epoch("2025-06-01T00:00:00"), "0xz", "us-strikes-iran-by", ["0xo"]) == "EXPLORATORY_IRAN"
    assert L.usable_for_training(L._epoch("2025-12-01T00:00:00"), "TRAIN")
    assert not L.usable_for_training(L._epoch("2026-02-01T00:00:00"), "TRAIN")


def test_unknown_market_is_quarantined():
    lg = L.Ledger(matched(100, "0x1", A, B, L.YES, 1, 0.5, cid="0xzz"), {M1: TAPE})
    assert len(lg.quarantine) == 2 and not lg.events


def test_fee_in_shares_is_not_a_missing_fill():
    # real pattern (fee-enabled market): taker buys NO and receives 90 - 6 % x 0.07 x 90 shares
    evs = [ev(100, A, "BUY", L.NO, 89.622, 0.93, "0x1", seq=0), ev(100, B, "BUY", L.YES, 90.0, 0.07, "0x1", seq=1)]
    lg = L.Ledger(evs, {M1: {**TAPE, "fees_enabled": True}})
    assert lg.tx_verdicts[("0x1", M1)] == "FEE_IN_SHARES" and abs(lg.fee_rates[("0x1", M1)] - 0.06) < 1e-3
    assert lg.snapshot(A, M1, 200)["x_status"] == "OBSERVABLE" and lg.snapshot(A, M1, 200)["fees"] == "UNKNOWN"
    # same gap on a market without fees: a fill is missing
    assert L.Ledger(evs, {M1: TAPE}).tx_verdicts[("0x1", M1)] == "UNBALANCED"
    # a gap far above any fee is still a missing fill, fees or not
    big = [ev(100, A, "BUY", L.NO, 50.0, 0.93, "0x2", seq=0), ev(100, B, "BUY", L.YES, 90.0, 0.07, "0x2", seq=1)]
    assert L.Ledger(big, {M1: {**TAPE, "fees_enabled": True}}).tx_verdicts[("0x2", M1)] == "UNBALANCED"


def test_ladder_reverse_order_is_still_B():
    info = {M1: TAPE, M2: TAPE}
    fam = L.family_ladder([(M1, "2026-02-28"), (M2, "2026-03-31")], proof="test")
    evs = mint(100, "0x1", A, B, 1000, 0.5, cid=M2) + mint(4000, "0x2", C, A, 2000, 0.3, cid=M1)  # YES D2, then NO D1
    assert L.classify(L.Ledger(evs, info), A, fam, 3600, 7200)["class"] == "B_INTERVAL_PACKAGE"


def test_ladder_reversal_on_later_deadline_is_A_not_B():
    info = {M1: TAPE, M2: TAPE}
    fam = L.family_ladder([(M1, "2026-02-28"), (M2, "2026-03-31")], proof="test")
    evs = mint(100, "0x1", B, A, 1000, 0.3, cid=M1) + mint(110, "0x2", B, A, 3000, 0.4, cid=M2) \
        + mint(4000, "0x3", A, C, 6000, 0.6, cid=M2)   # NO D1 small, NO D2 3000, then YES D2 6000
    assert L.classify(L.Ledger(evs, info), A, fam, 3600, 7200)["class"] == "A_TRUE_INVERSION"


def test_market_making_is_marked_per_token():
    evs = mint(4000, "0x0", C, A, 3000, 0.1)
    for i in range(10):
        evs += matched(4100 + i * 10, f"0xa{i}", A, B, L.YES, 1000, 0.10) + matched(4105 + i * 10, f"0xb{i}", B, A, L.YES, 1000, 0.10)
    assert L.classify(L.Ledger(evs, {M1: TAPE}), A, L.family_binary(M1), 3600, 7200)["class"] == "DIRECTIONAL_ADD"


def test_reversal_hidden_in_a_complete_set_is_A():
    evs = matched(100, "0x1", A, B, L.YES, 1000, 0.5) + matched(4000, "0x2", A, B, L.YES, 10000, 0.45) \
        + matched(4001, "0x3", A, C, L.NO, 11900, 0.53)
    assert L.classify(L.Ledger(evs, {M1: TAPE}), A, L.family_binary(M1), 3600, 7200)["class"] == "A_TRUE_INVERSION"


def test_neg_risk_complete_set_on_every_member():
    info = {c: {**TAPE, "neg_risk": True} for c in (M1, M2, M3)}
    fam = L.family_exclusive([M1, M2, M3], exhaustive=True)
    evs = []
    for i, c in enumerate((M1, M2, M3)):
        evs += matched(4000 + i, f"0xs{i}", A, B, L.YES, 3000, 0.3, cid=c)
    assert L.classify(L.Ledger(evs, info), A, fam, 3600, 7200)["class"] == "C_COMPLETE_SET"


def test_complete_set_on_d1_plus_yes_d2_is_not_B():
    info = {M1: TAPE, M2: TAPE}
    fam = L.family_ladder([(M1, "2026-02-28"), (M2, "2026-03-31")], proof="test")
    evs = mint(100, "0x1", A, A, 1000, 0.3, cid=M1) + mint(4000, "0x2", A, C, 1000, 0.5, cid=M2)  # YES+NO D1, YES D2
    assert L.classify(L.Ledger(evs, info), A, fam, 3600, 7200)["class"] != "B_INTERVAL_PACKAGE"


def test_redeem_without_outcome_burns_the_whole_position():
    evs = mint(100, "0x1", A, B, 1000, 0.6) + [ev(5000, A, "REDEEM", None, 0, usdc=1000.0)]
    cov = {**L.FULL_COVERAGE}
    lg = L.Ledger(evs, {M1: {**FULL, "coverage": cov}})
    s = lg.snapshot(A, M1, 6000)
    assert s["observable"]["flow_yes"] == 0 and s["observable"]["flow_no"] == 0
    assert abs(s["observable"]["cash_flow"] - (1000 - 600)) < 1e-9 and s["inventory"]["status"] == "EXACT"


def test_fee_enabled_market_without_fee_data_has_unknown_cash():
    lg = L.Ledger(matched(100, "0x1", A, B, L.YES, 100, 0.5), {M1: {**TAPE, "fees_enabled": True}})
    assert lg.snapshot(A, M1, 200)["observable"]["cash_flow"] is None
    lg2 = L.Ledger(matched(100, "0x1", A, B, L.YES, 100, 0.5), {M1: TAPE})
    assert lg2.snapshot(A, M1, 200)["observable"]["cash_flow"] == -50


def test_unchecked_transactions_are_flagged():
    s = L.Ledger(matched(100, "0x1", A, B, L.YES, 100, 0.5), {M1: TAPE}, check_tx=False).snapshot(A, M1, 200)
    assert "TX_UNCHECKED" in s["reasons"] and s["x_status"] == "OBSERVABLE"


def test_payoff_vector_carries_level_bounds():
    fam = L.family_binary(M1)
    v = L.payoff_vector(L.Ledger(mint(100, "0x1", A, B, 1000, 0.6), {M1: TAPE}), A, fam, 200)
    assert v["payout_lo"] == [1000.0, 0.0] and v["payout_hi"] is None
    vf = L.payoff_vector(L.Ledger(mint(100, "0x1", A, B, 1000, 0.6), {M1: FULL}), A, fam, 200)
    assert vf["payout_lo"] == vf["payout_hi"] == [1000.0, 0.0]


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for n, f in tests:
        f()
        print("ok", n)
    print(f"{len(tests)} passed")
