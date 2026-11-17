"""Builds EVIDENCE_INDEX.csv: one row per money leg used in REPORT.md, every field read from the archived data.

python3 -I scripts/build_index.py [--raw]   (same data sources as verify.py)
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import verify as V  # noqa: E402  (reuses its loaders, so the index reads exactly the verified files)

ROWS = []


def full_hash(root, rel, prefix):
    hits = {t["hash"] for t in V.load(root, rel)["result"] if t["hash"].startswith(prefix)}
    assert len(hits) == 1, (rel, prefix, hits)
    return hits.pop()


def add(rid, rel, level, chain, ref, block_or_time, frm, to, amount, asset, note):
    ROWS.append({"id": rid, "relation": rel, "level": level, "chain": chain, "tx": ref, "block_or_utc": block_or_time,
                 "from": frm, "to": to, "amount": amount, "asset": asset, "note": note})


def build():
    R, A = V.RICO_EXIT, V.AUGS
    # ricosuave666 exit wallet -> J4t48znS (source orders) and fills
    for rid, h, note in [("L01", "0x5da2a61dd3c01df76dece631bd66f0c0d1c35fe44e9213171f96616987c2789d", "LI.FI mayan order, Mayan Swift key 0x51466fd7…"),
                         ("L02", "0xad096e3d5351bde74ea50dab8e1e4bd1837525d0d8013b00dfa778280173de65", "Mayan Swift gasless order, key 0xa17cf61a…"),
                         ("L03", "0x2869df2eb42836b094cb59d36123a32e7dda3636e1b0854d92a79840e24633c5", "LI.FI mayan order, Mayan Swift key 0xf42e5919…"),
                         ("L04", "0x7711afb050503b2349b664567776284583589f901d2b6e1b2ce804a21e552622", "deBridge order 0xc2c2f654…")]:
        tx, rc = V.evm("r1", "polygon", h)
        amt = sum(v for a, f, t, v in V.transfers(rc) if a == V.USDC and f == R)
        add(rid, "ricosuave666 exit wallet -> J4t48znS (order)", "confirmed", "Polygon", h, int(rc["blockNumber"], 16), R, V.J4T, amt / 1e6, "USDC", note)
    for rid, key in [("L05", "51466fd7"), ("L06", "a17cf61a"), ("L07", "f42e5919")]:
        d = V.load("r2", f"http/mayan_order_{key}.json")
        tx = V.sol_tx(d["fulfillTxHash"])
        lam, tok, _ = V.sol_deltas(tx, V.J4T)
        amt, asset = (lam / 1e9, "SOL") if lam > 0 else (tok[V.SOL_USDC] / 1e6, "USDC")
        add(rid, "Mayan Swift fill to J4t48znS", "confirmed", "Solana", d["fulfillTxHash"], V.utc(tx["blockTime"]), "Mayan Swift solver", V.J4T, amt, asset, f"order {d['orderHash']}, state {d['stateAddr']}")
    tx = V.sol_tx("5SQUJEfVXmFMh64nbnD4Ykd1kGjUQfVDkhrYrqyUsjUL21TrCtpmcfEUVHA1xYTwg5hvGgeVoVmJwu1af6VAmXGx")
    add("L08", "deBridge fill to J4t48znS", "confirmed", "Solana", "5SQUJEfVXmFMh64nbnD4Ykd1kGjUQfVDkhrYrqyUsjUL21TrCtpmcfEUVHA1xYTwg5hvGgeVoVmJwu1af6VAmXGx",
        V.utc(tx["blockTime"]), "DLN taker 2snHHreX…", V.J4T, 1.259690717, "SOL", "order id 0xc2c2f654… in the instruction data")
    tx = V.sol_tx("5tHjtiH8n1oX9acYGWCD7ucaWZivgEomCzcmsRaP82LfcacJhxPsCqAtvAWt536J1pj2bzJSZjrnHWpymCzaGFhq")
    add("L09", "J4t48znS -> exit wallet on Ethereum (CCTP)", "confirmed", "Solana -> Ethereum", "5tHjtiH8n1oX9acYGWCD7ucaWZivgEomCzcmsRaP82LfcacJhxPsCqAtvAWt536J1pj2bzJSZjrnHWpymCzaGFhq",
        V.utc(tx["blockTime"]), V.J4T, R, 60077.603926, "USDC", "DepositForBurn, domain 0, minted 2025-07-16 21:58:35 UTC, tx 0xac53eccf6a3105855c47d207361184c2a1b616d90e1bf0567497f64aec4b4ea9")
    # AugsburgFClover <-> ricosuave666's wallets
    for rid, h in [("L10", "0x287aabc7af352f70e1c9a5f8355cda976977476c868effa10a540822d340d9b0"),
                   ("L11", "0xcbd9284509cd34dbf947150d73b484000ecd111a46e106f2d1d61b4e1d52f03c"),
                   ("L12", "0x3282d81f651d0b2b138d9abbb54bc9b0002d8645aa0c94aa6f1b33cd8975b618"),
                   ("L13", "0xeda99492f49df5df41cd96477d32fdeeef706d959e308b1836578d489d5ba1dc")]:
        _, rc = V.evm("r2", "polygon", h)
        amt = sum(v for a, f, t, v in V.transfers(rc) if a == V.USDC and t == R)
        add(rid, "AugsburgFClover withdrawal -> ricosuave666 exit wallet", "confirmed", "Polygon", h, int(rc["blockNumber"], 16), A, R, amt / 1e6, "USDC", "same hash as the Polymarket WITHDRAWAL row")
    for rid, oid in [("L14", "0x30923e8a75b0b309"), ("L15", "0xd2efe205fe9fa43f"), ("L16", "0xb16b9f4bd4238c94"), ("L17", "0x46d3370a2f9e1a92")]:
        r = [x for x in V.relay_orders("r2", A) if x["id"].startswith(oid)][0]
        md = r["data"]["metadata"]
        add(rid, "Relay order " + ("AugsburgFClover -> exit wallet" if r["user"].lower() == A else "6pJEdTi1 -> AugsburgFClover"), "confirmed",
            f"{r['data']['inTxs'][0]['chainId']} -> {r['data']['outTxs'][0]['chainId']}", r["id"], r["createdAt"][:19], r["user"], r["recipient"],
            md["currencyOut"]["amountFormatted"], md["currencyOut"]["currency"]["symbol"], f"in {r['data']['inTxs'][0]['hash']}, out {r['data']['outTxs'][0]['hash']}")
    for rid, sig, owner, amt, asset in [("L18", "qoFDmKqHSUr3Bvh6uqFtkyhwBqQPxLTLFvmWxu7PXESZX2HqyddRdtVuK9TkXoPmdcGGy8nHZ3W2J4W6gC2LQjd", V.I6PJ, 1.1, "SOL"),
                                        ("L19", "51JHwuzqgcmvFeYwG2LaUJfP91skyNycsNPpx2BDoZYFisRBC95G7aMQX8drxFZQ3HqZAG7hQLN5mTySPcsAjN9g", V.I6PJ, 24987.099103, "USDC"),
                                        ("L20", "4u8ca3wrjn4hUZNNmSDzZGXDPGaV7ukqxKBkjgzwXEr3xXcphm1Fc4b5ZgarD6Sgpc3qCLKQuYNK9qN3UyeVRYC7", V.I3CC, 6.0, "SOL"),
                                        ("L21", "5oPZnsZDGJVLXZumX6XMH8CCPTgRLrcRkskryoJTyB8mt69onjE8nWoXevNReSq2dvgKWXF49QjPr2yi8NnxYYRL", V.I3CC, 20.0, "SOL")]:
        add(rid, f"J4t48znS -> {owner[:8]}…", "confirmed", "Solana", sig, V.utc(V.sol_tx(sig)["blockTime"]), V.J4T, owner, amt, asset, "signed by J4t48znS")
    for rid, oid in [("L22", "0x6d67609a2961e1"), ("L23", "0xea7fdcb645ac3d"), ("L24", "0x2c1dd890565213")]:
        r = [x for x in V.relay_orders("r2", V.METU) if x["id"].startswith(oid)][0]
        md = r["data"]["metadata"]
        add(rid, "Relay order " + ("3cCK8epV -> metushelah" if r["user"] == V.I3CC else "metushelah -> J4t48znS"), "confirmed",
            f"{r['data']['inTxs'][0]['chainId']} -> {r['data']['outTxs'][0]['chainId']}", r["id"], r["createdAt"][:19], r["user"], r["recipient"],
            md["currencyOut"]["amountFormatted"], md["currencyOut"]["currency"]["symbol"], f"in {r['data']['inTxs'][0]['hash']}, out {r['data']['outTxs'][0]['hash']}")
    r = [x for x in V.relay_orders("r1", V.J4T) if x["user"].lower() == V.RICO][0]
    add("L25", "Relay order ricosuave666 -> J4t48znS", "confirmed", "137 -> Solana", r["id"], r["createdAt"][:19], V.RICO, V.J4T,
        r["data"]["metadata"]["currencyOut"]["amountFormatted"], "USDC", f"in {r['data']['inTxs'][0]['hash']}, out {r['data']['outTxs'][0]['hash']}")
    # 0xe559eb45
    add("L26", "ricosuave666 exit wallet -> 0xe559eb45", "confirmed", "Polygon", "0x913cf0b6068908e5a4c1ed4470102cb3a4295015c42edf2f1295e620c7647d31", "2025-06-26 14:07:14", R, V.E559, 74680.134173, "USDC", "first inflow of 0xe559eb45")
    add("L27", "0xe559eb45 -> deposit address of meeeeeeeeeeeeeeee", "supported", "Polygon", full_hash("r1", f"etherscan/{V.E559}/137_tokentx_p1.json", "0x759c7cec5ca6812b"), "2025-06-26 14:12:32", V.E559, "0x31c88bbb26203b52fd34fc44cde7843557b8b518", 1000.0, "USDC", "credited 999.612718 USDC.e 28 s later, tx 0x45b94b57e7eab880437d690e5a178388e3f4abf0a39443f1f21a6e69fd4802cc")
    r = [x for x in V.relay_orders("r1", V.E559) if x["recipient"].lower() == V.MEEE][0]
    add("L28", "Relay order 0xe559eb45 -> meeeeeeeeeeeeeeee", "confirmed", "137 -> 137", r["id"], r["createdAt"][:19], V.E559, V.MEEE, 1498.042354, "USDC.e", f"in {r['data']['inTxs'][0]['hash']}")
    add("L29", "0xe559eb45 -> Binance deposit 0xaa00faed", "supported", "Polygon", full_hash("r1", f"etherscan/{V.E559}/137_tokentx_p1.json", "0x198cd5f7ecc42e5a"), "2025-06-26 14:31:06", V.E559, "0xaa00faedb1146785792f00e2feac69adbdaba42b", 3000.0, "USDC", "swept to Binance 48 at 14:42:50")
    add("L30", "ricosuave666 exit wallet -> Binance deposit 0xaa00faed", "supported", "Ethereum", full_hash("r2", "etherscan/1_txlist_0xaa00faedb1146785792f00e2feac69adbdaba42b_p1.json", "0x9e11b24ce4710795"), "2025-07-29 15:38:23", R, "0xaa00faedb1146785792f00e2feac69adbdaba42b", 20.627325794318736, "ETH", "swept to Binance 14 at 15:43:11")
    add("L31", "0xe559eb45 -> 0x43d44a06 (Ethereum)", "confirmed", "Ethereum", "0x18644df4098f97672a2e847dcf4dbb9996c1046b079f46a01ec7a0329e928b03", "2025-07-14 17:40:35", V.E559, "0x43d44a06325db643f8eb5ac998b5355978069bfc", 65352.0, "USDT", "after a 10 USDT test at 17:38:59; PoS exit of 65,649.069103 USDT at 17:36:35")
    # truthlord, PorcoRosso
    for rid, h, take, rcv in [("L32", "0x8210149c6b6b999d049fbcbb091825dd4d465e25bb9163eb18c9c0f4759e09a7", 19979.024709, V.HFG),
                              ("L33", "0xf2c42c06d9193e9c44b07eb4d1fe1c07b90823d874ba8838259204af08736130", 999.20016, V.HFG),
                              ("L34", "0x3bf82ad2181cc7b35fec6fce3343ce833d378e0576aa6aaa538ba6a0ac3cf623", 28957.860335, V.HFG)]:
        _, rc = V.evm("r1", "polygon", h)
        add(rid, "truthlord exit wallet -> HfGp55mp (deBridge order)", "confirmed", "Polygon -> Solana", h, int(rc["blockNumber"], 16), V.TRUTH_EXIT, rcv, take, "USDC (take amount)", "receiver read from CreatedOrder")
    add("L35", "PorcoRosso exit wallet -> itself on Ethereum (deBridge)", "confirmed", "Polygon -> Ethereum", "0x641e71f920aaa1e0166c971ddedd9ce1bdc099c753a55df19ca6e33f9dc08a70", 72697761, V.PORCO_EXIT, V.PORCO_EXIT, 43.381968520308833448, "ETH (take amount)", "filled 2025-06-13 00:54:59 UTC, tx 0xf8bab9e89c4696e2e6fdbf31e0a1890b614e0dae6586b519fd9af168324beda8, FulfilledOrder id 0x89fcc555…")
    add("L36", "PorcoRosso exit wallet -> HdxkiXqe (LI.FI mayanMCTP)", "confirmed", "Polygon -> Solana", "0xfb2996b7c875c080112ea4b1f56248b925e9fa12bdef07d37833c7cff5027163", 73062201, V.PORCO_EXIT, V.HDX, 63072.677418, "USDC", "HdxkiXqe has more than 29,000 signatures in Oct-Nov 2026: service-like, not followed")
    # Pulser group F
    add("L37", "Pulser -> 0x0bb95597 (first deposit of 0x0bb95597)", "confirmed", "Polygon", "0x5d68fa366a958f8457bac7106d0a2106711d4055cb885fe6d5247df3c8b8f2c7", "2025-12-04 19:05:33", V.PULSER, V.F2, 200.0, "USDC.e", "same hash: WITHDRAWAL of Pulser, DEPOSIT of 0x0bb95597")
    add("L38", "0x0bb95597 -> Pulser", "confirmed", "Polygon", "0x80ccdfee56f397eb184c9d486d1fb60eb77550b37c6a59ca087255b42c633499", "2025-12-04 19:12:43", V.F2, V.PULSER, 140.3568, "USDC.e", "same hash on both sides")
    add("L39", "0x0bb95597 -> 0xbbcab537 (UMA proposer wallet, also used by Car)", "supported", "Polygon", "0xaf0bc26973cff40ad0748e796090a47cd12169358a476e0900ed04aa91a0825d", "2025-12-09 16:15:20", V.F2, "0xbbcab5377bbca9cccbc48d0a7afbeaf78c741f90", 250.0, "USDC.e", "0xbbcab537 calls UMA proposePrice/disputePrice; Car withdrew 10,700 USDC.e to it and received 250 from it")


if __name__ == "__main__":
    build()
    with (HERE / "EVIDENCE_INDEX.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ROWS[0]))
        w.writeheader()
        w.writerows(ROWS)
    print(len(ROWS), "rows")
