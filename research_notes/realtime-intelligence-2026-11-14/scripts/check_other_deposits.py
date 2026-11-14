"""What the export of amendment 002 still leaves out: transfers behind a second deposit of one entry and one key.

    python3 -I scripts/check_other_deposits.py <study folder>     (no network) -> data/links_other_deposits.json

feat_40 keeps one deposit per entry and root key (`mine[root] = (hop, tx, fo)`), so ana_99, which completes the links
feat_40 stored, does not see the transfers behind the other deposits of the same entry from the same key. This script
reruns the frozen feat_40.build_links with the evidence store of ana_99, and counts the distinct transfers behind every
deposit of an entry linked to a root of that entry, minus those already in the export. Descriptive; no test."""
import collections, json, os, sqlite3, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUP_KEY_PREFIXES = ("0xe2069610", "0x6ae40b5b")        # the two keys behind two wallets or more (FINANCIAL_LINKS.md)


def main(study):
    sys.path.insert(0, os.path.join(study, "code"))
    import ana_99_links_all_transfers as A, feat_40_groups as F      # the frozen code, read only
    dep, payers, hops, inflows = A.load()
    ev = A.AllTransfers()
    links = F.build_links(dep, payers, hops, collections.Counter(), inflows, ev)
    todo = [json.loads(l) for l in open(os.path.join(study, "derived", "funding_todo.jsonl"))]
    grp = sqlite3.connect("file:" + os.path.join(study, "derived", "groups.sqlite") + "?mode=ro", uri=True)
    rows = grp.execute("select id, wallet, root, tx from roots").fetchall()
    kept = {(eid, root) for eid, _, root, _ in rows}
    key = lambda x: (x.get("funding_tx"), x.get("block"), x.get("value"), x.get("through"))
    in_export = collections.defaultdict(set)
    for eid, w, root, tx in rows:
        in_export[(root, w)] |= {key(x) for x in ev.get((w, root, tx), [])}
    by_wallet = collections.defaultdict(list)
    for ts, w, root, kind, tx in links:
        by_wallet[w].append((ts, root, tx))
    every, second = collections.defaultdict(set), 0
    for e in todo:
        txs, seen = {d[2] for d in e["deposits"]}, collections.defaultdict(set)
        for ts, root, tx in by_wallet.get(e["wallet"], ()):
            if tx in txs and ts < e["t"] and (e["id"], root) in kept:
                seen[root].add(tx)
                every[(root, e["wallet"])] |= {key(x) for x in ev.get((e["wallet"], root, tx), [])}
        second += sum(1 for v in seen.values() if len(v) > 1)
    new = {k: v - in_export[k] for k, v in every.items() if v - in_export[k]}
    valued = {k: v for k, v in new.items() if any(x[2] for x in v)}
    out = {"roots_rows_with_another_deposit_of_the_same_entry": second,
           "key_wallet_pairs_with_transfers_missing_from_the_export": len(new),
           "of_which_with_an_amount": len(valued),
           "missing_distinct_transfers": sum(len(v) for v in new.values()),
           "missing_usd": round(sum(x[2] or 0 for v in new.values() for x in v) / 1e6, 2),
           "group_keys_concerned": sorted({k[0][:10] for k in new if k[0].startswith(GROUP_KEY_PREFIXES)})}
    json.dump(out, open(os.path.join(HERE, "data", "links_other_deposits.json"), "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1])
