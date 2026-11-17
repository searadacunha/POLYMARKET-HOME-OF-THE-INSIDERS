"""Tests of code/feat_30_detect.py. Run: python3 -m pytest -q -p no:cacheprovider tests
Real tapes are read only (data/tapes_all.sqlite, TRAIN markets of the h < 50 sample)."""
import copy
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "code"))
import feat_30_detect as F  # noqa: E402

S, L = F.S, F.L
TAPES = os.path.join(STUDY, "data", "tapes_all.sqlite")
PARAMS = os.path.join(STUDY, "frozen_deps", "exposure-signals", "params.json")
SAMPLE = os.path.join(STUDY, "data", "sample_expanded.jsonl")


def _markets(n=6):
    ms = [json.loads(l) for l in open(SAMPLE)]
    ms = [m for m in ms if F.period_of(m["closed_ts"]) == "TRAIN"]
    ms.sort(key=lambda m: hashlib.sha256(m["condition_id"].encode()).hexdigest())
    return ms[:n]


def _rows(cid):
    con = F.open_ro(TAPES)
    return con.execute("select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx, "
                       "token_id from trades where condition_id=? order by ts, rowid", (cid,)).fetchall()


def _strip(cands):
    return json.dumps(cands, sort_keys=True, default=str)


def test_candidates_equal_mission4():
    P = S.load_params(PARAMS)
    n_cand = 0
    for mk in _markets():
        rows = _rows(mk["condition_id"])
        a = S.market_pass(mk, rows, P)
        b = F.market_pass_m5(mk, rows, P)
        assert _strip(a["candidates"]) == _strip(b["candidates"]), mk["condition_id"]
        assert _strip(a["pv"]) == _strip(b["pv"])
        assert a["wallet_hours"] == b["wallet_hours"] and a["wallet_first"] == b["wallet_first"]
        n_cand += len(a["candidates"])
    assert n_cand > 0, "no candidate in the test markets: the equality check proved nothing"


def test_null_seed_equal_mission4():
    P = S.load_params(PARAMS)
    mk = _markets(3)[1]
    rows = _rows(mk["condition_id"])
    a = S.market_pass(mk, rows, P, null_seed=3)
    b = F.market_pass_m5(mk, rows, P, null_seed=3)
    assert _strip(a["candidates"]) == _strip(b["candidates"])


def test_truncation_invariance_of_extras_and_candidates():
    """Everything recorded at grid time t must be identical when the tape stops at t."""
    P = S.load_params(PARAMS)
    checked = 0
    for mk in _markets(4):
        rows = _rows(mk["condition_id"])
        full = F.market_pass_m5(mk, rows, P)
        ts = sorted(full["extras"])
        if len(ts) < 3:
            continue
        cut = ts[len(ts) // 2]
        part = F.market_pass_m5(mk, [r for r in rows if r[2] <= cut], P)
        for t in ts:
            if t > cut:
                continue
            a, b = dict(full["extras"][t]), part["extras"].get(t)
            if b is None:          # a hash-drawn R point can move when the grid is shorter: not a leak
                assert a["r_side"] is not None and not any(a["pv"]) and not any(a["ind"])
                continue
            b = dict(b)
            a.pop("r_side"); b.pop("r_side")
            assert a == b, (mk["condition_id"], t)
            checked += 1
        ca = [c for c in full["candidates"] if c["t"] <= cut]
        assert _strip(ca) == _strip([c for c in part["candidates"] if c["t"] <= cut])
    assert checked > 0


def test_iran_wallets_never_contribute():
    P = S.load_params(PARAMS)
    mk = _markets(6)[0]
    rows = _rows(mk["condition_id"])
    base = F.market_pass_m5(mk, rows, P)
    ws = sorted({x["wallet"] for c in base["candidates"] for x in c["contributors"]})
    if not ws:
        return
    P2 = copy.deepcopy(P)
    P2["infra"] = set(P2["infra"]) | {ws[0]}
    out = F.market_pass_m5(mk, rows, P2)
    assert all(x["wallet"] != ws[0] for c in out["candidates"] for x in c["contributors"])


def test_panel_units_respect_split_window_and_band():
    P = S.load_params(PARAMS)
    mks = _markets(5)
    markets = {m["condition_id"].lower(): {**m, "condition_id": m["condition_id"].lower(), "role": "TRAIN"}
               for m in mks}
    res = [F.market_pass_m5(m, _rows(m["condition_id"]), P) for m in mks]
    index = F.build_index_compact((r["wallet_hours"], r["wallet_first"]) for r in res)
    ref = S.build_index(res)
    for w in list(ref)[:200]:
        assert list(index[w][0]) == list(ref[w][0]) and index[w][1] == ref[w][1] \
            and list(index[w][2]) == list(ref[w][2])
    cands = [c for r in res for c in r["candidates"]]
    S.enrich_and_fire(cands, index, P)
    units, cnt = F.build_panel(markets, {r["cid"]: r["extras"] for r in res},
                               {r["cid"]: r["first_flag"] for r in res},
                               {(c["condition_id"].lower(), c["side"], c["t"]): c for c in cands}, {})
    assert units
    for u in units:
        assert F.period_of(u["t"]) == u["split"] == "TRAIN"
        assert 0.05 <= u["p"] <= 0.90
        assert "label" not in json.dumps(u) and "winner" not in json.dumps(u)
    keys = [(u["cid"], u["side"], t) for u in units for t in [u["t"]] if "COL" in u["types"]]
    assert len(keys) == len(set((k[0], k[1]) for k in keys)), "more than one COL unit per market-side"


def test_feature_code_never_reads_labels():
    src = open(os.path.join(STUDY, "code", "feat_30_detect.py")).read()
    assert "labels.jsonl" not in src and "winner" not in src
