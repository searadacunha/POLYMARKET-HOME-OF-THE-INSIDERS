"""feat_30: point-in-time wallet view and class moments of every tier-1 entry whose wallet history was read (col_30).
No outcome is read. Outputs:
  derived/wallet_features.sqlite (table wf), derived/wallet_counts.json;
  derived/inflow_todo.jsonl: the entries whose funding must be read on the chain (col_41), decided from the activity rows
    alone, so the list is the same before and after col_41 has run:
      - thin or dormant and not fresh by the deposit rows: collateral received in the 24 hours before (FRESH);
      - at most 2 earlier fills in the universe and a first activity row less than 48 hours before: collateral received
        in the 30 days before (R1: age of the wallet = first inflow of collateral, as pre-registered in phase 8);
  derived/funding_todo.jsonl: the deposits and chain inflows whose payer is traced next (thin or dormant, and fresh).

Run it, then col_41_inflows.py, then again: the second run merges the chain inflows (type I rows of asof.py).
An entry whose chain read is needed and missing is written with chain='missing': its FRESH-dependent classes and R1 are
unknown, excluded from alerts and controls, and counted (ana_00)."""
import collections, json, os, sqlite3, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asof, chainfund

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R1_AGE_S, R1_PRIOR, R1_LOOKBACK_S = 48 * 3600, 2, 30 * 86400
COLS = ("id integer primary key, address text, t integer, view_ok integer, watch_ok integer, entry_seen integer, rows_before integer, age_h real, "
        "prior_trades integer, prior_other_trades integer, prior_other_markets integer, prior_trade_median real, prior_trade_max real, "
        "last_other_trade_ts integer, dep_24h real, dep_7d real, dep_total real, n_dep integer, first_seen_ts integer, thin integer, fresh integer, "
        "dormant integer, ooc integer, heavy_t integer, heavy_price real, heavy_net_buy real, heavy_deposits real, net_buy_24h real, "
        "chain text, fresh_by_chain_only integer, r1_age_ts integer, window_short_24h integer, need24 integer, need_r1 integer, chain_in_24h real")
NCOLS = COLS.count(",") + 1


def merge(rows, extra):
    return sorted(rows + extra, key=lambda r: r[0]) if extra else rows


def main():
    ro = lambda p, **k: sqlite3.connect("file:" + p + "?mode=ro", uri=True, **k)
    ent = ro(os.path.join(ETUDE, "derived", "entries.sqlite"))
    act = ro(os.path.join(ETUDE, "data", "activity.sqlite"), timeout=60)
    cpath = os.path.join(ETUDE, "data", "inflows_chain.sqlite")
    chain, mint_payer, tagged = {}, {}, set()
    if os.path.exists(cpath):
        cc = ro(cpath)
        for i, wallet, t, from_ts, status, rows in cc.execute("select id, wallet, t, from_ts, status, rows from items"):
            chain[i] = (wallet, t, from_ts, json.loads(rows) if status == "ok" else None)
        if cc.execute("select count(*) from sqlite_master where name='mints'").fetchone()[0]:     # written by col_41 after the logs
            mint_payer = {tx: payer for tx, payer in cc.execute("select tx, payer from mints where status='ok'")}
        # addresses whose public name tag names Polymarket are Polymarket's own, like chainfund.INFRA (rewards, wrapping)
        tagged = {r[0] for r in ro(os.path.join(ETUDE, "data", "funding.sqlite")).execute("select address from payers where tags like '%Polymarket%'")}
    infra = chainfund.INFRA | tagged
    path = os.path.join(ETUDE, "derived", "wallet_features.sqlite")
    tmp = path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    out = sqlite3.connect(tmp); out.execute(f"create table wf({COLS})")
    c = collections.Counter(); rows_out = []
    todo = open(os.path.join(ETUDE, "derived", "funding_todo.jsonl.tmp"), "w")
    itodo = open(os.path.join(ETUDE, "derived", "inflow_todo.jsonl.tmp"), "w")
    cur_addr, hist, meta = None, None, None
    has_asof = act.execute("select count(*) from sqlite_master where name='asof'").fetchone()[0]
    for eid, addr, t, cond, oi, cash, prior_fills in ent.execute(
            "select id, address, t, condition_id, oi, cash, w_fills_before from entries where tier1=1 order by address, t"):
        c["tier1_entries"] += 1
        if addr != cur_addr:
            cur_addr = addr
            r = act.execute("select status, has_more, last_ts, body from activity where wallet=?", (addr,)).fetchone()
            if r is None:
                hist, meta = None, "not_read"
            elif r[0] != "ok":
                hist, meta = None, "read_error"
            else:
                hist, meta = json.loads(zlib.decompress(r[3])), (r[1], r[2])
        if hist is None:
            c["no_history_" + meta] += 1; continue
        has_more, last_ts = meta
        first_seen = hist[0][0] if hist else None            # the first page is oldest first: its first row is the wallet's first row
        view_ok = int(not has_more or t <= last_ts)          # the page read reaches the entry
        watch_ok = int(not has_more or last_ts >= t + asof.WATCH_S)
        floor = 0
        if not view_ok:                                      # beyond the first page: the as-of rows of col_31
            c["beyond_first_page"] += 1
            r = act.execute("select status, body, after, after_more from asof where key=?", (f"{addr}|{t}|{cond}|{oi}",)).fetchone() if has_asof else None
            if r is None or r[0] != "ok":
                c["beyond_first_page_not_read"] += 1; continue
            rows = json.loads(zlib.decompress(r[1])) + (json.loads(zlib.decompress(r[2])) if r[2] else [])
            view_ok, watch_ok, floor = 2, int(r[2] is not None and not r[3]), asof.THIN_ROWS   # 2 = view from the 500 rows before the entry
        else:
            rows = hist
        w0 = asof.watch(rows, t, cond, oi, cash, rows_before_floor=floor)        # activity rows only: decides what to read on the chain
        f0 = w0["flags"]
        need24 = (f0["thin"] or f0["dormant"]) and not f0["fresh"]
        need_r1 = (prior_fills or 0) <= R1_PRIOR and first_seen is not None and first_seen >= t - R1_AGE_S
        if need24 or need_r1:
            itodo.write(json.dumps({"id": eid, "wallet": addr, "t": t, "from_ts": t - (R1_LOOKBACK_S if need_r1 else asof.FRESH_S)}) + "\n")
            c["chain_needed"] += 1; c["chain_needed_fresh"] += need24; c["chain_needed_r1"] += need_r1
        status, extra, earliest = "not_needed", [], None
        if need24 or need_r1:
            want_from = t - (R1_LOOKBACK_S if need_r1 else asof.FRESH_S)
            got = chain.get(eid)
            # the read must be of this wallet and time, over a window that covers the one needed
            if got is None or got[3] is None or (got[0], got[1]) != (addr, t) or got[2] > want_from:
                status = "missing"
            else:
                status, item = "ok", got[3]
                d_txs = {x[7] for x in rows if x[1] == "D"}
                # built-in check: every deposit row of the window must be seen on the chain, or the read is not trusted
                lost = [x for x in rows if x[1] == "D" and want_from <= x[0] < t and x[7] not in {r["tx"] for r in item}]
                busy = {x[0] for x in rows if x[1] not in ("D", "I")}
                extra, earliest, drop = asof.chain_rows(item, addr, t, d_txs, infra, busy_ts=busy, mint_payer=mint_payer)
                if need24:   # only the 24-hour window counts for FRESH, even when 30 days were read for R1
                    extra = [x for x in extra if x[0] >= t - asof.FRESH_S]
                    for k_, n_ in drop.items():
                        c["chain_rows_left_out_" + k_] += n_
                    if drop.get("mint_unread"):
                        status = "missing"; c["chain_missing_mint_unread"] += 1
                else:
                    extra = []
                if lost:
                    status = "missing"; c["chain_missing_deposit_row_not_on_chain"] += 1
                if status == "missing":
                    extra, earliest = [], None
        w = asof.watch(merge(rows, extra), t, cond, oi, cash, rows_before_floor=floor) if extra else w0
        v, f, k = w["view"], w["flags"], w["heavy"]
        v["age_h"] = (t - first_seen) / 3600.0 if first_seen is not None and first_seen < t else None
        if first_seen is not None and first_seen < t - R1_AGE_S:
            r1_age = first_seen                              # older than 48 h by its own rows: no chain read needed
        elif need_r1 and status == "ok":
            r1_age = min(x for x in (first_seen, earliest) if x is not None)
        else:
            r1_age = None
        short = int(view_ok == 2 and bool(rows) and rows[0][0] > t - asof.FRESH_S)
        c["evaluated"] += 1; c[f"view_{view_ok}"] += 1; c[f"chain_{status}"] += 1; c["window_short_24h"] += short
        c["entry_not_in_history"] += (not w["entry_seen_in_history"]) and not (view_ok == 2 and not watch_ok)
        for name in ("thin", "fresh", "dormant", "ooc"):
            c[name] += f[name]
        by_chain = int(f["fresh"] and not f0["fresh"])
        c["fresh_by_chain_only"] += by_chain; c["heavy"] += bool(k)
        c["thin_fresh"] += bool(f["thin"] and f["fresh"]); c["dormant_fresh"] += bool(f["dormant"] and f["fresh"])
        v0 = w0["view"]      # the model features keep the deposit rows only, one definition for every entry
        rows_out.append((eid, addr, t, view_ok, watch_ok, int(w["entry_seen_in_history"]), v["rows_before"], v["age_h"], v["prior_trades"],
                         v["prior_other_trades"], v["prior_other_markets"], v["prior_trade_median"], v["prior_trade_max"], v["last_other_trade_ts"],
                         v0["dep_24h"], v0["dep_7d"], v0["dep_total"], v0["n_dep"], first_seen, int(f["thin"]), int(f["fresh"]), int(f["dormant"]),
                         int(f["ooc"]), k and k["t"], k and k["price"], k and k["net_buy"], k and k["deposits"], w["net_buy"],
                         status, by_chain, r1_age, short, int(need24), int(need_r1), round(sum(x[4] for x in extra), 2)))
        if f["fresh"] and (f["thin"] or f["dormant"]):
            deps = [d for d in v["deposits_7d"] if d[0] >= t - asof.FRESH_S]
            c["funding_entries"] += 1; c["funding_deposits"] += len(deps); c["funding_deposit_without_tx"] += sum(1 for d in deps if not d[2])
            todo.write(json.dumps({"id": eid, "wallet": addr, "t": t, "deposits": [list(d) for d in deps if d[2]]}) + "\n")
    assert all(len(r) == NCOLS for r in rows_out)
    out.executemany(f"insert into wf values({','.join('?' * NCOLS)})", rows_out); out.commit(); out.close(); todo.close(); itodo.close()
    for p in (path, os.path.join(ETUDE, "derived", "funding_todo.jsonl"), os.path.join(ETUDE, "derived", "inflow_todo.jsonl")):
        os.replace(p + ".tmp", p)
    json.dump(dict(c), open(os.path.join(ETUDE, "derived", "wallet_counts.json"), "w"), indent=1)
    print(json.dumps(dict(c), indent=1))


def _selftest():
    W, T = "0x" + "11" * 20, 1_000_000
    item = [{"from": "0x" + "aa" * 20, "ts": T - 100, "value": 2_500_000_000, "tx": "0xa"},
            {"from": "0xe111180000d2663c0091e4f400237545b87b996b", "ts": T - 50, "value": 9_000_000, "tx": "0xb"},   # exchange: a trade
            {"from": "0x" + "aa" * 20, "ts": T - 40, "value": 1_000_000, "tx": "0xdep"},                           # already a deposit row
            {"from": "0x" + "aa" * 20, "ts": T, "value": 1_000_000, "tx": "0xc"}]                                  # not before the entry
    rows, earliest, drop = asof.chain_rows(item, W, T, {"0xdep"}, chainfund.INFRA)
    assert rows == [[T - 100, "I", None, "0x" + "aa" * 20, 2500.0, None, None, "0xa"]] and earliest == T - 100 and drop == {"polymarket": 1, "dep_row": 1}, (rows, drop)
    print("feat_30 selftest ok")


if __name__ == "__main__":
    _selftest() if sys.argv[1:] == ["selftest"] else main()
