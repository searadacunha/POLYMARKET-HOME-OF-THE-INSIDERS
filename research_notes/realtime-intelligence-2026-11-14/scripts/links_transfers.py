"""Every transfer from the root key to the wallet behind each published funding link, and its receipt read again.

The export of the frozen study (financial_links.csv, written by ana_97 from feat_40) keeps one transfer per wallet, key
and deposit: the first one met. The claims audit of 14 November 2026 found two wallets that received two transfers from
their key before the deposit, so the amounts of the export are too low there. This script does not touch the study: it
reads the transfers stored by the study's collector (data/funding.sqlite of the study folder, table inflows: what the
wallet received in the 10,000 blocks before each deposit) and asks a public node for the receipt of each one.

    python3 -I scripts/links_transfers.py <study folder> > data/links_transfers.json        (network: one receipt per transfer)"""
import csv, json, os, sqlite3, sys, time, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODES = ["https://polygon-bor-rpc.publicnode.com", "https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"]
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
STABLES = {"0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"}
WINDOW = 10000


def receipt(tx):
    for url in NODES:
        req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx]}).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "research-client/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                res = json.loads(r.read()).get("result")
            if res:
                return res
        except Exception:
            time.sleep(1)
    return None


def confirmed(rec, payer, receiver, value):
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    return any(l.get("address", "").lower() in STABLES and (l.get("topics") or [None])[0] == TRANSFER and l["topics"][1].lower() == pad(payer)
               and l["topics"][2].lower() == pad(receiver) and int(l["data"], 16) == value for l in rec.get("logs") or [])


def main(study):
    fun = sqlite3.connect("file:" + os.path.join(study, "data", "funding.sqlite") + "?mode=ro", uri=True)
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", "study_export", "financial_links.csv"))))
    out, seen = [], {}
    for r in rows:
        key = (r["wallet"], r["deposit_tx"])
        if key in seen:
            continue
        block = fun.execute("select block from deposits where wallet=? and tx=?", key).fetchone()[0]
        inflow = fun.execute("select rows from inflows where wallet=? and tx=? and status='ok'", key).fetchone()
        mine = [x for x in json.loads(inflow[0]) if x["from"] == r["root_key"] and block - WINDOW < x["block"] <= block] if inflow else []
        tr = []
        for x in sorted(mine, key=lambda x: x["block"]):
            rec = receipt(x["tx"])
            tr.append({"tx": x["tx"], "block": x["block"], "usd": x["value"] / 1e6,
                       "receipt": "not served" if rec is None else ("confirmed" if confirmed(rec, r["root_key"], r["wallet"], x["value"]) else "NOT confirmed")})
        seen[key] = {"root_key": r["root_key"], "wallet": r["wallet"], "deposit_tx": r["deposit_tx"], "deposit_block": block,
                     "transfers_from_the_key_in_the_window": tr, "usd": round(sum(t["usd"] for t in tr), 2), "export_usd": float(r["funding_usd"])}
        out.append(seen[key])
    print(json.dumps({"read_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "deposits": len(out),
                      "transfers": sum(len(o["transfers_from_the_key_in_the_window"]) for o in out),
                      "confirmed": sum(t["receipt"] == "confirmed" for o in out for t in o["transfers_from_the_key_in_the_window"]),
                      "links": out}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
