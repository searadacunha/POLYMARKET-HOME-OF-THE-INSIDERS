"""ana_97: the funding links that involve more than one wallet, as a table with its evidence. No outcome is read.

A group is a plain key (no code, no public tag, fewer than 1,000 transactions, at most 10 wallets paid as of the entry)
behind the deposits of two wallets or more of this dataset. For each link: the wallet, the key, the transaction in which
the key paid (the wallet, or a pass-through key), its block and value, the deposit it explains, and the entry it precedes.

Output: derived/export/financial_links.csv and derived/export/financial_links_summary.json."""
import collections, csv, json, os, sqlite3, time

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ETUDE, "derived", *p)


def main():
    os.makedirs(D("export"), exist_ok=True)
    grp = sqlite3.connect("file:" + D("groups.sqlite") + "?mode=ro", uri=True)
    ent = sqlite3.connect("file:" + D("entries.sqlite") + "?mode=ro", uri=True)
    slug = {str(v["event_id"]): v["event_slug"] for v in map(json.loads, open(D("universe_markets.jsonl")))}
    info = {r[0]: r[1:] for r in ent.execute("select id, t, event_id, condition_id, oi, price, cash, grp from entries where tier1=1")}
    rows = grp.execute("select id, wallet, root, kind, tx, fanout, funding_tx, funding_block, funding_value, through from roots").fetchall()
    by_root = collections.defaultdict(set)
    for r in rows:
        by_root[r[2]].add(r[1])
    groups = {root: ws for root, ws in by_root.items() if len(ws) >= 2}
    flags = {r[0]: r[1:] for r in grp.execute("select id, c4, c5 from groups")}
    utc = lambda t: time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t))
    how = {0: "paid the deposit", 2: "sent the money that was swapped into the deposit", 1: "paid a pass-through key"}
    out = []
    for eid, wallet, root, kind, tx, fan, ftx, fblock, fvalue, through in rows:
        if root not in groups:
            continue
        t, ev, cond, oi, price, cash, family = info[eid]
        out.append({"root_key": root, "wallets_of_this_key": len(groups[root]), "wallet": wallet, "how": how[kind], "pass_through_key": through or "",
                    "funding_tx": ftx or "", "funding_block": fblock or "", "funding_usd": round(fvalue / 1e6, 2) if fvalue else "", "deposit_tx": tx,
                    "entry_utc": utc(t), "event": slug.get(str(ev), str(ev)), "family": family, "condition_id": cond, "side": "Yes" if oi == 0 else "No",
                    "entry_price": round(price, 4), "entry_usd": round(cash, 2), "same_event_group_alert": flags.get(eid, (0, 0))[0],
                    "recurrent_funder_alert": flags.get(eid, (0, 0))[1]})
    out.sort(key=lambda r: (-r["wallets_of_this_key"], r["root_key"], r["entry_utc"]))
    with open(D("export", "financial_links.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["root_key"]); w.writeheader(); w.writerows(out)
    sizes = collections.Counter(len(ws) for ws in groups.values())
    same_event = sum(1 for root in groups if any(r["root_key"] == root and r["same_event_group_alert"] for r in out))
    summary = {"plain_keys_behind_a_deposit": len(by_root), "keys_behind_two_wallets_or_more": len(groups), "groups_by_number_of_wallets": dict(sorted(sizes.items())),
               "groups_with_two_wallets_on_one_event_within_7_days": same_event, "links_listed": len(out),
               "entries_with_a_plain_key": len({r[0] for r in rows}), "entries_traced": grp.execute("select count(*) from groups").fetchone()[0],
               "links_by_how": dict(collections.Counter(r["how"] for r in out))}
    json.dump(summary, open(D("export", "financial_links_summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
