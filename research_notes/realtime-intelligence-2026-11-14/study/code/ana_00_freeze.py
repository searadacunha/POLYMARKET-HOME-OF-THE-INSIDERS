"""ana_00: write the analytic table, once. One row per eligible entry, with its classes and its two outcome-free scores.
The outcome is joined LAST, from derived/labels.jsonl, after every feature, class and score has been computed.
No rate is computed here: the counts printed are numbers of entries and of alerts, never of wins.

Output: derived/analytic_table.jsonl and derived/table_counts.json. The sha256 of the table goes into PROTOCOL.lock."""
import collections, hashlib, json, os, sqlite3, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ETUDE, "derived", *p)
BIG_USD = 10000.0
MOVE = 0.10
QUIET_PRICE = 0.50
PUBLIC_SAMPLE_PCT = 25                          # as in feat_20: wallets read for the negative-control family, by hash
S_FRESH_AGE_H, S_FRESH_PRIOR = 48.0, 2          # the phase-8 rule of the Maduro and Iran file, unchanged: age = first inflow of collateral
FRESH_DEPENDENT = ("C1_FRESH_FUNDED_BET", "C2_DORMANT_REACTIVATION", "C4_COFUNDED_GROUP", "C5_RECURRENT_FUNDER", "C6_QUIET_FRESH_LOW",
                   "C7_HEAVY_NEWCOMER", "B3_THIN_NOT_FRESH", "R1_S_FRESH_REPLICATION")
# Coarse categories for description only, first match wins. Fixed from the tag vocabulary alone.
CATEGORIES = (("geopolitics", {"geopolitics", "world", "middle-east", "iran", "israel", "ukraine", "russia", "china", "gaza", "military-strikes", "diplomacy-ceasefire"}),
              ("politics", {"politics", "elections", "global-elections", "world-elections", "trump", "trump-presidency", "congress", "primaries"}),
              ("tech_business", {"tech", "ai", "big-tech", "business", "openai", "elon-musk", "google"}),
              ("economy", {"economy", "finance", "fed-rates", "inflation", "macro-indicators", "economic-policy", "trade-war"}),
              ("culture", {"pop-culture", "movies", "music", "awards", "oscars", "eurovision"}),
              ("crypto", {"crypto"}))


def category(tags):
    t = set(tags or [])
    return next((name for name, keys in CATEGORIES if t & keys), "other")


def build(con_entries, con_wf, con_groups, universe, sets):
    """Rows without any outcome. Returns (rows, counters)."""
    end = {m["condition_id"]: m["end_ts"] for m in universe}
    cat = {m["condition_id"]: category(m["tags"]) for m in universe}
    wf_cols = [r[1] for r in con_wf.execute("pragma table_info(wf)")]
    wf = {r[0]: dict(zip(wf_cols, r)) for r in con_wf.execute("select * from wf")}
    groups = {r[0]: r[1:] for r in con_groups.execute("select id, n_roots, c4, c5, address, t, complete from groups")}
    cols = [r[1] for r in con_entries.execute("pragma table_info(entries)")]
    post = {r[0]: r[1:] for r in con_entries.execute("select id, buy_cash_24h, follow_price, follow_dt from entry_post")}
    rows, c = [], collections.Counter()
    for raw in con_entries.execute("select * from entries where eligible=1 order by id"):
        e = dict(zip(cols, raw))
        ev = sets.get(str(e["event_id"]))
        if ev is None:
            c["entry_of_event_without_set"] += 1; continue
        w = wf.get(e["id"]); g = groups.get(e["id"])
        # the three derived files must come from the same entries table: the id is checked against the wallet and the time
        assert w is None or (w["address"], w["t"]) == (e["address"], e["t"]), ("wallet_features does not match entries", e["id"])
        assert g is None or (g[3], g[4]) == (e["address"], e["t"]), ("groups does not match entries", e["id"])
        evaluated = int(w is not None and w["view_ok"] in (1, 2))
        # a negative-control entry is evaluated only through the hash sample: a wallet read because it also bought in INFO,
        # possibly later, would make the control family depend on the wallet's future (pre-freeze leakage audit)
        if evaluated and e["grp"] == "PUBLIC_PROCESS" and int(hashlib.sha256(e["address"].encode()).hexdigest(), 16) % 100 >= PUBLIC_SAMPLE_PCT:
            evaluated = 0; c["public_process_read_outside_sample"] += 1
        r = {"id": e["id"], "set": ev["set"], "grp": e["grp"], "event_id": str(e["event_id"]), "condition_id": e["condition_id"], "oi": e["oi"],
             "address": e["address"], "t": e["t"], "price": e["price"], "cash": e["cash"], "end_ts": end[e["condition_id"]], "tier1": e["tier1"],
             "evaluated": evaluated, "view": (w or {}).get("view_ok"), "watch_ok": (w or {}).get("watch_ok"), "category": cat[e["condition_id"]]}
        thin = fresh = dormant = ooc = False; heavy = None
        if evaluated:
            thin, fresh, dormant, ooc = bool(w["thin"]), bool(w["fresh"]), bool(w["dormant"]), bool(w["ooc"])
            heavy = (w["heavy_t"], w["heavy_price"]) if w["heavy_t"] is not None else None
        c1 = thin and fresh
        c2 = dormant and fresh
        c6 = c1 and (e["mk_fills_6h"] or 0) == 0 and e["price"] <= QUIET_PRICE
        c7 = heavy if (c1 and heavy) else None
        age = (w or {}).get("r1_age_ts")
        r1 = int(bool(evaluated and age is not None and (e["t"] - age) / 3600.0 <= S_FRESH_AGE_H and (e["w_fills_before"] or 0) <= S_FRESH_PRIOR))
        unknown = []                                    # class membership not known: excluded from alerts and controls, counted
        if evaluated and w["chain"] == "missing":       # only the classes that needed the chain read
            if w["need24"]:
                unknown += [k for k in FRESH_DEPENDENT if k != "R1_S_FRESH_REPLICATION"]
            if w["need_r1"]:
                unknown += ["R1_S_FRESH_REPLICATION"]
        if c1 and not w["watch_ok"] and heavy is None:  # the 24 hours after the entry were not read: C7 unknown
            unknown += ["C7_HEAVY_NEWCOMER"]
        if evaluated and (thin or dormant) and fresh:
            assert g is not None, ("fresh entry of a thin or dormant wallet without a funding row: run feat_40 again", e["id"])
            if not g[5]:
                unknown += ["C4_COFUNDED_GROUP", "C5_RECURRENT_FUNDER"]
        for u in set(unknown):
            c["unknown_" + u] += 1
        r.update(thin=int(thin), fresh=int(fresh), dormant=int(dormant), ooc=int(ooc), c1=int(c1), c2=int(c2), c3=int(ooc),
                 c4=int(bool(g and g[1]) and (thin or dormant) and fresh), c5=int(bool(g and g[2]) and (thin or dormant) and fresh), c6=int(c6), c7_t=c7 and c7[0], c7_p=c7 and c7[1], r1=r1,
                 b1=int(e["cash"] >= BIG_USD), b2=int(e["price_1h"] is not None and round(e["price"] - e["price_1h"], 6) >= MOVE),
                 b3=int(evaluated and thin and not fresh), n_roots=(g[0] if g else None), unknown=sorted(set(unknown)),
                 fresh_by_chain_only=(w or {}).get("fresh_by_chain_only"), documented=int(bool(ev.get("documented_case"))))
        if evaluated:
            r["x"] = models.vector(dict(e, **{k: w[k] for k in ("prior_trades", "prior_other_markets", "age_h", "dep_24h", "dep_7d", "prior_trade_median",
                                                                 "last_other_trade_ts")}))
        p = post.get(e["id"])
        r["buy_cash_24h"], r["follow_price"], r["follow_dt"] = p if p else (None, None, None)
        rows.append(r)
        c["rows"] += 1; c[f"rows_{ev['set']}_{e['grp']}"] += 1; c["evaluated"] += evaluated
        c["screened_not_evaluated"] += int(e["tier1"] and not evaluated)
        c["c1_watch_window_not_fully_read"] += int(bool(c1) and not (w or {}).get("watch_ok"))     # C7 can be missed there: counted, not guessed
    return rows, c


def score(rows, counts, seed=20261114):
    """M1 and M2, fitted on DISCOVERY x INFO entries with a history; thresholds are the 99th percentile there."""
    fit = [r["x"] for r in rows if r["evaluated"] and r["set"] == "DISCOVERY" and r["grp"] == "INFO"]
    counts["m_fit_rows"] = len(fit)
    if len(fit) < 500:
        for r in rows:
            r.update(m1=0, m2=0, m1_score=None, m2_score=None)
        return {}
    m1 = models.rarity_fit(fit); m2 = models.iforest_fit(fit, seed=seed)
    for r in rows:
        if r["evaluated"]:
            r["m1_score"] = round(models.rarity_score(m1, r["x"])[0], 6); r["m2_score"] = round(models.iforest_score(m2, r["x"]), 6)
        else:
            r["m1_score"] = r["m2_score"] = None
    d = [r for r in rows if r["evaluated"] and r["set"] == "DISCOVERY" and r["grp"] == "INFO"]
    cut1 = models.quantile([r["m1_score"] for r in d], 0.99); cut2 = models.quantile([r["m2_score"] for r in d], 0.99)
    for r in rows:
        r["m1"] = int(r["m1_score"] is not None and r["m1_score"] >= cut1); r["m2"] = int(r["m2_score"] is not None and r["m2_score"] >= cut2)
    return {"m1_threshold": cut1, "m2_threshold": cut2}


def join_labels(rows, labels, counts):
    """The only place where an outcome meets a row."""
    for r in rows:
        lab = labels[r["condition_id"]]
        r["win"] = int((lab["winner"] == "YES") == (r["oi"] == 0)); r["closed_ts"] = lab["closed_ts"]
        counts["rows_entered_after_real_close"] += int(r["t"] > lab["closed_ts"])


def main():
    out = D("analytic_table.jsonl")
    running = subprocess.run(["pgrep", "-f", "code/((col|feat)_[0-9]|run_[0-9]+_chain)"], capture_output=True, text=True).stdout.split()
    if running:
        sys.exit(f"a collector or feature step is running (pids {running}): the table is written from finished files only")
    if os.path.exists(out):
        sys.exit("the analytic table already exists: it is written once (delete nothing; a change is an amendment)")
    universe = [json.loads(l) for l in open(D("universe_markets.jsonl"))]
    sets = json.load(open(D("sets.json")))
    ro = lambda p: sqlite3.connect("file:" + p + "?mode=ro", uri=True)
    rows, c = build(ro(D("entries.sqlite")), ro(D("wallet_features.sqlite")), ro(D("groups.sqlite")), universe, sets)
    thresholds = score(rows, c)
    for name in ("c1", "c2", "c3", "c4", "c5", "c6", "c7_t", "r1", "m1", "m2", "b1", "b2", "b3"):
        for r in rows:
            if r.get(name):
                c[f"alerts_{name}"] += 1; c[f"alerts_{name}_{r['set']}_{r['grp']}"] += 1
    labels = {}
    for l in open(D("labels.jsonl")):                    # outcome: read here and nowhere before
        x = json.loads(l); labels[x["condition_id"]] = x
    join_labels(rows, labels, c)
    with open(out + ".tmp", "w") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
    os.replace(out + ".tmp", out)
    c = dict(c, **thresholds)
    json.dump(c, open(D("table_counts.json"), "w"), indent=1)
    print(json.dumps(c, indent=1))


if __name__ == "__main__":
    main()
