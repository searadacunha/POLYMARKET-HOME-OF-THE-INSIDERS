# Steps 1-2: complete funder transfer inventory (native USDC, USDC.e), classification, the 14 funding transfers, POL.
from lib import *
import json, csv
REPO = "/Volumes/PHI-Data/Projects/Polymarket-early-detection-20261113/investigations/followup-20261113/sources/data/"
TEN = "https://gateway.tenderly.co/public/polygon"
USDCE = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
logs = json.load(open(P("s1_logs.json")))
nonce = json.load(open(P("s1_nonce.json")))
head = nonce["head"]
def call(to, data, blk="latest"):
    return r1("eth_call", [{"to": to, "data": data}, blk])
def sstr(h):
    b = bytes.fromhex(h[2:]); n = int.from_bytes(b[32:64], "big"); return b[64:64+n].decode()
# USDC.e identity check
usdce = {"name": sstr(call(USDCE, "0x06fdde03")), "symbol": sstr(call(USDCE, "0x95d89b41")), "decimals": hexint(call(USDCE, "0x313ce567")), "code_len": (len(r1("eth_getCode", [USDCE, "latest"]))-2)//2}
usdc = {"name": sstr(call(USDC, "0x06fdde03")), "symbol": sstr(call(USDC, "0x95d89b41")), "decimals": hexint(call(USDC, "0x313ce567"))}
print("USDC", usdc, "USDC.e", usdce)
# explicit USDC.e scans (adaptive 5M ranges on tenderly)
def scan(addr, topics, a=76_000_000, b=head, step=5_000_000):
    res = []; cur = a
    while cur <= b:
        e = min(cur+step-1, b)
        r, _ = rpc("eth_getLogs", [{"fromBlock": hex(cur), "toBlock": hex(e), "address": addr, "topics": topics}], [TEN]); res += r; cur = e+1
    return res
ce_out = scan(USDCE, [TRANSFER, pad(FUNDER)]); ce_in = scan(USDCE, [TRANSFER, None, pad(FUNDER)])
print("USDC.e out", len(ce_out), "in", len(ce_in))
# positive control for USDC.e scan: a known USDC.e transfer? use the contract with a wide topic window of 1 block range from latest with no topic filter
ctrl = rpc("eth_getLogs", [{"fromBlock": hex(head-60), "toBlock": hex(head), "address": USDCE, "topics": [TRANSFER]}], [TEN])[0]
print("USDC.e control (any transfer, last 60 blocks):", len(ctrl))
# classify native USDC logs
txcache = {}
def tx(h):
    if h not in txcache: txcache[h] = r1("eth_getTransactionByHash", [h])
    return txcache[h]
blkts = {}
def ts(b):
    if b not in blkts: blkts[b] = hexint(r1("eth_getBlockByNumber", [hex(b), False])["timestamp"])
    return blkts[b]
rows = []
for dirn in ("out", "in"):
    for l in logs["scans"][f"usdc_native_{dirn}"]["logs"]:
        t = tx(l["transactionHash"]); b = hexint(l["blockNumber"]); amt = int(l["data"], 16)
        frm = "0x"+l["topics"][1][-40:]; to = "0x"+l["topics"][2][-40:]
        rows.append({"dir": dirn, "block": b, "ts": ts(b), "tx": l["transactionHash"], "logIndex": hexint(l["logIndex"]), "from": frm, "to": to, "amount_raw": amt, "amount": amt/1e6, "tx_from": t["from"], "tx_to": t["to"], "tx_nonce": hexint(t["nonce"]), "funder_initiated": t["from"].lower() == FUNDER})
rows.sort(key=lambda r: (r["block"], r["logIndex"]))
json.dump({"usdc": usdc, "usdce": usdce, "usdce_out": len(ce_out), "usdce_in": len(ce_in), "usdce_control": len(ctrl), "rows": rows}, open(P("s2_funder_transfers.json"), "w"), indent=1)
out = [r for r in rows if r["dir"] == "out"]
print("native out logs", len(out), "zero-value", sum(r["amount_raw"] == 0 for r in out), "funder-initiated nonzero", sum(r["funder_initiated"] and r["amount_raw"] > 0 for r in out), "nonzero not funder-initiated", sum((not r["funder_initiated"]) and r["amount_raw"] > 0 for r in out))
print("zero-value ones funder-initiated:", sum(r["amount_raw"] == 0 and r["funder_initiated"] for r in out))
inn = [r for r in rows if r["dir"] == "in"]
print("in logs", len(inn), "total", sum(r["amount"] for r in inn))
# POL
print("POL balances:", {b: hexint(r1("eth_getBalance", [FUNDER, hex(b)]))/1e18 for b in (77472116, 77472117, 77472526, 77472527, 77481230, 77502770, 77595648, head)})
