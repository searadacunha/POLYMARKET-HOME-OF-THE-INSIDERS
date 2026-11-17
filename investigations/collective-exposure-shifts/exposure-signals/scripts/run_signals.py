#!/usr/bin/env python3
"""Run the collective exposure detector on TRAIN markets only (observed, or one null seed). Reads tapes read-only.
Never reads labels. Writes only under --out.

usage: run_signals.py --tapes T.sqlite [--tapes ...] --markets M.jsonl [--markets ...] --params params.json
                      --out DIR [--null-seed K] [--edges E.jsonl] [--workers 4] [--max-markets N]
"""
import argparse
import gzip
import json
import multiprocessing as mp
import os
import sqlite3
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signals as S  # noqa: E402

L = S.L
IRAN = "0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20"
ALLOWED = "TRAIN"
_CTX = {}


def open_ro(path):
    return sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(path))}?mode=ro&immutable=1", uri=True)


def _init(tapes, P, seed):
    _CTX["cons"] = {p: open_ro(p) for p in tapes}
    _CTX["P"], _CTX["seed"] = P, seed


def _work(job):
    mk, tape = job
    rows = _CTX["cons"][tape].execute(
        "select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx, token_id "
        "from trades where condition_id=? order by ts, rowid", (mk["condition_id"],)).fetchall()
    r = S.market_pass(mk, rows, _CTX["P"], null_seed=_CTX["seed"])
    r["stats"]["tape"] = os.path.basename(tape)
    return r


def select_train(markets_paths, tapes):
    markets = {}
    for p in markets_paths:
        for line in open(p):
            m = json.loads(line)
            markets.setdefault(m["condition_id"].lower(), m)
    jobs, refused = [], {}
    seen = set()
    for t in tapes:
        con = open_ro(t)
        for cid, status in con.execute("select condition_id, status from status"):
            c = cid.lower()
            if c not in markets or c in seen:
                continue
            seen.add(c)
            m = markets[c]
            part = L.partition_of(c, m.get("closed_ts") or 0, m.get("event_slug") or "", iran_cids=[IRAN])
            if part != ALLOWED or status != "ok":
                refused[part if part != ALLOWED else f"status_{status}"] = \
                    refused.get(part if part != ALLOWED else f"status_{status}", 0) + 1
                continue
            jobs.append(({**m, "condition_id": cid}, t))
        con.close()
    jobs.sort(key=lambda j: j[0]["condition_id"])
    return jobs, refused, len(markets) - len(seen)


def summary(alerts, cands, results):
    fam = {f: sum(1 for a in alerts if f in a["primary_for"]) for f in S.FAMILIES}
    fam_all = {f: sum(1 for a in alerts if f in a["families_fired"]) for f in S.FAMILIES}
    return {"candidates": len(cands), "alerts": len(alerts), "primary_units_by_family": fam,
            "firings_by_family": fam_all,
            "markets_run": sum(1 for r in results if not r["stats"]["skipped"]),
            "markets_skipped": {k: sum(1 for r in results if r["stats"]["skipped"] == k)
                                for k in {r["stats"]["skipped"] for r in results if r["stats"]["skipped"]}},
            "pv_units": sum(len(r["pv"]) for r in results)}


def write_parquet(alerts, out):
    import pyarrow as pa
    import pyarrow.parquet as pq
    rows, crow = [], []
    for a in alerts:
        rows.append({
            "alert_id": a["alert_id"], "event_id": a["event_id"], "event_slug": a["event_slug"],
            "condition_id": a["condition_id"], "token_id": a["token_id"], "side": a["side"], "t": a["t"],
            "window_start": a["window"][0], "available_ts": a["available_ts"], "price_side": a["price_side"],
            "price_side_prev": a["price_side_prev"], "n_wallets": a["F1"]["n_wallets"],
            "total_usd": a["F2"]["total_usd"], "top_share": a["F2"]["top_share"], "hhi": a["F2"]["hhi"],
            "mean_surprise": a["F3"]["mean_surprise"], "young_share": a["F4"]["young_share"],
            "median_age_days": a["F4"]["median_age_days"], "repeat_pairs": a["F5"]["repeat_pairs"],
            "f6_status": a["F6"]["status"], "linked_pairs": a["F6"]["linked_pairs"],
            "lead_repeats": a["F7"]["lead_repeats"], "internal_share": a["F7"]["internal_share"],
            "cp_top_share": a["F7"]["top_share"], "flow_z": a["F8"]["z"], "score": a["score"],
            "families_fired": a["families_fired"], "primary_for": a["primary_for"],
            "reasons": a["reasons"], "source_txs": a["source_txs"], "params_sha256": a["params_sha256"]})
        for c in a["contributors"]:
            crow.append({"alert_id": a["alert_id"], "wallet": c["wallet"],
                         "net_change_shares": c["net_change_shares"], "net_change_usd": c["net_change_usd"],
                         "class": c["class"], "x_status": c["x_status"], "first_fill_ts": c["first_fill_ts"],
                         "txs": c["txs"]})
    pq.write_table(pa.Table.from_pylist(rows), os.path.join(out, "alerts.parquet"))
    pq.write_table(pa.Table.from_pylist(crow), os.path.join(out, "alert_contributors.parquet"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", action="append", required=True)
    ap.add_argument("--markets", action="append", required=True)
    ap.add_argument("--params", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--null-seed", type=int)
    ap.add_argument("--edges")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-markets", type=int)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    P = S.load_params(a.params)
    shas = {"params": S.sha256_file(a.params), "signals.py": S.sha256_file(S.__file__),
            "run_signals.py": S.sha256_file(__file__), "ledger.py": S.sha256_file(L.__file__)}
    jobs, refused, no_tape = select_train(a.markets, a.tapes)
    assert all(L.partition_of(m["condition_id"], m.get("closed_ts") or 0, m.get("event_slug") or "",
                              iran_cids=[IRAN]) == ALLOWED for m, _ in jobs), "non-TRAIN market selected"
    if a.max_markets:
        jobs = jobs[:a.max_markets]
    t0 = time.time()
    with mp.Pool(a.workers, initializer=_init, initargs=(a.tapes, P, a.null_seed)) as pool:
        results = list(pool.imap(_work, jobs, chunksize=4))
    t_a = time.time() - t0
    index = S.build_index(results)
    cands = [c for r in results for c in r["candidates"]]
    edges = S.load_edges(a.edges)
    alerts = S.enrich_and_fire(cands, index, P, edges=edges, infra=frozenset(P["infra"]))
    for al in alerts:
        al["params_sha256"] = shas["params"]
        al["partition"] = ALLOWED
        al["source_txs"] = sorted({tx for c in al["contributors"] for tx in c["txs"]})
        al["known_at_t"] = {
            "fills": f"tape fills with ts <= t ({al['t']}), as served by data-api v2/trades in Nov 2026",
            "positions": "position-ledger snapshots at t and t-W (only events with ts <= T)",
            "prices": "last executed price of the token at or before t",
            "wallet_history": "TRAIN sample tapes only, hours strictly before t-W",
            "groups_lead_follow": "candidates of other events with t' < t",
            "funding_edges": "none collected" if edges is None else "edges with ts < t-W",
            "availability_assumption": f"t + {P['latency_s']} s declared indexing latency, not measured"}
    summ = summary(alerts, cands, results)
    manifest = {"run": "null" if a.null_seed is not None else "observed", "null_seed": a.null_seed,
                "partition": ALLOWED, "sha256": shas, "tapes": [os.path.basename(t) for t in a.tapes],
                "markets_selected": len(jobs), "markets_refused_by_partition": refused,
                "markets_without_tape": no_tape, "phase_a_seconds": round(t_a), "summary": summ,
                "stats_totals": {k: sum(r["stats"].get(k) or 0 for r in results)
                                 for k in ("rows", "events", "quarantined", "tx_unbalanced", "grid_points",
                                           "candidates")}}
    if a.null_seed is None:
        with open(os.path.join(a.out, "alerts.jsonl"), "w") as f:
            for al in alerts:
                f.write(json.dumps(al, sort_keys=True) + "\n")
        with open(os.path.join(a.out, "pv_baseline.jsonl"), "w") as f:
            for r in results:
                for x in r["pv"]:
                    f.write(json.dumps(x, sort_keys=True) + "\n")
        with gzip.open(os.path.join(a.out, "grid_prices.jsonl.gz"), "wt") as f:
            for r in results:
                f.write(json.dumps({"condition_id": r["cid"], "grid": r["grid"]}) + "\n")
        with open(os.path.join(a.out, "market_stats.jsonl"), "w") as f:
            for r in results:
                f.write(json.dumps({"condition_id": r["cid"], **r["stats"]}, sort_keys=True) + "\n")
        write_parquet(alerts, a.out)
        manifest["outputs"] = {n: S.sha256_file(os.path.join(a.out, n)) for n in
                               ("alerts.jsonl", "pv_baseline.jsonl", "grid_prices.jsonl.gz", "market_stats.jsonl")}
    else:
        # null runs keep counts and feature distributions only
        def q(vals):
            v = sorted(x for x in vals if x is not None)
            return [v[int(p * (len(v) - 1))] for p in (0.5, 0.9, 0.99)] if v else None
        manifest["feature_quantiles"] = {
            "n_wallets": q([c["F1"]["n_wallets"] for c in cands]),
            "total_usd": q([c["F2"]["total_usd"] for c in cands]),
            "mean_surprise": q([c["F3"]["mean_surprise"] for c in cands]),
            "repeat_pairs": q([c["F5"]["repeat_pairs"] for c in cands]),
            "lead_repeats": q([c["F7"]["lead_repeats"] for c in cands])}
    with open(os.path.join(a.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    print(json.dumps(summ), f"phase_a={t_a:.0f}s", flush=True)


if __name__ == "__main__":
    main()
