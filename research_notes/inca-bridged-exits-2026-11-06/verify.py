"""Offline verifier for research_notes/inca-bridged-exits-2026-11-06.

python3 -I verify.py            recompute every claim from evidence/ (gzip copies of the raw responses)
python3 -I verify.py --raw      same checks on the raw archives outside git, and write evidence/NEEDED.txt

Every check reads primary data only: Polygon/Ethereum receipts and transactions, Etherscan token pages,
Solana getTransaction responses, Relay order pages and Polymarket activity. No network access.
"""
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from abi import (TRANSFER, LIFI_STARTED, MAYAN_ORDER_CREATED, DLN_CREATED, b58, decode_dln_created,  # noqa: E402
                 decode_lifi_started, u)

RAW_MODE = "--raw" in sys.argv
ROOTS = {"r1": Path.home() / "Projects/Polymarket-inca-raw-20261106/raw",
         "r2": Path.home() / "Projects/Polymarket-inca-bridges-raw-20261106/raw"}
EVID = HERE / "evidence"
NEEDED = set()
RESULTS = []

USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
USDCE = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
USDT_ETH = "0xdac17f958d2ee523a2206206994597c13d831ec7"
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
POOL = "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"  # Uniswap pool that pays Polymarket withdrawals in native USDC
RELAY_SOLVER = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"

RICO = "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2"
RICO_EXIT = "0xf09366c69108ddad2305ee1764a60efe92b48477"
AUGS = "0x509cd9d117e06a082df649a06e317195f048240a"
METU = "0x4e74acf9447df43029fedc1fe592775110de6a9f"
MEEE = "0x03727dd8df63b9aaedebb30db24a7f07522fa86b"
E559 = "0xe559eb45d13e9a2e0e5d69c181de790f38e4b9a0"
J4T = "J4t48znSuoXVyfytFMBCu7Y5Y4RtmCvK985EkUAZKxVe"
I3CC = "3cCK8epVbySrZMoecevF6keiVKLmDs11oCMTCTgxYJd8"
I6PJ = "6pJEdTi1YST6irUvRy1BxW5iXzFASryLSMBepbMSNFoA"
TRUTH_EXIT = "0x4d1489edf5236653ae36db319f5267e1a921a6de"
HFG = "HfGp55mpjgQpZS7sgn5cwggdSHFyVY3qeevxHNekwN9x"
PORCO_EXIT = "0xfefea9427bef554cc572bc4e887a0b9642fd8f4e"
HDX = "HdxkiXqeN6qpK2YbG51W23QSWj3Yygc1eEk2zwmKJExp"
PULSER = "0x6a8328b1ae11569f7b27600073558879885e4c59"
F2 = "0x0bb95597b85b89f83f66929be66edcf4ae7f9725"


def load(root: str, rel: str):
    if RAW_MODE:
        data = json.loads((ROOTS[root] / rel).read_bytes())
    else:
        data = json.loads(gzip.decompress((EVID / root / (rel + ".gz")).read_bytes()))
    NEEDED.add(f"{root}/{rel}")  # only files actually read (end-of-pagination probes raise first)
    return data


def check(cid: str, ok: bool, detail: str):
    RESULTS.append({"id": cid, "ok": bool(ok), "detail": detail})


def utc(ts) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ---------- readers ----------
def evm(root, chain_dir, h):
    tx = load(root, f"{chain_dir}/{h}.eth_getTransactionByHash.json")["result"]
    rc = load(root, f"{chain_dir}/{h}.eth_getTransactionReceipt.json")["result"]
    return tx, rc


def transfers(rc):
    return [(l["address"].lower(), "0x" + l["topics"][1][26:], "0x" + l["topics"][2][26:], int(l["data"], 16))
            for l in rc["logs"] if l["topics"] and l["topics"][0] == TRANSFER and len(l["topics"]) == 3]


def activity(root, addr):
    rows, n = [], 0
    while True:
        rel = f"polymarket/{addr}/v2activity_p{n:03d}.json"
        try:
            page = load(root, rel)
        except FileNotFoundError:
            break
        rows += page["data"]
        n += 1
        if not page.get("pagination", {}).get("next_cursor"):
            break
    if not n:
        raise FileNotFoundError(addr)
    return rows


def dw(root, addr):
    return load(root, f"polymarket_dw/{addr}/p000.json")["data"]


def relay_orders(root, user):
    out, n = [], 0
    while True:
        rel = f"relay/{user}/p{n:03d}.json"
        try:
            page = load(root, rel)
        except FileNotFoundError:
            break
        out += page.get("requests", [])
        n += 1
        if not page.get("continuation"):
            break
    return out


def es_tokens(root, addr, chain=137):
    rel = f"etherscan/{addr}/{chain}_tokentx_p1.json" if root == "r1" or chain == 137 else f"etherscan/{chain}_tokentx_{addr}_p1.json"
    return load(root, rel)["result"]


def sol_tx(sig):
    return load("r2", f"sol/tx/{sig}.json")["result"]


def sol_deltas(tx, owner):
    """Net SOL (lamports) and SPL token changes of `owner` in a parsed Solana transaction."""
    keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
    m = tx["meta"]
    lam = (m["postBalances"][keys.index(owner)] - m["preBalances"][keys.index(owner)]) if owner in keys else 0
    pre = {(b.get("owner"), b["mint"]): int(b["uiTokenAmount"]["amount"]) for b in m.get("preTokenBalances", [])}
    post = {(b.get("owner"), b["mint"]): int(b["uiTokenAmount"]["amount"]) for b in m.get("postTokenBalances", [])}
    tok = {mint: post.get((o, mint), 0) - pre.get((o, mint), 0) for (o, mint) in set(pre) | set(post) if o == owner}
    return lam, {k: v for k, v in tok.items() if v}, keys


def cash_by_market(rows):
    out = {}
    for r in rows:
        if r["type"] not in ("TRADE", "REDEEM"):
            continue
        x = out.setdefault(r["title"], {"buy": 0.0, "sell": 0.0, "redeem": 0.0})
        v = float(r["usdc_size"] or 0)
        if r["type"] == "REDEEM":
            x["redeem"] += v
        else:
            x["buy" if r["side"] == "BUY" else "sell"] += v
    return {k: round(v["sell"] + v["redeem"] - v["buy"], 2) for k, v in out.items()} | \
           {"__buys__" + k: round(v["buy"], 2) for k, v in out.items()}


# ---------- A. source-side bridge orders of the three other Inca accounts ----------
def nonevm_receiver(rc):
    """LI.FI BridgeToNonEVMChainBytes32-style event of the diamond: data is the 32-byte Solana receiver."""
    out = [l["data"][2:] for l in rc["logs"] if l["topics"] and l["topics"][0].startswith("0x7be3e48a")]
    return b58(bytes.fromhex(out[0])) if len(out) == 1 else None


def check_bridges():
    # ricosuave666: four Solana-bound orders from its exit wallet, all to J4t48znS
    for cid, h, bridge, minamt in [
        ("A1", "0x5da2a61dd3c01df76dece631bd66f0c0d1c35fe44e9213171f96616987c2789d", "mayan", 2271082192),
        ("A3", "0x2869df2eb42836b094cb59d36123a32e7dda3636e1b0854d92a79840e24633c5", "mayan", 9323074500)]:
        tx, rc = evm("r1", "polygon", h)
        lf = [decode_lifi_started(l) for l in rc["logs"] if l["topics"] and l["topics"][0] == LIFI_STARTED][0]
        ok = (tx["from"] == RICO_EXIT and lf["bridge"] == bridge and lf["destinationChainId"] == 1151111081099710
              and lf["minAmount"] == minamt and nonevm_receiver(rc) == J4T)
        check(cid, ok, f"LI.FI {lf['bridge']} order from {tx['from']} to Solana {nonevm_receiver(rc)}, {lf['minAmount'] / 1e6} USDC, tx {h}")
    h = "0xad096e3d5351bde74ea50dab8e1e4bd1837525d0d8013b00dfa778280173de65"  # Mayan Swift, gasless order
    tx, rc = evm("r1", "polygon", h)
    w = [tx["input"][10 + 64 * i: 10 + 64 * (i + 1)] for i in range(26)]
    amt, trader, dest, destchain = int(w[1], 16), "0x" + w[2][24:], b58(bytes.fromhex(w[9])), int(w[10], 16)
    key = [l["data"] for l in rc["logs"] if l["topics"] and l["topics"][0] == MAYAN_ORDER_CREATED]
    moved = [t for t in transfers(rc) if t[1] == RICO_EXIT and t[2] == "0xc38e4e6a15593f908255214653d3d947ca1c2338"]
    check("A2", tx["input"][:10] == "0x3a30b37f" and amt == 98419998631 and trader == RICO_EXIT and dest == J4T
          and destchain == 1 and len(key) == 1 and moved and moved[0][3] == amt,
          f"Mayan Swift order key {key[0] if key else None}: trader {trader}, {amt / 1e6} USDC, destAddr {dest} (Wormhole chain {destchain})")
    h = "0x7711afb050503b2349b664567776284583589f901d2b6e1b2ce804a21e552622"
    tx, rc = evm("r1", "polygon", h)
    o = [decode_dln_created(l) for l in rc["logs"] if l["topics"] and l["topics"][0] == DLN_CREATED][0]
    check("A4", tx["from"] == RICO_EXIT and o["takeChainId"] == 7565164 and b58(bytes.fromhex(o["receiverDst"][2:])) == J4T
          and o["takeAmount"] == 1259690717, f"deBridge order {o['orderId']}: {o['giveAmount'] / 1e6} USDC to Solana "
          f"{b58(bytes.fromhex(o['receiverDst'][2:]))}, take {o['takeAmount'] / 1e9} SOL")
    # truthlord: three deBridge orders to HfGp55mp; 2026 orders to BSC, to itself
    for cid, h, take in [("B1", "0x8210149c6b6b999d049fbcbb091825dd4d465e25bb9163eb18c9c0f4759e09a7", 19979024709),
                         ("B2", "0xf2c42c06d9193e9c44b07eb4d1fe1c07b90823d874ba8838259204af08736130", 999200160),
                         ("B3", "0x3bf82ad2181cc7b35fec6fce3343ce833d378e0576aa6aaa538ba6a0ac3cf623", 28957860335)]:
        tx, rc = evm("r1", "polygon", h)
        o = [decode_dln_created(l) for l in rc["logs"] if l["topics"] and l["topics"][0] == DLN_CREATED][0]
        rcv = b58(bytes.fromhex(o["receiverDst"][2:]))
        check(cid, tx["from"] == TRUTH_EXIT and o["takeChainId"] == 7565164 and rcv == HFG and o["takeAmount"] == take
              and b58(bytes.fromhex(o["takeTokenAddress"][2:])) == SOL_USDC,
              f"deBridge order {o['orderId']}: {o['giveAmount'] / 1e6} USDC to Solana {rcv}, take {take / 1e6} USDC")
    for h in ["0x069a9311cc1187972fe0de11245d4ab5da3f48a68b1d849aa52eae5770d162df",
              "0x4f173a7a486df8262a318da793bbd91ff6a60c4f431bf9af8ee39476b43f9743",
              "0x244a838621e6a9bd18dc4d5ef84a848936235ef0bb25192598a3f68bb9e24740"]:
        tx, rc = evm("r1", "polygon", h)
        o = [decode_dln_created(l) for l in rc["logs"] if l["topics"] and l["topics"][0] == DLN_CREATED][0]
        check("B4", o["takeChainId"] == 56 and o["receiverDst"] == TRUTH_EXIT, f"deBridge order {o['orderId']} to BSC, receiver {o['receiverDst']} (itself)")
    # PorcoRosso: deBridge to Ethereum (to itself) and LI.FI Mayan MCTP to Solana HdxkiXqe
    tx, rc = evm("r1", "polygon", "0x641e71f920aaa1e0166c971ddedd9ce1bdc099c753a55df19ca6e33f9dc08a70")
    o = [decode_dln_created(l) for l in rc["logs"] if l["topics"] and l["topics"][0] == DLN_CREATED][0]
    check("C1", tx["from"] == PORCO_EXIT and o["takeChainId"] == 1 and o["receiverDst"] == PORCO_EXIT
          and o["takeTokenAddress"] == "0x" + "00" * 20 and o["takeAmount"] == 43381968520308833448,
          f"deBridge order {o['orderId']}: {o['giveAmount'] / 1e6} USDC to {o['takeAmount'] / 1e18} ETH on Ethereum, receiver itself")
    tx, rc = evm("r1", "polygon", "0xfb2996b7c875c080112ea4b1f56248b925e9fa12bdef07d37833c7cff5027163")
    lf = [decode_lifi_started(l) for l in rc["logs"] if l["topics"] and l["topics"][0] == LIFI_STARTED][0]
    check("C2", tx["from"] == PORCO_EXIT and lf["bridge"] == "mayanMCTP" and nonevm_receiver(rc) == HDX and lf["minAmount"] == 63072677418,
          f"LI.FI mayanMCTP {lf['minAmount'] / 1e6} USDC to Solana {nonevm_receiver(rc)}")
    # no shared bridge destination between the three accounts
    pr27 = {"4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy", "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV",
            "FyJ2zJY4yyCr8EZJSDVFB862JRiCYr6yWxEuMgVkaFcH"}  # PR 27 Solana beneficiary, Bybit deposit, shared recipient
    check("A5", len({J4T, HFG, HDX}) == 3 and not ({J4T, HFG, HDX} & pr27),
          "the three Solana destinations are distinct and none is a PR 27 Solana address")


# ---------- D-H. accounts sharing ricosuave666's personal wallets ----------
def relay_by_id(orders, oid):
    hit = [r for r in orders if r["id"] == oid]
    return hit[0] if len(hit) == 1 else None


def check_rico_network():
    rico = activity("r1", RICO)
    rico_w = {r["transaction_hash"]: float(r["usdc_size"]) for r in rico if r["type"] == "WITHDRAWAL"}
    augs = activity("r2", AUGS)
    augs_w = {r["transaction_hash"]: float(r["usdc_size"]) for r in augs if r["type"] == "WITHDRAWAL"}
    # D1: every Polymarket-withdrawal credit of the exit wallet comes from ricosuave666 or AugsburgFClover
    toks = es_tokens("r1", RICO_EXIT)
    pool_in = [t for t in toks if t["to"].lower() == RICO_EXIT and t["from"].lower() == POOL]
    by = {"ricosuave666": 0, "AugsburgFClover": 0, "other": 0}
    amt = {"ricosuave666": 0, "AugsburgFClover": 0}
    for t in pool_in:
        k = "ricosuave666" if t["hash"] in rico_w else "AugsburgFClover" if t["hash"] in augs_w else "other"
        by[k] += 1
        if k != "other":
            amt[k] += int(t["value"])
    check("D1", by["other"] == 0 and by["AugsburgFClover"] == 4,
          f"pool credits of {RICO_EXIT}: {by} ; USDC {amt['ricosuave666'] / 1e6} from ricosuave666, {amt['AugsburgFClover'] / 1e6} from AugsburgFClover")
    # D2: the four AugsburgFClover withdrawals, read from their receipts: USDC.e leaves the proxy, USDC reaches the exit wallet
    legs = []
    for h in ["0x287aabc7af352f70e1c9a5f8355cda976977476c868effa10a540822d340d9b0",
              "0xcbd9284509cd34dbf947150d73b484000ecd111a46e106f2d1d61b4e1d52f03c",
              "0x3282d81f651d0b2b138d9abbb54bc9b0002d8645aa0c94aa6f1b33cd8975b618",
              "0xeda99492f49df5df41cd96477d32fdeeef706d959e308b1836578d489d5ba1dc"]:
        _, rc = evm("r2", "polygon", h)
        tr = transfers(rc)
        out_ = sum(v for a, f, t, v in tr if a == USDCE and f == AUGS)
        in_ = sum(v for a, f, t, v in tr if a == USDC and t == RICO_EXIT)
        legs.append((h, out_, in_, h in augs_w))
    check("D2", all(o > 0 and i > 0 and w for _, o, i, w in legs),
          f"4 same-hash withdrawals: {sum(o for _, o, _, _ in legs) / 1e6} USDC.e out of AugsburgFClover, "
          f"{sum(i for _, _, i, _ in legs) / 1e6} USDC into the exit wallet")
    # D3: deposits of AugsburgFClover paid from the exit wallet through two deposit addresses (behaviour)
    rows = []
    for dep_addr, h_dep in [("0xc0809d7e28dd52a35887bbd822635e13f3c6d7a4", "0x3b9110c41092f3b232e7197129fa3281ee03c5e960670699ed2af75416a6d48d"),
                            ("0x5b9a5de307d566cac0cc02c32416c91998ff7e19", "0x3aa989078be33b97655467fb21a84aecb23a688872274c8cb3a6a275eed5d1fe")]:
        t = [x for x in es_tokens("r2", dep_addr) if x["contractAddress"].lower() == USDC and int(x["value"]) >= 10**6]
        fin = [x for x in t if x["from"].lower() == RICO_EXIT and x["to"].lower() == dep_addr]
        fout = [x for x in t if x["from"].lower() == dep_addr]
        cred = [r for r in augs if r["type"] == "DEPOSIT" and r["transaction_hash"] == h_dep][0]
        rows.append((dep_addr, len(t), int(fin[0]["value"]) / 1e6, int(fout[0]["timeStamp"]) - int(fin[0]["timeStamp"]),
                     float(cred["usdc_size"]), int(cred["timestamp"]) - int(fin[0]["timeStamp"])))
    check("D3", all(n == 2 and 0 < fwd < 60 and 0 < lag < 1200 and abs(cr / v - 1) < 0.002 for _, n, v, fwd, cr, lag in rows),
          "deposit addresses " + "; ".join(f"{a}: {v} USDC from the exit wallet, forwarded {fwd} s later, "
                                            f"{cr} USDC.e credited {lag} s after" for a, n, v, fwd, cr, lag in rows))
    # D4: Relay orders between AugsburgFClover and ricosuave666's wallets
    ao = relay_orders("r2", AUGS)
    want = {"0x30923e8a75b0b309": (AUGS, RICO_EXIT.lower(), 137), "0xd2efe205fe9fa43f": (AUGS, RICO_EXIT.lower(), 137),
            "0xb16b9f4bd4238c94": (I6PJ, AUGS, 792703809), "0x46d3370a2f9e1a92": (I6PJ, AUGS, 792703809)}
    seen = []
    for r in ao:
        k = r["id"][:18]
        if k in want:
            u_, rc_, chain = want[k]
            ok = r["status"] == "success" and r["user"].lower() == u_.lower() and r["recipient"].lower() == rc_.lower()
            ins = r["data"]["inTxs"][0]
            seen.append((k, ok, ins["chainId"] == chain, r["createdAt"][:19],
                         r["data"]["metadata"]["currencyIn"]["amountFormatted"], r["data"]["metadata"]["currencyOut"]["amountFormatted"]))
    check("D4", len(seen) == 4 and all(a and b for _, a, b, *_ in seen), "Relay orders " + "; ".join(
        f"{k} {t} {i}->{o}" for k, a, b, t, i, o in seen))
    # E: metushelah, funded from J4t48znS through 3cCK8epV and Relay, cashed out to J4t48znS
    mo = relay_orders("r2", METU)
    ids = {r["id"]: r for r in mo}
    dep = [r for r in activity("r2", METU) if r["type"] == "DEPOSIT"]
    calls = []
    for r in dep:
        tx, _ = evm("r2", "polygon", r["transaction_hash"])
        tail = "0x" + tx["input"][-64:]
        o = ids.get(tail)
        calls.append((r["transaction_hash"], tail in ids, o and o["user"] == I3CC and o["recipient"].lower() == METU))
    check("E1", len(calls) == 2 and all(a and b for _, a, b in calls),
          "both metushelah deposits are Relay fills whose calldata ends with an order id of user 3cCK8epV")
    w = [r for r in mo if r["user"].lower() == METU]
    check("E2", len(w) == 1 and w[0]["recipient"] == J4T and w[0]["status"] == "success",
          f"metushelah withdrawal Relay order {w[0]['id']} to {w[0]['recipient']}: "
          f"{w[0]['data']['metadata']['currencyIn']['amountFormatted']} USDC.e -> {w[0]['data']['metadata']['currencyOut']['amountFormatted']} USDC")
    sol = []
    for sig, lam in [("4u8ca3wrjn4hUZNNmSDzZGXDPGaV7ukqxKBkjgzwXEr3xXcphm1Fc4b5ZgarD6Sgpc3qCLKQuYNK9qN3UyeVRYC7", 6_000_000_000),
                     ("5oPZnsZDGJVLXZumX6XMH8CCPTgRLrcRkskryoJTyB8mt69onjE8nWoXevNReSq2dvgKWXF49QjPr2yi8NnxYYRL", 20_000_000_000)]:
        t = sol_tx(sig)
        l3, _, _ = sol_deltas(t, I3CC)
        lj, _, _ = sol_deltas(t, J4T)
        sol.append((sig[:12], utc(t["blockTime"]), l3 == lam, lj <= -lam))
    check("E3", all(a and b for _, _, a, b in sol), "J4t48znS -> 3cCK8epV SOL transfers " + "; ".join(f"{s} {t}" for s, t, _, _ in sol))
    cm = cash_by_market(activity("r2", METU))
    y19, y16 = cm.get("Israel strike on Yemen by September 19?"), cm.get("Will Israel strike Yemen on September 16 ET?")
    stake = cm.get("__buys__Israel strike on Yemen by September 19?", 0) + cm.get("__buys__Will Israel strike Yemen on September 16 ET?", 0)
    check("E4", y19 == 109.45 and y16 == 294.87, f"metushelah cash: +{y19} (by Sept 19) and +{y16} (on Sept 16), total {round(y19 + y16, 2)}, stake {stake}")
    # F/G: J4t48znS -> 6pJEdTi1 -> AugsburgFClover, and the 6 January 2026 sequence
    ro = relay_orders("r1", J4T)
    jan = [r for r in ro if r["user"].lower() == RICO and r["recipient"] == J4T]
    check("G1", len(jan) == 1 and jan[0]["createdAt"].startswith("2026-01-06T11:55"),
          f"ricosuave666 Relay order {jan[0]['id']} {jan[0]['createdAt']}: {jan[0]['data']['metadata']['currencyIn']['amountFormatted']} USDC.e -> "
          f"{jan[0]['data']['metadata']['currencyOut']['amountFormatted']} USDC to {J4T}")
    ca = cash_by_market(augs)
    total = round(sum(v for k, v in ca.items() if not k.startswith("__buys__")), 2)
    check("G3", total == -2498.46, f"AugsburgFClover cash over all its markets: {total}")
    check("G2", ca.get("__buys__Israel strikes Iran by January 31, 2026?") == 7000.0 and ca.get("__buys__Israel strikes Iran by March 31, 2026?") == 2000.0,
          "AugsburgFClover buys on 6 Jan 2026: 7,000 'by January 31, 2026', 2,000 'by March 31, 2026'")
    # H: the 74,680.134173 USDC wallet
    e = es_tokens("r1", E559)
    first = [x for x in e if x["contractAddress"].lower() == USDC and x["to"].lower() == E559][0]
    check("H1", first["from"].lower() == RICO_EXIT and int(first["value"]) == 74680134173 and utc(first["timeStamp"]) == "2025-06-26 14:07:14",
          f"first USDC inflow of {E559}: {int(first['value']) / 1e6} from the exit wallet at {utc(first['timeStamp'])}, tx {first['hash']}")
    me = activity("r2", MEEE)
    md = sorted([r for r in me if r["type"] == "DEPOSIT"], key=lambda r: int(r["timestamp"]))
    eo = relay_orders("r1", E559)
    rel = [r for r in eo if r["recipient"].lower() == MEEE]
    da = [x for x in es_tokens("r2", "0x31c88bbb26203b52fd34fc44cde7843557b8b518")
          if x["contractAddress"].lower() == USDC and int(x["value"]) >= 10**6]  # zero-value poisoning rows ignored
    lag = int(md[0]["timestamp"]) - int(da[0]["timeStamp"])
    check("H2", len(md) == 2 and utc(md[0]["timestamp"]) == "2025-06-26 14:13:00" and len(rel) == 1 and len(da) == 2
          and da[0]["from"].lower() == E559 and int(da[0]["value"]) == 1000000000 and lag == 28
          and rel[0]["data"]["inTxs"][0]["hash"] == md[1]["transaction_hash"],
          f"meeeeeeeeeeeeeeee deposits: {md[0]['usdc_size']} at {utc(md[0]['timestamp'])} (28 s after 1,000 USDC from {E559} to its deposit address) "
          f"and {md[1]['usdc_size']} via Relay order {rel[0]['id'] if rel else None}")
    eth = load("r2", f"etherscan/1_tokentx_{E559}_p1.json")["result"]
    real = [x for x in eth if x["contractAddress"].lower() == USDT_ETH and int(x["value"]) >= 10**6]
    exit_ = [x for x in real if x["to"].lower() == E559]
    sent = [x for x in real if x["from"].lower() == E559]
    check("H3", len(exit_) == 1 and int(exit_[0]["value"]) == 65649069103
          and sum(int(x["value"]) for x in sent if x["to"].lower() == "0x43d44a06325db643f8eb5ac998b5355978069bfc") == 65362000000,
          f"Ethereum: {int(exit_[0]['value']) / 1e6} USDT out of the Polygon PoS bridge at {utc(exit_[0]['timeStamp'])}, "
          f"then {sum(int(x['value']) for x in sent) / 1e6} USDT to 0x43d44a06325db643f8eb5ac998b5355978069bfc")


# ---------- J. Pulser (PR 30 and group F) ----------
PR30_CSV = HERE / "data" / "pr30_direct_transfers.csv"


def check_pulser():
    import csv
    rows = list(csv.DictReader(PR30_CSV.open()))
    ok = 0
    for r in rows:
        h, fr, to = r["polygon_tx_hash"], r["from_wallet"].lower(), r["to_wallet"].lower()
        _, rc_es = evm("r2", "polygon_etherscan", h)       # Etherscan v2 proxy (independent of the drpc copy)
        _, rc_dr = evm("r1", "polygon", h)                 # drpc copy used by PR 29
        same = [(l["address"], l["topics"], l["data"]) for l in rc_es["logs"]] == [(l["address"], l["topics"], l["data"]) for l in rc_dr["logs"]]
        moved = sum(v for a, f, t, v in transfers(rc_es) if a == USDCE and f == fr and t == to)
        ok += rc_es["status"] == "0x1" and same and abs(moved / 1e6 - float(r["usdc_amount"])) <= 2e-6
    check("J1", ok == len(rows) == 27, f"PR 30 transfers re-read from Etherscan receipts: {ok} of {len(rows)} match sender, receiver and amount; logs identical to drpc")
    # J2: Pulser <-> 0x0bb95597 (group F), same hash on both sides, first deposit of 0x0bb95597
    f2 = sorted(dw("r2", F2), key=lambda r: int(r["timestamp"]))
    first = f2[0]
    _, rc1 = evm("r2", "polygon", "0x5d68fa366a958f8457bac7106d0a2106711d4055cb885fe6d5247df3c8b8f2c7")
    _, rc2 = evm("r2", "polygon", "0x80ccdfee56f397eb184c9d486d1fb60eb77550b37c6a59ca087255b42c633499")
    a = [v for x, f, t, v in transfers(rc1) if x == USDCE and f == PULSER and t == F2]
    b = [v for x, f, t, v in transfers(rc2) if x == USDCE and f == F2 and t == PULSER]
    check("J2", first["type"] == "DEPOSIT" and first["transaction_hash"] == "0x5d68fa366a958f8457bac7106d0a2106711d4055cb885fe6d5247df3c8b8f2c7"
          and a == [200000000] and b == [140356800],
          f"Pulser -> 0x0bb95597 200.0 USDC.e at {utc(first['timestamp'])} (its first deposit), 0x0bb95597 -> Pulser 140.3568 at {utc(f2[1]['timestamp'])}")
    # J3: how often Pulser pays the first deposit of an account it trades with
    partners = [p for p in (HERE / "data" / "pulser_proxy_partners.txt").read_text().split() if p]
    pw = {r["transaction_hash"] for r in dw("r1", PULSER) if r["type"] == "WITHDRAWAL"}
    firsts = []
    for p in partners:
        d = sorted([r for r in dw("r2", p) if r["type"] == "DEPOSIT"], key=lambda r: int(r["timestamp"]))
        if d and d[0]["transaction_hash"] in pw:
            firsts.append(p)
    uma = {"0xee3afe347d5c74317041e2618c49534daf887c24", "0x2c0367a9db231ddebd88a94b4f6461a6e47c58b1"}  # UMA oracles on Polygon
    calls = {}
    for w in ("0xbbcab5377bbca9cccbc48d0a7afbeaf78c741f90", "0x3e8379fa4e49648d88dc6c885abd776adbdc2132"):
        txl = load("r2", f"etherscan/{w}/137_txlist_p1.json")["result"]
        calls[w] = sum(1 for t in txl if t["from"].lower() == w and t["to"].lower() in uma)
    flows = list(csv.DictReader((HERE.parent / "inca-crosscheck-2026-11-06/data/flows.csv").open()))  # PR 29, in git
    car = [r for r in flows if r["wallet"] == "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b" and r["counterparty"] == "0xbbcab5377bbca9cccbc48d0a7afbeaf78c741f90"]
    to_ = round(sum(float(r["usdc"]) for r in car if r["type"] == "WITHDRAWAL"), 2)
    from_ = round(sum(float(r["usdc"]) for r in car if r["type"] == "DEPOSIT"), 2)
    check("J4", calls["0xbbcab5377bbca9cccbc48d0a7afbeaf78c741f90"] == 40 and calls["0x3e8379fa4e49648d88dc6c885abd776adbdc2132"] == 168
          and to_ == 10700.0 and from_ == 250.0, f"UMA oracle calls: {calls}; Car -> 0xbbcab537 {to_}, 0xbbcab537 -> Car {from_}")
    import csv as _csv
    t5 = HERE.parent.parent / "investigations/maduro-iran/sources/phase2/TABLE5_population_iran.csv"
    t5a = HERE.parent.parent / "investigations/maduro-iran/sources/phase2/TABLE5_population_iranA.csv"
    rows5 = [r for f in (t5, t5a) for r in _csv.DictReader(f.open())]
    got = sorted((r["wallet"], r["first_buy_utc"], r["capital_usd"], r["vwap"]) for r in rows5 if r["wallet"] in (PULSER, F2))
    check("J5", (F2, "2026-02-28 05:55:05", "1150.0", "0.23") in got and (PULSER, "2026-02-28 05:58:47", "220.0", "0.22") in got
          and (PULSER, "2026-02-26 21:45:20", "2000.0", "0.1") in got, f"February 2026 entries (phase 2 tables on main): {got}")
    check("J3", len(partners) == 16 and len(firsts) == 7, f"Pulser pays the first deposit of {len(firsts)} of its {len(partners)} direct Polymarket partners")


# ---------- K. Solana arrivals, return path to Ethereum and the shared Binance deposit ----------
def check_solana_and_return():
    from abi import b58decode, DLN_FULFILLED, decode_dln_fulfilled
    # K1: three Mayan Swift orders filled to J4t48znS; the order state account named by Mayan's index is in the fill
    for key, src, amount_out in [("51466fd7", "0x5da2a61dd3c01df76dece631bd66f0c0d1c35fe44e9213171f96616987c2789d", ("SOL", 15611415587)),
                                 ("a17cf61a", None, ("USDC", 98378852846)),
                                 ("f42e5919", "0x2869df2eb42836b094cb59d36123a32e7dda3636e1b0854d92a79840e24633c5", ("SOL", 64309615064))]:
        d = load("r2", f"http/mayan_order_{key}.json")
        tx = sol_tx(d["fulfillTxHash"])
        lam, tok, keys = sol_deltas(tx, J4T)
        got = lam if amount_out[0] == "SOL" else tok.get(SOL_USDC, 0)
        prog = {i.get("programId") for i in tx["transaction"]["message"]["instructions"]}
        check("K1", d["destAddress"] == J4T and d["stateAddr"] in keys and got == amount_out[1]
              and "BLZRi6frs4X4DNLw56V4EXai1b6QVESN1BhHBTYM9VcY" in prog and (src is None or d["sourceTxHash"] == src),
              f"Mayan Swift {d['orderHash'][:18]}: fill {d['fulfillTxHash'][:16]} at {utc(tx['blockTime'])}, "
              f"{got / (1e9 if amount_out[0] == 'SOL' else 1e6)} {amount_out[0]} to J4t48znS, state {d['stateAddr']} in the fill")
    # K2: the deBridge fill on Solana carries the order id of A4 and pays exactly the take amount in SOL
    tx = sol_tx("5SQUJEfVXmFMh64nbnD4Ykd1kGjUQfVDkhrYrqyUsjUL21TrCtpmcfEUVHA1xYTwg5hvGgeVoVmJwu1af6VAmXGx")
    oid = "c2c2f654a3666411a7df472002245475af17094929b9cedd4de7a7df1437cdbe"
    blobs = [b58decode(i["data"]).hex() for i in tx["transaction"]["message"]["instructions"] if i.get("data")]
    lam, _, _ = sol_deltas(tx, J4T)
    check("K2", any(oid in b for b in blobs) and lam == 1259690717, f"DLN fill at {utc(tx['blockTime'])}: order id in the instruction data, +{lam / 1e9} SOL to J4t48znS")
    # K3: the deBridge fill on Ethereum (PorcoRosso) carries the order id of C1
    _, rc = evm("r2", "ethereum_etherscan", "0xf8bab9e89c4696e2e6fdbf31e0a1890b614e0dae6586b519fd9af168324beda8")
    f = [decode_dln_fulfilled(l) for l in rc["logs"] if l["topics"] and l["topics"][0] == DLN_FULFILLED]
    check("K3", len(f) == 1 and f[0]["orderId"] == "0x89fcc5557ea9140a42c7490de394b3581ed3d75050a565788587746ca69604a8"
          and f[0]["receiverDst"] == PORCO_EXIT and f[0]["takeAmount"] == 43381968520308833448,
          f"FulfilledOrder {f[0]['orderId'] if f else None} on Ethereum to PorcoRosso's own address")
    # K4: Relay fills into J4t48znS equal the order outputs (metushelah 16 Sept 2025, ricosuave666 6 Jan 2026)
    for sig, amt in [("AzViX9FP", 6436688402), ("5XWZBBDo", 24982496121)]:
        full = [p for p in load("r2", "sol/uci4HkXp8GGrCRhGQJ6YMxGDj7jQWwoQyvrB5QjmDdb/sigs_p000.json")["result"] if p["signature"].startswith(sig)][0]["signature"]
        _, tok, _ = sol_deltas(sol_tx(full), J4T)
        check("K4", tok.get(SOL_USDC) == amt, f"Relay fill {full[:16]}: +{tok.get(SOL_USDC, 0) / 1e6} USDC to J4t48znS")
    # K5: J4t48znS -> 6pJEdTi1 legs, and 6pJEdTi1's Relay orders pay AugsburgFClover
    t1 = sol_tx("qoFDmKqHSUr3Bvh6uqFtkyhwBqQPxLTLFvmWxu7PXESZX2HqyddRdtVuK9TkXoPmdcGGy8nHZ3W2J4W6gC2LQjd")
    t2 = sol_tx("51JHwuzqgcmvFeYwG2LaUJfP91skyNycsNPpx2BDoZYFisRBC95G7aMQX8drxFZQ3HqZAG7hQLN5mTySPcsAjN9g")
    l6, _, _ = sol_deltas(t1, I6PJ)
    _, tj, _ = sol_deltas(t2, J4T)
    _, t6, _ = sol_deltas(t2, I6PJ)
    check("K5", l6 == 1_100_000_000 and tj.get(SOL_USDC) == -24987099103 and t6.get(SOL_USDC) == 24987099103,
          f"J4t48znS -> 6pJEdTi1: 1.1 SOL at {utc(t1['blockTime'])}; 24,987.099103 USDC at {utc(t2['blockTime'])}")
    # K6: CCTP burn from J4t48znS to the exit wallet on Ethereum (domain 0), and its mint there
    tx = sol_tx("5tHjtiH8n1oX9acYGWCD7ucaWZivgEomCzcmsRaP82LfcacJhxPsCqAtvAWt536J1pj2bzJSZjrnHWpymCzaGFhq")
    ix = [i for i in tx["transaction"]["message"]["instructions"] if i.get("programId") == "CCTPiPYPc6AsJuwueEnWgSgucamXDZwBd53dQ11YiKX3"][0]
    d = b58decode(ix["data"])
    amount, domain, recip = int.from_bytes(d[8:16], "little"), int.from_bytes(d[16:20], "little"), "0x" + d[32:52].hex()
    eth = load("r2", f"etherscan/1_tokentx_{RICO_EXIT}_p1.json")["result"]
    mint = [x for x in eth if x["from"] == "0x" + "0" * 40 and int(x["value"]) == amount]
    check("K6", domain == 0 and recip == RICO_EXIT and len(mint) == 1,
          f"CCTP DepositForBurn {amount / 1e6} USDC at {utc(tx['blockTime'])}, domain {domain}, recipient {recip}; minted on Ethereum at {utc(mint[0]['timeStamp']) if mint else None}")
    # K7: one Binance deposit address credited by the exit wallet (Ethereum) and by 0xe559eb45 (Polygon)
    BIN = "0xaa00faedb1146785792f00e2feac69adbdaba42b"
    txl = load("r2", f"etherscan/1_txlist_{BIN}_p1.json")["result"]
    ins = [x for x in txl if x["to"].lower() == BIN and int(x["value"]) > 0]
    outs = [x for x in txl if x["from"].lower() == BIN and int(x["value"]) > 0]
    swept = all(any(o["to"].lower() == "0x28c6c06298d514db089934071355e5743bf21d60" and 0 < int(o["timeStamp"]) - int(i["timeStamp"]) < 3600 for o in outs) for i in ins if int(i["value"]) >= 10**17)
    rico_leg = [x for x in ins if x["from"].lower() == RICO_EXIT]
    poly = [x for x in es_tokens("r2", BIN) if x["contractAddress"].lower() == USDC]
    e_leg = [x for x in poly if x["from"].lower() == E559]
    p_out = [x for x in poly if x["from"].lower() == BIN and x["to"].lower() == "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"]
    check("K7", swept and len(rico_leg) == 1 and len(e_leg) == 1 and len(p_out) == 1,
          f"Binance deposit {BIN}: {int(rico_leg[0]['value']) / 1e18} ETH from the exit wallet at {utc(rico_leg[0]['timeStamp'])} (Ethereum, swept to Binance 14); "
          f"{int(e_leg[0]['value']) / 1e6} USDC from {E559} at {utc(e_leg[0]['timeStamp'])} (Polygon, swept to Binance 48)")


# ---------- B5-B7. truthlord on Solana ----------
GEU = "GeuDFmsBhiSndUUf8sie2wpnQHLhi55Be2yXACA6aDat"
ERG = "ERgKoqmGtmeTy7iUXF8r3nGnd5N5FDA8aU4fBZ79AA6i"
HFG_USDC = "CDYN5tLW3QXYbLBSCsvSZH3D3QLvc3A3toVGNByah3An"


def check_truthlord_solana():
    from abi import b58decode
    sigs = load("r2", f"sol/{HFG_USDC}/sigs_p000.json")["result"]
    for oid, take in [("46096f6ed5101475c02ee7e48a2bef2b059bd436e93cd33ee25e142a11e6395f", 19979024709),
                      ("8b4630b081a897487747763e361804e1df5938a741be634c1056a3cc9ec41d7c", 999200160),
                      ("e16cfb905cdff0c4b5e6d3e6c364137fd69de592e42fc674356e2a0016495325", 28957860335)]:
        hit = None
        for sg in sigs:
            if utc(sg["blockTime"])[:10] not in ("2025-06-16", "2025-08-20") or sg.get("err"):
                continue
            tx = sol_tx(sg["signature"])
            blobs = [b58decode(i["data"]).hex() for i in tx["transaction"]["message"]["instructions"] if i.get("data")]
            if any(oid in b for b in blobs):
                hit = (sg["signature"], tx)
        ok = False
        if hit:
            _, tok, _ = sol_deltas(hit[1], HFG)
            ok = tok.get(SOL_USDC) == take
        check("B5", ok, f"deBridge fill of order 0x{oid[:16]}…: {hit[0][:16] if hit else None} at {utc(hit[1]['blockTime']) if hit else None}, "
              f"+{take / 1e6} USDC to HfGp55mp (order id in the instruction data)")
    legs = []
    owner_sigs = []
    n = 0
    while True:
        try:
            owner_sigs += load("r2", f"sol/{HFG}/sigs_p{n:03d}.json")["result"]
        except FileNotFoundError:
            break
        n += 1
    for pre in ("4xfeMt1WVkbL46", "3ZgKMDeJwdiqAJ"):
        sg = [x["signature"] for x in owner_sigs if x["signature"].startswith(pre)][0]
        tx = sol_tx(sg)
        _, th, _ = sol_deltas(tx, HFG)
        _, tg, _ = sol_deltas(tx, GEU)
        legs.append((utc(tx["blockTime"]), -th.get(SOL_USDC, 0), tg.get(SOL_USDC, 0)))
    go = relay_orders("r1", GEU)
    to_truth = [r for r in go if r["status"] == "success" and r["recipient"].lower() == "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44"]
    check("B6", all(a == b > 0 for _, a, b in legs) and len(to_truth) == 3,
          "HfGp55mp -> GeuDFmsB " + "; ".join(f"{a / 1e6} USDC at {t}" for t, a, _ in legs)
          + f"; GeuDFmsB -> truthlord: {len(to_truth)} successful Relay orders, "
          + ", ".join(r["data"]["metadata"]["currencyOut"]["amountFormatted"] for r in to_truth)
          + f" = {round(sum(float(r['data']['metadata']['currencyOut']['amountFormatted']) for r in to_truth), 2)} USDC.e")
    sg = [x["signature"] for x in owner_sigs if x["signature"].startswith("9ctPajkoqEuuLT")][0]
    tx = sol_tx(sg)
    _, th, _ = sol_deltas(tx, HFG)
    _, te, _ = sol_deltas(tx, ERG)
    check("B7", th.get(SOL_USDC) == -19979024710 and te.get(SOL_USDC) == 19979024710,
          f"HfGp55mp -> {ERG} 19,979.02471 USDC at {utc(tx['blockTime'])}, 15 min after the deBridge order of 07:40:43")


def main():
    for f in (check_bridges, check_rico_network, check_solana_and_return, check_truthlord_solana, check_pulser):
        try:
            f()
        except Exception as e:  # a missing file or a decoding error is a failed check, never a silent pass
            check(f.__name__, False, f"{type(e).__name__}: {e}")
    if RAW_MODE:
        (EVID / "NEEDED.txt").parent.mkdir(exist_ok=True)
        (EVID / "NEEDED.txt").write_text("\n".join(sorted(NEEDED)) + "\n")
    n = sum(r["ok"] for r in RESULTS)
    for r in RESULTS:
        print("PASS" if r["ok"] else "FAIL", r["id"], r["detail"])
    print(f"{n}/{len(RESULTS)} checks pass")
    if not RAW_MODE:
        (HERE / "verification.json").write_text(json.dumps({"passed": n, "total": len(RESULTS), "checks": RESULTS}, indent=1))
    sys.exit(0 if n == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
