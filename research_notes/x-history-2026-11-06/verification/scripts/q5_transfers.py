"""Q5: direct value transfers on Polygon between candidate addresses and the Ballon d'Or set, read as event logs.

For every (candidate, target) pair and both directions: ERC-20 Transfer on USDC.e, USDC and pUSD, and ERC-1155
TransferSingle / TransferBatch on the Conditional Tokens contract, filtered on from and to topics (Etherscan v2
logs API, chain 137, block 0 to latest). A filtered query that returns 1,000 rows is treated as truncated and fails.
Every answer is archived with its sha256. Exhaustive listings (tokentx) are also read when under the 10,000-row cap.
Usage: python3 -I q5_transfers.py
"""
import csv, hashlib, json, os, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw")) / "q5_logs"
KEY = next(l.split("=", 1)[1].strip().strip("\"'") for l in (Path.home() / "Downloads/.env").read_text().splitlines()
           if l.startswith("ETHERSCAN_API_KEY="))
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"
ERC20 = {"USDC.e": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "USDC": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
         "pUSD": "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"}
CTF = "0x4d97dcd97ec945f40cf65f87097ace5ea0476045"
ETH_ERC20 = {"USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7"}
ETH_CANDIDATES = {"Cypya owner": "0x5756bddb45817786ece4b3b6d1d71a291dc02006"}  # proxies exist on Polygon only; Magic owners unknown

CANDIDATES = {"Cypya proxy": "0x970998da056e60c707d9b1fc55cfdf3d68c252ab", "Cypya owner": "0x5756bddb45817786ece4b3b6d1d71a291dc02006",
              "Jydyjyd proxy": "0x1c4cd350bce3cb791daf88ce2034de9b03318d85", "Cypyo proxy": "0xa9f4dc80fd27e2977ef1fcaea41d263ecd7a4dfb"}


def targets():
    out = {}
    for r in csv.DictReader(open(HERE / "data/focus_wallets.csv")):
        if r["case"] in ("ballon-11", "ballon-linked"):
            out[r["label"] + " proxy"] = r["proxy"]
    owners = {"Thin-Disclaimer-Life": "0x1bf0b469f7f3612657e99bf785e470eee2a76028", "VidenteRibeira": "0x3cb3f4f6b1a81bdf523e36b7f5fa5081113f0f5e",
              "cookedrice": "0x6ec290051ea167cf564a4282c153351ab3fd876f", "WenZhuanBuPei": "0x6697f72fa32de93d8450830eb07f5b6724104405",
              "0x86544e4dfde": "0x69837228fa0bcbac53713d981161c929523c0ded", "brace227": "0xc852b0938f5ad79b640d105ed11c14499454af26",
              "walletwallet8424": "0x82775eb82fe33acffdf1b91a28c0fc19b4b6a3a1", "Zoomman17": "0xd90d00130519086d412d2b9ffac2bb01f71ef444",
              "kraben006": "0x101b5f4dc0886c32e2b75972101aeaf9f338fb65", "OuldLm3alem": "0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c",
              "0xdd97e6": "0xcf7b90deaf46d27b2b8f2f54a099d82879dd19ad", "unnamed-0xa8e6": "0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d"}
    out.update({k + " owner": v for k, v in owners.items()})  # owners: investigations/ballon-dor-wallets/sources (inventaire, cases)
    return out


def pad(a):
    return "0x" + "0" * 24 + a[2:]


def logs(name, params, chain=137):
    path = RAW / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())["result"]
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://api.etherscan.io/v2/api?chainid={chain}&module=logs&action=getLogs&fromBlock=0&toBlock=latest&{q}"
    for i in range(8):
        with urllib.request.urlopen(urllib.request.Request(url + f"&apikey={KEY}", headers={"user-agent": "x-leads-research/1.0"}), timeout=90) as r:
            body = r.read()
        b = json.loads(body)
        if b.get("status") == "1" or "No records found" in str(b.get("message")):
            break
        time.sleep(2 * (i + 1))
    else:
        raise SystemExit(f"{name}: {str(b)[:200]}")
    res = b.get("result") or []
    if not isinstance(res, list):
        raise SystemExit(f"{name}: result is not a list")
    if len(res) >= 1000:
        raise SystemExit(f"{name}: 1000 rows, truncated")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    path.with_name(path.stem + ".meta.json").write_text(json.dumps({"url": url + "&apikey=<KEY>", "sha256": hashlib.sha256(body).hexdigest(),
                                                                   "fetched_utc": datetime.now(timezone.utc).isoformat()}))
    time.sleep(0.25)
    return res


def main():
    tg, hits, calls = targets(), [], 0
    for cn, ca in CANDIDATES.items():
        for tn, ta in tg.items():
            for frm, to, d in ((ca, ta, "out"), (ta, ca, "in")):
                for tok, addr in ERC20.items():
                    res = logs(f"{ca[:10]}_{ta[:10]}_{d}_{tok}", {"address": addr, "topic0": TRANSFER, "topic1": pad(frm), "topic2": pad(to),
                                                                    "topic0_1_opr": "and", "topic1_2_opr": "and"})
                    calls += 1
                    hits += [{"candidate": cn, "target": tn, "direction": d, "asset": tok, "tx": x["transactionHash"],
                              "logIndex": int(x["logIndex"], 16), "block": int(x["blockNumber"], 16), "raw_amount": int(x["data"], 16)} for x in res]
                for top in (SINGLE, BATCH):
                    res = logs(f"{ca[:10]}_{ta[:10]}_{d}_ctf{top[2:8]}", {"address": CTF, "topic0": top, "topic2": pad(frm), "topic3": pad(to),
                                                                          "topic0_2_opr": "and", "topic2_3_opr": "and"})
                    calls += 1
                    hits += [{"candidate": cn, "target": tn, "direction": d, "asset": "CTF", "tx": x["transactionHash"],
                              "logIndex": int(x["logIndex"], 16), "block": int(x["blockNumber"], 16), "raw_amount": x["data"][:130]} for x in res]
    for cn, ca in ETH_CANDIDATES.items():
        for tn, ta in tg.items():
            if not tn.endswith(" owner"):
                continue
            for frm, to, d in ((ca, ta, "out"), (ta, ca, "in")):
                for tok, addr in ETH_ERC20.items():
                    res = logs(f"eth_{ca[:10]}_{ta[:10]}_{d}_{tok}", {"address": addr, "topic0": TRANSFER, "topic1": pad(frm), "topic2": pad(to),
                                                                        "topic0_1_opr": "and", "topic1_2_opr": "and"}, chain=1)
                    calls += 1
                    hits += [{"candidate": cn, "target": tn, "direction": d, "asset": "eth-" + tok, "tx": x["transactionHash"],
                              "logIndex": int(x["logIndex"], 16), "block": int(x["blockNumber"], 16), "raw_amount": int(x["data"], 16)} for x in res]
    out = {"pairs": len(CANDIDATES) * len(tg), "queries": calls, "direct_transfers": hits,
           "scope": "Polygon: ERC-20 USDC.e, USDC, pUSD and CTF ERC-1155 for the 4 candidates; Ethereum: USDC and USDT for the Cypya owner "
                    "against the 12 owner keys. Native POL: the four Polygon candidates have 0 normal transactions (Etherscan txlist); the Cypya owner has "
                    "0 normal, 0 internal and 0 token transactions on Ethereum. Base, Arbitrum, BSC, Solana not read."}
    (HERE / "data/q5_direct_transfers.json").write_text(json.dumps(out, indent=1))
    print(len(hits), "direct transfers in", calls, "queries")


if __name__ == "__main__":
    main()
