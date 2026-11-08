"""Writes EVIDENCE_INDEX.csv from evidence/ only. Rows are selected by address and time window, never typed by hand.
Run after package.py: python3 -I scripts/relations.py"""
import csv, gzip, json
from datetime import datetime, timezone
from pathlib import Path

NOTE = Path(__file__).resolve().parent.parent
EV = NOTE / "evidence"
PR27 = NOTE.parent / "iran-cluster-e-network-2026-11-05"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOK = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC.e", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC"}
POOL = "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"
A = {  # labels used in the index; classification evidence is in REPORT.md section 8 and verify.py
    "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a": "9TungSahur (Polymarket proxy)",
    "0xcb18ea2923d957bd9cf049cce60a87638722f867": "DonkeyDonkey999 (Polymarket proxy)",
    "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2": "ricosuave666 (Polymarket proxy)",
    "0xc4fdb47064604dc198a911afae48d9e4236b4b39": "TBFMM (Polymarket proxy, PR 27)",
    "0x909fa9f89976058b8b3ab87adc502ec7415ea8c3": "ILOVEYOUBABYZZ (Polymarket proxy, PR 27)",
    "0xe756468f0869e27d6c1c51a10993fd7ce4627866": "rrrrgggbbbclat (Polymarket proxy, PR 27)",
    "0xfd9e4d14a02a0ea10b87142198af8fed7c2dda6c": "Bigboyslatvian (Polymarket proxy, PR 27)",
    "0x283ad35049970a1d0ca4c766acfefa4f44f91298": "0x283ad350 (Polymarket proxy, no username)",
    "0xa26792e288079f9ee81d09e81058a5edbca522e4": "0xa26792e2 (deposit address credited to 9TungSahur)",
    "0x3f77a673a29e8cea345f0ed1f4f40a914156fc32": "0x3f77a673 (deposit-service hot wallet)",
    "0xfa0b641678f5115ad8a8de5752016bd1359681b9": "Crypto.com 6 (exchange hot wallet)",
    "0x1929347e025d4f5f8d6b2bd2261e2f4efcacd215": "Fun.xyz CheckoutPool",
    "0x9063493a4233006be654da772ef4dc38720cac55": "0x9063493a (Crypto.com customer deposit, PR 27)",
    "0x519fa16e9897132b7633f634b76306a327839e06": "0x519fa16e (Binance customer deposit, PR 27)",
    "0x93b7e169b93ece646d08cedbb8fa505796a5b96b": "0x93b7e169 (Bybit customer deposit, PR 27)",
    "0x529c2eef349edaf657cb23c2493bfd4369eb09bf": "0x529c2eef (wallet of the same unidentified service as PR 27's 0xa6c22144)",
    "0x09133414aa940fbe81a81d9c936275685c2aea88": "0x09133414 (Binance customer deposit)",
    "0xbfaa1d49144c84dac4163704e5ba3e876a7c345a": "0xbfaa1d49 (Stake.com customer deposit)",
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit 5 (exchange hot wallet)",
    "0x4d209741d0e8ae2758685bcb6d44f0704ac616dd": "0x4d209741 (Polymarket proxy, control)",
    "0x0bc0369198d851db9dfc865f088661c50dd901dd": "0x0bc03691 (wallet of the control 0x4d209741, first used 13 June 2025)",
    "0xf09366c69108ddad2305ee1764a60efe92b48477": "0xf09366c6 (ricosuave666's exit wallet)",
    "0xe559eb45d13e9a2e0e5d69c181de790f38e4b9a0": "0xe559eb45 (wallet first funded on 26 June 2025)",
    "0xc38e4e6a15593f908255214653d3d947ca1c2338": "Mayan Swift (bridge)",
}
ROWS = []


def load(p):
    b = p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix == ".gz" else b)


def iso(t):
    return datetime.fromtimestamp(int(t), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def add(rel, level, f, t, chain, h, token, amount, ts, source, src_file, via="", relay_id="", note=""):
    ROWS.append({"row_id": f"E{len(ROWS) + 1:03d}", "relation": rel, "evidence_level": level, "from_label": A.get(f, ""),
                 "from_address": f, "to_label": A.get(t, ""), "to_address": t, "via": via, "chain": chain, "tx_hash": h,
                 "relay_id": relay_id, "token": token, "amount": f"{amount:.6f}", "timestamp_utc": ts, "source": source,
                 "source_file": src_file, "note": note})


REC = {r["hash"]: r for r in load(EV / "polygon_receipts.json.gz")}
ACT = {}
for d in ("polymarket_full", "polymarket_dw"):
    for p in (EV / d).glob("*.json"):
        for r in load(p)["rows"]:
            ACT.setdefault((r["proxy_wallet"], r["transaction_hash"].lower(), r["type"]), r)


def legs(h):
    return [("0x" + l["topics"][1][26:], "0x" + l["topics"][2][26:], int(l["data"], 16) / 1e6, TOK[l["address"].lower()])
            for l in REC[h]["receipt"]["logs"] if l["address"].lower() in TOK and l["topics"] and l["topics"][0] == TRANSFER
            and len(l["topics"]) == 3]


def pm_flows(proxy, typ, cp, t0, t1, rel, level, note=""):
    """Polymarket DEPOSIT or WITHDRAWAL rows of `proxy` between t0 and t1 whose receipt pays or is paid by `cp`."""
    n = 0
    for (w, h, ty), r in sorted(ACT.items(), key=lambda kv: kv[1]["timestamp"]):
        if w != proxy or ty != typ or not (t0 <= iso(r["timestamp"]) <= t1):
            continue
        if h not in REC:  # third-party rows outside the analysed set keep only the receipts that were read
            continue
        for f, t, amt, tok in legs(h):
            if typ == "WITHDRAWAL" and f == POOL and t == cp and any(a == proxy and b == POOL for a, b, _, _ in legs(h)):
                add(rel, level, proxy, cp, "polygon", h, tok, amt, iso(r["timestamp"]), "receipt", "evidence/polygon_receipts.json.gz", POOL, note=note); n += 1
            elif typ == "WITHDRAWAL" and f == proxy and t == cp:
                add(rel, level, proxy, cp, "polygon", h, tok, amt, iso(r["timestamp"]), "receipt", "evidence/polygon_receipts.json.gz", note=note); n += 1
            elif typ == "DEPOSIT" and t == proxy and f == cp:
                add(rel, level, cp, proxy, "polygon", h, tok, amt, iso(r["timestamp"]), "receipt", "evidence/polygon_receipts.json.gz", note=note); n += 1
    return n


def es_rows(addr, f, t, t0, t1, rel, level, contract=None, note=""):
    p = EV / "etherscan" / f"{addr}_tokentx.json.gz"
    n = 0
    for r in load(p)["rows"]:
        if (r["from"].lower() == f and r["to"].lower() == t and int(r["value"]) > 0 and t0 <= iso(r["timeStamp"]) <= t1
                and (contract is None or r["contractAddress"].lower() == contract)):
            add(rel, level, f, t, "polygon", r["hash"].lower(), r["tokenSymbol"], int(r["value"]) / 10 ** int(r["tokenDecimal"]),
                iso(r["timeStamp"]), "etherscan", f"evidence/etherscan/{addr}_tokentx.json.gz", note=note); n += 1
    return n


def relay_rows(addr_file, user, rcpt, rel, level, note=""):
    n = 0
    for q in load(EV / "relay" / f"{addr_file}.json.gz")["requests"]:
        if q["status"] == "success" and q["user"].lower() == user and q["recipient"].lower() == rcpt:
            md = q["data"]["metadata"]
            h = next(x["hash"].lower() for x in q["data"]["inTxs"])
            add(rel, level, user, rcpt, f"{md['currencyIn']['currency']['chainId']}->{md['currencyOut']['currency']['chainId']}", h,
                md["currencyIn"]["currency"]["symbol"], float(md["currencyIn"]["amountFormatted"]), q["createdAt"][:19].replace("T", " "),
                "relay", f"evidence/relay/{addr_file}.json.gz", relay_id=q["id"],
                note=(note + "; " if note else "") + f"received {float(md['currencyOut']['amountFormatted']):.6f} {md['currencyOut']['currency']['symbol']}")
            n += 1
    return n


def main():
    TS9, DD = "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a", "0xcb18ea2923d957bd9cf049cce60a87638722f867"
    A267, F3F = "0xa26792e288079f9ee81d09e81058a5edbca522e4", "0x3f77a673a29e8cea345f0ed1f4f40a914156fc32"
    R1 = "R1 DonkeyDonkey999 funds 9TungSahur through 9TungSahur's deposit address, 11-12 June 2025"
    L2 = "L2 transfer through the receiver's deposit address (behaviour, amounts, timing)"
    assert pm_flows(DD, "WITHDRAWAL", A267, "2025-06-11", "2025-06-12", R1, L2) == 3
    assert pm_flows(TS9, "DEPOSIT", F3F, "2025-06-11", "2025-06-12", R1, L2, "credited 98.8 % of each leg about 19 min later") == 3
    assert es_rows(A267, "0xfa0b641678f5115ad8a8de5752016bd1359681b9", A267, "2025-06-12", "2025-06-13", R1, L2,
                   "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619", "2 WETH withdrawn from Crypto.com, credited 40 s later") == 1
    assert pm_flows(TS9, "DEPOSIT", "0x1929347e025d4f5f8d6b2bd2261e2f4efcacd215", "2025-06-12", "2025-06-13", R1, L2) == 1
    R2, L3, K = ("R2 exits of 13-19 June 2025 to customer deposit addresses",
                 "L3 shared customer-specific address (same exchange account or customer wallet credited)",
                 "K known from PR 27, confirmed independently")
    assert pm_flows(TS9, "WITHDRAWAL", "0x9063493a4233006be654da772ef4dc38720cac55", "2025-06-13", "2025-06-14", R2, K) == 6
    assert pm_flows(DD, "WITHDRAWAL", "0x519fa16e9897132b7633f634b76306a327839e06", "2025-06-13", "2025-06-14", R2, K) == 2
    assert pm_flows(TS9, "WITHDRAWAL", "0x93b7e169b93ece646d08cedbb8fa505796a5b96b", "2025-06-13", "2025-06-14", R2, L3, "new: not in PR 27") == 2
    assert pm_flows(DD, "WITHDRAWAL", "0x93b7e169b93ece646d08cedbb8fa505796a5b96b", "2025-06-13", "2025-06-20", R2, L3, "new: not in PR 27") == 5
    assert pm_flows("0x909fa9f89976058b8b3ab87adc502ec7415ea8c3", "WITHDRAWAL", "0x93b7e169b93ece646d08cedbb8fa505796a5b96b",
                    "2025-06-13", "2025-07-11", R2, L3, "new: not in PR 27") == 3
    W529 = "0x529c2eef349edaf657cb23c2493bfd4369eb09bf"
    R3 = "R3 wallet 0x529c2eef paid by 9TungSahur (2025), by two PR 27 network accounts (2026) and by a control's wallet"
    L3U = "L3u shared address of an unidentified service; customer-specific not established"
    assert pm_flows(TS9, "WITHDRAWAL", W529, "2025-06-13", "2025-06-14", R3, L3U, "new") == 3
    assert relay_rows(W529, "0xe756468f0869e27d6c1c51a10993fd7ce4627866", W529, R3, L3U, "new") == 2
    assert relay_rows(W529, "0xfd9e4d14a02a0ea10b87142198af8fed7c2dda6c", W529, R3, L3U, "new") == 1
    RT, W0BC = "0x4d209741d0e8ae2758685bcb6d44f0704ac616dd", "0x0bc0369198d851db9dfc865f088661c50dd901dd"
    assert pm_flows(RT, "WITHDRAWAL", W0BC, "2025-06-13", "2025-06-14", R3, L3U, "control 0x4d209741 to its own wallet (gas from Bybit 5)") == 3
    assert es_rows(W529, W0BC, W529, "2025-06-14", "2025-06-15", R3, L3U, note="exploratory: found while classifying the payers") == 1
    R4, L4 = ("R4 Bybit hot wallet pays 0x09133414 and 0x529c2eef after the Bybit deposits of 13 June 2025",
              "L4 relation through an exchange hot wallet (timing; customer not provable)")
    BY5 = "0xf89d7b9c864f589bbf53a82105107622b35eaa40"
    assert es_rows("0x09133414aa940fbe81a81d9c936275685c2aea88", BY5, "0x09133414aa940fbe81a81d9c936275685c2aea88", "2025-06-13", "2025-06-14", R4, L4) == 1
    assert es_rows(W529, BY5, W529, "2025-06-14", "2025-06-23", R4, L4) == 4
    R5 = "R5 DonkeyDonkey999 to Binance deposit 0x09133414 (October 2024), the address later paid by Bybit 5"
    assert es_rows("0x09133414aa940fbe81a81d9c936275685c2aea88", DD, "0x09133414aa940fbe81a81d9c936275685c2aea88", "2024-10-25", "2024-10-27", R5, L3) == 6
    B = "0xbfaa1d49144c84dac4163704e5ba3e876a7c345a"
    R6 = "R6 Stake.com deposit 0xbfaa1d49 credited by DonkeyDonkey999 (2024), TBFMM and 0x283ad350 (2026)"
    assert es_rows(B, DD, B, "2024-10-28", "2024-10-29", R6, L3, note="new") == 1
    assert relay_rows(B, "0xc4fdb47064604dc198a911afae48d9e4236b4b39", B, R6, L3, "new; BSC side read from the Relay order") == 1
    assert relay_rows(B, "0x283ad35049970a1d0ca4c766acfefa4f44f91298", B, R6, L3, "new; BSC side read from the Relay order") == 1
    R7, L1 = "R7 PR 27 transfers into DonkeyDonkey999, 13 January 2026", "L1 direct transfer (same hash in both activities)"
    assert pm_flows(DD, "DEPOSIT", "0xc4fdb47064604dc198a911afae48d9e4236b4b39", "2026-01-13", "2026-01-14", R7, K) == 1
    assert pm_flows(DD, "DEPOSIT", "0x909fa9f89976058b8b3ab87adc502ec7415ea8c3", "2026-01-13", "2026-01-14", R7, K) == 1
    RC, F09 = "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2", "0xf09366c69108ddad2305ee1764a60efe92b48477"
    R8, EXT = ("R8 ricosuave666's winnings and the transfers out of its exit wallet",
               "EXT figures compatible with published indictment reports; no account named there; identity not established")
    assert pm_flows(RC, "WITHDRAWAL", F09, "2025-06-13", "2025-06-14", R8, EXT, "the redemption of 13 June 2025 was 162,663.94 USDC") == 1
    assert es_rows(F09, F09, "0xc38e4e6a15593f908255214653d3d947ca1c2338", "2025-06-15", "2025-06-16", R8, "C bridge, destination not read") == 1
    assert es_rows(F09, F09, "0xe559eb45d13e9a2e0e5d69c181de790f38e4b9a0", "2025-06-26", "2025-06-27", R8, EXT,
                   note="first inflow of 0xe559eb45; 10 POL of gas sent by the same wallet 20 s later") == 1
    cols = list(ROWS[0])
    with open(NOTE / "EVIDENCE_INDEX.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(ROWS)
    print("EVIDENCE_INDEX.csv rows", len(ROWS))


if __name__ == "__main__":
    main()
