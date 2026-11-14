"""feat_40: funding roots of the entries and the two group classes. No outcome is read.

A ROOT of an entry is a plain key behind one of the wallet's deposits of the 24 hours before the entry: the apparent
payer of the deposit; or, when the deposit is the wallet's own money being swapped by a contract, a sender of the
collateral the wallet received in the 10,000 blocks before it; or, behind either of them, the sender that paid a
pass-through key (a key with almost no transaction of its own) in the 10,000 blocks before.
A PLAIN KEY is an address with no code, no public name tag, fewer than 1,000 transactions sent (read today), and which,
at the time considered, had paid at most FANOUT_MAX distinct wallets of this dataset. Everything else is a service.

C4_COFUNDED_GROUP   at the entry of a wallet: another wallet with the same root entered a market of the same event in the
                    7 days before. The alert is the entry that completes the pair; the earlier entry is not an alert.
C5_RECURRENT_FUNDER at the entry of a wallet: its root had paid another wallet that entered a market of a DIFFERENT event
                    at least 7 days earlier.
Output: derived/groups.sqlite (tables roots, groups), derived/groups_counts.json."""
import collections, json, os, sqlite3

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FANOUT_MAX = 10
BUSY_NONCE = 1000
PASS_THROUGH_NONCE = 5
WINDOW = 10000                  # blocks before a deposit or a payment, as in col_40
WEEK = 7 * 86400


def build_links(deposits, payers, hops, counts, inflows=None, evidence=None):
    """deposits: {wallet: [(ts, tx, payer, block)]}; inflows: {(wallet, tx): [{"from", "block", "tx"}]} for deposits paid by a
    contract. Returns [(ts, wallet, root, kind, tx)] sorted by time; kind 0 = apparent payer, 2 = sender of what the wallet
    received before a swapped deposit, 1 = sender behind a pass-through key. With a dict as `evidence`, the transfer that
    makes each link is recorded there under (wallet, root, deposit tx): its transaction, block, value and, for kind 1, the
    pass-through key."""
    def person_like(a):                                 # no code, no tag, not busy; fan-out is checked later, as of each entry
        k = payers.get(a)
        if k is None:
            counts["address_not_described"] += 1; return False
        return k[0] == 0 and k[3] == "ok" and k[2] == "[]" and k[1] < BUSY_NONCE
    links = []

    def note(wallet, root, tx, **ev):
        if evidence is not None:
            evidence.setdefault((wallet, root, tx), ev)

    def add(ts, wallet, tx, sender, block, kind, row=None):
        if sender == wallet or not person_like(sender):
            return
        links.append((ts, wallet, sender, kind, tx))
        note(wallet, sender, tx, funding_tx=(row or {}).get("tx", tx), block=block, value=(row or {}).get("value"), through=None)
        if payers[sender][1] <= PASS_THROUGH_NONCE:
            for h in hops.get(sender, []):
                s = h.get("from", "").lower()
                if s and block - WINDOW <= h["block"] <= block and s not in (wallet, sender) and person_like(s):
                    links.append((ts, wallet, s, 1, tx))
                    note(wallet, s, tx, funding_tx=h.get("tx"), block=h["block"], value=h.get("value"), through=sender)
    for wallet, ds in deposits.items():
        for ts, tx, payer, block in ds:
            add(ts, wallet, tx, payer, block, 0)
            for r in (inflows or {}).get((wallet, tx), []):
                if r["tx"] != tx and block - WINDOW <= r["block"] <= block:
                    add(ts, wallet, tx, r["from"].lower(), r["block"], 2, r)
    return sorted(set(links))


def classify(entries, links):
    """entries: [{"id", "wallet", "t", "event", "txs"}]. Returns ({id: (c4, c5, roots)}, counters); c4 and c5 are None or
    (other wallet, root). Entries are processed in time order, so each one sees only what came before it."""
    c = collections.Counter()
    by_wallet, by_root = collections.defaultdict(list), collections.defaultdict(list)
    for ts, wallet, root, hop, tx in links:
        by_wallet[wallet].append((ts, root, hop, tx)); by_root[root].append((ts, wallet))
    seen = collections.defaultdict(list)                # root -> (entry time, wallet, event) of earlier entries
    out = {}
    for e in sorted(entries, key=lambda e: (e["t"], e["id"])):
        mine = {}
        for ts, root, hop, tx in by_wallet.get(e["wallet"], ()):
            if tx in e["txs"] and ts < e["t"]:
                fo = len({w for dts, w in by_root[root] if dts < e["t"]})
                if fo <= FANOUT_MAX:
                    mine[root] = (hop, tx, fo)
                else:
                    c["root_dropped_fanout"] += 1
        c["entries"] += 1; c["entries_with_root"] += bool(mine)
        c4 = c5 = None
        for root in sorted(mine):
            for t2, w2, ev2 in seen[root]:
                if w2 == e["wallet"]:
                    continue
                if c4 is None and ev2 == e["event"] and e["t"] - WEEK <= t2 <= e["t"]:
                    c4 = (w2, root)
                if c5 is None and ev2 != e["event"] and t2 <= e["t"] - WEEK:
                    c5 = (w2, root)
        c["c4"] += c4 is not None; c["c5"] += c5 is not None
        out[e["id"]] = (c4, c5, mine)
        for root in mine:
            seen[root].append((e["t"], e["wallet"], e["event"]))
    return out, c


def main():
    ent = sqlite3.connect("file:" + os.path.join(ETUDE, "derived", "entries.sqlite") + "?mode=ro", uri=True)
    fun = sqlite3.connect("file:" + os.path.join(ETUDE, "data", "funding.sqlite") + "?mode=ro", uri=True, timeout=60)
    payers = {r[0]: r[1:] for r in fun.execute("select address, is_contract, nonce_today, tags, tags_status from payers")}
    hops, hop_read = collections.defaultdict(list), set()
    for payer, block, rows in fun.execute("select payer, block, rows from hops where status='ok'"):
        hop_read.add((payer, block))
        for r in json.loads(rows):                       # windows of one key can overlap: one row per transfer
            if r not in hops[payer]:
                hops[payer].append(r)
    hops = dict(hops)
    todo_rows = [json.loads(l) for l in open(os.path.join(ETUDE, "derived", "funding_todo.jsonl"))]
    current = {(e["wallet"], d[2]) for e in todo_rows for d in e["deposits"]}   # deposits read for earlier lists are not used
    dep = collections.defaultdict(list)
    for wallet, tx, ts, payer, block in fun.execute("select wallet, tx, ts, payer, block from deposits where status='ok' and payer is not null"):
        if (wallet, tx) in current:
            dep[wallet].append((ts, tx, payer, block))
    counts = collections.Counter(dict(fun.execute("select 'deposits_' || status, count(*) from deposits group by status")))
    counts.update(dict(fun.execute("select 'inflows_' || status, count(*) from inflows group by status")))
    inflows = {(r[0], r[1]): json.loads(r[2]) for r in fun.execute("select wallet, tx, rows from inflows where status='ok'") if (r[0], r[1]) in current}
    evidence = {}
    links = build_links(dep, payers, hops, counts, inflows, evidence)
    counts.update(collections.Counter(f"links_kind_{x[3]}" for x in links))
    event = dict(ent.execute("select id, event_id from entries where tier1=1"))
    status = {(r[0], r[1]): r[2:] for r in fun.execute("select wallet, tx, status, payer, block from deposits")}
    entries, complete = [], {}
    plain_pass = lambda a: a in payers and payers[a][0] == 0 and payers[a][3] == "ok" and payers[a][2] == "[]" and payers[a][1] <= PASS_THROUGH_NONCE

    def known(a, block):                                # described, and read one hop further when it is a pass-through key
        return a in payers and payers[a][3] == "ok" and (not plain_pass(a) or (a, block) in hop_read)
    for e in todo_rows:
        entries.append({"id": e["id"], "wallet": e["wallet"], "t": e["t"], "event": event[e["id"]], "txs": {d[2] for d in e["deposits"]}})
        ok = bool(e["deposits"])                        # a fresh entry with no deposit to trace is not complete
        for d in e["deposits"]:                         # every deposit read, its payer known, a swap's senders known
            st = status.get((e["wallet"], d[2]))
            if st is None or st[0] != "ok" or st[1] is None or not known(st[1], st[2]):
                ok = False
            elif payers[st[1]][0] == 1:
                rows = inflows.get((e["wallet"], d[2]))
                if rows is None or not all(known(r["from"], r["block"]) for r in rows if r["from"] != e["wallet"] and st[2] - WINDOW < r["block"] <= st[2]):
                    ok = False
        complete[e["id"]] = int(ok); counts["entries_funding_incomplete"] += int(not ok)
    res, c = classify(entries, links)
    wallet_of = {e["id"]: e["wallet"] for e in entries}
    counts.update(c); counts["links"] = len(links); counts["roots"] = len({x[2] for x in links})
    counts["roots_paying_two_wallets_or_more"] = sum(1 for n in collections.Counter(r for r, w in {(x[2], x[1]) for x in links}).values() if n >= 2)
    path = os.path.join(ETUDE, "derived", "groups.sqlite")
    if os.path.exists(path + ".tmp"):
        os.remove(path + ".tmp")
    out = sqlite3.connect(path + ".tmp")
    out.execute("create table roots(id integer, wallet text, root text, kind integer, tx text, fanout integer, funding_tx text, funding_block integer, "
                "funding_value integer, through text)")
    out.execute("create table groups(id integer primary key, n_roots integer, c4 integer, c4_other text, c4_root text, c5 integer, c5_other text, c5_root text, "
                "address text, t integer, complete integer)")
    t_of = {e["id"]: e["t"] for e in entries}
    for eid, (c4, c5, mine) in res.items():
        for r, (h, tx, fo) in mine.items():
            ev = evidence.get((wallet_of[eid], r, tx), {})
            out.execute("insert into roots values(?,?,?,?,?,?,?,?,?,?)", (eid, wallet_of[eid], r, h, tx, fo, ev.get("funding_tx"), ev.get("block"), ev.get("value"), ev.get("through")))
        out.execute("insert into groups values(?,?,?,?,?,?,?,?,?,?,?)", (eid, len(mine), int(c4 is not None), c4 and c4[0], c4 and c4[1],
                                                                        int(c5 is not None), c5 and c5[0], c5 and c5[1], wallet_of[eid], t_of[eid], complete[eid]))
    out.commit(); out.close(); os.replace(path + ".tmp", path)
    json.dump(dict(counts), open(os.path.join(ETUDE, "derived", "groups_counts.json"), "w"), indent=1)
    print(json.dumps(dict(counts), indent=1))


def _selftest():
    payers = {"0xf": (0, 3, "[]", "ok"), "0xsvc": (0, 5000, "[]", "ok"), "0xtag": (0, 2, '["Bridge"]', "ok"), "0xk": (0, 1, "[]", "ok"),
              "0xhub": (0, 40, "[]", "ok"), "0xc": (1, 1, "[]", "ok")}
    dep = {"w1": [(100, "t1", "0xf", 10)], "w2": [(200, "t2", "0xf", 20)], "w3": [(300, "t3", "0xsvc", 30)], "w4": [(310, "t4", "0xsvc", 31)],
           "w5": [(400, "t5", "0xk", 40)], "w6": [(410, "t6", "0xtag", 41)], "w7": [(420, "t7", "0xc", 42)], "w8": [(900000, "t8", "0xf", 50)]}
    hops = {"0xk": [{"from": "0xhub", "block": 39}, {"from": "0xhub", "block": 45}, {"from": "0xf", "block": 40 - WINDOW - 1}]}
    cnt = collections.Counter(); links = build_links(dep, payers, hops, cnt)
    assert (400, "w5", "0xhub", 1, "t5") in links and (400, "w5", "0xk", 0, "t5") in links and not any(x[2] in ("0xsvc", "0xtag", "0xc") for x in links)
    assert (400, "w5", "0xf", 1, "t5") not in links                      # paid the pass-through key too long before
    swapped = build_links({"w7": [(420, "t7", "0xc", 42)]}, payers, {}, collections.Counter(),
                          {("w7", "t7"): [{"from": "0xf", "block": 41, "tx": "t0"}, {"from": "0xc", "block": 42, "tx": "t7"}, {"from": "0xhub", "block": 42 - WINDOW - 5, "tx": "tz"}]})
    assert swapped == [(420, "w7", "0xf", 2, "t7")], swapped             # the key that sent the money before the swap; not the pool, not an old transfer
    E = lambda i, w, t, ev, tx: {"id": i, "wallet": w, "t": t, "event": ev, "txs": {tx}}
    res, c = classify([E(1, "w1", 150, "A", "t1"), E(2, "w2", 250, "A", "t2"), E(3, "w3", 350, "A", "t3"), E(4, "w4", 360, "A", "t4"),
                       E(5, "w8", 900100, "B", "t8")], links)
    assert res[1][0] is None and res[2][0] == ("w1", "0xf")            # the second wallet of the pair is the alert, not the first
    assert res[3][0] is None and res[4][0] is None                     # a busy key is a service: no link
    assert res[5][0] is None and res[5][1] == ("w1", "0xf")            # same root, another event, more than a week later
    assert res[2][1] is None and c["c4"] == 1 and c["c5"] == 1
    many = {f"x{i}": [(i, f"tx{i}", "0xf", i)] for i in range(12)}
    r2, c2 = classify([E(i, f"x{i}", 1000 + i, "A", f"tx{i}") for i in range(12)], build_links(many, payers, {}, collections.Counter()))
    assert c2["c4"] == 0 and c2["root_dropped_fanout"] == 12         # a key that paid 12 wallets is treated as a service
    print("groups selftest ok")


if __name__ == "__main__":
    import sys
    _selftest() if sys.argv[1:] == ["selftest"] else main()
