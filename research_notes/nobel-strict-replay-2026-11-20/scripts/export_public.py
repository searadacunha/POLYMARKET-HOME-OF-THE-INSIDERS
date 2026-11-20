"""Slim, publishable copies of the public inputs of part C, so that verify.py can recompute part C offline.

    python3 -I -B export_public.py RAW_DIR OUT_DIR

Only market data and on-chain facts are kept. The data API's profile fields (name, pseudonym, bio, images) are dropped.
Every raw response stays on the computing machine; `raw_index.csv` lists each one with its SHA-256 and fetch time."""
import csv, gzip, json, os, sys

MACHADO = "0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d"
T_FROM, ANN = 1760011200, 1760086800      # 2025-10-09 12:00 UTC to the announcement, 2025-10-10 09:00 UTC
HERE = os.path.dirname(os.path.abspath(__file__))
ACC = os.path.join(HERE, "..", "..", "..", "investigations", "followup-20261113", "sources", "data", "nobel_accounts.csv")


def main(raw_dir, out):
    idx = [json.loads(l) for l in open(os.path.join(raw_dir, "index.jsonl"))]
    load = lambda r: json.loads(gzip.open(os.path.join(raw_dir, r["file"])).read())
    ev = load(next(r for r in idx if r["key"].startswith("gamma:")))
    title = {m["conditionId"]: (m.get("groupItemTitle") or m["question"]).strip() for m in ev["markets"]}
    yes, no = json.loads(next(m for m in ev["markets"] if m["conditionId"] == MACHADO)["clobTokenIds"])
    tape = []                                   # identical rows are distinct fills: every row of every page is kept
    for r in idx:
        if r["key"].startswith(f"trades:{MACHADO}:"):
            for x in load(r).get("data") or []:
                t = int(x["timestamp"])
                if T_FROM <= t < ANN:
                    tape.append((x["transaction_hash"], x["token_id"], x["proxy_wallet"].lower(), x["side"], x["size"], x["price"], t))
    tape.sort(key=lambda k: (k[6], k[0], k[1], k[2], k[3], str(k[4]), str(k[5])))
    with open(os.path.join(out, "machado_tape.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t", "tx", "outcome", "side", "wallet", "shares", "price"])
        for tx, tok, wal, side, size, price, t in tape:
            w.writerow([t, tx, "Yes" if tok == yes else "No" if tok == no else tok, side, wal, size, price])
    pts = load(next(r for r in idx if r["key"] == f"prices:{yes}:10"))["history"]
    json.dump({"token": yes, "fidelity_minutes": 10, "source": "CLOB prices-history", "history": [[int(p["t"]), float(p["p"])] for p in pts]},
              open(os.path.join(out, "machado_yes_prices_10min.json"), "w"))
    accounts = {r["proxy"].lower(): r["handle"] for r in csv.DictReader(open(ACC))}
    blocks = {int(r["key"].split(":")[1]): int(load(r)["result"]["timestamp"], 16) for r in idx if r["key"].startswith("block:")}
    with open(os.path.join(out, "accounts_activity.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["handle", "t", "type", "market", "outcome", "side", "usdc", "price", "tx"])
        rows = []                               # every row kept: two identical rows are two fills
        for r in idx:
            if r["key"].startswith("activity:"):
                p = r["key"].split(":")[1]
                for x in (load(r).get("data") or []):
                    if int(x["timestamp"]) < ANN:
                        rows.append((accounts[p], int(x["timestamp"]), x["type"], title.get(x.get("condition_id"), "") if x["type"] == "TRADE" else "",
                                     x.get("outcome") or "", x.get("side") or "", x.get("usdc_size"), x.get("price"), x.get("transaction_hash")))
        for row in sorted(rows, key=lambda r: (r[0], r[1], r[2], str(r[8]), str(r[6]), str(r[7]))):
            w.writerow(row)
    with open(os.path.join(out, "accounts_inflows.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["handle", "block", "t", "from", "token", "amount", "tx", "log_index"])
        rows = []
        for r in idx:
            if r["key"].startswith("logs:"):
                to = "0x" + r["key"].split(":")[2][-40:]
                for l in load(r)["result"]:
                    b = int(l["blockNumber"], 16)
                    rows.append((accounts[to], b, blocks.get(b), "0x" + l["topics"][1][-40:], l["address"].lower(), int(l["data"], 16) / 1e6,
                                 l["transactionHash"], int(l["logIndex"], 16)))
        for row in sorted(set(rows), key=lambda r: (r[0], r[1], r[7])):
            w.writerow(row)
    with open(os.path.join(out, "raw_index.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["request", "sha256", "bytes", "fetched_utc"])
        for r in idx:
            w.writerow([r["key"], r["sha256"], r["bytes"], r["fetched_utc"]])
    print(f"tape rows {len(tape)}, price points {len(pts)}, raw responses {len(idx)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
