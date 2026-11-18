"""Funding links two and three intermediaries away. EXPLORATORY: written after the results of the frozen study were read;
it reads no outcome and changes no class, test or verdict.

    python3 -I scripts/links_multihop.py trace <study folder> <work folder>     network: logs of the collateral tokens
    python3 -I scripts/links_multihop.py report <study folder> <work folder>    writes the summary and the published edges
    python3 -I scripts/links_multihop.py selftest

Rules, fixed before the first run (started 14 November 2026, 18:25:12 UTC), all taken from the frozen study unless said:
  - depth 1 is the root of a link written by the frozen feat_40 (derived/groups.sqlite, table roots): the plain key that
    paid the deposit, sent the money swapped into it, or paid a pass-through key behind it;
  - from a plain key K that paid at block b, depth d + 1 reads the transfers of USDC, USDC.e and pUSD received by K in
    the WINDOW = 10,000 blocks before b (col_40's window), 1 USD or more, from any sender other than K, the wallet,
    the zero address and Polymarket's own contracts (chainfund.INFRA); at most depth 3;
  - a sender is a SERVICE when it has code, a public name tag, or 1,000 transactions or more (read today): it is counted,
    never followed and never a link (shared services such as exchanges, bridges, solvers pay unrelated people);
  - a plain key reached at depth 1 to 3 is DISCRIMINATING when it is an ancestor of 2 to 10 wallets of the dataset
    (FANOUT_MAX = 10 of feat_40; above 10 it is a hub and counted as a service);
  - groups are the connected sets of wallets that share a discriminating ancestor; the group classes are recounted with
    the frozen feat_40.classify on the extended links (fan-out as of each entry), and only their firing is counted.
Every discriminating edge (a transfer from a key to the next key or to a wallet) is read again from its receipt."""
import collections, json, os, sqlite3, sys, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINDOW = 10000
MAX_DEPTH = 3
FANOUT_MAX = 10
BUSY = 1000
MIN_VALUE = 1_000_000          # 1 USD in 6-decimal units
PUBLISHED_KEYS = {"0xe206961002feebd9edb152eed9b630a351874043"}   # the documented Nobel 2025 key, already published
CONTROL = {"wallets": ["0x5a8e6f7f", "0x870f371b"], "upstream_key": "0x36626bd83accd8c1e0b9268a9db98a2233fc8c55"}


def study_modules(study):
    sys.path.insert(0, os.path.join(study, "code"))
    import chainfund, col_40_funding as C, feat_40_groups as F      # the frozen code, read only
    return chainfund, C, F


def is_service(desc):
    """desc = (is_contract, nonce_today, tags json, tags_status). Unknown descriptions are never a link."""
    if desc is None or desc[3] != "ok" or desc[2] is None:
        return True
    return bool(desc[0]) or desc[2] != "[]" or desc[1] >= BUSY


def frontier_step(frontier, reads, desc, infra, depth):
    """frontier: {(key, block): set(wallets)}. reads: {(key, block): rows}. Returns (edges, next frontier, service counts).
    edges: (sender, key, block of transfer, tx, value, depth of sender)."""
    edges, nxt, svc = [], collections.defaultdict(set), collections.Counter()
    for (k, b), wallets in frontier.items():
        for r in reads.get((k, b)) or []:
            s = r["from"]
            if s == k or s in wallets or s in infra or r["value"] < MIN_VALUE or not (b - WINDOW <= r["block"] <= b):
                continue
            if is_service(desc.get(s)):
                svc["service_sender"] += 1; continue
            edges.append((s, k, r["block"], r["tx"], r["value"], depth))
            nxt[(s, r["block"])] |= wallets
    return edges, dict(nxt), svc


def components(ancestors):
    """ancestors: {wallet: {key: depth}}. Groups of wallets joined by keys with fan-out 2 to FANOUT_MAX."""
    by_key = collections.defaultdict(set)
    for w, ks in ancestors.items():
        for k in ks:
            by_key[k].add(w)
    disc = {k: ws for k, ws in by_key.items() if 2 <= len(ws) <= FANOUT_MAX}
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for ws in disc.values():
        ws = sorted(ws)
        for w in ws[1:]:
            parent[find(w)] = find(ws[0])
    groups = collections.defaultdict(set)
    for ws in disc.values():
        for w in ws:
            groups[find(w)].add(w)
    hubs = sum(1 for ws in by_key.values() if len(ws) > FANOUT_MAX)
    return [sorted(g) for g in groups.values()], disc, hubs


def trace(study, work):
    chainfund, C, F = study_modules(study)
    os.makedirs(work, exist_ok=True)
    db = sqlite3.connect(os.path.join(work, "multihop.sqlite"))
    db.executescript(C.SCHEMA + "create table if not exists reads(address text, block integer, status text, rows text, primary key(address, block));")
    fun = sqlite3.connect("file:" + os.path.join(study, "data", "funding.sqlite") + "?mode=ro", uri=True)
    grp = sqlite3.connect("file:" + os.path.join(study, "derived", "groups.sqlite") + "?mode=ro", uri=True)
    known = {r[0]: r[1:5] for r in fun.execute("select address, is_contract, nonce_today, tags, tags_status from payers")}
    frontier = collections.defaultdict(set)
    for wallet, root, block in grp.execute("select wallet, root, funding_block from roots where funding_block is not null"):
        frontier[(root, block)].add(wallet)
    counts = collections.Counter()
    for depth in range(2, MAX_DEPTH + 1):
        todo = [(k, b) for (k, b) in frontier if db.execute("select 1 from reads where address=? and block=? and status='ok'", (k, b)).fetchone() is None]
        counts[f"reads_depth_{depth}"] = len(frontier); counts[f"reads_new_depth_{depth}"] = len(todo)
        t0 = time.time()

        def done(key, status, rows):
            with db:
                db.execute("insert or replace into reads values(?,?,?,?)", (key[0], key[1], status, json.dumps(rows)))
        C.transfers_in([((k, b), k, b - WINDOW, b) for k, b in todo], done)
        print(f"depth {depth}: {len(todo)} reads in {time.time() - t0:.0f} s", flush=True)
        reads = {(a, b): json.loads(r) for a, b, s, r in db.execute("select address, block, status, rows from reads where status='ok'")}
        counts[f"reads_failed_depth_{depth}"] = sum(1 for k in frontier if k not in reads)
        senders = {r["from"] for k in frontier for r in reads.get(k) or []} - set(known)
        mine = {r[0] for r in db.execute("select address from payers")}
        C.describe(db, sorted(senders - mine))
        desc = dict(known); desc.update({r[0]: r[1:5] for r in db.execute("select address, is_contract, nonce_today, tags, tags_status from payers")})
        edges, nxt, svc = frontier_step(frontier, reads, desc, chainfund.INFRA, depth)
        counts.update({f"{k}_depth_{depth}": v for k, v in svc.items()})
        with db:
            db.execute("create table if not exists edges(sender text, key text, block integer, tx text, value integer, depth integer, wallets text)")
            db.execute("delete from edges where depth=?", (depth,))
            for e in edges:
                db.execute("insert into edges values(?,?,?,?,?,?,?)", e + (json.dumps(sorted(nxt[(e[0], e[2])])),))
        counts[f"edges_depth_{depth}"] = len(edges)
        frontier = collections.defaultdict(set, nxt)
    json.dump(dict(counts), open(os.path.join(work, "trace_counts.json"), "w"), indent=1)
    print(json.dumps(dict(counts), indent=1))


def report(study, work):
    chainfund, C, F = study_modules(study)
    sys.path.insert(0, os.path.join(HERE, "scripts"))
    from links_transfers import receipt, STABLES, TRANSFER
    db = sqlite3.connect("file:" + os.path.join(work, "multihop.sqlite") + "?mode=ro", uri=True)
    grp = sqlite3.connect("file:" + os.path.join(study, "derived", "groups.sqlite") + "?mode=ro", uri=True)
    fun = sqlite3.connect("file:" + os.path.join(study, "data", "funding.sqlite") + "?mode=ro", uri=True)
    ent = sqlite3.connect("file:" + os.path.join(study, "derived", "entries.sqlite") + "?mode=ro", uri=True)
    roots = grp.execute("select id, wallet, root, kind, tx, funding_block, funding_tx, funding_value, through from roots").fetchall()
    edges = db.execute("select sender, key, block, tx, value, depth, wallets from edges").fetchall()
    ancestors = collections.defaultdict(dict)
    for _, w, root, *_ in roots:
        ancestors[w][root] = 1
    for s, k, b, tx, v, d, ws in edges:
        for w in json.loads(ws):
            if s not in ancestors[w] or ancestors[w][s] > d:
                ancestors[w][s] = d
    groups, disc, hubs = components(ancestors)
    join_depth = {k: max(ancestors[w][k] for w in ws) for k, ws in disc.items()}     # the farthest wallet decides how far the link is
    depth_of_group = [min(join_depth[k] for k, ws in disc.items() if ws & set(g)) for g in groups]
    # the group classes recounted on the extended links, with the frozen classify (fan-out as of each entry)
    ts_of = {(w, tx): ts for w, tx, ts in fun.execute("select wallet, tx, ts from deposits")}
    links = set()
    for _, w, root, kind, tx, *_ in roots:
        if (w, tx) in ts_of:
            links.add((ts_of[(w, tx)], w, root, kind, tx))
            for k, d in ancestors[w].items():
                if d >= 2:
                    links.add((ts_of[(w, tx)], w, k, 10 + d, tx))
    todo = [json.loads(l) for l in open(os.path.join(study, "derived", "funding_todo.jsonl"))]
    ev = dict(ent.execute("select id, event_id from entries where tier1=1"))
    entries = [{"id": e["id"], "wallet": e["wallet"], "t": e["t"], "event": ev[e["id"]], "txs": {d[2] for d in e["deposits"]}} for e in todo]
    res1, c1 = F.classify(entries, sorted({x for x in links if x[3] < 10}))
    res3, c3 = F.classify(entries, sorted(links))
    sets, documented, wallet_entries = {}, set(), collections.defaultdict(list)
    for line in open(os.path.join(study, "derived", "analytic_table.jsonl")):
        r = json.loads(line)
        sets[r["id"]] = f'{r["set"]}_{r["grp"]}'
        if r["documented"]:
            documented.add(r["id"])
    for e in entries:
        wallet_entries[e["wallet"]].append(e)
    described = []
    for g, d in sorted(zip(groups, depth_of_group), key=lambda x: (-len(x[0]), x[1])):
        es = [e for w in g for e in wallet_entries[w]]
        evs = collections.Counter(e["event"] for e in es)
        same = any(a["wallet"] != b["wallet"] and a["event"] == b["event"] and abs(a["t"] - b["t"]) <= 7 * 86400 for a in es for b in es)
        described.append({"wallets": len(g), "join_depth": d, "events": len(evs), "entries": len(es), "two_wallets_on_one_event_within_7_days": same,
                          "sets": dict(collections.Counter(sets.get(e["id"], "not_in_table") for e in es)),
                          "entries_on_an_event_of_a_documented_case": sum(e["id"] in documented for e in es)})
    fire = lambda res, i: collections.Counter(sets.get(eid, "not_in_table") for eid, v in res.items() if v[i] is not None)
    # receipts of every discriminating edge, and of the depth-1 transfers of the keys that join a group
    check = []
    for s, k, b, tx, v, d, ws in edges:
        if s in disc:
            check.append((tx, s, k, v, d))
    for _, w, root, kind, tx, fb, ftx, fv, through in roots:
        if root in disc and ftx and fv:
            check.append((ftx, root, through or w, fv, 1))
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    status = collections.Counter(); seen = set(); detail = []
    for tx, s, k, v, d in check:
        if (tx, s, k, v) in seen:
            continue
        seen.add((tx, s, k, v))
        rec = receipt(tx)
        ok = rec is not None and any(l.get("address", "").lower() in STABLES and (l.get("topics") or [None])[0] == TRANSFER and len(l["topics"]) == 3
                                     and l["topics"][1].lower() == pad(s) and l["topics"][2].lower() == pad(k) and int(l["data"], 16) == v for l in rec.get("logs") or [])
        st = "not served" if rec is None else ("confirmed" if ok else "NOT confirmed")
        status[st] += 1
        if s in PUBLISHED_KEYS or k in PUBLISHED_KEYS:
            detail.append({"tx": tx, "from": s, "to": k, "usd": v / 1e6, "depth": d, "receipt": st})
    ctrl = [w for w in ancestors if any(w.startswith(p) for p in CONTROL["wallets"])]
    ctrl_group = [g for g in groups if all(w in g for w in ctrl)] if len(ctrl) == len(CONTROL["wallets"]) else []
    summary = {
        "rules": {"window_blocks": WINDOW, "max_depth": MAX_DEPTH, "fanout_max": FANOUT_MAX, "busy_nonce": BUSY, "min_usd": MIN_VALUE / 1e6},
        "trace_counts": json.load(open(os.path.join(work, "trace_counts.json"))),
        "wallets_traced": len(ancestors),
        "discriminating_keys_by_join_depth": dict(sorted(collections.Counter(join_depth.values()).items())),
        "hub_keys_over_fanout": hubs,
        "groups_by_size": dict(sorted(collections.Counter(len(g) for g in groups).items())),
        "groups_by_joining_depth": dict(sorted(collections.Counter(depth_of_group).items())),
        "groups": described,
        "c4_entries_by_set": {"depth_1_frozen_rule": dict(fire(res1, 0)), "depth_1_to_3": dict(fire(res3, 0))},
        "c5_entries_by_set": {"depth_1_frozen_rule": dict(fire(res1, 1)), "depth_1_to_3": dict(fire(res3, 1))},
        "receipts_of_discriminating_edges": dict(status),
        "positive_control_nobel_second_network": {"wallets_found": len(ctrl), "joined_in_one_group": bool(ctrl_group),
                                                   "upstream_key": CONTROL["upstream_key"], "through_key": CONTROL["upstream_key"] in disc, "group_size": len(ctrl_group[0]) if ctrl_group else None},
        "published_key_edges": detail,
        "outcomes_read": False}
    json.dump(summary, open(os.path.join(HERE, "data", "links_multihop_summary.json"), "w"), indent=1)
    private = {"groups": groups, "discriminating_keys": {k: sorted(ws) for k, ws in disc.items()}}
    json.dump(private, open(os.path.join(work, "groups_private.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "published_key_edges"}, indent=1))


def selftest():
    infra = {"0xpm"}
    desc = {"0xk2": (0, 3, "[]", "ok"), "0xcex": (0, 50000, "[]", "ok"), "0xpool": (1, 1, "[]", "ok"), "0xtag": (0, 2, '["Bridge"]', "ok")}
    reads = {("0xk1", 100): [{"from": "0xk2", "block": 95, "tx": "a", "value": 5_000_000}, {"from": "0xcex", "block": 96, "tx": "b", "value": 9_000_000},
                             {"from": "0xpool", "block": 97, "tx": "c", "value": 9_000_000}, {"from": "0xtag", "block": 97, "tx": "d", "value": 9_000_000},
                             {"from": "0xpm", "block": 97, "tx": "e", "value": 9_000_000}, {"from": "0xk2", "block": 98, "tx": "f", "value": 10},
                             {"from": "0xk2", "block": 100 - WINDOW - 1, "tx": "g", "value": 9_000_000}, {"from": "0xnew", "block": 99, "tx": "h", "value": 9_000_000}]}
    edges, nxt, svc = frontier_step({("0xk1", 100): {"w1"}}, reads, desc, infra, 2)
    assert [e[:4] for e in edges] == [("0xk2", "0xk1", 95, "a")], edges          # a plain key, in the window, 1 USD or more
    assert svc["service_sender"] == 4 and nxt == {("0xk2", 95): {"w1"}}          # exchange, pool, tagged, undescribed: services
    g, disc, hubs = components({"w1": {"0xa": 1, "0xup": 2}, "w2": {"0xb": 1, "0xup": 2}, "w3": {"0xc": 1}, **{f"x{i}": {"0xhub": 3} for i in range(11)}})
    assert g == [["w1", "w2"]] and set(disc) == {"0xup"} and hubs == 1             # a shared key two hops up joins w1 and w2; a hub of 11 does not
    print("links_multihop selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1:2]
    if cmd == ["selftest"]:
        selftest()
    elif cmd == ["trace"]:
        trace(sys.argv[2], sys.argv[3])
    elif cmd == ["report"]:
        report(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
