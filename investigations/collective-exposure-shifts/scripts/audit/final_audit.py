#!/usr/bin/env python3
"""Final independent audit of the collective-exposure-shifts study (mission 7 of 7).

Recomputes every published number from the raw inputs, with code written for the audit (stats.py, score.py and
report_tables.py are NOT imported). Only the declared sensitivity re-runs reuse `build_alerts.evaluate_market`,
because their purpose is to change one rule of that engine and nothing else.

Inputs (read-only): the two local tapes, the population and labels archived in git, and the published result files.
Output: one JSON with every check, plus the two publication tables (best alerts, false positives) as CSV and JSON.

Usage:
  python3 scripts/audit/final_audit.py --inv . --tapes tapes.sqlite --tapes2 tapes2.sqlite \
      --labels labels.jsonl.gz --universe universe_markets.jsonl.gz --out results/audit [--skip-reruns]
"""
import argparse, bisect, csv, gzip, hashlib, json, math, os, random, sqlite3, sys, urllib.parse
from collections import defaultdict

W = 3600
SLIPPAGE = (0.0, 0.005, 0.01, 0.02, 0.05)
AUDIT_SEED = 7_20261117          # deliberately different from the study seed
DRAWS = 10000
TOL = 1e-9


# ---------------------------------------------------------------- helpers
def jl(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as f:
        return [json.loads(l) for l in f if l.strip()]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ro(path):
    con = sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(path))}?mode=ro&immutable=1", uri=True)
    con.execute("pragma temp_store=memory")
    return con


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def binom_sf(k, n, p):
    """P(X >= k), X ~ Bin(n, p), summed in log space (independent of stats.py)."""
    if n == 0 or k <= 0:
        return 1.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    lp, lq = math.log(p), math.log1p(-p)
    terms = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq
             for i in range(k, n + 1)]
    m = max(terms)
    return min(1.0, math.exp(m) * sum(math.exp(t - m) for t in terms))


def cluster_ci(rows, field, seed=AUDIT_SEED, draws=DRAWS):
    """Percentile CI of the mean of `field`, resampling whole events."""
    by = defaultdict(list)
    for r in rows:
        by[r.get("event_id") or r["condition_id"]].append(r[field])
    cells = [(sum(v), len(v)) for v in by.values()]
    if not cells:
        return None
    rng = random.Random(seed)
    out = []
    for _ in range(draws):
        s = n = 0
        for _ in range(len(cells)):
            a, b = cells[rng.randrange(len(cells))]
            s += a
            n += b
        out.append(s / n)
    out.sort()
    return [round(out[int(0.025 * draws)], 4), round(out[int(0.975 * draws) - 1], 4)]


def cluster_diff(a_rows, b_rows, field="excess", seed=AUDIT_SEED, draws=DRAWS):
    by = defaultdict(lambda: [0.0, 0, 0.0, 0])
    for r in a_rows:
        c = by[r.get("event_id") or r["condition_id"]]
        c[0] += r[field]; c[1] += 1
    for r in b_rows:
        c = by[r.get("event_id") or r["condition_id"]]
        c[2] += r[field]; c[3] += 1
    cells = list(by.values())
    rng = random.Random(seed)
    obs = mean([r[field] for r in a_rows]) - mean([r[field] for r in b_rows])
    ds = []
    for _ in range(draws):
        sa = na = sb = nb = 0
        for _ in range(len(cells)):
            c = cells[rng.randrange(len(cells))]
            sa += c[0]; na += c[1]; sb += c[2]; nb += c[3]
        if na and nb:
            ds.append(sa / na - sb / nb)
    ds.sort()
    p = (sum(1 for d in ds if d <= 0) + 1) / (len(ds) + 1)
    return {"diff": round(obs, 4), "ci": [round(ds[int(0.025 * len(ds))], 4), round(ds[int(0.975 * len(ds)) - 1], 4)],
            "p_one_sided": round(p, 4), "n_a": len(a_rows), "n_b": len(b_rows)}


def hash_slot(cid):
    return int(hashlib.sha256(cid.encode()).hexdigest()[:8], 16) % 1000


# ---------------------------------------------------------------- checks
def check_sample(universe, inv):
    out = {}
    for name, thr, path in (("primary", 25, "results/sample_markets.jsonl"),
                            ("replication", 50, "results/sample_expanded.jsonl")):
        expect = {m["condition_id"] for m in universe if m["volume"] < 1_000_000 and hash_slot(m["condition_id"]) < thr}
        pub = {m["condition_id"] for m in jl(os.path.join(inv, path))}
        out[name] = {"recomputed": len(expect), "published": len(pub), "identical": expect == pub}
    out["primary_subset_of_replication"] = (
        {m["condition_id"] for m in jl(os.path.join(inv, "results/sample_markets.jsonl"))}
        <= {m["condition_id"] for m in jl(os.path.join(inv, "results/sample_expanded.jsonl"))})
    return out


def split_of(ts):
    import datetime as dt
    t = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
    if dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc) <= t <= dt.datetime(2025, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc):
        return "TRAIN"
    if dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc) <= t <= dt.datetime(2026, 6, 30, 23, 59, 59, tzinfo=dt.timezone.utc):
        return "VALID"
    if dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc) <= t <= dt.datetime(2026, 10, 31, 23, 59, 59, tzinfo=dt.timezone.utc):
        return "TEST"
    return "EXCLUDED_PERIOD"


def check_labels_and_splits(scored, winners, meta):
    bad_win = bad_split = bad_excess = missing = 0
    for r in scored:
        w = winners.get(r["condition_id"])
        if w is None:
            missing += 1
            continue
        if r["win"] != (1 if w == r["side"].lower() else 0):
            bad_win += 1
        if abs(r["excess"] - (r["win"] - r["price"])) > TOL:
            bad_excess += 1
        if split_of(meta[r["condition_id"]]["closed_ts"]) != r.get("split"):
            bad_split += 1
    return {"rows": len(scored), "label_missing": missing, "win_mismatch": bad_win,
            "excess_mismatch": bad_excess, "split_mismatch": bad_split}


def unscored_alerts(alerts, scored):
    key = lambda r: (r["condition_id"], r["side"], r["t"], r["variant"])
    s = {key(r) for r in scored}
    lost = [r for r in alerts if key(r) not in s]
    return {"alerts": len(alerts), "scored": len(scored), "not_scored": len(lost),
            "not_scored_s4_primary": sum(1 for r in lost if r["variant"] == "S4" and r.get("primary"))}


class Tape:
    def __init__(self, paths):
        self.cons = [ro(p) for p in paths]
        self.where = {}
        for i, c in enumerate(self.cons):
            for (cid,) in c.execute("select condition_id from status where status='ok'"):
                self.where.setdefault(cid, i)
        self.cache = {}

    def rows(self, cid):
        if cid not in self.cache:
            if len(self.cache) > 64:
                self.cache.clear()
            self.cache[cid] = self.cons[self.where[cid]].execute(
                "select ts, wallet, side, outcome, size, price, tx from trades where condition_id=? "
                "order by ts, tx, wallet", (cid,)).fetchall()
        return self.cache[cid]


def verify_alert(r, tape):
    """Re-derive one alert from the tape with audit code: price, its age, every wallet's shift, its fills."""
    rows = tape.rows(r["condition_id"])
    t, side = r["t"], r["side"]
    d = 1.0 if side == "Yes" else -1.0
    other = "No" if side == "Yes" else "Yes"
    last_side = last_other = None
    for f in rows:
        if f[0] > t:
            break
        if f[3] == side:
            last_side = f
        elif f[3] == other:
            last_other = f
    res = {"price_tape": last_side[5] if last_side else None,
           "price_match": bool(last_side and abs(last_side[5] - r["price"]) < 1e-9),
           "price_age_s": (t - last_side[0]) if last_side else None,
           "complement_gap": (round(abs(last_side[5] - (1 - last_other[5])), 4) if last_side and last_other else None),
           "uses_fill_after_t": False}
    wallets = []
    ok = 0
    coexist = 0
    for w, usd_pub in zip(r["wallets"], r["shift_usd"]):
        mine = [f for f in rows if f[1] == w and f[0] <= t]
        def x_at(ts):
            x = 0.0
            for f in mine:
                if f[0] > ts:
                    break
                s = f[4] if f[2] == "BUY" else -f[4]
                x += s if f[3] == "Yes" else -s
            return x
        dx = d * (x_at(t) - x_at(t - W))
        usd = dx * r["price"]
        qy = sum((f[4] if f[2] == "BUY" else -f[4]) for f in mine if f[3] == "Yes")
        qn = sum((f[4] if f[2] == "BUY" else -f[4]) for f in mine if f[3] == "No")
        if qy > 1e-6 and qn > 1e-6:
            coexist += 1
        win_fills = [f for f in mine if f[0] > t - W]
        good = abs(usd - usd_pub) <= 0.01 + 1e-6 * abs(usd_pub) and usd >= 500 - 1e-6
        ok += good
        wallets.append({"wallet": w, "shift_usd_pub": usd_pub, "shift_usd_audit": round(usd, 2), "match": good,
                        "fills_in_window": len(win_fills),
                        "first_fill_ts": min((f[0] for f in win_fills), default=None),
                        "last_fill_ts": max((f[0] for f in win_fills), default=None),
                        "txs": sorted({f[6] for f in win_fills})[:20]})
    res.update({"wallets_verified": ok, "wallets_listed": len(r["wallets"]), "coexistence_wallets": coexist,
                "total_usd_audit": round(sum(x["shift_usd_audit"] for x in wallets), 2),
                "signal_complete_ts": max((x["last_fill_ts"] for x in wallets if x["last_fill_ts"]), default=None),
                "wallet_detail": wallets})
    # Executed liquidity after the alert, a lower bound proxy for capacity (NOT a book): notional of fills on the
    # alert side at a price <= entry + 1 point within the next hour.
    nxt = [f for f in rows if t < f[0] <= t + W and f[3] == side and f[5] <= r["price"] + 0.01]
    res["executed_notional_next_hour_le_p_plus_1pt"] = round(sum(f[4] * f[5] for f in nxt), 2)
    return res


def describe(rows, label):
    out = {"label": label, "n": len(rows), "events": len({r.get("event_id") for r in rows})}
    if not rows:
        return out
    out.update({"wins": sum(r["win"] for r in rows), "win_rate": round(mean([r["win"] for r in rows]), 4),
                "mean_price": round(mean([r["price"] for r in rows]), 4),
                "excess": round(mean([r["excess"] for r in rows]), 4),
                "excess_ci_events": cluster_ci(rows, "excess"),
                "binom_p_one_sided": round(binom_sf(sum(r["win"] for r in rows), len(rows),
                                                    mean([r["price"] for r in rows])), 4)})
    for s in SLIPPAGE:
        pay = [((1 - min(r["price"] + s, 0.999)) if r["win"] else -min(r["price"] + s, 0.999)) for r in rows]
        out[f"mean_payoff_{s}"] = round(mean(pay), 5)
    return out


def compare_published(desc, tests):
    """Match the audit recomputation with the published tests.json numbers."""
    t1, t7 = tests["tests"]["T1"], tests["tests"]["T7"]
    allr, test = desc["all"], desc["TEST"]
    return {
        "T1_n": (allr["n"], t1["n"]), "T1_wins": (allr["wins"], t1["wins"]),
        "T1_excess": (allr["excess"], round(t1["excess"], 4)),
        "T1_p": (allr["binom_p_one_sided"], round(t1["p_value"], 4)),
        "T7_n": (test["n"], t7["n"]), "T7_excess": (test["excess"], round(t7["excess"], 4) if t7["excess"] is not None else None),
        "T7_p": (test["binom_p_one_sided"], round(t7["p_value"], 4)),
        "T5_mean_payoff_1pct": (allr["mean_payoff_0.01"], round(tests["tests"]["T5"]["mean_payoff_1pct"], 5)),
        "verdict_published": tests["verdict"],
        "all_equal": (allr["n"] == t1["n"] and allr["wins"] == t1["wins"] and test["n"] == t7["n"]
                      and abs(allr["excess"] - round(t1["excess"], 4)) < 1e-4
                      and abs(allr["binom_p_one_sided"] - round(t1["p_value"], 4)) < 1e-3
                      and abs(test["binom_p_one_sided"] - round(t7["p_value"], 4)) < 1e-3),
    }


def verdict_rule(test_rows, p7):
    n = len(test_rows)
    pay = mean([((1 - min(r["price"] + 0.01, 0.999)) if r["win"] else -min(r["price"] + 0.01, 0.999)) for r in test_rows])
    if n >= 30 and p7 < 0.005 and pay and pay > 0:
        return "EXPLOITABLE"
    return "NOT_SUPPORTED" if n >= 30 else "INCONCLUSIVE"


# ---------------------------------------------------------------- sensitivity re-runs (engine reused on purpose)
def rerun(inv, tape_paths, sample_path, splits_path, winners, mode):
    sys.path.insert(0, os.path.join(inv, "scripts"))
    import build_alerts as ba
    orig_dedupe = ba.dedupe
    if mode == "causal_first":
        # the first candidate in time is the alert; nothing later can displace it
        ba.dedupe = lambda cands: [min(cands, key=lambda c: c["t"])] if cands else []
    meta = {m["condition_id"]: m for m in jl(os.path.join(inv, sample_path))}
    splits = json.load(open(os.path.join(inv, splits_path)))
    out = []
    for p in tape_paths:
        con = ro(p)
        for (cid,) in con.execute("select condition_id from status where status='ok'"):
            if cid not in meta:
                continue
            q = ("select distinct ts, wallet, side, outcome, size, price, tx from trades where condition_id=? "
                 "order by ts, tx, wallet") if mode == "distinct_rows" else \
                ("select ts, wallet, side, outcome, size, price from trades where condition_id=? order by ts, tx, wallet")
            rows = con.execute(q, (cid,)).fetchall()
            if mode == "distinct_rows":
                rows = [r[:6] for r in rows]
            m = dict(meta[cid]); m["split"] = splits.get(cid)
            al, _ = ba.evaluate_market(cid, rows, m)
            for a in al:
                if a["variant"] == "S4" and a["primary"] and cid in winners:
                    a["win"] = 1 if winners[cid] == a["side"].lower() else 0
                    a["excess"] = a["win"] - a["price"]
                    out.append(a)
    ba.dedupe = orig_dedupe
    return out


# ---------------------------------------------------------------- publication tables
def table_rows(rows, verif, n):
    out = []
    for r in rows[:n]:
        v = verif[(r["condition_id"], r["side"], r["t"])]
        biggest = max(v["wallet_detail"], key=lambda w: w["shift_usd_audit"])
        out.append({
            "split": r["split"], "event_slug": r.get("event_slug"), "condition_id": r["condition_id"],
            "side": r["side"], "alert_ts_utc": iso(r["t"]), "alert_ts": r["t"],
            "signal_complete_ts_utc": iso(v["signal_complete_ts"]) if v["signal_complete_ts"] else None,
            "entry_price_last_fill": r["price"], "price_age_s": v["price_age_s"],
            "n_wallets": r["n_wallets"], "total_shift_usd": r["total_usd"],
            "winner": r["winner"], "win": r["win"], "excess": round(r["excess"], 4),
            "payoff_per_share_1pct": round(((1 - min(r["price"] + 0.01, 0.999)) if r["win"] else -min(r["price"] + 0.01, 0.999)), 4),
            "largest_wallet": biggest["wallet"], "largest_wallet_shift_usd": biggest["shift_usd_audit"],
            "largest_wallet_txs": biggest["txs"][:3],
            "wallets_verified": f'{v["wallets_verified"]}/{v["wallets_listed"]}',
            "executed_notional_next_hour_le_p_plus_1pt": v["executed_notional_next_hour_le_p_plus_1pt"],
            "market_url": f'https://polymarket.com/event/{r.get("event_slug")}',
            "tape_url": f'https://data-api.polymarket.com/v2/trades?condition={r["condition_id"]}&limit=1000&taker_only=false',
            "tx_urls": [f"https://polygonscan.com/tx/{x}" for x in biggest["txs"][:3]],
        })
    return out


def iso(ts):
    import datetime as dt
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_csv(path, rows):
    if not rows:
        open(path, "w").close()
        return
    keys = [k for k in rows[0] if k not in ("largest_wallet_txs",)]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(r[k]) if isinstance(r[k], list) else r[k]) for k in keys})


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inv", required=True)
    ap.add_argument("--tapes", required=True)
    ap.add_argument("--tapes2", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-reruns", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    R = lambda p: os.path.join(a.inv, p)

    universe = jl(a.universe)
    winners = {r["condition_id"]: r["winner"].strip().lower() for r in jl(a.labels)}
    meta = {m["condition_id"]: m for m in jl(R("results/sample_expanded.jsonl"))}
    report = {"audit": "collective-exposure-shifts final audit", "audit_seed": AUDIT_SEED,
              "inputs": {"tapes_sha256": sha256(a.tapes), "tapes2_sha256": sha256(a.tapes2),
                         "labels_sha256": sha256(a.labels), "universe_sha256": sha256(a.universe)}}
    manifest = json.load(open(R("data_manifest.json")))
    man = {f["path"]: f for f in manifest["files"] if f.get("sha256")}
    report["manifest_check"] = {
        "tapes.sqlite": report["inputs"]["tapes_sha256"] == man["tapes.sqlite"]["sha256"],
        "tapes2.sqlite": report["inputs"]["tapes2_sha256"] == man["tapes2.sqlite"]["sha256"],
        "tapes2_size_manifest": man["tapes2.sqlite"]["size"], "tapes2_size_actual": os.path.getsize(a.tapes2)}
    report["sample"] = check_sample(universe, a.inv)

    tape = Tape([a.tapes, a.tapes2])
    for run, prefix, tests_file in (("primary", "", "results/tests.json"),
                                    ("replication", "replication_", "results/replication_tests.json")):
        alerts = jl(R(f"results/{prefix}alerts.jsonl"))
        scored = jl(R(f"results/{prefix}scored.jsonl"))
        placebo = jl(R(f"results/{prefix}scored.jsonl.placebo.jsonl"))
        tests = json.load(open(R(tests_file)))
        rep = {"labels_splits": check_labels_and_splits(scored, winners, meta),
               "unscored": unscored_alerts(alerts, scored)}
        s4 = sorted([r for r in scored if r["variant"] == "S4" and r.get("primary")], key=lambda r: r["t"])
        verif = {}
        for r in s4:
            verif[(r["condition_id"], r["side"], r["t"])] = verify_alert(r, tape)
        vs = list(verif.values())
        rep["alert_reconstruction"] = {
            "s4_primary": len(s4),
            "price_matches_tape": sum(v["price_match"] for v in vs),
            "wallets_listed": sum(v["wallets_listed"] for v in vs),
            "wallets_reproduced": sum(v["wallets_verified"] for v in vs),
            "alerts_with_coexistence_wallet": sum(1 for v in vs if v["coexistence_wallets"]),
            "price_age_s_median": sorted(v["price_age_s"] for v in vs)[len(vs) // 2],
            "price_age_s_over_3600": sum(1 for v in vs if v["price_age_s"] > 3600),
            "complement_gap_over_0_05": sum(1 for v in vs if (v["complement_gap"] or 0) > 0.05),
            "signal_complete_after_alert": sum(1 for k, v in verif.items() if v["signal_complete_ts"] and v["signal_complete_ts"] > k[2]),
            "executed_notional_next_hour_median": sorted(v["executed_notional_next_hour_le_p_plus_1pt"] for v in vs)[len(vs) // 2],
            "executed_notional_next_hour_sum": round(sum(v["executed_notional_next_hour_le_p_plus_1pt"] for v in vs), 2),
        }
        desc = {"all": describe(s4, "S4 primary, all splits")}
        for sp in ("TRAIN", "VALID", "TEST"):
            desc[sp] = describe([r for r in s4 if r["split"] == sp], f"S4 primary, {sp}")
        rep["recomputed"] = desc
        rep["published_vs_audit"] = compare_published(desc, tests)
        rep["verdict_audit"] = verdict_rule([r for r in s4 if r["split"] == "TEST"], desc["TEST"].get("binom_p_one_sided", 1.0))
        # placebo actually matched to S4 primary alerts only (the published T2 pools placebo drawn for every variant)
        keys = {f'{r["condition_id"]}:{r["side"]}:{r["t"]}' for r in s4}
        pl = [p for p in placebo if p["for_alert"] in keys]
        rep["T2_placebo_matched_to_s4_only"] = cluster_diff(s4, pl) if pl else None
        rep["T2_published"] = {"n_placebo": tests["tests"]["T2"]["n_placebo"], "diff": round(tests["tests"]["T2"]["diff"], 4)}
        st = json.load(open(R(f"results/{'replication_status' if prefix else 'alerts_status'}.json")))["per_market"]
        rep["frequency"] = {"markets": len(st), "markets_ok": sum(1 for m in st if m["status"] == "ok"),
                            "s4_primary_per_market": round(len(s4) / len(st), 4)}
        report[run] = rep

        if run == "replication":
            ranked = sorted(s4, key=lambda r: -r["total_usd"])           # outcome-blind ranking
            test_ranked = [r for r in ranked if r["split"] == "TEST"]
            best = table_rows(test_ranked, verif, a.top)                  # strongest TEST alerts, whatever the outcome
            fps = table_rows([r for r in test_ranked if r["win"] == 0], verif, 10 ** 6)  # every TEST false positive
            json.dump({"best_alerts_rule": "replication S4 primary alerts in TEST, ranked by total shift USD "
                                           "(outcome-blind), top %d, outcome shown after ranking" % a.top,
                       "false_positives_rule": "every replication S4 primary alert in TEST whose side lost",
                       "best_alerts": best, "false_positives": fps},
                      open(os.path.join(a.out, "publication_tables.json"), "w"), indent=1)
            write_csv(os.path.join(a.out, "best_alerts.csv"), best)
            write_csv(os.path.join(a.out, "false_positives.csv"), fps)
            json.dump([{"key": f"{k[0]}:{k[1]}:{k[2]}", **{x: y for x, y in v.items() if x != "wallet_detail"}}
                       for k, v in verif.items()],
                      open(os.path.join(a.out, "alert_reconstruction.json"), "w"), indent=0)

    if not a.skip_reruns:
        sens = {}
        for mode in ("causal_first", "distinct_rows"):
            rows = rerun(a.inv, [a.tapes, a.tapes2], "results/sample_expanded.jsonl", "results/splits_expanded.json",
                         winners, mode)
            sens[mode] = {"all": describe(rows, mode), "TEST": describe([r for r in rows if r["split"] == "TEST"], mode)}
            sens[mode]["verdict_rule"] = verdict_rule([r for r in rows if r["split"] == "TEST"],
                                                      sens[mode]["TEST"].get("binom_p_one_sided", 1.0))
        report["sensitivity_replication"] = sens

    json.dump(report, open(os.path.join(a.out, "final_audit.json"), "w"), indent=1)
    print(json.dumps({k: report[k] for k in ("manifest_check", "sample")}, indent=1))
    for run in ("primary", "replication"):
        print(run, json.dumps({k: report[run][k] for k in ("labels_splits", "unscored", "alert_reconstruction",
                                                            "published_vs_audit", "verdict_audit",
                                                            "T2_placebo_matched_to_s4_only", "T2_published")}, indent=1))
    if "sensitivity_replication" in report:
        print(json.dumps(report["sensitivity_replication"], indent=1))


if __name__ == "__main__":
    main()
