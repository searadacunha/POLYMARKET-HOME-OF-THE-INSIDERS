"""Unit checks of code/ana_50_models.py on synthetic numbers (no real label is read)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "code"))
import ana_50_models as A  # noqa: E402


def test_holm_bh_known_values():
    ps = {"a": 0.01, "b": 0.04, "c": 0.03}
    h = A.holm(ps)
    assert abs(h["a"] - 0.03) < 1e-12 and abs(h["c"] - 0.06) < 1e-12 and abs(h["b"] - 0.06) < 1e-12
    b = A.bh(ps)
    assert abs(b["a"] - 0.03) < 1e-12 and abs(b["b"] - 0.04) < 1e-12


def test_event_boot_null_and_effect():
    rng = np.random.default_rng(0)
    ev = np.repeat(np.arange(200), 3)
    null = rng.normal(0, 1, 600)
    r0 = A.event_boot(null - null.mean(), ev, "t0", B=3000)
    assert r0["p"] > 0.2
    r1 = A.event_boot(rng.normal(0.3, 1, 600), ev, "t1", B=3000)
    assert r1["p"] < 0.01 and r1["lower95_one_sided"] > 0


def test_twoway_boot_runs_with_empty_wallets():
    d = np.array([0.1, -0.1, 0.2, 0.0])
    r = A.twoway_boot(d, ["e1", "e1", "e2", "e3"], [["w1"], [], ["w1", "w2"], []], "tw", B=200)
    assert 0 < r["p"] <= 1


def test_logit_recovers_signal_and_penalty_shrinks():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(4000, 2))
    y = (rng.random(4000) < 1 / (1 + np.exp(-(0.5 + 1.5 * X[:, 0])))).astype(float)
    m = A.Logit().fit(X, y, 0.1)
    assert abs(m.beta[1] * 1 / m.sd[0] - 1.5) < 0.2 and abs(m.beta[2]) < 0.15
    m2 = A.Logit().fit(X, y, 1e4)
    assert abs(m2.beta[1]) < abs(m.beta[1])


def test_calibration_of_perfect_forecast():
    rng = np.random.default_rng(2)
    p = rng.uniform(0.05, 0.95, 20000)
    y = (rng.random(20000) < p).astype(float)
    c = A.calibration(y, p)
    assert abs(c["slope"] - 1) < 0.08 and abs(c["intercept"]) < 0.08 and c["ece"] < 0.02


def test_twoway_weights_keep_every_wallet():
    wl, flat, owner, lens = A._wallet_index([["a", "b"], [], ["c"], []])
    ww = np.array([1.0, 10.0, 100.0])
    sums = np.bincount(owner, weights=ww[flat], minlength=4)
    assert list(sums) == [11.0, 0.0, 100.0, 0.0]


def _t(stat, p, up, rej=False, status=None):
    d = {"stat": stat, "p": p, "upper95_one_sided": up, "rejected_holm": rej}
    if status:
        d["status"] = status
    return d


def test_verdict_rules():
    base = {k: _t(0.0, 0.5, 0.001) for k in ("T2", "T5", "T6", "T7")}
    valid = {"T1": _t(0.01, 0.01, 0.02)}
    ng, ctl = {"p": 0.05}, {"passed": True, "null_T1_mean": -0.0005}
    # supported
    test = {**base, "T1": _t(0.02, 0.001, 0.03, True), "T4": _t(0.05, 0.001, 0.08)}
    assert A.verdict_from(valid, test, ng, ctl)["H1"] == "SUPPORTED"
    assert A.verdict_from({"T1": _t(-0.01, 0.9, 0)}, test, ng, ctl)["H1"] == "INCONSISTENT"
    # precise negative needs T1 bias-corrected bound and T4 bound
    test = {**base, "T1": _t(-0.003, 0.9, 0.0012), "T4": _t(0.0, 0.5, 0.02)}
    assert A.verdict_from(valid, test, ng, ctl)["H1"] == "NEGATIVE_PRECISE"
    assert A.verdict_from(valid, test, ng, {"passed": True, "null_T1_mean": -0.002})["H1"] == "UNDERPOWERED"
    test["T4"] = _t(0.0, 0.5, 0.04)
    assert A.verdict_from(valid, test, ng, ctl)["H1"] == "UNDERPOWERED"
    test = {**base, "T1": _t(None, None, None, status="IMPOSSIBLE"), "T4": _t(0, 0.5, 0.01)}
    assert A.verdict_from(valid, test, ng, ctl)["H1"] == "IMPOSSIBLE"


def test_labels_refuse_unexpected_winner(tmp_path):
    import gzip, json, pytest
    p = tmp_path / "l.jsonl.gz"
    with gzip.open(p, "wt") as f:
        f.write(json.dumps({"condition_id": "0xA", "winner": "Yes"}) + "\n")
    with pytest.raises(SystemExit):
        A.load_labels(str(p), {"0xa"})


def test_fit_refuses_single_class():
    import pytest
    with pytest.raises(SystemExit):
        A.Logit().fit(np.zeros((10, 1)), np.ones(10), 1.0)


def test_wallet_clusters_follow_most_recurrent_wallet():
    mk = lambda ev, ws: {"event_id": ev, "col_s": {"wallets": ws}, "ind": {"single_s": None}}
    us = [mk("e1", ["a", "b"]), mk("e2", ["b"]), mk("e3", ["c"]), mk("e4", [])]
    assert A.wallet_clusters(us, us) == ["w:b", "w:b", "w:c", "e:e4"]
