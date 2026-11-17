"""Anti-lookahead and behaviour tests for the collective exposure detector. Run: python3 -m pytest -q tests"""
import json
import os
import random
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import signals as S  # noqa: E402
import run_signals as R  # noqa: E402

P = S.load_params(os.path.join(HERE, "..", "params.json"))
DAY = 86400
T0 = 1_740_000_000 - 1_740_000_000 % DAY      # 2025-02-19 00:00 UTC, a TRAIN date


def market_rows(cid, seed, plant_at=None, planted=("0xp1", "0xp2", "0xp3"), days=10):
    """Synthetic tape: balanced 2-wallet transactions among 40 background wallets, small sizes, price random walk.
    Optional planted collective YES shift: 3 wallets buy 3,000 YES each within 10 minutes, minted against one
    counterparty buying NO."""
    rnd = random.Random(seed)
    bg = [f"0x{seed:02x}bg{i:02d}" for i in range(40)]
    rows, rid, p, ts = [], 0, 0.4, T0
    while ts < T0 + days * DAY:
        ts += rnd.randint(60, 900)
        p = min(0.85, max(0.1, p + rnd.uniform(-0.01, 0.01)))
        a, b = rnd.sample(bg, 2)
        q = rnd.uniform(10, 150)
        tx = f"0xtx{seed}_{rid}"
        if rnd.random() < 0.5:
            rows += [(rid, cid, ts, a, "BUY", "Yes", 0, q, round(p, 3), tx, "tokY"),
                     (rid + 1, cid, ts, b, "SELL", "Yes", 0, q, round(p, 3), tx, "tokY")]
        else:
            rows += [(rid, cid, ts, a, "BUY", "No", 1, q, round(1 - p, 3), tx, "tokN"),
                     (rid + 1, cid, ts, b, "SELL", "No", 1, q, round(1 - p, 3), tx, "tokN")]
        rid += 2
    if plant_at is not None:
        for k, w in enumerate(planted):
            ts = plant_at + 120 * k
            tx = f"0xplant{seed}_{k}"
            rows += [(rid, cid, ts, w, "BUY", "Yes", 0, 3000.0, 0.4, tx, "tokY"),
                     (rid + 1, cid, ts, "0xcounter", "BUY", "No", 1, 3000.0, 0.6, tx, "tokN")]
            rid += 2
    rows.sort(key=lambda r: (r[2], r[0]))
    return rows


def mk(cid, ev):
    return {"condition_id": cid, "event_id": ev, "event_slug": f"ev-{ev}", "closed_ts": T0 + 30 * DAY,
            "yes_token": "tokY", "no_token": "tokN", "neg_risk": False}


def pipeline(markets, edges=None, cut=None):
    res = []
    for m, rows in markets:
        rows = [r for r in rows if cut is None or r[2] <= cut]
        res.append(S.market_pass(m, rows, P))
    cands = [c for r in res for c in r["candidates"]]
    return S.enrich_and_fire(cands, S.build_index(res), P, edges=edges, infra=frozenset(P["infra"])), res


def canon(x):
    return json.dumps(x, sort_keys=True, default=str)


def test_positive_control_fires_and_background_does_not():
    rows = market_rows("0xm1", 1, plant_at=T0 + 5 * DAY + 1000)
    alerts, _ = pipeline([(mk("0xm1", "e1"), rows)])
    hit = [a for a in alerts if a["side"] == "YES" and {"F1", "F2"} <= set(a["families_fired"])]
    assert hit, "planted 3-wallet shift not detected"
    assert {"0xp1", "0xp2", "0xp3"} <= {c["wallet"] for c in hit[0]["contributors"]}
    assert all(c["net_change_shares"] >= 3000 - 1e-6 for c in hit[0]["contributors"] if c["wallet"].startswith("0xp"))
    bg_alerts, _ = pipeline([(mk("0xm1", "e1"), market_rows("0xm1", 1))])
    assert not [a for a in bg_alerts if "F1" in a["families_fired"]]


def test_alert_carries_required_fields():
    alerts, _ = pipeline([(mk("0xm1", "e1"), market_rows("0xm1", 1, plant_at=T0 + 5 * DAY))])
    a = alerts[0]
    for k in ("event_id", "condition_id", "token_id", "contributors", "available_ts", "score", "reasons",
              "families_fired", "window", "alert_id"):
        assert k in a
    assert a["available_ts"] > a["t"] and a["window"][1] == a["t"]
    assert all(c["txs"] and "net_change_shares" in c for c in a["contributors"])


def test_truncation_invariance_whole_pipeline():
    """Alerts at or before T are identical whether or not the data after T exist (all families, both phases)."""
    planted = ("0xq1", "0xq2", "0xq3")
    mkts = [(mk("0xm1", "e1"), market_rows("0xm1", 1, plant_at=T0 + 2 * DAY + 500, planted=planted)),
            (mk("0xm2", "e2"), market_rows("0xm2", 2, plant_at=T0 + 4 * DAY + 700, planted=planted)),
            (mk("0xm3", "e3"), market_rows("0xm3", 3, plant_at=T0 + 6 * DAY + 300, planted=planted))]
    full, _ = pipeline(mkts)
    assert any("F5" in a["families_fired"] for a in full), "repeated group should fire F5 in a later event"
    for cut in (T0 + 3 * DAY, T0 + 5 * DAY + 1234, T0 + 7 * DAY):
        trunc, _ = pipeline(mkts, cut=cut)
        a = [canon(x) for x in full if x["t"] <= cut]
        b = [canon(x) for x in trunc if x["t"] <= cut]
        assert a == b, f"look-ahead: alerts before {cut} change when later data are added"


def test_group_repetition_uses_only_earlier_events():
    planted = ("0xq1", "0xq2", "0xq3")
    mkts = [(mk("0xm1", "e1"), market_rows("0xm1", 1, plant_at=T0 + 2 * DAY, planted=planted)),
            (mk("0xm2", "e2"), market_rows("0xm2", 2, plant_at=T0 + 4 * DAY, planted=planted))]
    alerts, _ = pipeline(mkts)
    first = [a for a in alerts if a["condition_id"] == "0xm1" and a["side"] == "YES"]
    assert first and all(a["F5"]["repeat_pairs"] == 0 for a in first)


def test_funding_edges_after_the_window_never_count():
    planted = ("0xq1", "0xq2", "0xq3")
    rows = market_rows("0xm1", 1, plant_at=T0 + 5 * DAY, planted=planted)
    m = mk("0xm1", "e1")
    base, _ = pipeline([(m, rows)], edges={})
    hit = [a for a in base if "F1" in a["families_fired"] and a["side"] == "YES"][0]
    late = {frozenset(("0xq1", "0xq2")): [hit["window"][0] + 1]}         # paid inside / after the window
    early = {frozenset(("0xq1", "0xq2")): [hit["window"][0] - 10]}       # paid before the window
    infra = {frozenset(("0xq1", P_infra())): [hit["window"][0] - 10]}
    a_late, _ = pipeline([(m, rows)], edges=late)
    a_early, _ = pipeline([(m, rows)], edges=early)
    a_infra, _ = pipeline([(m, rows)], edges=infra)
    pick = lambda al: [a for a in al if a["alert_id"] == hit["alert_id"]][0]  # noqa: E731
    assert pick(a_late)["F6"]["linked_pairs"] == 0 and "F6" not in pick(a_late)["families_fired"]
    assert pick(a_early)["F6"]["linked_pairs"] == 1 and "F6" in pick(a_early)["families_fired"]
    assert pick(a_infra)["F6"]["linked_pairs"] == 0


def P_infra():
    return sorted(P["infra"])[0]


def test_edge_loader_drops_technical_relations(tmp_path):
    p = tmp_path / "e.jsonl"
    rows = [{"from": "0xA", "to": "0xB", "ts": 5, "tx": "0x1", "kind": "direct_transfer", "source": "polygon"},
            {"from": "0xA", "to": "0xC", "ts": 5, "tx": "0x2", "kind": "exchange", "source": "cex"},
            {"from": "0xA", "to": "0xD", "ts": 5, "tx": "0x3", "kind": "bridge", "source": "relay"},
            {"from": "0xA", "to": "0xE", "ts": 5, "tx": None, "kind": "direct_transfer", "source": "?"}]
    p.write_text("\n".join(json.dumps(r) for r in rows))
    e = S.load_edges(str(p))
    assert list(e) == [frozenset(("0xa", "0xb"))]


def test_infra_wallets_never_contribute():
    rows = market_rows("0xm1", 1, plant_at=T0 + 5 * DAY, planted=("0xq1", "0xq2", sorted(P["infra"])[0]))
    alerts, _ = pipeline([(mk("0xm1", "e1"), rows)])
    assert not any(c["wallet"] in P["infra"] for a in alerts for c in a["contributors"])


def test_null_shift_keeps_hour_of_day_and_activity():
    f = S.day_shift(7, 10 * DAY)
    for ts in (T0 + 3600 * 5 + 17, T0 + 9 * DAY + 3600 * 23):
        s = f("0xw", "0xm", T0, ts)
        assert s % DAY == ts % DAY and T0 <= s < T0 + 10 * DAY and s != ts


def test_null_run_keeps_rows_and_changes_alignment():
    rows = market_rows("0xm1", 1, plant_at=T0 + 5 * DAY)
    obs = S.market_pass(mk("0xm1", "e1"), rows, P)
    nul = S.market_pass(mk("0xm1", "e1"), rows, P, null_seed=3)
    assert nul["stats"]["events"] == obs["stats"]["events"]
    assert sum(len(v) for v in nul["wallet_hours"].values()) > 0


def test_detector_code_never_touches_labels():
    for name in ("signals.py", "run_signals.py"):
        src = open(os.path.join(HERE, "..", "scripts", name)).read()
        assert not re.search(r"labels\.jsonl|['\"]winner['\"]|resolved_outcome|early-detection", src, re.I), name


def test_partition_guard_refuses_valid_and_test(tmp_path):
    db = tmp_path / "t.sqlite"
    con = sqlite3.connect(db)
    con.execute("create table status(condition_id text, status text, pages int, oldest_ts int, n_rows int, "
                "fetched_at text)")
    con.execute("create table trades(condition_id text, ts int, wallet text, side text, outcome text, "
                "outcome_index int, size real, price real, tx text, token_id text)")
    ms = {"0xtrain": T0, "0xvalid": 1_770_000_000, "0xtest": 1_785_000_000}
    for c in ms:
        con.execute("insert into status values (?, 'ok', 1, 0, 0, '')", (c,))
    con.commit()
    mp = tmp_path / "m.jsonl"
    mp.write_text("\n".join(json.dumps({"condition_id": c, "closed_ts": t, "event_slug": c}) for c, t in ms.items()))
    jobs, refused, _ = R.select_train([str(mp)], [str(db)])
    assert [j[0]["condition_id"] for j in jobs] == ["0xtrain"]
    assert refused == {"VALID": 1, "TEST": 1}
