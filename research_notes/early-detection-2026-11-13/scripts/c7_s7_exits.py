# Step 7: one hop on the two exits + decode of the capital fill and the Across deposit from Polygon receipts.
from lib import *
import json, collections, datetime
TEN = "https://gateway.tenderly.co/public/polygon"
head = json.load(open(P("s1_nonce.json")))["head"]
EX = "0xb282b48ae713fa2201282e298f3393130c4f851d"
SPOKE = "0x9295ee1d8c5b022be115a2ad3c30c72e34e7f096"
res = {}
def iso(t): return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
res["exit_addr"] = EX
res["code_len"] = (len(r1("eth_getCode", [EX, "latest"]))-2)//2
res["nonce_latest"] = hexint(r1("eth_getTransactionCount", [EX, "latest"]))
res["balance_pol_latest"] = hexint(r1("eth_getBalance", [EX, "latest"]))/1e18
res["usdc_balance_latest"] = hexint(r1("eth_call", [{"to": USDC, "data": "0x70a08231"+pad(EX)[2:]}, "latest"]))/1e6
res["nonce_at_exit_block"] = hexint(r1("eth_getTransactionCount", [EX, hex(77502770)]))
res["nonce_before_exit_block"] = hexint(r1("eth_getTransactionCount", [EX, hex(77502769)]))
# all ERC20 transfers touching the address, any token, 76M..head, adaptive
def scan(topics, a, b, step):
    cur = a; r_ = []
    while cur <= b:
        e = min(cur+step-1, b)
        try: r, _ = rpc("eth_getLogs", [{"fromBlock": hex(cur), "toBlock": hex(e), "topics": topics}], [TEN])
        except Exception:
            if step <= 1000: raise
            step //= 4; continue
        r_ += r; cur = e+1
    return r_
inn = scan([TRANSFER, None, pad(EX)], 76_000_000, head, 5_000_000); out = scan([TRANSFER, pad(EX)], 76_000_000, head, 5_000_000)
res["n_in_logs"] = len(inn); res["n_out_logs"] = len(out)
def summ(L, nm):
    c = collections.Counter(l["address"] for l in L)
    nz = [l for l in L if int(l["data"], 16) > 0]
    nzu = [l for l in nz if l["address"] == USDC]
    res[nm] = {"by_token": dict(c), "nonzero_logs": len(nz), "native_usdc_nonzero": len(nzu)}
    if nz:
        blks = [hexint(l["blockNumber"]) for l in nz]; res[nm]["first_nonzero_block"] = min(blks); res[nm]["last_nonzero_block"] = max(blks)
summ(inn, "in"); summ(out, "out")
# native USDC transfers, full list (nonzero)
nat = []
for dirn, L in (("in", inn), ("out", out)):
    for l in L:
        if l["address"] == USDC and int(l["data"], 16) > 0:
            b = hexint(l["blockNumber"]); nat.append({"dir": dirn, "block": b, "ts": hexint(r1("eth_getBlockByNumber", [hex(b), False])["timestamp"]), "tx": l["transactionHash"], "from": "0x"+l["topics"][1][-40:], "to": "0x"+l["topics"][2][-40:], "amount": int(l["data"], 16)/1e6})
nat.sort(key=lambda r: (r["block"])); 
for r in nat: r["utc"] = iso(r["ts"])
res["native_usdc_transfers"] = nat
# balance history of the exit address (native USDC) at selected blocks
res["usdc_balance_at"] = {str(b): hexint(r1("eth_call", [{"to": USDC, "data": "0x70a08231"+pad(EX)[2:]}, hex(b)]))/1e6 for b in (77502769, 77502770, 77510000, 77600000, 78000000, head)}
# nonce-change blocks (if EOA)
nn = res["nonce_latest"]; first_n = None
if nn and nn < 400:
    firsts = {}
    for k in (1, nn):
        lo, hi = 76_000_000, head
        while hi - lo > 1:
            m = (lo+hi)//2
            if hexint(r1("eth_getTransactionCount", [EX, hex(m)])) >= k: hi = m
            else: lo = m
        firsts[k] = (hi, hexint(r1("eth_getBlockByNumber", [hex(hi), False])["timestamp"]))
    res["nonce_first_change"] = {"block": firsts[1][0], "utc": iso(firsts[1][1])}; res["nonce_last_change"] = {"block": firsts[nn][0], "utc": iso(firsts[nn][1])}
# the exit tx itself
t = r1("eth_getTransactionByHash", ["0xa3b2afdee9ce0c39b9dce54f327760fb1c7c43822f94a8901a6262d94ad77463"]); res["exit_tx_from"] = t["from"]; res["exit_tx_nonce"] = hexint(t["nonce"])
# ---- Across deposit decode (receipt of the 70k exit) ----
def words(d): 
    h = d[2:]; return [h[i:i+64] for i in range(0, len(h), 64)]
rc = r1("eth_getTransactionReceipt", ["0x708b58858b25ea4cad8987054c11981046071b7758d92244dd5a7c1898755b43"])
dep = []
for l in rc["logs"]:
    if l["address"].lower() == SPOKE: dep.append({"topics": l["topics"], "words": words(l["data"])})
res["across_deposit_logs"] = dep
cap = r1("eth_getTransactionReceipt", ["0x609bb6181c0f916bd27e934b24c72bedddbc3e1c5f7c3013028b827a4b139ba7"])
res["capital_receipt"] = {"tx_from": r1("eth_getTransactionByHash", ["0x609bb6181c0f916bd27e934b24c72bedddbc3e1c5f7c3013028b827a4b139ba7"])["from"], "logs": [{"address": l["address"], "topics": l["topics"], "words": words(l["data"])} for l in cap["logs"] if l["address"].lower() in (SPOKE,)]}
json.dump(res, open(P("s7_exits.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("native_usdc_transfers", "across_deposit_logs", "capital_receipt")}, indent=1)[:3500])
print("native usdc transfers:", len(nat)); 
for r in nat[:30]: print(r["utc"], r["dir"], r["from"][:10], r["to"][:10], r["amount"], r["tx"][:14])
print("DEPOSIT", json.dumps(dep)[:2500]); print("CAPITAL", json.dumps(res["capital_receipt"])[:2500])
