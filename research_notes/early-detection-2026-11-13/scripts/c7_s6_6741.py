# Step 6: every ERC20 Transfer in/out of the 6741 proxy between 2025-10-09 21:00 and 2025-10-11 00:00 UTC
from lib import *
import json, datetime, collections
TEN = "https://gateway.tenderly.co/public/polygon"
PX = "0xa430506774f9efaf39903ee7e0db1351f66891ca"
def blk_ts(b): return hexint(r1("eth_getBlockByNumber", [hex(b), False])["timestamp"])
def first_block_at(t, lo=77_400_000, hi=77_600_000):
    while hi - lo > 1:
        m = (lo+hi)//2
        if blk_ts(m) >= t: hi = m
        else: lo = m
    return hi
T0 = int(datetime.datetime(2025, 10, 9, 21, 0, tzinfo=datetime.timezone.utc).timestamp()); T1 = int(datetime.datetime(2025, 10, 11, 0, 0, tzinfo=datetime.timezone.utc).timestamp())
b0 = first_block_at(T0); b1 = first_block_at(T1) - 1
print("blocks", b0, b1, blk_ts(b0), blk_ts(b1))
logs = []
def scan(topics, a, b, step):
    cur = a; res = []
    while cur <= b:
        e = min(cur+step-1, b)
        try: r, _ = rpc("eth_getLogs", [{"fromBlock": hex(cur), "toBlock": hex(e), "topics": topics}], [TEN])
        except Exception as ex:
            if step <= 500: raise
            step //= 4; continue
        res += r; cur = e+1
    return res
out = scan([TRANSFER, pad(PX)], b0, b1, 20000); inn = scan([TRANSFER, None, pad(PX)], b0, b1, 20000)
print("out logs", len(out), "in logs", len(inn))
ts = {}
def T(b):
    if b not in ts: ts[b] = blk_ts(b)
    return ts[b]
tokinfo = {}
def tok(a):
    if a in tokinfo: return tokinfo[a]
    def c(d):
        try: return r1("eth_call", [{"to": a, "data": d}, "latest"])
        except Exception: return None
    s = c("0x95d89b41"); dc = c("0x313ce567"); sym = None
    if s and len(s) > 130:
        bb = bytes.fromhex(s[2:]); n = int.from_bytes(bb[32:64], "big"); sym = bb[64:64+n].decode(errors="replace")
    tokinfo[a] = {"symbol": sym, "decimals": hexint(dc) if dc and dc != "0x" and len(dc) <= 66 else None}
    return tokinfo[a]
rows = []
for dirn, L in (("out", out), ("in", inn)):
    for l in L:
        if len(l["topics"]) != 3: continue
        rows.append({"dir": dirn, "token": l["address"], "block": hexint(l["blockNumber"]), "logIndex": hexint(l["logIndex"]), "tx": l["transactionHash"], "from": "0x"+l["topics"][1][-40:], "to": "0x"+l["topics"][2][-40:], "raw": int(l["data"], 16) if l["data"] != "0x" else 0})
# dedupe self transfers (proxy->proxy would appear twice)
seen = set(); rr = []
for r in rows:
    k = (r["tx"], r["logIndex"])
    if k in seen: continue
    seen.add(k); rr.append(r)
rows = rr
tokcount = collections.Counter(r["token"] for r in rows)
for a in tokcount: tok(a)
print({a: (tokinfo[a], n) for a, n in tokcount.most_common(12)})
for r in rows:
    ti = tokinfo[r["token"]]; r["symbol"] = ti["symbol"]; r["amount"] = r["raw"] / 10**(ti["decimals"] if ti["decimals"] is not None else 6)
    r["utc"] = datetime.datetime.fromtimestamp(T(r["block"]), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    r["cp"] = r["to"] if r["dir"] == "out" else r["from"]
rows.sort(key=lambda r: (r["block"], r["logIndex"]))
USDCE = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
dollar = [r for r in rows if r["token"] in (USDC, USDCE) or (r["symbol"] or "").lower() in ("pusd",) ]
json.dump({"b0": b0, "b1": b1, "tokens": tokinfo, "all": rows}, open(P("s6_6741_transfers.json"), "w"), indent=1)
# counterparty aggregation for USDC / USDC.e
agg = collections.defaultdict(lambda: {"in": 0, "out": 0, "n_in": 0, "n_out": 0})
for r in dollar:
    a = agg[(r["token"], r["cp"])]; a[r["dir"]] += r["amount"]; a["n_" + r["dir"]] += 1
print("dollar-token transfers", len(dollar))
codes = {}
for (t, cp), a in sorted(agg.items(), key=lambda kv: -(kv[1]["in"] + kv[1]["out"]))[:25]:
    if cp not in codes: codes[cp] = (len(r1("eth_getCode", [cp, "latest"]))-2)//2
    print(("USDC.e" if t == USDCE else "USDC "), cp, "code", codes[cp], {k: (round(v, 2) if isinstance(v, float) else v) for k, v in a.items()})
print("---- native USDC rows ----")
for r in rows:
    if r["token"] == USDC: print(r["utc"], r["dir"], r["cp"], r["amount"], r["tx"])
print("---- large USDC.e rows (>=1000) not to/from top-3 counterparties ----")
top3 = [cp for (t, cp), a in sorted(agg.items(), key=lambda kv: -(kv[1]["in"] + kv[1]["out"]))[:3]]
print("top3", top3)
for r in dollar:
    if r["token"] == USDCE and r["amount"] >= 1000 and r["cp"] not in top3: print(r["utc"], r["dir"], r["cp"], r["amount"], r["tx"])
