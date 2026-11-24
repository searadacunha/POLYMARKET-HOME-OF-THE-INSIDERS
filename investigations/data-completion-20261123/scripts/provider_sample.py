"""Second-provider control of the collected logs: re-read a deterministic sample of cohort transactions from another
public RPC (eth_getTransactionReceipt) and compare every collected log of those transactions field by field.

The sample is the 200 transactions with the smallest SHA-256 of their hash among cohort transactions with a fill, a
redemption or a collateral transfer. A missing receipt or a refused call is recorded as such, never as agreement.
"""

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import ledger_build as B  # noqa: E402
from monitoring.phi_monitor import net  # noqa: E402

SECOND = "https://polygon.drpc.org"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()
    plan, _, logs, _ = B.load(a.raw)
    by_tx = {}
    for x in logs.values():
        by_tx.setdefault(x["tx"], []).append(x)
    sample = sorted(by_tx, key=lambda t: hashlib.sha256(t.encode()).digest())[:a.n]
    counts, diffs = Counter(), []
    for i in range(0, len(sample), 10):
        batch = sample[i:i + 10]
        body = [{"jsonrpc": "2.0", "id": j, "method": "eth_getTransactionReceipt", "params": [t]} for j, t in enumerate(batch)]
        for attempt in range(6):
            status, raw = net.fetch(SECOND, data=body, timeout=60, tries=2)
            if status == 200:
                break
            time.sleep(5 * (attempt + 1))
        else:
            counts["batch_refused"] += len(batch)
            continue
        got = {r["id"]: r for r in json.loads(raw)}
        for j, t in enumerate(batch):
            r = got.get(j)
            if not r or "error" in r or not r.get("result"):
                counts["receipt_missing"] += 1
                continue
            rc = r["result"]
            theirs = {int(l["logIndex"], 16): l for l in rc["logs"]}
            for x in by_tx[t]:
                l = theirs.get(x["log_index"])
                same = l is not None and l["address"].lower() == x["address"] and \
                    [s.lower() for s in l["topics"]] == x["topics"] and l["data"].lower() == x["data"] and \
                    l["blockHash"].lower() == x["block_hash"] and int(l["blockNumber"], 16) == x["block"]
                counts["log_agrees" if same else "log_differs"] += 1
                if not same:
                    diffs.append({"tx": t, "log_index": x["log_index"]})
        time.sleep(0.5)
    out = {"provider_primary": plan["provider"], "provider_second": SECOND, "transactions_sampled": len(sample),
           "rule": "200 smallest sha256(tx hash) among all collected cohort transactions", "counts": dict(counts),
           "differences": diffs[:50]}
    (a.results / "provider_sample.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
