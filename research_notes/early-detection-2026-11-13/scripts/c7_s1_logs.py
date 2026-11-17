# Step 1b: Transfer logs touching the funder (native USDC, USDC.e, plus unfiltered-token scan by topic only), adaptive range.
from lib import *
import json, sys, os
head = hexint(r1("eth_blockNumber", []))
TEN = "https://gateway.tenderly.co/public/polygon"
START = 76_000_000  # ~Aug 2025, long before first activity (block 77472117)
def getlogs(addr, topics, a, b, urls=None):
    p = {"fromBlock": hex(a), "toBlock": hex(b), "topics": topics}
    if addr: p["address"] = addr
    return rpc("eth_getLogs", [p], urls)
def scan(addr, topics, a, b, step, urls=None, log=None):
    res = []; cur = a
    while cur <= b:
        end = min(cur + step - 1, b)
        try:
            r, u = getlogs(addr, topics, cur, end, urls)
        except Exception as e:
            if step <= 1000: raise
            step = max(step // 4, 1000); print("shrink", step, str(e)[:150], flush=True); continue
        if log is not None: log.append((cur, end, len(r), u))
        res += r; cur = end + 1
    return res
if __name__ == "__main__":
    step0 = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000
    out = {"head": head, "start": START, "scans": {}}
    USDCE = None
    for name, addr in [("usdc_native", USDC), ("any_token", None)]:
        for dirn, topics in [("out", [TRANSFER, pad(FUNDER)]), ("in", [TRANSFER, None, pad(FUNDER)])]:
            lg = []
            logs = scan(addr, topics, START, head, step0, urls=[TEN], log=lg)
            out["scans"][f"{name}_{dirn}"] = {"n": len(logs), "ranges": lg, "logs": logs}
            print(name, dirn, len(logs), "ranges", len(lg), flush=True)
            json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"s1_logs.json"), "w"))
