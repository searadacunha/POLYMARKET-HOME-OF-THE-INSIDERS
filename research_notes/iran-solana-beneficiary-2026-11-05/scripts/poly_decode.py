"""Décode les reçus Polygon archivés : transferts ERC-20 (USDC.e, USDC, pUSD...) et queue du calldata.

python3 -I poly_decode.py <raw/polygon> [hash...]   (hors ligne)
"""
import json, sys
from pathlib import Path

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKENS = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174": ("USDC.e", 6),
          "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": ("USDC", 6),
          "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": ("USDT", 6)}


def decode(d: Path, h: str):
    rc = json.loads((d / f"{h}.eth_getTransactionReceipt.json").read_text())["result"]
    tx = json.loads((d / f"{h}.eth_getTransactionByHash.json").read_text())["result"]
    transfers = []
    for l in rc["logs"]:
        if l["topics"] and l["topics"][0] == TRANSFER and len(l["topics"]) == 3:
            sym, dec = TOKENS.get(l["address"].lower(), (l["address"].lower(), None))
            transfers.append({"token": sym, "contract": l["address"].lower(), "from": "0x" + l["topics"][1][-40:],
                              "to": "0x" + l["topics"][2][-40:], "raw": int(l["data"], 16), "decimals": dec,
                              "log_index": int(l["logIndex"], 16)})
    return {"hash": h, "status": int(rc["status"], 16), "block": int(rc["blockNumber"], 16), "from": rc["from"],
            "to": rc["to"], "input_tail32": "0x" + tx["input"][-64:], "input_len": (len(tx["input"]) - 2) // 2,
            "transfers": transfers}


if __name__ == "__main__":
    d = Path(sys.argv[1])
    hs = sys.argv[2:] or sorted({p.name.split(".")[0] for p in d.glob("0x*.eth_getTransactionReceipt.json")})
    for h in hs:
        r = decode(d, h)
        print(h, "status", r["status"], "block", r["block"], "from", r["from"], "to", r["to"], "tail", r["input_tail32"])
        for t in r["transfers"]:
            amt = t["raw"] / 10 ** t["decimals"] if t["decimals"] else t["raw"]
            print("    ", t["token"], t["from"], "->", t["to"], amt)
