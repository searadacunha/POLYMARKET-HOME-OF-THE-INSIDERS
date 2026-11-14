# Step 8: second-RPC cross-checks: receipts (>=6) and eth_getLogs completeness windows (drpc, 10k-block windows vs Tenderly 5M-block scan).
from lib import *
import json
DR = "https://polygon.drpc.org"; TEN = "https://gateway.tenderly.co/public/polygon"; OTHER = ["https://1rpc.io/matic", "https://polygon-bor-rpc.publicnode.com"]
s4 = json.load(open(P("s4_withdrawals.json")))["withdrawals"]
s2 = json.load(open(P("s2_funder_transfers.json")))["rows"]
fund = [r["tx"] for r in s2 if r["dir"] == "out" and r["funder_initiated"] and r["amount_raw"] > 0]
txs = fund[:3] + [fund[7], fund[-1]] + [w["tx"] for w in s4[:2]] + [s4[-1]["tx"], s4[13]["tx"]] + ["0x609bb6181c0f916bd27e934b24c72bedddbc3e1c5f7c3013028b827a4b139ba7", "0x708b58858b25ea4cad8987054c11981046071b7758d92244dd5a7c1898755b43", "0xa3b2afdee9ce0c39b9dce54f327760fb1c7c43822f94a8901a6262d94ad77463"]
def norm(rc):
    return {"status": rc["status"], "block": rc["blockNumber"], "from": rc["from"], "to": rc["to"], "gasUsed": rc["gasUsed"], "logs": [(l["address"], l["topics"], l["data"], l["logIndex"]) for l in rc["logs"]]}
res = {"receipts": [], "logs_windows": []}
for h in txs:
    row = {"tx": h}
    for nm, u in (("drpc", DR), ("tenderly", TEN), ("1rpc", OTHER[0]), ("publicnode", OTHER[1])):
        try: rc, _ = rpc("eth_getTransactionReceipt", [h], [u]); row[nm] = norm(rc) if rc else None
        except Exception as e: row[nm] = "ERR " + str(e)[:120]
    ok = [k for k in ("drpc", "tenderly", "1rpc", "publicnode") if isinstance(row[k], dict)]
    row["served_by"] = ok; row["identical_across_served"] = len({json.dumps(row[k], sort_keys=True) for k in ok}) == 1 and len(ok) >= 2
    for k in ("drpc", "tenderly", "1rpc", "publicnode"):
        if isinstance(row[k], dict): row[k] = "ok n_logs=%d" % len(row[k]["logs"])
    res["receipts"].append(row); print(h[:14], row["served_by"], row["identical_across_served"], flush=True)
# block timestamps from two RPCs
res["block_ts"] = []
for b in (77472527, 77481230, 77498125, 77502770):
    a = hexint(rpc("eth_getBlockByNumber", [hex(b), False], [DR])[0]["timestamp"]); t = hexint(rpc("eth_getBlockByNumber", [hex(b), False], [TEN])[0]["timestamp"])
    res["block_ts"].append({"block": b, "drpc": a, "tenderly": t, "equal": a == t})
# logs completeness windows
def key(l): return (l["transactionHash"], l["logIndex"])
for dirn, topics in (("out", [TRANSFER, pad(FUNDER)]), ("in", [TRANSFER, None, pad(FUNDER)])):
    tset = set(); dset = set(); a = 77_471_000
    while a < 77_610_000:
        b = a + 8_999
        r1_, _ = rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(b), "topics": topics}], [TEN]); r2_, _ = rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(b), "topics": topics}], [DR])
        tset |= {key(l) for l in r1_}; dset |= {key(l) for l in r2_}; a = b + 1
    res["logs_windows"].append({"dir": dirn, "range": [77_471_000, a-1], "tenderly_n": len(tset), "drpc_n": len(dset), "equal": tset == dset})
    print(dirn, len(tset), len(dset), tset == dset, flush=True)
# nonce at block on two RPCs
res["nonce_check"] = [{"block": b, "drpc": hexint(rpc("eth_getTransactionCount", [FUNDER, hex(b)], [DR])[0]), "tenderly": hexint(rpc("eth_getTransactionCount", [FUNDER, hex(b)], [TEN])[0])} for b in (77472526, 77472527, 77481230, 77502770, 97000000)]
json.dump(res, open(P("s8_crosscheck.json"), "w"), indent=1)
print(res["block_ts"], res["nonce_check"])
