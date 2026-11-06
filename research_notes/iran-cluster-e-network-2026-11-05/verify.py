#!/usr/bin/env python3
"""Offline verifier for the cluster E network note.

Reads only the archived responses in evidence/ and in the previous note's evidence/ (no network).
It does not import the collection or build scripts. Exit code 0 only when every check passes.
Writes verification.json next to this file.

    python3 -I verify.py
"""
import gzip, hashlib, json, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE / "evidence"
PREV = HERE.parent / "iran-solana-beneficiary-2026-11-05" / "evidence"
PM_REF = "funxyz|su4gnoxz14"
BIN_DEP = "0x519fa16e9897132b7633f634b76306a327839e06"
W7702 = "0xa6c221448af73af8350291c5cdcd877b39683766"
CDC_DEP = "0x9063493a4233006be654da772ef4dc38720cac55"
BYB_EVM = "0x93b7e169b93ece646d08cedbb8fa505796a5b96b"
BEN = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
USDC_POL = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
USDCE_POL = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
PUSD = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
BSC_USDC = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
USDC_SOL = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
A = {  # account name -> Polymarket proxy wallet
    "BlueElephant666": "0xcc32a117ac254fe51fd867b928e45492b1f6dc7e", "SemiconductorIT": "0xd36fa21eb3fa7b1aaf97c8499253f76f82a16d48",
    "oveiStheair": "0x97e490d61b530d5078348d76143a25c43a47164d", "aaamsaasa": "0x0a142164f48dab6448872f0abac310d03e305316",
    "carltiosway": "0xd109e93d5a86a68982c0b5e94323d01ab728de03", "yellowtop1": "0x3e44cfbf234a9616c5f9edddd6bd6bd068854d4a",
    "Momentumgod": "0x75f23439b88c30ff00b07dcc1a93961780d47c82",
    "TBFMM": "0xc4fdb47064604dc198a911afae48d9e4236b4b39", "ILOVEYOUBABYZZ": "0x909fa9f89976058b8b3ab87adc502ec7415ea8c3",
    "ALLOWMETOSHOWU1": "0xc8a6d6b4f5d66a1211ed678edb828acca25c5d97", "Domariocarios": "0x72630d496a5c3c86665d029a4e05875c0ea9a031",
    "rrrrgggbbbclat": "0xe756468f0869e27d6c1c51a10993fd7ce4627866", "ParkingLocator": "0x4f5e7aca62b7fc31e0611b24085bb38574c88903",
    "0x8C33013f (no username)": "0x8c33013f39b98b3a784f7718ce8a7947db6b59fa",
    "TheOneWhoKnocks1312": "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a", "DonkeyDonkey999": "0xcb18ea2923d957bd9cf049cce60a87638722f867",
    "0x82be522b (no username)": "0x82be522b4c2936ee10129239cef501f8ba2bcf36", "FluentCastle1352": "0xb355589a08b22bd9c5602b345ad8294aa04a1494",
    "Bigboyslatvian": "0xfd9e4d14a02a0ea10b87142198af8fed7c2dda6c",
}
KNOWN_BEFORE = {"BlueElephant666", "SemiconductorIT", "oveiStheair", "aaamsaasa", "carltiosway", "yellowtop1", "Momentumgod"}
ALIAS = {"0x200b195893faf4da3f431125afc17d0903fc8ea6": "ALLOWMETOSHOWU1", "0x44a2c68087a3e6a9a3eedd9cf9c25fd76241e978": "rrrrgggbbbclat"}
results = []


def check(name, ok, **values):
    results.append({"check": name, "status": "PASS" if ok else "FAIL", **values})


def load(p):
    return json.loads(Path(p).read_text())


def ts(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


# 1. Integrity of every evidence file
listed = {}
for line in (HERE / "SHA256SUMS.txt").read_text().splitlines():
    h, p = line.split("  ", 1)
    listed[p] = h
bad = [p for p, h in listed.items() if not (HERE / p).is_file() or hashlib.sha256((HERE / p).read_bytes()).hexdigest() != h]
extra = [str(p.relative_to(HERE)) for p in EV.rglob("*") if p.is_file() and str(p.relative_to(HERE)) not in listed]
meta_bad = []
for p in EV.rglob("*.meta.json"):
    m, body = load(p), p.with_name(p.name[:-len(".meta.json")] + ".json")
    if "sha256" in m and body.exists() and hashlib.sha256(body.read_bytes()).hexdigest() != m["sha256"]:
        meta_bad.append(str(body.relative_to(HERE)))
check("integrity_sha256", not bad and not extra and not meta_bad, files=len(listed), mismatched=bad, unlisted=extra, meta_mismatched=meta_bad)

# 2. Relay orders (user-side and recipient-side pages), deduplicated
orders, done = {}, {}
for p in sorted((EV / "relay").glob("relay_user_*")):
    if p.name.endswith("_DONE.json"):
        done[p.name[len("relay_user_"):-len("_DONE.json")].lower()] = load(p)
    elif not p.name.endswith(".meta.json"):
        for r in load(p).get("requests", []):
            orders[r["id"]] = r


def low(a):
    return a.lower() if (a or "").startswith("0x") else a


def O(r):
    m = r["data"]["metadata"]
    return {"id": r["id"], "ok": r["status"] == "success" and r.get("referrer") == PM_REF, "t": ts(r["createdAt"]),
            "user": low(r["user"]), "to": low(r["recipient"]), "o": m["currencyIn"]["currency"]["chainId"],
            "d": m["currencyOut"]["currency"]["chainId"], "in": float(m["currencyIn"]["amountFormatted"]),
            "out": float(m["currencyOut"]["amountFormatted"]), "out_raw": m["currencyOut"]["amount"], "in_raw": m["currencyIn"]["amount"],
            "in_tx": [low(x.get("hash")) for x in r["data"].get("inTxs") or []], "out_tx": [low(x.get("hash")) for x in r["data"].get("outTxs") or []]}


OR = [O(r) for r in orders.values()]

prev_ids = set()
for p in (PREV / "http").glob("relay_*.json"):
    if not p.name.endswith(".meta.json"):
        prev_ids |= {r["id"] for r in load(p).get("requests", []) if r.get("recipient") == BEN}
ben_ids = {o["id"] for o in OR if o["to"] == BEN}
check("relay_index_control_beneficiary", ben_ids == prev_ids and len(ben_ids) == 11 and done[BEN.lower()]["termination"] == "END",
      orders=len(ben_ids), same_as_previous_note=ben_ids == prev_ids)

used = list(A.values()) + [BIN_DEP, W7702, CDC_DEP, BYB_EVM] + list(ALIAS)
missing_done = [a for a in A.values() if a not in done]
check("relay_pages_complete", not missing_done and all(done[a]["termination"] == "END" for a in done if a in used),
      addresses_with_complete_pages=sum(1 for a in used if a in done), not_queried=missing_done)

# 3. Polymarket activity (reduced copies), this note first, then the previous note
acts = {}
for base in (EV / "polymarket_reduced", PREV / "polymarket_reduced"):
    got = defaultdict(list)
    for p in sorted(base.glob("pm_v2activity_*_p*.json")):
        got[p.name.split("pm_v2activity_")[1].split("_p")[0].lower()] += load(p).get("data", [])
    for a, xs in got.items():
        acts.setdefault(a, xs)
WD = {(x.get("transaction_hash") or "").lower(): (a, x) for a, xs in acts.items() for x in xs if x["type"] == "WITHDRAWAL"}
DEP = {(x.get("transaction_hash") or "").lower(): (a, x) for a, xs in acts.items() for x in xs if x["type"] == "DEPOSIT"}
NAME = {v: k for k, v in A.items()}
names_ok = {n: any(x.get("name") == n for x in acts.get(a, [])) for n, a in A.items() if "(" not in n}
check("accounts_are_polymarket_accounts", all(names_ok.values()) and all(acts.get(a) for a in A.values()),
      accounts=len(A), new_accounts=len(A) - len(KNOWN_BEFORE), username_matches=names_ok)


def etx(addr, base=PREV):
    return load(base / "etherscan" / f"137_tokentx_{addr}_p1.json")["result"]


def txlist(addr):
    return load(PREV / "etherscan" / f"137_txlist_{addr}_p1.json")["result"]


def receipt(h):
    for base in (EV / "polygon", PREV / "polygon"):
        p = base / f"{h}.eth_getTransactionReceipt.json"
        if p.exists():
            return load(p)["result"]
    return None


def erc20(rc, token=None):
    return [(l["address"].lower(), "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], int(l["data"], 16))
            for l in rc["logs"] if l["topics"][0] == TRANSFER and len(l["topics"]) == 3 and (token is None or l["address"].lower() == token)]


tags = {}
for base in (EV / "http", PREV / "http"):
    for p in base.glob("bs_meta_*.json"):
        if p.name.endswith(".meta.json"):
            continue
        c = int(p.name.split("_")[2])
        for k, v in (load(p).get("addresses") or {}).items():
            tags.setdefault((c, k.lower()), [t.get("name") for t in v.get("tags", [])])


def tagged(c, a, word):
    return any(word in (t or "") for t in tags.get((c, a.lower()), []))


# 4. 0x519fa16e is a Binance customer deposit address
gas = [x for x in txlist(BIN_DEP) if x["to"] == BIN_DEP and int(x["value"]) > 0]
outs = [t for t in etx(BIN_DEP) if t["from"] == BIN_DEP and t["contractAddress"] == USDC_POL and int(t["value"]) > 0]
check("binance_deposit_address", gas and all(g["from"] == "0x9430801ebaf509ad49202aabc5f5bc6fd8a3daf8" for g in gas)
      and tagged(137, "0x9430801ebaf509ad49202aabc5f5bc6fd8a3daf8", "Binance: Deposit Funder")
      and all(tagged(137, t["to"], "Binance") for t in outs),
      gas_topups=len(gas), usdc_outflows=len(outs), outflow_recipients=sorted({t["to"] for t in outs}))

# 5. 0xa6c22144: EIP-7702 delegated wallet, every outflow to one address
d7702 = load(EV / "polygon" / "0xe2924bfc47fde965301f1e96e692884437dd41f7a8df0823a415db27bb5c1cbd.eth_getTransactionByHash.json")["result"]
w_outs = [t for t in etx(W7702) if t["from"] == W7702 and t["contractAddress"] == USDC_POL and int(t["value"]) > 0]
check("eip7702_wallet_single_sink", d7702["type"] == "0x4" and d7702["to"] == W7702
      and d7702["authorizationList"][0]["address"] == "0x0000fb7702036ff9f76044a501ac1aa74cbab16b"
      and {t["to"] for t in w_outs} == {"0x852dc1c875f0117ea0808610010893e4c576b6a9"},
      outflows=len(w_outs), total_usdc=round(sum(int(t["value"]) for t in w_outs) / 1e6, 6))

# 6. 0x9063493a: forwards every inflow to Crypto.com 39
c_outs = [t for t in etx(CDC_DEP, EV) if t["from"] == CDC_DEP and t["contractAddress"] == USDC_POL and int(t["value"]) > 0]
c_in = [t for t in etx(CDC_DEP, EV) if t["to"] == CDC_DEP and t["contractAddress"] == USDC_POL and int(t["value"]) > 0]
check("crypto_com_deposit_address", {t["to"] for t in c_outs} == {"0x2d17db18b41c92e64abaefb7e35ed70ed45b6dc8"}
      and tagged(137, "0x2d17db18b41c92e64abaefb7e35ed70ed45b6dc8", "Crypto.com")
      and abs(sum(int(t["value"]) for t in c_outs) - sum(int(t["value"]) for t in c_in)) < 10 ** 6,
      inflows=len(c_in), outflows=len(c_outs), forwarded_usdc=round(sum(int(t["value"]) for t in c_outs) / 1e6, 6))


b_gas = [x for x in load(EV / "etherscan" / f"137_txlist_{BYB_EVM}_p1.json")["result"] if x["to"] == BYB_EVM and int(x["value"]) > 0]
b_out = [t for t in etx(BYB_EVM, EV) if t["from"] == BYB_EVM and t["contractAddress"] in (USDC_POL, USDCE_POL) and int(t["value"]) > 0]
check("bybit_evm_deposit_address", b_gas and all(tagged(137, g["from"], "Bybit: Deposit Funder") for g in b_gas)
      and b_out and all(tagged(137, t["to"], "Bybit") for t in b_out),
      gas_topups=len(b_gas), outflows=len(b_out), outflow_recipients=sorted({t["to"] for t in b_out}))

# 7. Withdrawals of each account into the shared destinations
def via_relay(dest):
    got = defaultdict(lambda: [0, 0.0, 0])
    for o in OR:
        if not o["ok"] or o["to"] != dest or o["o"] != 137:
            continue
        acct = NAME.get(o["user"]) or ALIAS.get(o["user"])
        if not acct:
            continue
        g = got[acct]
        g[0] += 1
        g[1] += o["in"]
        if o["user"] in ALIAS:  # the intermediary's own inflow is a WITHDRAWAL of the account
            g[2] += 1
        elif o["in_tx"] and o["in_tx"][0] in WD and WD[o["in_tx"][0]][0] == o["user"]:
            g[2] += 1
    return got


def direct(dest, base=PREV):
    got = defaultdict(lambda: [0, 0.0])
    for t in etx(dest, base):
        if t["to"] == dest and t["contractAddress"] in (USDC_POL, USDCE_POL) and int(t["value"]) > 0 and t["hash"].lower() in WD:
            a = WD[t["hash"].lower()][0]
            if a in NAME:
                got[NAME[a]][0] += 1
                got[NAME[a]][1] += int(t["value"]) / 1e6
    return got


def swaps(dest, hashes):
    """Uniswap-route withdrawals: the receipt shows the proxy's USDC.e into the pool and the pool's USDC to the destination."""
    got = defaultdict(lambda: [0, 0.0])
    for h in hashes:
        rc = receipt(h)
        e = erc20(rc)
        src = [f for tok, f, to, v in e if tok == USDCE_POL]
        dst = [v for tok, f, to, v in e if tok == USDC_POL and to == dest]
        if len(src) == 1 and src[0] in NAME and dst:
            got[NAME[src[0]]][0] += 1
            got[NAME[src[0]]][1] += dst[0] / 1e6
    return got


def merge(*ds):
    out = defaultdict(lambda: [0, 0.0])
    for d in ds:
        for k, v in d.items():
            out[k][0] += v[0]
            out[k][1] += v[1]
    return {k: [v[0], round(v[1], 6)] for k, v in sorted(out.items())}


r_bin = via_relay(BIN_DEP)
bin_swaps = [t["hash"] for t in etx(BIN_DEP) if t["to"] == BIN_DEP and t["from"] == "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"
             and t["hash"].lower() not in WD and receipt(t["hash"])]
binance = merge(r_bin, direct(BIN_DEP), swaps(BIN_DEP, bin_swaps))
check("accounts_paying_binance_deposit", set(binance) == {"SemiconductorIT", "yellowtop1", "carltiosway", "ILOVEYOUBABYZZ", "ALLOWMETOSHOWU1",
                                                         "Domariocarios", "DonkeyDonkey999", "rrrrgggbbbclat"}
      and all(v[2] == v[0] for v in r_bin.values()), accounts=binance, relay_orders_matched_to_withdrawals={k: v[2] for k, v in r_bin.items()})

r_w = via_relay(W7702)
wallet = merge(r_w, direct(W7702))
bsc_w = [o for o in OR if o["ok"] and o["to"] == W7702 and o["d"] == 56 and o["user"] == A["0x8C33013f (no username)"]]
net_fills = {h for o in OR if o["ok"] and o["to"] == W7702 and (o["user"] in NAME or o["user"] in ALIAS) for h in o["out_tx"] if h}
w_in = [t for t in etx(W7702) if t["to"] == W7702 and t["contractAddress"] in (USDC_POL, USDCE_POL) and int(t["value"]) > 0]
origin = defaultdict(int)
for t in w_in:
    h = t["hash"].lower()
    origin["network_relay_fill" if h in net_fills else "network_withdrawal" if h in WD and WD[h][0] in NAME
           else "binance_48" if t["from"] == "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"
           else "poisoning_dust_under_0.01" if int(t["value"]) < 10_000 else "other"] += 1
check("accounts_paying_7702_wallet", set(wallet) == {"carltiosway", "Momentumgod", "ILOVEYOUBABYZZ", "ALLOWMETOSHOWU1", "ParkingLocator",
                                                     "0x8C33013f (no username)"} and len(bsc_w) == 1 and origin["other"] == 0,
      accounts=wallet, polygon_inflows_by_origin=dict(origin))

cdc_swaps = [t["hash"] for t in c_in if t["from"] == "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"]
cdc = merge(via_relay(CDC_DEP), swaps(CDC_DEP, cdc_swaps))
bybit130 = [t for t in c_in if t["from"] == "0x1347378b1d0eb69d3462e09b3dfa2fe28ebe74ec"]
byb = merge(via_relay(BYB_EVM))
check("accounts_paying_bybit_evm_deposit", set(byb) == {"DonkeyDonkey999", "rrrrgggbbbclat", "ALLOWMETOSHOWU1", "Bigboyslatvian"}, accounts=byb)
check("accounts_paying_crypto_com_deposit", set(cdc) == {"TBFMM", "TheOneWhoKnocks1312"} and tagged(137, "0x1347378b1d0eb69d3462e09b3dfa2fe28ebe74ec", "Bybit"),
      accounts=cdc, from_bybit_wallet_130=round(sum(int(t["value"]) for t in bybit130) / 1e6, 6))


# 8. Account-to-account transfers
def chain(a_user, mid, b_proxy, window=120):
    """Order a_user -> mid, then mid -> b (or mid -> mid, then a DEPOSIT of b), same amount, within `window` seconds."""
    hops = []
    for o1 in OR:
        if o1["ok"] and o1["user"] == a_user and o1["to"] == mid:
            nxt = [o2 for o2 in OR if o2["ok"] and o2["user"] == mid and 0 <= o2["t"] - o1["t"] <= window and o2["in_raw"] == o1["out_raw"]]
            for o2 in nxt:
                if o2["to"] not in (b_proxy, mid):
                    continue
                # the receiving account's DEPOSIT row: same hash as the fill, or (same-chain fill without hash) same exact amount just after
                by_hash = o2["to"] == b_proxy and any(DEP.get(h, (None,))[0] == b_proxy for h in o2["out_tx"] if h)
                by_amount = any(x["type"] == "DEPOSIT" and abs(float(x["usdc_size"]) - o2["out"]) < 1e-6 and 0 <= int(x["timestamp"]) - o2["t"] <= window
                                for x in acts.get(b_proxy, []))
                hops.append({"amount_sent": o1["in"], "amount_received": o2["out"], "seconds": int(o2["t"] - o1["t"]),
                             "deposit_row": by_hash or by_amount, "matched_by": "hash" if by_hash else "amount_and_time"})
    return hops


pairs = sorted((NAME[WD[h][0]], NAME[DEP[h][0]], WD[h][1]["usdc_size"]) for h in WD if h in DEP and WD[h][0] in NAME and DEP[h][0] in NAME
               and WD[h][0] != DEP[h][0])
same_tx = [p for p in pairs if p[:2] == ("TBFMM", "BlueElephant666")]
t2o = chain(A["TBFMM"], "0xfe775af18824f4951f19e264901030f8528bf972", A["oveiStheair"])
i2a = chain(A["ILOVEYOUBABYZZ"], "0x20bd758daa8d5c2a51e95370079d34f38d91f8b2", A["ALLOWMETOSHOWU1"])
d2a = chain(A["Domariocarios"], "0x20bd758daa8d5c2a51e95370079d34f38d91f8b2", A["ALLOWMETOSHOWU1"])


def pusd_hop(user, mid, receiver, h):
    rc = receipt(h)
    minted = [v for tok, f, to, v in erc20(rc) if tok == PUSD and f == "0x" + "0" * 40 and to == receiver]
    o1 = [o for o in OR if o["ok"] and o["user"] == user and o["to"] == mid]
    return bool(minted) and DEP.get(h.lower(), (None,))[0] == receiver and len(o1) == 1 and abs(o1[0]["out"] - minted[0] / 1e6) < 1e-6


a2x = pusd_hop(A["aaamsaasa"], "0x98d4e9aa9527316598c4ee6783329b529e292bcb", A["0x82be522b (no username)"],
               "0x521924de3ba4175ead5ce4c7a83fa73283d59da38188ca64ea17d86c69bf7dcb")
a2f = pusd_hop(A["aaamsaasa"], "0xed412759234979acf5818121bc37c606373262b2", A["FluentCastle1352"],
               "0x9420c48e3cb8c9320b7d2adccdf4591cd7f3029d50add08171ef45f52dafbd17")
check("direct_account_transfers", pairs == [("0x82be522b (no username)", "Bigboyslatvian", 5281.901178),
                                             ("ILOVEYOUBABYZZ", "DonkeyDonkey999", 2073.0), ("TBFMM", "BlueElephant666", 1.0),
                                             ("TBFMM", "BlueElephant666", 122.0), ("TBFMM", "BlueElephant666", 1400.0),
                                             ("TBFMM", "DonkeyDonkey999", 32.0)] and len(t2o) == 2 and all(x["deposit_row"] for x in t2o + i2a + d2a)
      and len(i2a) == 1 and len(d2a) == 1 and a2x and a2f,
      same_hash_withdrawal_and_deposit=pairs, tbfmm_to_oveistheair=t2o,
      iloveyoubabyzz_to_allowmetoshowu1=i2a, domariocarios_to_allowmetoshowu1=d2a,
      aaamsaasa_to_0x82be522b=a2x, aaamsaasa_to_fluentcastle1352=a2f)

# 9. Intermediate addresses used by one account only
al = []
for o in OR:
    if o["ok"] and o["user"] == "0x200b195893faf4da3f431125afc17d0903fc8ea6" and o["to"] != o["user"]:
        al.append(any(abs(float(x["usdc_size"]) - o["in"]) < 1e-6 and 0 <= o["t"] - int(x["timestamp"]) <= 60
                      for x in acts[A["ALLOWMETOSHOWU1"]] if x["type"] == "WITHDRAWAL"))
r44 = [t for t in etx("0x44a2c68087a3e6a9a3eedd9cf9c25fd76241e978", EV) if t["contractAddress"] == PUSD and t["to"] == "0x44a2c68087a3e6a9a3eedd9cf9c25fd76241e978"]
check("intermediate_addresses", al and all(al) and len(r44) == 1 and WD.get(r44[0]["hash"].lower(), (None,))[0] == A["rrrrgggbbbclat"],
      allowmetoshowu1_relay_orders_matched=f"{sum(al)}/{len(al)}", rrrrgggbbbclat_pusd_to_0x44a2c680=len(r44))


# 10. 14 January 2026: Bybit deposit, Bybit hot wallet payout, Polymarket deposit of TBFMM
def sol_usdc(base, addr, t0, t1):
    rows = []
    for p in sorted((base / "sol" / addr).glob("gtfa_*_p*.json")):
        if p.name.endswith(".meta.json"):
            continue
        for tx in load(p)["result"]["data"]:
            if t0 <= tx["blockTime"] <= t1:
                m, d = tx["meta"], defaultdict(int)
                for side, sgn in (("preTokenBalances", -1), ("postTokenBalances", 1)):
                    for b in m.get(side) or []:
                        if b["mint"] == USDC_SOL:
                            d[b["owner"]] += sgn * int(b["uiTokenAmount"]["amount"])
                rows.append((tx["blockTime"], tx["transaction"]["signatures"][0], {k: v for k, v in d.items() if v}))
    return sorted(rows)


ag = sol_usdc(PREV, "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV", 1768391000, 1768393000)
h4 = sol_usdc(EV, "4H4WacXekz1eGebGTQanvcNytAxiei4uBzJy36h9qj1g", 1768391000, 1768393000)
ag_in = sum(d.get("Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV", 0) for _, _, d in ag if d.get("AobVSwdW9BbpMdJvTqeCN4hPAmh4rHm7vwLnQ5ATSyrS", 0) < 0)
sweep = [(t, d) for t, _, d in ag if d.get("Gem2VAypSg7Ai7vjDKPTtqFahpoQWkfgVkyzx3rPoTka", 0) > 0]
pay = [(t, d) for t, _, d in h4 if d.get("Gem2VAypSg7Ai7vjDKPTtqFahpoQWkfgVkyzx3rPoTka", 0) < 0]
o14 = [o for o in OR if o["ok"] and o["user"] == "4H4WacXekz1eGebGTQanvcNytAxiei4uBzJy36h9qj1g" and o["to"] == A["TBFMM"]]
check("bybit_passthrough_to_tbfmm", ag_in == 4940682190 and len(sweep) == 1 and sweep[0][1]["Gem2VAypSg7Ai7vjDKPTtqFahpoQWkfgVkyzx3rPoTka"] == 4940682190
      and len(pay) == 1 and pay[0][1]["4H4WacXekz1eGebGTQanvcNytAxiei4uBzJy36h9qj1g"] == 4939682190 and 0 < pay[0][0] - sweep[0][0] < 120
      and len(o14) == 1 and o14[0]["in_raw"] == "4939682190" and any(DEP.get(h, (None,))[0] == A["TBFMM"] for h in o14[0]["out_tx"] if h),
      deposited_usdc=ag_in / 1e6, swept_usdc=4940.68219, paid_out_usdc=4939.68219, seconds_after_sweep=int(pay[0][0] - sweep[0][0]) if pay and sweep else None)


# 11. 28 February 2026 on BSC: ILOVEYOUBABYZZ into the Binance deposit, Binance hot wallets into three deposit addresses
def bsc_logs():
    out = {}
    for p in sorted((EV / "bsc").glob("*.json")):
        if p.name.endswith(".meta.json") or not (p.name.endswith(".receipt.json") or p.name.startswith("logs_")):
            continue
        res = load(p)["result"]
        for l in (res["logs"] if isinstance(res, dict) else res):
            if l["address"].lower() == BSC_USDC and len(l["topics"]) == 3:
                out[(l["transactionHash"], l["logIndex"])] = (int(l["blockNumber"], 16), "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], int(l["data"], 16))
    return sorted(out.values())


L = bsc_logs()
fill = [x for x in L if x[1] == "0xf70da97812cb96acdf810712aa562db8dfa3dbef" and x[2] == BIN_DEP]
out519 = [x for x in L if x[1] == BIN_DEP]
dep = {"SemiconductorIT": "0x937db5b193b367425919de9c08ed78f9119a883c", "Domariocarios": "0x9028a9e6545e76e74b26f832ec501d63b80b44e7",
       "yellowtop1": "0x5b1323e6f7ebb4643e6d61da582adac8097c64ab"}
funded = {n: [x for x in L if x[2] == a] for n, a in dep.items()}
bridged = {n: [o for o in OR if o["ok"] and o["user"] == a and o["to"] == A[n] and o["o"] == 56] for n, a in dep.items()}
hot = {"0x8894e0a0c962cb723c1976a4421c95949be2d4e3", "0xe2fc31f816a9b94326492132018c3aecc4a93ae1"}
i28 = [o for o in OR if o["ok"] and o["user"] == A["ILOVEYOUBABYZZ"] and o["to"] == BIN_DEP and o["d"] == 56 and abs(o["in"] - 26258.784687) < 1e-6]
rr = [o for o in OR if o["ok"] and o["user"] == "0xe8e0741f10903c96bba5f2b38a0d124414ab58bd" and o["to"] == A["rrrrgggbbbclat"] and o["o"] == 56]
rr_rc = load(EV / "bsc" / "0x9f030d0f173b99868c878fc6ace13dfec68176650b95a394d7e717f201bf437e.receipt.json")["result"]
rr_buy = sorted(int(x["timestamp"]) for x in acts[A["rrrrgggbbbclat"]] if x["type"] == "TRADE" and x.get("side") == "BUY"
                and x.get("title") == "US strikes Iran by February 28, 2026?")
check("feb28_rrrrgggbbbclat_funding", len(rr) == 1 and rr[0]["in"] == 10000.0 and rr_rc["status"] == "0x1" and int(rr_rc["blockNumber"], 16) == 83801778
      and rr[0]["in_tx"][0] == rr_rc["transactionHash"].lower() and rr_buy and rr_buy[0] > rr[0]["t"],
      block=int(rr_rc["blockNumber"], 16), first_buy_utc=datetime.fromtimestamp(rr_buy[0], timezone.utc).isoformat() if rr_buy else None)
check("feb28_binance_sequence", len(fill) == 1 and len(out519) == 1 and out519[0][2] == "0x8894e0a0c962cb723c1976a4421c95949be2d4e3"
      and out519[0][3] == fill[0][3] and len(i28) == 1
      and all(len(v) == 1 and v[0][1] in hot and fill[0][0] < v[0][0] for v in funded.values())
      and all(len(v) == 1 and abs(v[0]["in"] * 10 ** 18 - funded[n][0][3]) < 10 ** 12 for n, v in bridged.items())
      and tagged(137, "0x8894e0a0c962cb723c1976a4421c95949be2d4e3", "Binance") and tagged(56, "0xe2fc31f816a9b94326492132018c3aecc4a93ae1", "Binance"),
      into_binance_deposit=fill[0][3] / 1e18 if fill else None, block=fill[0][0] if fill else None,
      forwarded_block=out519[0][0] if out519 else None,
      funded={n: (v[0][0], v[0][1], v[0][3] / 1e18) for n, v in funded.items() if v})

# 12. June 2025: the same pattern on "Israel military action against Iran by Friday?"
jun = {}
for n in ("ILOVEYOUBABYZZ", "TheOneWhoKnocks1312", "DonkeyDonkey999"):
    xs = [x for x in acts[A[n]] if x.get("title") == "Israel military action against Iran by Friday?" and x["type"] == "TRADE"]
    b = [x for x in xs if x["side"] == "BUY"]
    s = [x for x in xs if x["side"] == "SELL" and float(x["price"]) >= 0.99]
    jun[n] = {"buy_usdc": round(sum(float(x["usdc_size"]) for x in b), 2), "max_buy_price": max(float(x["price"]) for x in b),
              "last_buy_utc": datetime.fromtimestamp(max(int(x["timestamp"]) for x in b), timezone.utc).isoformat(),
              "first_sell_099_utc": datetime.fromtimestamp(min(int(x["timestamp"]) for x in s), timezone.utc).isoformat()}
check("june_2025_pattern", all(v["max_buy_price"] <= 0.17 and v["last_buy_utc"] < "2025-06-12T23" and v["first_sell_099_utc"] > "2025-06-13" for v in jun.values()),
      accounts=jun)

# 13. Profile creation times (exploratory, noticed after the links were found)
prof = {}
for base in (EV / "polymarket_reduced", PREV / "polymarket_reduced"):
    for p in base.glob("pm_profile_*.json"):
        prof.setdefault(p.name[len("pm_profile_"):-5].lower(), load(p).get("createdAt"))
feb4 = sorted((prof[a], n) for n, a in A.items() if (prof.get(a) or "").startswith("2026-02-04"))
feb15 = sorted((prof[a], n) for n, a in A.items() if (prof.get(a) or "").startswith("2026-02-15"))
check("profile_creation_clusters", len(feb4) == 6 and feb4[0][0] >= "2026-02-04T17:41" and feb4[-1][0] < "2026-02-04T18:24" and len(feb15) == 4,
      feb_4=feb4, feb_15=feb15)

# 14. The two open Solana leads of the previous note: no Relay order, and no contact with the network
net = {a.lower() for a in A.values()} | {BIN_DEP, W7702, CDC_DEP, BEN.lower(), "f7p3dfrjrtbtrp8frf6qhlomxbkrbzpvbljtqcfcgmne",
                                          "4h4wacxekz1egebgtqanvcnytaxiei4ubzjy36h9qj1g", "agnhk1vsurw1ic3yndtp3nelthgjaf9kwgpkvuzv4fwy"}
j98 = []
for p in sorted((PREV / "sol" / "98jocp4jVAkpnD9uuhFYrwPksirqg3dDTnMMSd7bm5PG").glob("gtfa_*_p*.json")):
    if not p.name.endswith(".meta.json"):
        j98 += load(p)["result"]["data"]
touch = sorted({k.lower() for tx in j98 for k in [x["pubkey"] if isinstance(x, dict) else x for x in tx["transaction"]["message"]["accountKeys"]]} & net)
leads = {a: done.get(a.lower(), {}) for a in ("98jocp4jVAkpnD9uuhFYrwPksirqg3dDTnMMSd7bm5PG", "CN5kywyqAzQD7bN6SPTB5r8r6UL6GKfpDvujYBdqv5j9")}
check("open_solana_leads", all(v.get("requests") == 0 and v.get("termination") == "END" for v in leads.values())
      and len(j98) == 84 and touch == ["4dlzqynk9szjf6pcav73828tzhgjaf9kwgpkvuzv4fwy"],
      relay_orders={k[:8]: v.get("requests") for k, v in leads.items()}, wallet_98jocp4j_transactions=len(j98), network_addresses_touched=touch)

# 15. Who paid the BSC deposit addresses of ILOVEYOUBABYZZ, TBFMM and 0x8c33013f (exchange hot wallets only)
legs = {("ILOVEYOUBABYZZ", "0x08d495fb86399f37a5bda51a2f85a9e21a019ca5"), ("TBFMM", "0x80f4af8b526f0b6a8b70a81b192f11a464f69efc"),
        ("0x8C33013f (no username)", "0x8284600d3a6c04d29b1539209838073843052201")}
BSC_USDT = "0x55d398326f99059ff775485246999027b3197955"
paid, seen_l = defaultdict(list), set()
for p in sorted((EV / "bsc").glob("logs_*.json")):
    if p.name.endswith(".meta.json"):
        continue
    for l in load(p)["result"]:
        if l["address"].lower() in (BSC_USDC, BSC_USDT) and (l["transactionHash"], l["logIndex"]) not in seen_l:
            seen_l.add((l["transactionHash"], l["logIndex"]))
            to = "0x" + l["topics"][2][-40:]
            for n, d in legs:
                if to == d:
                    paid[n].append(("0x" + l["topics"][1][-40:], round(int(l["data"], 16) / 1e18, 6)))
nonce = {int(p.name[:-5].split("_")[-1]): int(load(p)["result"], 16) for p in (EV / "bsc").glob("nonce_0xef3aeff9_*.json") if not p.name.endswith(".meta.json")}
rate = (nonce[75089792] - nonce[73781987]) if {75089792, 73781987} <= set(nonce) else None
payers = {a for v in paid.values() for a, _ in v}
check("deposit_address_payers_are_hot_wallets", payers == {"0x8894e0a0c962cb723c1976a4421c95949be2d4e3", "0xef3aeff9a5f61c6dda33069c58c1434006e13b20",
                                                         "0x318d2aae4c99c2e74f7b5949fa1c34df837789b8", "0xe2fc31f816a9b94326492132018c3aecc4a93ae1"}
      and rate is not None and rate > 100_000 and tagged(137, "0x318d2aae4c99c2e74f7b5949fa1c34df837789b8", "Bybit"),
      payers={k: v for k, v in sorted(paid.items())}, unlabeled_payer_transactions_in_11_days=rate)

# 16. Rarity test of PLAN_RARITY.md, recomputed from the population wallets' own Relay pages
pop = (HERE / "population.txt").read_text().split()
coll = [w for w in pop if w in done and done[w]["termination"] == "END"]


def groups_of(wallets):
    T = defaultdict(lambda: defaultdict(list))
    for o in OR:
        if o["user"] in wallets and o["o"] == 137 and o["ok"] and o["to"] != o["user"]:
            T[o["to"]][o["user"]].append(o["t"])
    shared = {r: dict(u) for r, u in T.items() if len(u) >= 2}
    par = {w: w for w in wallets}

    def f(x):
        while par[x] != x:
            x = par[x]
        return x
    for u in shared.values():
        us = sorted(u)
        for v in us[1:]:
            par[f(v)] = f(us[0])
    g = defaultdict(set)
    for u in shared.values():
        for w in u:
            g[f(w)].add(w)
    return T, shared, sorted((sorted(x) for x in g.values()), key=lambda x: (-len(x), x))


if (HERE / "rarity.json").exists():
    T, shared, groups = groups_of(set(coll))
    netw = set(A.values())
    _, shared2, groups2 = groups_of(set(coll) - netw)
    gaps = sorted(int(min(abs(x - y) for x in u[a] for y in u[b])) for u in shared.values() for i, a in enumerate(sorted(u)) for b in sorted(u)[i + 1:])
    no_wd = [w for w in coll if not any(w in u for u in T.values())]
    R = load(HERE / "rarity.json")
    gi = {w: i for i, g in enumerate(groups) for w in g}
    per = defaultdict(list)
    for u in shared.values():
        us = sorted(u)
        for i, a in enumerate(us):
            for b in us[i + 1:]:
                per[gi[a]].append(int(min(abs(x - y) for x in u[a] for y in u[b])))
    net_g = [i for i, g in enumerate(groups) if set(g) & netw]
    check("rarity_test", len(coll) == len(pop) == 115 and R["groups"] == groups and R["collected"] == len(coll),
          population=len(pop), collected=len(coll), wallets_without_relay_withdrawal=len(no_wd),
          S1_wallets_sharing_a_recipient=sum(len(g) for g in groups), S1_group_sizes=[len(g) for g in groups],
          S1_network_wallets_in_groups=sum(1 for g in groups for w in g if w in netw),
          S2_wallets_sharing_outside_network=sum(len(g) for g in groups2), S2_group_sizes=[len(g) for g in groups2],
          S2_shared_recipients=sorted(shared2), S3_min_gap_seconds_by_pair=gaps,
          non_network_wallets_with_relay_withdrawal=len([w for w in coll if w not in netw and w not in no_wd]),
          S3_network_pairs=len(per[net_g[0]]) if net_g else 0, S3_network_pairs_under_1h=sum(1 for x in per[net_g[0]] if x < 3600) if net_g else 0,
          S3_by_group={f"group {i + 1} of {len(groups[i])}": (min(v), max(v), len(v)) for i, v in per.items() if i not in net_g})

# 17. Rarity follow-up: two more shared destinations inside the network, and group G outside it
s93 = [(NAME.get(o["user"]) or ALIAS.get(o["user"]) or o["user"], o["to"]) for o in OR if o["ok"] and o["to"] == "FyJ2zJY4yyCr8EZJSDVFB862JRiCYr6yWxEuMgVkaFcH"]
G = {"froshoo": "0x5e0b017aef88af84fb3897fecce7413c6754981a", "suffix-295": "0xb390ae2cc3fd8cb2670a62129faeb775faee106c",
     "unfiltered009": "0x95bd107886bd48d6737029603e3db242fb781652", "arsonicscribe": "0x4ec2f11d2893eb1bc3bab7449910540c93adf7ec"}
g_wd = [o for o in OR if o["ok"] and o["user"] in G.values() and o["to"] == "0xc5bb1be0407db7312911ec765d399d02461e411a"]
g_prof = sorted(prof.get(a) or "" for a in G.values())
g_names = all(any(x.get("name") == n for x in acts.get(a, [])) for n, a in G.items())
g_touch = {c for o in OR if o["user"] in G.values() or o["to"] in G.values() for c in (o["user"], o["to"])} & ({a for a in A.values()} | {BIN_DEP, W7702, CDC_DEP, BEN})
c5_out = [t for t in etx("0xc5bb1be0407db7312911ec765d399d02461e411a", EV) if t["from"] == "0xc5bb1be0407db7312911ec765d399d02461e411a"
          and t["contractAddress"] in (USDC_POL, USDCE_POL) and int(t["value"]) > 10 ** 6]
c5_cb = sum(int(t["value"]) for t in c5_out if tagged(137, t["to"], "Coinbase")) / max(1, sum(int(t["value"]) for t in c5_out))
mcn = prof.get("0x1305d2f820f1d7b460ec590cffd5498240469c4d") or ""
check("rarity_follow_up", {n for n, _ in s93} == {"ALLOWMETOSHOWU1", "rrrrgggbbbclat"} and len({u for u, _ in s93 if u}) == 2
      and {o["user"] for o in g_wd} == set(G.values()) and g_names and all(p.startswith("2026-02-22") for p in g_prof) and not g_touch
      and c5_cb > 0.5 and mcn.startswith("2026-02-28T04:07"),
      group_g_sink_share_to_coinbase=round(c5_cb, 4), mcnutty425_profile=mcn,
      network_shared_extra=sorted(set(s93)), group_g_withdrawals=len(g_wd), group_g_amount=round(sum(o["in"] for o in g_wd), 6),
      group_g_first_last=[min(o["t"] for o in g_wd), max(o["t"] for o in g_wd)] if g_wd else None, group_g_profiles=g_prof,
      group_g_touches_network=sorted(g_touch))

# 18. Every full address, hash and signature written in the reports exists in the archived evidence
corpus = []
for base in (EV, PREV):
    for p in base.rglob("*"):
        if p.is_file() and not p.name.endswith(".meta.json"):
            corpus.append(gzip.open(p, "rt").read() if p.suffix == ".gz" else p.read_text(errors="replace"))
corpus = "\n".join(corpus).lower()
refs, missing = set(), []
for doc in ("REPORT.md", "NEW_FINDINGS.md"):
    if (HERE / doc).exists():
        text = (HERE / doc).read_text()
        refs |= set(re.findall(r"\b0x[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\b", text))
        refs |= set(re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{32,88}\b", text))
missing = sorted(r for r in refs if r.lower() not in corpus and not (r.startswith("0x") and len(r) == 42 and "0" * 24 + r.lower()[2:] in corpus))  # EVM addresses may appear only as padded log topics
check("report_references_exist_in_evidence", not missing and len(refs) > 20, references=len(refs), missing=missing)

ok = all(r["status"] == "PASS" for r in results)
(HERE / "verification.json").write_text(json.dumps({"all_pass": ok, "checks": results}, indent=1, default=str))
for r in results:
    print(r["status"], r["check"])
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
