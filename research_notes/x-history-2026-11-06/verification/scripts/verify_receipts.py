"""Two-node check and OrderFilled decoding for every receipt archived by `collect.py rcpt2`.

For each transaction: both nodes must return the same block hash, block number, status and the same list of logs
(logIndex, address, topics, data), and the same block timestamp. Mismatches are reported, never dropped.
OrderFilled of the exchange 0xe111180000d2663c0091e4f400237545b87b996b (topic 0xd543adfd...) is decoded from the
archived words: side (0 buy, 1 sell), token id, maker amount, taker amount, fee; 6 decimals for USDC and shares.
OrdersMatched (topic 0x174b3811...) names the taker order's maker, which identifies the taker of the match.
Writes data/receipts_check.json and data/receipts_orderfilled.csv.
"""
import csv, json, os
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(os.environ.get("RECEIPTS_DIR") or Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw")) / "polygon2")
HERE = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("OUT_DIR") or HERE / "data")
EXCHANGE = "0xe111180000d2663c0091e4f400237545b87b996b"
FILLED, MATCHED = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee", "0x174b3811690657c217184f89418266767c87e4805d09680c39fc9c031c0cab7c"
FILLED_V1 = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"  # keccak of OrderFilled(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)
MATCHED_V1 = "0x63bf4d16b7fa898ef4c4b2b6d90fd201e9c56313b65638af6088d149d2ce956c"  # keccak of OrdersMatched(bytes32,address,uint256,uint256,uint256,uint256)
EXCHANGES_V1 = {"0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e", "0xc5d563a36ae78145c45a50134d48a1215220f80a"}  # CTF and NegRisk CTF exchanges before 2026
NODES = ["publicnode", "drpc"]
U = Decimal(10) ** 6


def norm(rc):
    r = rc["result"]
    return {"blockHash": r["blockHash"], "blockNumber": r["blockNumber"], "status": r["status"], "from": r["from"], "to": r["to"],
            "logs": [(int(l["logIndex"], 16), l["address"].lower(), [t.lower() for t in l["topics"]], l["data"].lower()) for l in r["logs"]]}


def main():
    if not (RAW / NODES[0]).is_dir():
        raise SystemExit(f"no receipts under {RAW}")
    hashes = sorted(p.name.split(".")[0] for p in (RAW / NODES[0]).glob("*.receipt.json") if not p.name.endswith(".meta.json"))
    report, rows = {"transactions": len(hashes), "agree": 0, "disagree": [], "missing_second_node": []}, []
    for h in hashes:
        a_path, b_path = RAW / NODES[0] / f"{h}.receipt.json", RAW / NODES[1] / f"{h}.receipt.json"
        if not b_path.exists():
            report["missing_second_node"].append(h); continue
        a, b = norm(json.loads(a_path.read_text())), norm(json.loads(b_path.read_text()))
        ta = json.loads((RAW / NODES[0] / f"{h}.block.json").read_text())
        tb = json.loads((RAW / NODES[1] / f"{h}.block.json").read_text())
        if a != b or ta != tb:
            report["disagree"].append(h); continue
        report["agree"] += 1
        t = datetime.fromtimestamp(int(ta["timestamp"], 16), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        taker = next(("0x" + l[2][2][-40:] for l in a["logs"] if (l[1] == EXCHANGE and l[2][0] == MATCHED)
                      or (l[1] in EXCHANGES_V1 and l[2][0] == MATCHED_V1)), "")
        for idx, addr, topics, data in a["logs"]:
            w = [int(data[2 + i:66 + i], 16) for i in range(0, len(data) - 2, 64)]
            if addr == EXCHANGE and topics[0] == FILLED:
                side = "BUY" if w[0] == 0 else "SELL"
                usdc, shares = (w[2], w[3]) if w[0] == 0 else (w[3], w[2])
            elif addr in EXCHANGES_V1 and topics[0] == FILLED_V1:
                # makerAssetId, takerAssetId, makerAmountFilled, takerAmountFilled, fee; asset id 0 is USDC
                side = "BUY" if w[0] == 0 else "SELL"
                w = [w[0], w[1] if w[0] == 0 else w[0], w[2], w[3], w[4]]
                usdc, shares = (w[2], w[3]) if side == "BUY" else (w[3], w[2])
            else:
                continue
            rows.append({"tx": h, "block": int(a["blockNumber"], 16), "utc": t, "logIndex": idx, "order_hash": topics[1],
                         "maker": "0x" + topics[2][-40:], "taker": "0x" + topics[3][-40:], "match_taker_order_maker": taker,
                         "maker_side": side, "token_id": str(w[1]), "usdc": str(Decimal(usdc) / U), "shares": str(Decimal(shares) / U),
                         "price": str(round(Decimal(usdc) / Decimal(shares), 6)) if shares else "", "fee_raw": w[4]})
    (OUT / "receipts_check.json").write_text(json.dumps(report, indent=1))
    with open(OUT / "receipts_orderfilled.csv", "w", newline="") as f:
        if rows:
            wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in report.items()}), len(rows), "OrderFilled")


if __name__ == "__main__":
    main()
