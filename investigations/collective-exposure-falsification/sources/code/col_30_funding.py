#!/usr/bin/env python3
"""Early funding relations of contributor wallets (M4), Polygon, strictly outcome-blind.

Wallets: every wallet listed as a contributor of a candidate at any panel unit (col_s / col_o), all splits.
Window: the wallet's FIRST 100 ERC-20 transfers (Etherscan v2 `account/tokentx`, chainid 137, ascending, one call).
That window holds the account's funding at creation; later transfers of active wallets (each Polymarket trade
settles in USDC) are not read. Status: `complete` (< 100 transfers: whole history seen), `early` (first 100 only),
`error` (after retries; downstream UNKNOWN, never 0). Kept rows: USDC.e and native USDC, timestamp <= 2026-10-31.

Outputs (funding.json):
  status[w]      complete | early | error
  direct[a|b]    timestamps of USDC transfers between two collected wallets whose transaction `to` is NOT a
                 Polymarket contract of params.json["infra"] (checked with proxy/eth_getTransactionByHash)
  unresolved     pair keys whose candidate transfer could not be checked (downstream: UNKNOWN, not 0)
  funders[w]     {funder: first inbound USDC timestamp} for non-hub funders; a hub is any address that sent USDC
                 to >= 10 distinct collected wallets (exchanges, bridges, relayers, hot wallets), an infra
                 contract, or the zero address
The API key is read from ~/Downloads/.env (ETHERSCAN_API_KEY) and never printed or stored.

usage: col_30_funding.py --panel panel.jsonl.gz --params params.json --cache DIR --out funding.json [--rps 4]
"""
import argparse
import gzip
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import os
import time
import urllib.parse
import urllib.request
from collections import defaultdict

API = "https://api.etherscan.io/v2/api"
USDC = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"}
END_TS = 1793491199  # 2026-10-31T23:59:59Z
WINDOW = 100
HUB_MIN = 10
ZERO = "0x0000000000000000000000000000000000000000"


def api_key():
    for line in open(os.path.expanduser("~/Downloads/.env")):
        if line.startswith("ETHERSCAN_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ETHERSCAN_API_KEY not found")


class Client:
    def __init__(self, key, rps):
        self.key, self.gap, self.last, self.calls = key, 1.0 / rps, 0.0, 0

    lock = threading.Lock()

    def _slot(self):
        with self.lock:  # shared rate limit across threads
            now = time.time()
            nxt = max(now, self.last + self.gap)
            self.last = nxt
            self.calls += 1
        if nxt > now:
            time.sleep(nxt - now)

    def get(self, **params):
        params.update(chainid=137, apikey=self.key)
        url = API + "?" + urllib.parse.urlencode(params)
        for attempt in range(5):
            self._slot()
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-client"}),
                                            timeout=60) as r:
                    j = json.loads(r.read())
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2 * (attempt + 1))
                continue
            res = j.get("result")
            msg = (str(j.get("message", "")) + " " + (res if isinstance(res, str) else "")).lower()
            if "rate limit" in msg or "max calls" in msg:
                time.sleep(2 * (attempt + 1))
                continue
            return j
        raise RuntimeError("rate limited 5 times")


def wallets_from_panel(path):
    ws = set()
    with gzip.open(path, "rt") as f:
        for l in f:
            u = json.loads(l)
            ws.update(u["col_s"]["wallets"])
            ws.update(u["col_o"]["wallets"])
    return sorted(ws)


def fetch_wallet(cl, w):
    """USDC rows among the wallet's first WINDOW ERC-20 transfers, and a status. Never raises."""
    try:
        j = cl.get(module="account", action="tokentx", address=w, page=1, offset=WINDOW, sort="asc",
                   startblock=0, endblock=99999999)
    except Exception:
        return [], "error"
    res = j.get("result")
    if j.get("status") != "1":
        if "no transactions found" in str(j.get("message", "")).lower():
            return [], "complete"
        return [], "error"
    if not isinstance(res, list):
        return [], "error"
    rows = [{"from": r["from"].lower(), "to": r["to"].lower(), "ts": int(r["timeStamp"]), "tx": r["hash"].lower(),
             "value": int(r["value"]) / 10 ** int(r["tokenDecimal"])}
            for r in res if r["contractAddress"].lower() in USDC and int(r["timeStamp"]) <= END_TS]
    return rows, ("early" if len(res) >= WINDOW else "complete")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--params", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rps", type=float, default=4.0)
    a = ap.parse_args()
    infra = {x.lower() for x in json.load(open(a.params))["infra"]}
    ws = wallets_from_panel(a.panel)
    wset = set(ws)
    os.makedirs(a.cache, exist_ok=True)
    cl = Client(api_key(), a.rps)
    status, rows_by = {}, {}
    t0 = time.time()
    def one(w):
        f = os.path.join(a.cache, w + ".json")
        if os.path.exists(f):
            return w, json.load(open(f))
        rows, st = fetch_wallet(cl, w)
        d = {"status": st, "rows": rows, "window": WINDOW}
        if st != "error":  # errors are retried on the next run
            json.dump(d, open(f, "w"))
        return w, d

    with ThreadPoolExecutor(4) as ex:
        for k, (w, d) in enumerate(ex.map(one, ws)):
            status[w], rows_by[w] = d["status"], d["rows"]
            if (k + 1) % 250 == 0:
                print(f"{k + 1}/{len(ws)} wallets, {cl.calls} calls, {time.time() - t0:.0f}s", flush=True)

    recv = defaultdict(set)
    for w, rows in rows_by.items():
        for r in rows:
            if r["to"] == w:
                recv[r["from"]].add(w)
    hubs = {f for f, s in recv.items() if len(s) >= HUB_MIN} | infra | {ZERO}

    cand = {}
    for w, rows in rows_by.items():
        for r in rows:
            a_, b_ = r["from"], r["to"]
            if a_ != b_ and a_ in wset and b_ in wset and a_ not in infra and b_ not in infra:
                cand[r["tx"]] = (a_, b_, r["ts"])
    txcache = os.path.join(a.cache, "_tx_to.json")
    tx_to = json.load(open(txcache)) if os.path.exists(txcache) else {}
    for tx in sorted(cand):
        if tx in tx_to and tx_to[tx] not in ("error", "unknown"):
            continue
        try:
            j = cl.get(module="proxy", action="eth_getTransactionByHash", txhash=tx)
            tx_to[tx] = ((j.get("result") or {}).get("to") or "").lower() or "unknown"
        except Exception:
            tx_to[tx] = "error"
    json.dump(tx_to, open(txcache, "w"))
    direct, unresolved, dropped = defaultdict(list), set(), defaultdict(int)
    for tx, (a_, b_, ts) in cand.items():
        to = tx_to.get(tx, "error")
        key = "|".join(sorted((a_, b_)))
        if to in infra:
            dropped["trade_or_protocol_tx"] += 1
        elif to in ("error", "unknown"):
            unresolved.add(key)
        else:
            direct[key].append(ts)
    funders = {}
    for w, rows in rows_by.items():
        fr = {}
        for r in rows:
            if r["to"] == w and r["from"] not in hubs and r["from"] != w:
                fr[r["from"]] = min(fr.get(r["from"], r["ts"]), r["ts"])
        funders[w] = fr
    cnt = defaultdict(int)
    for s in status.values():
        cnt[s] += 1
    out = {"status": status, "direct": {k: sorted(v) for k, v in direct.items()}, "funders": funders,
           "unresolved": sorted(unresolved), "window": WINDOW,
           "counts": {"wallets": len(ws), **cnt, "hubs": len(hubs), "candidate_edges": len(cand),
                      "direct_pairs": len(direct), "unresolved_pairs": len(unresolved), "dropped": dict(dropped),
                      "wallets_with_inbound_usdc": sum(1 for w, rows in rows_by.items()
                                                       if any(r["to"] == w for r in rows)),
                      "api_calls": cl.calls}}
    json.dump(out, open(a.out, "w"), sort_keys=True)
    print(json.dumps(out["counts"]))


if __name__ == "__main__":
    main()
