"""ana_99: every funding transfer behind the links of feat_40, not only the first one met. No outcome is read.

Amendment 002. The frozen feat_40 records, for each (wallet, root key, deposit), the first transfer it meets
(`evidence.setdefault`), so a key that paid a wallet twice before one deposit shows one amount in derived/groups.sqlite
and in the export of ana_97. This script runs the frozen rule itself, feat_40.build_links on the inputs feat_40.main
reads, with an evidence store that keeps every transfer. It changes no link, no class and no test:
  - it keeps only the (entry, wallet, root, deposit) links that feat_40 wrote to derived/groups.sqlite (the fan-out
    rule there is applied as of each entry);
  - it refuses to write anything if a link of groups.sqlite is not found again, or if the first transfer it finds for a
    link is not the one feat_40 stored.

Output: derived/export/financial_links_transfers.csv (one row per link and transfer, keys behind two wallets or more)
and derived/export/financial_links_transfers_summary.json (counts over every link, totals per key)."""
import collections, csv, json, os, sqlite3, sys, time

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ETUDE, "code"))
import feat_40_groups as F      # noqa: E402  (the frozen rule)

D = lambda *p: os.path.join(ETUDE, "derived", *p)


class AllTransfers(dict):
    """Evidence store for feat_40.build_links: keeps every transfer noted under a key, in the order build_links meets them."""
    def setdefault(self, key, ev):
        lst = dict.setdefault(self, key, [])
        if ev not in lst:       # shortcut: two identical transfers (same tx, block, value) in one transaction count once; rows carry no log index
            lst.append(ev)
        return lst[0]


def load():
    """The inputs of feat_40.main, read the same way (read-only)."""
    fun = sqlite3.connect("file:" + os.path.join(ETUDE, "data", "funding.sqlite") + "?mode=ro", uri=True, timeout=60)
    payers = {r[0]: r[1:] for r in fun.execute("select address, is_contract, nonce_today, tags, tags_status from payers")}
    hops = collections.defaultdict(list)
    for payer, block, rows in fun.execute("select payer, block, rows from hops where status='ok'"):
        for r in json.loads(rows):
            if r not in hops[payer]:
                hops[payer].append(r)
    todo_rows = [json.loads(l) for l in open(D("funding_todo.jsonl"))]
    current = {(e["wallet"], d[2]) for e in todo_rows for d in e["deposits"]}
    dep = collections.defaultdict(list)
    for wallet, tx, ts, payer, block in fun.execute("select wallet, tx, ts, payer, block from deposits where status='ok' and payer is not null"):
        if (wallet, tx) in current:
            dep[wallet].append((ts, tx, payer, block))
    inflows = {(r[0], r[1]): json.loads(r[2]) for r in fun.execute("select wallet, tx, rows from inflows where status='ok'") if (r[0], r[1]) in current}
    return dep, payers, dict(hops), inflows


def gather(frozen_rows, evidence):
    """frozen_rows: rows of groups.sqlite roots. Returns (links with every transfer, problems)."""
    out, problems = [], []
    for eid, wallet, root, kind, tx, fan, ftx, fblock, fvalue, through in frozen_rows:
        evs = evidence.get((wallet, root, tx))
        if not evs:
            problems.append(f"link not found again: entry {eid} {wallet} {root} {tx}"); continue
        first = evs[0]
        if (first.get("funding_tx"), first.get("block"), first.get("value"), first.get("through")) != (ftx, fblock, fvalue, through):
            problems.append(f"first transfer differs from feat_40: entry {eid} {wallet} {root} {tx}"); continue
        out.append({"id": eid, "wallet": wallet, "root": root, "kind": kind, "deposit_tx": tx, "fanout": fan, "transfers": evs})
    return out, problems


def per_key_totals(links):
    """Distinct transfers of each (root, wallet): a transfer inside the windows of two deposits counts once."""
    seen = collections.defaultdict(dict)
    for l in links:
        for ev in l["transfers"]:
            seen[(l["root"], l["wallet"])][(ev.get("funding_tx"), ev.get("block"), ev.get("value"), ev.get("through"))] = ev
    return seen


def main():
    dep, payers, hops, inflows = load()
    evidence = AllTransfers()
    F.build_links(dep, payers, hops, collections.Counter(), inflows, evidence)
    grp = sqlite3.connect("file:" + D("groups.sqlite") + "?mode=ro", uri=True)
    frozen = grp.execute("select id, wallet, root, kind, tx, fanout, funding_tx, funding_block, funding_value, through from roots").fetchall()
    links, problems = gather(frozen, evidence)
    if problems:
        sys.exit("refused, the frozen links are not found again:\n" + "\n".join(problems[:20]))
    ent = sqlite3.connect("file:" + D("entries.sqlite") + "?mode=ro", uri=True)
    slug = {str(v["event_id"]): v["event_slug"] for v in map(json.loads, open(D("universe_markets.jsonl")))}
    info = {r[0]: r[1:] for r in ent.execute("select id, t, event_id, condition_id, oi, price, cash from entries where tier1=1")}
    flags = {r[0]: r[1:] for r in grp.execute("select id, c4, c5 from groups")}
    wallets_of = collections.defaultdict(set)
    for l in links:
        wallets_of[l["root"]].add(l["wallet"])
    utc = lambda t: time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t))
    how = {0: "paid the deposit", 2: "sent the money that was swapped into the deposit", 1: "paid a pass-through key"}
    rows = []
    for l in links:
        if len(wallets_of[l["root"]]) < 2:
            continue
        t, ev, cond, oi, price, cash = info[l["id"]]
        for i, x in enumerate(l["transfers"]):
            rows.append({"root_key": l["root"], "wallets_of_this_key": len(wallets_of[l["root"]]), "wallet": l["wallet"], "how": how[l["kind"]],
                         "transfer_rank": i + 1, "transfers_of_this_link": len(l["transfers"]), "pass_through_key": x.get("through") or "",
                         "funding_tx": x.get("funding_tx") or "", "funding_block": x.get("block") or "",
                         "funding_usd": round(x["value"] / 1e6, 2) if x.get("value") else "", "deposit_tx": l["deposit_tx"], "entry_utc": utc(t),
                         "event": slug.get(str(ev), str(ev)), "condition_id": cond, "side": "Yes" if oi == 0 else "No", "entry_price": round(price, 4),
                         "entry_usd": round(cash, 2), "same_event_group_alert": flags.get(l["id"], (0, 0))[0], "recurrent_funder_alert": flags.get(l["id"], (0, 0))[1]})
    rows.sort(key=lambda r: (-r["wallets_of_this_key"], r["root_key"], r["entry_utc"], r["wallet"], r["transfer_rank"]))
    os.makedirs(D("export"), exist_ok=True)
    tmp = D("export", "financial_links_transfers.csv.tmp")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["root_key"]); w.writeheader(); w.writerows(rows)
    os.replace(tmp, D("export", "financial_links_transfers.csv"))
    totals = per_key_totals(links)
    usd = lambda evs: round(sum(e["value"] for e in evs if e.get("value")) / 1e6, 2)
    first_only = {}
    for l in links:                                      # what the frozen export adds up: the first transfer of each link
        first_only.setdefault((l["root"], l["wallet"]), {})[(l["transfers"][0].get("funding_tx"), l["transfers"][0].get("block"))] = l["transfers"][0]
    multi = [l for l in links if len(l["transfers"]) > 1]
    summary = {"links_of_groups_sqlite": len(frozen), "links_found_again": len(links),
               "links_with_more_than_one_transfer": len(multi),
               "links_with_more_than_one_transfer_by_kind": dict(collections.Counter(how[l["kind"]] for l in multi)),
               "links_without_a_stored_value": sum(1 for l in links if not any(e.get("value") for e in l["transfers"])),
               "key_wallet_pairs": len(totals),
               "key_wallet_pairs_undercounted_by_the_frozen_export": sum(1 for k in totals if usd(totals[k].values()) > usd(first_only[k].values())),
               "usd_all_transfers": round(sum(usd(v.values()) for v in totals.values()), 2),
               "usd_first_transfer_only": round(sum(usd(v.values()) for v in first_only.values()), 2),
               "keys_behind_two_wallets_or_more": {r: {"wallets": len(ws), "distinct_transfers": sum(len(totals[(r, w)]) for w in ws),
                                                       "usd_all_transfers": round(sum(usd(totals[(r, w)].values()) for w in ws), 2),
                                                       "usd_first_transfer_only": round(sum(usd(first_only[(r, w)].values()) for w in ws), 2)}
                                                   for r, ws in sorted(wallets_of.items()) if len(ws) >= 2},
               "rows_written": len(rows)}
    json.dump(summary, open(D("export", "financial_links_transfers_summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


def _selftest():
    payers = {"0xk": (0, 3, "[]", "ok"), "0xpool": (1, 1, "[]", "ok")}
    dep = {"w": [(500, "d1", "0xpool", 100)]}
    inflows = {("w", "d1"): [{"from": "0xk", "block": 90, "tx": "a", "value": 10}, {"from": "0xk", "block": 95, "tx": "b", "value": 20},
                             {"from": "0xk", "block": 95, "tx": "b", "value": 20}]}
    first = {}
    F.build_links(dep, payers, {}, collections.Counter(), inflows, first)
    every = AllTransfers()
    F.build_links(dep, payers, {}, collections.Counter(), inflows, every)
    assert first[("w", "0xk", "d1")]["value"] == 10                                   # the frozen store keeps the first transfer
    assert [e["value"] for e in every[("w", "0xk", "d1")]] == [10, 20]                 # this one keeps both, a repeated row once
    frozen = [(1, "w", "0xk", 2, "d1", 1, "a", 90, 10, None)]
    links, problems = gather(frozen, every)
    assert not problems and len(links[0]["transfers"]) == 2
    _, bad = gather([(1, "w", "0xk", 2, "d1", 1, "b", 95, 20, None)], every)
    assert bad and "differs" in bad[0]                                                 # a first transfer that is not feat_40's is refused
    _, bad = gather([(1, "w", "0xz", 2, "d1", 1, "a", 90, 10, None)], every)
    assert bad and "not found" in bad[0]
    # one transfer inside the windows of two deposits of the same wallet counts once
    tot = per_key_totals([{"root": "0xk", "wallet": "w", "transfers": [{"funding_tx": "a", "block": 90, "value": 10, "through": None}]},
                          {"root": "0xk", "wallet": "w", "transfers": [{"funding_tx": "a", "block": 90, "value": 10, "through": None}]}])
    assert len(tot[("0xk", "w")]) == 1
    print("ana_99 selftest ok")


if __name__ == "__main__":
    _selftest() if sys.argv[1:] == ["selftest"] else main()
