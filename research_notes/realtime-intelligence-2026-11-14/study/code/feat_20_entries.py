"""feat_20: entries and their context, from the fills of 1,000 USD or more. No outcome is read here.

An ENTRY is the first BUY fill of 1,000 USD or more of one wallet on one side of one market. Everything attached to an
entry uses fills dated strictly before it (fills of the same second belong to the same matches and are not "before"),
plus the entry fill itself. What happens after the entry goes to a separate table (entry_post) that no feature reads.

Output: derived/entries.sqlite (tables entries, entry_post), derived/entries_counts.json, derived/tier1_wallets.txt."""
import bisect, collections, hashlib, json, os, sqlite3, sys

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICE_MAX = 0.90            # above: the outcome is treated as publicly settled
END_GRACE_S = 86400         # an end at 00:00 UTC is a date: 17,630 of 32,552 end dates fall there and the event happens during that
                            # day (the Nobel market "ends" nine hours before the announcement), so that day is included. An end at any
                            # other time is a deadline: nothing after it (pre-freeze audit of 14 November 2026)


def grace(end_ts):
    return END_GRACE_S if end_ts % 86400 == 0 else 0
THIN_MARKETS = 2            # at most this many OTHER markets with a fill before the entry
DORMANT_S = 60 * 86400
OOC_MIN_PRIOR, OOC_MULT = 5, 5.0
PUBLIC_SAMPLE_PCT = 25      # share of wallets seen only in the negative-control family whose history is read (by hash)
H1, H6, H24 = 3600, 6 * 3600, 24 * 3600

COLS = ("id integer primary key, t integer, wallet integer, address text, cond integer, condition_id text, event_id text, grp text, "
        "oi integer, price real, size real, cash real, tx text, hours_to_end real, market_age_h real, prev_price real, prev_age_s integer, "
        "price_1h real, price_24h real, mk_fills_before integer, mk_fills_24h integer, mk_cash_24h real, mk_fills_6h integer, "
        "side_buy_cash_24h real, co_entrants_6h integer, w_fills_before integer, w_markets_other integer, w_cash_before real, "
        "w_first_ts integer, w_last_ts integer, w_median_cash real, w_max_cash real, eligible integer, u_thin integer, u_dormant integer, "
        "u_ooc integer, tier1 integer")


def implied(oi, price, side_oi):
    """Price of token `side_oi` implied by a fill of token `oi` at `price`."""
    return price if oi == side_oi else 1.0 - price


def main():
    uni = {}
    for l in open(os.path.join(ETUDE, "derived", "universe_markets.jsonl")):
        m = json.loads(l); uni[m["condition_id"]] = m
    src = sqlite3.connect("file:" + os.path.join(ETUDE, "data", "fills_all.sqlite") + "?mode=ro", uri=True, timeout=60)
    status = dict(src.execute("select status, count(*) from conds group by status"))
    cinfo = {r[0]: uni[r[1]] for r in src.execute("select id, condition_id from conds where status='ok'")}
    addr = dict(src.execute("select id, address from wallets"))
    final_path = os.path.join(ETUDE, "derived", "entries.sqlite"); out_path = final_path + ".tmp"
    if os.path.exists(out_path):
        os.remove(out_path)
    out = sqlite3.connect(out_path)
    out.execute(f"create table entries({COLS})")
    out.execute("create table entry_post(id integer primary key, buy_cash_1h real, buy_cash_24h real, follow_price real, follow_dt integer)")
    mk_ts, mk_yes = collections.defaultdict(list), collections.defaultdict(list)       # market -> times and YES prices of its fills
    mk_rows = collections.defaultdict(list)                                           # market -> (ts, wallet, oi, side, cash)
    tok_entries = collections.defaultdict(list)                                       # (market, oi) -> (ts, wallet)
    w_mk = collections.defaultdict(set)                                               # wallet -> markets with a fill
    w_cash = collections.defaultdict(list)                                            # wallet -> sorted cash of its fills
    w_span = {}                                                                       # wallet -> [first ts, last ts, total cash]
    seen, rows, c = set(), [], collections.Counter()
    pending_post = []                                                                 # (entry id, market, oi, wallet, t)

    def flush_group(group):
        for ts, w, cd, oi, side, size, price, tx in group:              # 1. entries of this second, from the state before it
            if side != 1 or (w, cd, oi) in seen:
                continue
            seen.add((w, cd, oi)); m = cinfo[cd]; cash = size * price; c["entries"] += 1
            times, yes = mk_ts[cd], mk_yes[cd]
            prev = implied(0, yes[-1], oi) if yes else None
            i1, i24 = bisect.bisect_right(times, ts - H1), bisect.bisect_right(times, ts - H24)
            p1 = implied(0, yes[i1 - 1], oi) if i1 else None
            p24 = implied(0, yes[i24 - 1], oi) if i24 else None
            recent = [r for r in mk_rows[cd][bisect.bisect_left(times, ts - H24):] if r[1] != w]
            f6 = sum(1 for r in recent if r[0] >= ts - H6)
            side_cash = sum(r[4] for r in recent if r[2] == oi and r[3] == 1)
            co = len({x[1] for x in tok_entries[(cd, oi)] if x[0] >= ts - H6 and x[1] != w})
            cashes, span = w_cash[w], w_span.get(w); n_other = len(w_mk[w]) - (cd in w_mk[w])
            med = (cashes[len(cashes) // 2] if len(cashes) % 2 else (cashes[len(cashes) // 2 - 1] + cashes[len(cashes) // 2]) / 2) if cashes else None
            eligible = int(price <= PRICE_MAX and ts < m["end_ts"] + grace(m["end_ts"]))
            u_thin = int(n_other <= THIN_MARKETS)
            u_dormant = int(span is not None and ts - span[1] >= DORMANT_S)
            u_ooc = int(len(cashes) >= OOC_MIN_PRIOR and cash >= OOC_MULT * med and cash > cashes[-1])
            tier1 = int(eligible and (u_thin or u_dormant or u_ooc))
            c["eligible"] += eligible; c["tier1"] += tier1; c[f"eligible_{m['group']}"] += eligible
            rows.append((None, ts, w, addr[w], cd, m["condition_id"], str(m["event_id"]), m["group"], oi, price, size, cash, "0x" + tx.hex(),
                         (m["end_ts"] - ts) / 3600.0, (ts - m["start_ts"]) / 3600.0 if m.get("start_ts") else None, prev,
                         (ts - times[-1]) if times else None, p1, p24, len(times), len(recent), sum(r[4] for r in recent), f6, side_cash, co,
                         len(cashes), n_other, span[2] if span else 0.0, span[0] if span else None, span[1] if span else None,
                         med, cashes[-1] if cashes else None, eligible, u_thin, u_dormant, u_ooc, tier1))
        for ts, w, cd, oi, side, size, price, tx in group:              # 2. then the state takes the fills of this second
            mk_ts[cd].append(ts); mk_yes[cd].append(implied(oi, price, 0)); mk_rows[cd].append((ts, w, oi, side, size * price))
            w_mk[w].add(cd); bisect.insort(w_cash[w], size * price)
            sp = w_span.setdefault(w, [ts, ts, 0.0]); sp[1] = ts; sp[2] += size * price
            if side == 1:
                tok_entries[(cd, oi)].append((ts, w))

    group, cur = [], None
    # fills of one second are taken in the order the source served them (rowid), so the entry chosen inside a second is fixed
    for r in src.execute("select ts, wallet, cond, outcome_index, side, size, price, tx from fills order by ts, rowid"):
        c["fills"] += 1
        if r[2] not in cinfo:
            c["fills_of_unknown_market"] += 1; continue
        if r[0] != cur and group:
            flush_group(group); group = []
        cur = r[0]; group.append(r)
        if len(rows) >= 50000:
            out.executemany("insert into entries values(" + ",".join("?" * 37) + ")", rows); rows.clear()
    if group:
        flush_group(group)
    out.executemany("insert into entries values(" + ",".join("?" * 37) + ")", rows); out.commit()
    # what followed each entry: kept apart, used only when results are read
    post = []
    for eid, t, w, cd, oi in out.execute("select id, t, wallet, cond, oi from entries"):
        times = mk_ts[cd]; i = bisect.bisect_left(times, t); b1 = b24 = 0.0; fp = fdt = None
        for ts2, w2, oi2, side2, cash2 in mk_rows[cd][i:]:
            if ts2 > t + H24:
                break
            if w2 == w and oi2 == oi and side2 == 1:
                b24 += cash2; b1 += cash2 if ts2 <= t + H1 else 0.0
            elif fp is None and w2 != w and ts2 >= t + 300:
                j = bisect.bisect_left(times, ts2)
                fp, fdt = implied(0, mk_yes[cd][j], oi), ts2 - t
        post.append((eid, b1, b24, fp, fdt))
    out.executemany("insert into entry_post values(?,?,?,?,?)", post)
    out.execute("create index e_wallet on entries(wallet, t)"); out.execute("create index e_event on entries(event_id, t)"); out.commit()
    # wallets whose full history is read next: every wallet with a tier-1 entry in the INFO group, and a hash sample of the others
    info = {r[0] for r in out.execute("select distinct address from entries where tier1=1 and grp='INFO'")}
    pub = {r[0] for r in out.execute("select distinct address from entries where tier1=1 and grp='PUBLIC_PROCESS'")} - info
    pub_s = {a for a in pub if int(hashlib.sha256(a.encode()).hexdigest(), 16) % 100 < PUBLIC_SAMPLE_PCT}
    with open(os.path.join(ETUDE, "derived", "tier1_wallets.txt"), "w") as f:
        f.write("\n".join(sorted(info | pub_s)) + "\n")
    c = dict(c, markets_ok=len(cinfo), markets_status=status, tier1_wallets_info=len(info), tier1_wallets_public_only=len(pub),
             tier1_wallets_public_sampled=len(pub_s), wallets_with_entry=out.execute("select count(distinct wallet) from entries").fetchone()[0])
    out.close(); os.replace(out_path, final_path)                      # written whole, then put in place
    json.dump(c, open(os.path.join(ETUDE, "derived", "entries_counts.json"), "w"), indent=1)
    print(json.dumps(c, indent=1))


if __name__ == "__main__":
    sys.exit(main())
