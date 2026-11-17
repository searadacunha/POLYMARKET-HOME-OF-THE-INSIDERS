#!/usr/bin/env python3
"""Anti-lookahead check on real TRAIN tapes: for a hash-drawn set of TRAIN markets, alerts at or before a cut are
identical whether the tape is cut there or not (both phases). Writes a JSON verdict. Reads no label.

usage: check_truncation_real.py --tapes ... --markets ... --params params.json --out F.json [--n 5]
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signals as S  # noqa: E402
import run_signals as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", action="append", required=True)
    ap.add_argument("--markets", action="append", required=True)
    ap.add_argument("--params", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()
    P = S.load_params(a.params)
    jobs, _, _ = R.select_train(a.markets, a.tapes)
    jobs.sort(key=lambda j: hashlib.sha256(j[0]["condition_id"].encode()).hexdigest())
    cons = {p: R.open_ro(p) for p in a.tapes}
    data = []
    for m, tape in jobs:
        rows = cons[tape].execute(
            "select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx, token_id "
            "from trades where condition_id=? order by ts, rowid", (m["condition_id"],)).fetchall()
        if len(rows) >= 2000:                      # markets with enough activity to produce candidates
            data.append((m, rows))
        if len(data) == a.n:
            break
    lo = min(r[0][2] for _, r in [(m, rows) for m, rows in data])
    hi = max(r[-1][2] for _, r in [(m, rows) for m, rows in data])

    def run(cut):
        res = [S.market_pass(m, [r for r in rows if cut is None or r[2] <= cut], P) for m, rows in data]
        cands = [c for r in res for c in r["candidates"]]
        return S.enrich_and_fire(cands, S.build_index(res), P, edges=None, infra=frozenset(P["infra"]))

    full = run(None)
    checks = []
    for frac in (0.25, 0.5, 0.75):
        cut = int(lo + frac * (hi - lo))
        tr = run(cut)
        A = [json.dumps(x, sort_keys=True) for x in full if x["t"] <= cut]
        B = [json.dumps(x, sort_keys=True) for x in tr if x["t"] <= cut]
        checks.append({"cut": cut, "alerts_before_cut": len(A), "identical": A == B})
    out = {"markets": [m["condition_id"] for m, _ in data], "rows": sum(len(r) for _, r in data),
           "alerts_full": len(full), "checks": checks, "pass": all(c["identical"] for c in checks)}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))
    sys.exit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()
