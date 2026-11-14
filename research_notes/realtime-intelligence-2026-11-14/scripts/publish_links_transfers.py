"""Publish the export of amendment 002 (every funding transfer of a link) and read each transfer again on chain.

    python3 -I scripts/publish_links_transfers.py <study folder>          (network: one receipt per distinct transfer)

Reads derived/export/financial_links_transfers.csv and its summary, written in the study folder by the frozen
code/ana_99_links_all_transfers.py. Writes, in this note:
  data/study_export/financial_links_transfers.csv          rows of the keys already published (a documented case)
  data/study_export/financial_links_transfers_summary.json the summary; a key of no documented case is named by rank
  data/links_transfers_v2_recheck.json                     the receipt of every distinct transfer, all keys; the
                                                           transfers of an unpublished key are counted, not listed
A key is published when it is already in data/study_export/financial_links.csv (the export reviewed before)."""
import csv, json, os, sys, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
from links_transfers import receipt, STABLES, TRANSFER      # noqa: E402

OUT = lambda *p: os.path.join(HERE, "data", *p)


def confirmed_cents(rec, payer, receiver, usd):
    """A Transfer of a collateral token from payer to receiver whose value, in USD, rounds to the exported cents
    (ana_99 writes amounts rounded to 0.01 USD; 87.712391 is exported as 87.71)."""
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    return any(l.get("address", "").lower() in STABLES and (l.get("topics") or [None])[0] == TRANSFER and len(l["topics"]) == 3
               and l["topics"][1].lower() == pad(payer) and l["topics"][2].lower() == pad(receiver)
               and round(int(l["data"], 16) / 1e6, 2) == round(usd, 2) for l in rec.get("logs") or [])


def main(study):
    src = os.path.join(study, "derived", "export")
    rows = list(csv.DictReader(open(os.path.join(src, "financial_links_transfers.csv"))))
    summary = json.load(open(os.path.join(src, "financial_links_transfers_summary.json")))
    published = {r["root_key"] for r in csv.DictReader(open(OUT("study_export", "financial_links.csv")))}
    alias = {k: f"undocumented key {i + 1}" for i, k in enumerate(sorted(k for k in summary["keys_behind_two_wallets_or_more"] if k not in published))}
    checks, seen = [], set()
    for r in rows:
        key = (r["funding_tx"], r["root_key"], r["wallet"], r["funding_usd"])
        if key in seen:
            continue
        seen.add(key)
        rec = receipt(r["funding_tx"])
        receiver = r["pass_through_key"] or r["wallet"]     # a pass-through row: the key paid the pass-through key, which paid the wallet
        status = "not served" if rec is None else ("confirmed" if confirmed_cents(rec, r["root_key"], receiver, float(r["funding_usd"])) else "NOT confirmed")
        checks.append({"root_key": r["root_key"], "wallet": r["wallet"], "funding_tx": r["funding_tx"], "funding_block": int(r["funding_block"]),
                       "usd": float(r["funding_usd"]), "receipt": status, "receiver_checked": receiver})
    pub = [c for c in checks if c["root_key"] in published]
    hidden = [c for c in checks if c["root_key"] not in published]
    with open(OUT("study_export", "financial_links_transfers.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(r for r in rows if r["root_key"] in published)
    summary["keys_behind_two_wallets_or_more"] = {alias.get(k, k): v for k, v in summary["keys_behind_two_wallets_or_more"].items()}
    summary["rows_published"] = sum(r["root_key"] in published for r in rows)
    json.dump(summary, open(OUT("study_export", "financial_links_transfers_summary.json"), "w"), indent=1)
    by = lambda cs: {s: sum(c["receipt"] == s for c in cs) for s in ("confirmed", "NOT confirmed", "not served")}
    json.dump({"read_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "distinct_transfers": len(checks), "by_receipt": by(checks),
               "published_keys": pub, "unpublished_keys": {alias[k]: {"transfers": sum(c["root_key"] == k for c in hidden),
                                                                      "usd": round(sum(c["usd"] for c in hidden if c["root_key"] == k), 2),
                                                                      "by_receipt": by([c for c in hidden if c["root_key"] == k])} for k in alias}},
              open(OUT("links_transfers_v2_recheck.json"), "w"), indent=1)
    print(json.dumps(by(checks)))


if __name__ == "__main__":
    main(sys.argv[1])
