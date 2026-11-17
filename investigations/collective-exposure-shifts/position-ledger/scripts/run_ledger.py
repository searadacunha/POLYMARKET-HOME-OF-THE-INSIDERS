#!/usr/bin/env python3
"""Build the point-in-time ledger over the archived fill tapes, one event (market family) at a time, resumable.

Reads only: the tape SQLite files (opened immutable, read-only), the sample market lists, gamma_meta.jsonl and the
Iran cohort list. Never reads labels.jsonl. Writes only under --out:
  ledger/<unit-hash>.jsonl.gz   every applied event with provenance and the running flows after it
  episodes.jsonl                A / B / D episodes (D verified or not) with the transactions behind them
  units.jsonl                   one summary per unit: conservation checks, status counts, class counts per partition
  missing_tape.jsonl            sampled markets with no tape (never collected), one line each
  checkpoint.jsonl              units done: their markets, tapes and ledger sha256 (resume skips them)

Work proceeds unit by unit (an event and its sampled markets); a restart drops any units/episodes line whose unit
is not in the checkpoint, then continues. A unit whose market list changed since it was checkpointed stops the run.

usage: run_ledger.py --tapes T1.sqlite [--tapes T2.sqlite] --markets M.jsonl [--markets ...] --meta gamma_meta.jsonl
                     --iran-cohort data/iran_cohort_wallets.json --out out/ [--extra-cid 0x..] [--max-units N]
"""
import argparse, collections, datetime as dt, gzip, hashlib, json, os, sqlite3, sys, time, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger as L  # noqa: E402

W = 3600            # classification window, seconds (the frozen plan's exposure window)
IRAN = "0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20"
EPISODE_CLASSES = ("A_TRUE_INVERSION", "B_INTERVAL_PACKAGE", "D_YES_ACCUM_KEEP_NO", "D_UNVERIFIED_NO_RETENTION")


def open_ro(path):
    return sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(path))}?mode=ro&immutable=1", uri=True)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def gamma_closed_ts(m):
    t = m.get("closedTime")
    if not t:
        return None
    t = t.replace(" ", "T")
    if t.endswith("+00"):
        t += ":00"
    return int(dt.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp())


def keep_checkpointed(path, done):
    """Drop lines of units that are not checkpointed (left by a crash), keep the first line per unit for units."""
    if not os.path.exists(path):
        return 0
    kept, seen, dropped = [], set(), 0
    is_units = path.endswith("units.jsonl")
    for line in open(path):
        u = json.loads(line)["unit"]
        if u not in done or (is_units and u in seen):
            dropped += 1
            continue
        seen.add(u)
        kept.append(line)
    if dropped:
        with open(path + ".tmp", "w") as f:
            f.writelines(kept)
        os.replace(path + ".tmp", path)
    return dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", action="append", required=True)
    ap.add_argument("--markets", action="append", default=[])
    ap.add_argument("--extra-cid", action="append", default=[])
    ap.add_argument("--meta", required=True)
    ap.add_argument("--iran-cohort", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-units", type=int)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    iran_wallets = set(json.load(open(a.iran_cohort))["wallets"])
    assert len(iran_wallets) == 36, "Iran cohort must have 36 wallets"

    meta = {}
    for line in open(a.meta):
        r = json.loads(line)
        meta[r["condition_id"]] = r
    markets = {}
    for path in a.markets:
        for line in open(path):
            m = json.loads(line)
            markets.setdefault(m["condition_id"].lower(), m)
    for c in a.extra_cid:
        g = meta[c.lower()]
        markets.setdefault(c.lower(), {"condition_id": c.lower(), "event_slug": g["event"]["slug"],
                                       "neg_risk": g.get("negRisk"), "closed_ts": gamma_closed_ts(g)})

    source = {}      # market -> first tape that holds it (declared order)
    cons = [(p, open_ro(p)) for p in a.tapes]
    for p, con in cons:
        for cid, status, pages, oldest, n in con.execute("select condition_id, status, pages, oldest_ts, n_rows from status"):
            cid = cid.lower()
            if cid in markets and cid not in source:
                source[cid] = (p, con, status, pages, oldest, n)

    done = {}
    ck_path = os.path.join(a.out, "checkpoint.jsonl")
    if os.path.exists(ck_path):
        for line in open(ck_path):
            c = json.loads(line)
            done[c["unit"]] = c
    for name in ("units.jsonl", "episodes.jsonl"):
        n = keep_checkpointed(os.path.join(a.out, name), set(done))
        if n:
            print(f"resume: dropped {n} uncheckpointed lines from {name}", flush=True)

    with open(os.path.join(a.out, "missing_tape.jsonl"), "w") as f:
        for cid in sorted(set(markets) - set(source)):
            m = markets[cid]
            f.write(json.dumps({"cid": cid, "event_slug": m.get("event_slug"), "status": "NO_TAPE",
                                "frozen_close_partition": L.partition_of(cid, m.get("closed_ts"), m.get("event_slug") or "",
                                                                         iran_cids=[IRAN])}) + "\n")

    units = collections.defaultdict(list)
    for cid in source:
        units[markets[cid].get("event_slug") or cid].append(cid)
    order = sorted(units, key=lambda u: (min(markets[c].get("start_ts") or 0 for c in units[u]), u))
    n_run = 0
    t_start = time.time()
    for unit in order:
        cids = sorted(units[unit])
        tapes_used = sorted({os.path.basename(source[c][0]) for c in cids})
        if unit in done:
            if done[unit].get("cids") != cids:
                raise SystemExit(f"unit {unit} was checkpointed with markets {done[unit].get('cids')} but now has "
                                 f"{cids}: use a fresh --out")
            continue
        if a.max_units is not None and n_run >= a.max_units:
            break
        n_run += 1
        info, events, tape_status = {}, [], {}
        for cid in cids:
            p, con, status, pages, oldest, n = source[cid]
            g = meta.get(cid, {})
            m = markets[cid]
            info[cid] = {"history_complete": status == "ok", "neg_risk": g.get("negRisk"),
                         "fees_enabled": g.get("feesEnabled"), "coverage": L.TAPE_COVERAGE}
            tape_status[cid] = {"tape": os.path.basename(p), "status": status, "pages": pages, "rows": n,
                                "gamma_version": g.get("version"), "fees_enabled": g.get("feesEnabled"),
                                "neg_risk": g.get("negRisk"), "gamma_meta": g.get("status", "absent"),
                                "frozen_close_partition": L.partition_of(cid, m.get("closed_ts"), unit, iran_cids=[IRAN])}
            rows = con.execute("select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx "
                               "from trades where condition_id=? order by ts, rowid", (cid,)).fetchall()
            events += L.events_from_tape_rows(rows, os.path.basename(p))
        lg = L.Ledger(events, info)

        fams = [L.family_binary(c) for c in cids]
        fam_note = "single market"
        if len(cids) >= 2:
            metas = [meta[c] for c in cids if c in meta and meta[c].get("status") == "ok"]
            if len(metas) < len(cids):
                fam_note = "no family: Gamma metadata missing for a member"
            elif all(m.get("negRisk") for m in metas):
                fams.append(L.family_exclusive(cids, exhaustive=False,
                                               proof="neg-risk event; only sampled members, world OTHER kept"))
                fam_note = "exclusive (neg-risk)"
            elif not any(m.get("negRisk") for m in metas):
                lad = L.prove_ladder(metas)
                fams.append(lad)
                fam_note = "ladder" if lad["type"] == "ladder" else f"unproven: {lad['proof']}"
            else:
                fam_note = "no family: mixed neg-risk flags"

        lpath = os.path.join(a.out, "ledger", hashlib.sha256(unit.encode()).hexdigest()[:16] + ".jsonl.gz")
        os.makedirs(os.path.dirname(lpath), exist_ok=True)
        tmp = lpath + ".tmp"
        run = collections.defaultdict(lambda: [0.0, 0.0])
        with gzip.open(tmp, "wt") as f:
            for e in lg.events:
                r = run[(e["wallet"], e["cid"])]
                d0, d1, _ = L.token_delta(e, tuple(r))
                r[0] += d0
                r[1] += d1
                # status, reasons and lower bound as of the end of this event's second (snapshot at e.ts)
                s = lg.snapshot(e["wallet"], e["cid"], e["ts"])
                f.write(json.dumps({"ts": e["ts"], "cid": e["cid"], "wallet": e["wallet"], "kind": e["kind"],
                                    "oi": e["oi"], "qty": e["qty"], "price": e["price"], "tx": e["tx"],
                                    "src": e["src"], "flow_yes": r[0], "flow_no": r[1],
                                    "tx_check": lg.tx_verdicts.get((e["tx"], e["cid"])),
                                    "x_status_end_of_second": s["x_status"], "reasons": s["reasons"],
                                    "inventory_lo_end_of_second": s["inventory"]["lo"]},
                                   separators=(",", ":")) + "\n")
        tx_wallets = collections.defaultdict(set)
        for e in lg.events:
            if e["tx"]:
                tx_wallets[(e["tx"], e["cid"])].add(e["wallet"])
        os.replace(tmp, lpath)

        classes = collections.Counter()
        episodes = []
        for fam in fams:
            if fam["type"] == "unproven":
                continue
            members = set(fam["members"])
            act = collections.defaultdict(set)
            for e in lg.events:
                if e["cid"] in members:
                    act[e["wallet"]].add(L.window_index(e["ts"], W))
            for w, ks in act.items():
                for k in sorted(ks):
                    t0, t1 = k * W, (k + 1) * W
                    part = L.observation_partition(t1, w, unit, fam["members"], iran_wallets, [IRAN])
                    r = L.classify(lg, w, fam, t0, t1)
                    classes[(part, fam["type"], r["class"])] += 1
                    if r["class"] in EPISODE_CLASSES:
                        win = [e for c in fam["members"] for e in lg.window_events(w, c, t0, t1)]
                        episodes.append({"unit": unit, "family": fam["type"], "members": fam["members"],
                                         "worlds": fam["worlds"], "wallet": w, "t0": t0, "t1": t1,
                                         "class": r["class"], "partition": part,
                                         "market_close_ts": {c: markets[c].get("closed_ts") for c in fam["members"]},
                                         "shape_t0": r["evidence"]["v0"]["shape"],
                                         "shape_t1": r["evidence"]["v1"]["shape"],
                                         "status": [r["evidence"]["v0"]["status"], r["evidence"]["v1"]["status"]],
                                         "txs": sorted({e["tx"] for e in win if e["tx"]}),
                                         # other wallets in the same transactions: co-participants of a match,
                                         # not linked accounts; no identity is inferred from them
                                         "co_participants_not_linked": sorted(
                                             {x for e in win if e["tx"] for x in tx_wallets[(e["tx"], e["cid"])]}
                                             - {w})[:50]})
        x_status = collections.Counter()
        for cid in cids:
            close = max((e["ts"] for e in lg.events if e["cid"] == cid), default=0)
            for w in lg.wallets(cid):
                x_status[lg.snapshot(w, cid, close)["x_status"]] += 1
        neg = sum(1 for b in lg.books.values() if b["min0"][-1] < -L.EPS or b["min1"][-1] < -L.EPS)
        summary = {"unit": unit, "markets": tape_status, "family": fam_note,
                   "events_in": len(events), "events_applied": len(lg.events),
                   "quarantined": collections.Counter(r for _, r in lg.quarantine),
                   "tx_checks": collections.Counter(lg.tx_verdicts.values()),
                   "rows_without_tx": sum(lg.no_tx_rows.values()),
                   "implied_fee_rates": collections.Counter(
                       f"{v:.3f}" if v is not None else "none" for v in lg.fee_rates.values()),
                   "wallet_market_pairs": len(lg.books), "pairs_with_proven_unobserved_inflow": neg,
                   "x_status_at_last_fill": x_status,
                   "classes": {f"{p}|{t}|{c}": n for (p, t, c), n in sorted(classes.items())},
                   "ledger_file": os.path.relpath(lpath, a.out), "ledger_sha256": sha256_file(lpath)}
        with open(os.path.join(a.out, "units.jsonl"), "a") as f:
            f.write(json.dumps(summary) + "\n")
        if episodes:
            with open(os.path.join(a.out, "episodes.jsonl"), "a") as f:
                for x in episodes:
                    f.write(json.dumps(x) + "\n")
        with open(ck_path, "a") as f:     # written last: a crash before it makes the restart redo this unit cleanly
            f.write(json.dumps({"unit": unit, "cids": cids, "tapes": tapes_used,
                                "ledger_sha256": summary["ledger_sha256"], "events": len(lg.events)}) + "\n")
            f.flush()
            os.fsync(f.fileno())
        print(f"{n_run} {unit[:50]} ev={len(lg.events)} tx={dict(summary['tx_checks'])} "
              f"{time.time() - t_start:.0f}s", flush=True)
    print("RUN_COMPLETE" if a.max_units is None or n_run < a.max_units else "RUN_PARTIAL", flush=True)


if __name__ == "__main__":
    main()
