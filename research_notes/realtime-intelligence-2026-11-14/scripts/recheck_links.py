"""Independent re-reading of the funding links of data/study_export/financial_links.csv.

The links were found by reading, for each wallet, the logs of the collateral tokens over a range of blocks. This script
does not use that method: it takes the transaction named for each link, asks a public node for its receipt, and checks
that the receipt holds a transfer of a collateral token from the payer named to the receiver named, for the value named.

    python3 -I scripts/recheck_links.py > data/links_recheck.json        (network: one receipt per link)

A receipt that no node serves is reported as not served, never as a failed link."""
import csv, gzip, json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
STABLES = {"0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"}
NODES = ["https://polygon-bor-rpc.publicnode.com", "https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"]


def receipt(tx):
    for url in NODES:
        try:
            req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx]}).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (compatible; research-client/1.0)", "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=40) as r:
                raw = r.read()
                raw = gzip.decompress(raw) if r.headers.get("Content-Encoding") == "gzip" else raw
            j = json.loads(raw)
            if j.get("result"):
                return j["result"]
        except Exception:                                  # the next node is asked
            pass
        time.sleep(0.4)
    return None


def main():
    with open(os.path.join(HERE, "data", "study_export", "financial_links.csv")) as f:
        rows = list(csv.DictReader(f))
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows)
    out = {"read_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "links": 0, "confirmed": 0, "not_served": 0, "not_confirmed": [], "checked": []}
    cache = {}
    for r in rows[:limit]:
        tx = r["funding_tx"]
        if not tx:
            continue
        payer = r["root_key"].lower(); receiver = (r["pass_through_key"] or r["wallet"]).lower()
        value = int(round(float(r["funding_usd"]) * 1e6)) if r["funding_usd"] else None
        if tx not in cache:
            cache[tx] = receipt(tx); time.sleep(0.3)
        rec = cache[tx]; out["links"] += 1
        if rec is None:
            out["not_served"] += 1; continue
        found = any(len(l.get("topics", [])) == 3 and l["topics"][0] == TRANSFER and l["address"].lower() in STABLES
                    and "0x" + l["topics"][1][-40:] == payer and "0x" + l["topics"][2][-40:] == receiver
                    and (value is None or abs(int(l["data"], 16) - value) <= 10000) for l in rec.get("logs", []))
        out["confirmed"] += found
        out["checked"].append({"funding_tx": tx, "payer": payer, "receiver": receiver, "block": int(rec["blockNumber"], 16), "confirmed": bool(found)})
        if not found:
            out["not_confirmed"].append({"funding_tx": tx, "payer": payer, "receiver": receiver})
    json.dump(out, sys.stdout, indent=1); print()


if __name__ == "__main__":
    main()
