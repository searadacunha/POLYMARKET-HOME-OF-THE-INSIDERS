"""Experiment C: chain-only Relay matching on an independent sample, validated against the Relay API afterwards.

python3 -I -B experiment_c.py <raw_dir> <out_dir> step     with step in: logs, truth-s1, keys, search, truth-s2, score

The sample is fixed here before any of it is read: Relay Depository logs of four 40-block windows on Polygon,
none within 200,000 blocks of the case (block 83,584,716). S1 (15 and 20 February 2026) teaches which solver
keys pay fills; S2 (6 and 12 March 2026) is searched with those keys only, and its search results are written
and hashed BEFORE the S2 ground truth is requested. The Relay API is used only as ground truth.

Matching rules (from section 4 of REPORT.md): on Solana, a solver transaction whose memo is the Depository log
`id`; on an EVM chain, a solver transaction whose calldata ends with the `id`. One worker; every raw response is
archived under <raw_dir> with its SHA-256; keys are read from the local pool and never written.
"""
import hashlib, json, sys, time, urllib.error, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiment_a_forward import Net, recipient_of  # noqa: E402
from relay_onchain import DEPOSITORIES, MEMO_PROGRAMS, T_ERC20, T_NATIVE, decode_deposit_log  # noqa: E402

WINDOWS = {"S1": [83_000_000, 83_250_000], "S2": [83_850_000, 84_100_000]}
WIDTH = 40            # blocks per window (about 80 s)
FILL_SLACK = 300      # seconds after the window's last block in which fills are searched
SOLANA = 792703809
MAX_PAGES = 50
# keyless fallbacks for chains the free Etherscan plan does not serve (added before the S2 search, see REPORT 4.8)
RPC = {10: "https://mainnet.optimism.io", 56: "https://bsc-dataseed.bnbchain.org", 8453: "https://mainnet.base.org",
       42161: "https://arb1.arbitrum.io/rpc", 1: "https://ethereum-rpc.publicnode.com", 137: "https://polygon.drpc.org"}
BLOCKSCOUT = {10: "https://optimism.blockscout.com", 8453: "https://base.blockscout.com", 1: "https://eth.blockscout.com",
              42161: "https://arbitrum.blockscout.com", 137: "https://polygon.blockscout.com"}
UA = {"user-agent": "relay-onchain-research/1.0", "accept": "application/json"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Get:
    """Archived GET with retries on 429/5xx; any other HTTP error stops the run."""

    def __init__(self, raw: Path):
        raw.mkdir(parents=True, exist_ok=True)
        # numbering continues after the files already archived, so a resumed step never overwrites a response
        self.raw, self.n, self.bytes = raw, len(list(raw.glob("*.meta.json"))), 0

    def __call__(self, url, label, redact=None, delay=0.4, tries=8):
        for i in range(tries):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                    raw = r.read()
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    time.sleep(15 * (i + 1)); continue
                raise SystemExit(f"{label}: HTTP {e.code}")
            except (urllib.error.URLError, TimeoutError):
                time.sleep(15 * (i + 1)); continue
            self.n += 1; self.bytes += len(raw)
            name = f"{self.n:04d}_{label}"
            (self.raw / f"{name}.json").write_bytes(raw)
            (self.raw / f"{name}.meta.json").write_text(json.dumps({"url": url.replace(redact, "<KEY>") if redact else url,
                                                                   "sha256": sha(raw), "bytes": len(raw),
                                                                   "fetched_utc": datetime.now(timezone.utc).isoformat()}))
            time.sleep(delay)
            return json.loads(raw)
        raise SystemExit(f"{label}: failed after {tries} tries")


def etherscan_key():
    for line in (Path.home() / "Downloads/.env").read_text().splitlines():
        if line.startswith("ETHERSCAN_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("no Etherscan key")


def es(get, key, chain, q, label):
    """Etherscan v2 call; returns result, or the string 'UNSUPPORTED' when the free plan does not serve the chain."""
    for i in range(6):
        d = get(f"https://api.etherscan.io/v2/api?chainid={chain}&{q}&apikey={key}", label, redact=key)
        res = d.get("result")
        if "Free API access is not supported for this chain" in str(res) or "Missing or unsupported chainid" in str(res):
            return "UNSUPPORTED"  # exact messages only: any other error is retried, never read as empty
        if q.startswith("module=proxy") and isinstance(res, dict):
            return res
        if d.get("status") == "1" or "No transactions found" in str(d.get("message")):
            return res if res is not None else []
        time.sleep(3 * (i + 1))  # rate limit or busy: never read as an empty list
    raise SystemExit(f"etherscan {chain} {q[:60]}: {str(d)[:200]}")


def step_logs(net, out):
    rows, windows = [], {}
    for s, starts in WINDOWS.items():
        for b in starts:
            logs = net.post("https://polygon.drpc.org", "eth_getLogs",
                            [{"address": next(iter(DEPOSITORIES)), "fromBlock": hex(b), "toBlock": hex(b + WIDTH - 1), "topics": [[T_ERC20, T_NATIVE]]}], "logs")
            t = [int(net.post("https://polygon.drpc.org", "eth_getBlockByNumber", [hex(x), False], "block")["timestamp"], 16) for x in (b, b + WIDTH - 1)]
            windows[f"{s}_{b}"] = {"sample": s, "from_block": b, "to_block": b + WIDTH - 1, "t_first": t[0], "t_last": t[1], "logs": len(logs)}
            for log in logs:
                d = decode_deposit_log(log)
                if d:
                    rows.append({**d, "sample": s, "window": f"{s}_{b}", "tx": log["transactionHash"].lower(),
                                 "log_index": int(log["logIndex"], 16), "block": int(log["blockNumber"], 16)})
    ids = defaultdict(int)
    for r in rows:
        ids[r["id"]] += 1
    (out / "c_deposits.json").write_text(json.dumps({"windows": windows, "deposits": rows,
                                                     "duplicate_ids": {k: v for k, v in ids.items() if v > 1}}, indent=1))
    print({k: v["logs"] for k, v in windows.items()}, "deposits", len(rows))


def flat_request(r):
    d = r.get("data") or {}
    m = d.get("metadata") or {}
    ci, co = m.get("currencyIn") or {}, m.get("currencyOut") or {}
    return {"request_id": r["id"], "status": r["status"], "user": r.get("user"), "recipient": r.get("recipient"), "referrer": r.get("referrer"),
            "origin_chain": (ci.get("currency") or {}).get("chainId"), "dest_chain": (co.get("currency") or {}).get("chainId"),
            "in_txs": [(x.get("hash") or "").lower() for x in d.get("inTxs") or []],
            "out_txs": [{"hash": x.get("hash"), "chain": x.get("chainId")} for x in d.get("outTxs") or []],
            "amount_in": ci.get("amount"), "amount_out": co.get("amount")}


def step_truth(get, out, sample):
    dep = json.loads((out / "c_deposits.json").read_text())["deposits"]
    txs = sorted({d["tx"] for d in dep if d["sample"] == sample})
    p = out / f"c_truth_{sample}.json"
    truth = json.loads(p.read_text()) if p.exists() else {}  # resumable: a stopped run keeps what it has
    for h in txs:
        if h in truth:
            continue
        b = get(f"https://api.relay.link/requests/v2?hash={h}", f"relay_{sample}", delay=13)
        if not isinstance(b, dict) or not isinstance(b.get("requests"), list) or b.get("continuation"):
            raise SystemExit(f"relay {h}: unexpected envelope {str(b)[:200]}")  # never read as 'no request'
        truth[h] = [flat_request(r) for r in b["requests"]]
        p.write_text(json.dumps(truth, indent=1))
    p.write_text(json.dumps(truth, indent=1))
    print(sample, "transactions", len(txs), "with a request", sum(1 for v in truth.values() if v))


def step_keys(net, get, out):
    """Solver keys and EVM solver addresses, learned from the S1 ground truth only."""
    truth = json.loads((out / "c_truth_S1.json").read_text())
    key = None
    sol, evm, unread = defaultdict(int), defaultdict(int), defaultdict(int)
    for reqs in truth.values():
        for r in reqs:
            for o in r["out_txs"]:
                if not o["hash"]:
                    continue
                if o["chain"] == SOLANA:
                    tx = net.post("https://mainnet.helius-rpc.com/", "getTransaction",
                                  [o["hash"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}], "s1_fill")
                    ak = tx["transaction"]["message"]["accountKeys"]
                    sol[ak[0]["pubkey"] if isinstance(ak[0], dict) else ak[0]] += 1
                elif o["chain"] not in (8253038,):
                    key = key or etherscan_key()
                    tx = es(get, key, o["chain"], f"module=proxy&action=eth_getTransactionByHash&txhash={o['hash']}", "s1_fill_evm")
                    if tx == "UNSUPPORTED" and o["chain"] in RPC:
                        tx = net.post(RPC[o["chain"]], "eth_getTransactionByHash", [o["hash"]], "s1_fill_evm_rpc")
                    if isinstance(tx, dict):
                        evm[(tx["from"].lower(), o["chain"])] += 1
                    else:
                        unread[o["chain"]] += 1
    res = {"solana_solver_keys": dict(sorted(sol.items(), key=lambda x: -x[1])),
           "evm_solvers": [{"address": a, "chain": c, "fills": n} for (a, c), n in sorted(evm.items(), key=lambda x: -x[1])],
           "fills_not_read_by_chain": dict(unread)}
    (out / "c_keys.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def memo_ids(tx):
    out = []
    for ins in tx["transaction"]["message"]["instructions"]:
        m = ins.get("parsed") if ins.get("programId") in MEMO_PROGRAMS else None
        if isinstance(m, str) and m.startswith("0x") and len(m) == 66:
            out.append(m.lower())
    return out


def evm_window(get, ekey, s, c, lo, hi, ids, cost):
    """Solver transactions on chain c in [lo, hi] whose calldata ends with a sampled id; None if no explorer serves c."""
    b0 = es(get, ekey, c, f"module=block&action=getblocknobytime&timestamp={lo}&closest=before", "blk")
    b1 = es(get, ekey, c, f"module=block&action=getblocknobytime&timestamp={hi}&closest=after", "blk")
    via = "etherscan"
    if "UNSUPPORTED" in (b0, b1):
        if c not in BLOCKSCOUT:
            return None
        via = "blockscout"
        b0 = get(f"{BLOCKSCOUT[c]}/api?module=block&action=getblocknobytime&timestamp={lo}&closest=before", "blk_bs", delay=3, tries=3)["result"]["blockNumber"]
        b1 = get(f"{BLOCKSCOUT[c]}/api?module=block&action=getblocknobytime&timestamp={hi}&closest=after", "blk_bs", delay=3, tries=3)["result"]["blockNumber"]
    hits, page = [], 1
    while True:
        q = f"module=account&action=txlist&address={s['address']}&startblock={b0}&endblock={b1}&page={page}&offset=1000&sort=asc"
        if via == "etherscan":
            txs = es(get, ekey, c, q, "search_evm")
        else:
            d = get(f"{BLOCKSCOUT[c]}/api?{q}", "search_evm_bs", delay=3, tries=3)
            if d.get("status") != "1" and "No transactions found" not in str(d.get("message")):
                raise SystemExit(f"blockscout {c}: {str(d)[:200]}")
            txs = d.get("result") or []
        cost[f"evm_pages_{via}_{c}"] += 1; cost["evm_tx_scanned"] += len(txs)
        for tx in txs:
            tail = "0x" + tx["input"][-64:].lower()
            if len(tx["input"]) >= 66 and tail in ids:
                hits.append((tail, {"chain": c, "hash": tx["hash"].lower(), "solver": s["address"], "time": int(tx["timeStamp"]),
                                    "err": tx.get("isError") != "0", "to": tx["to"].lower()}))
        if len(txs) < 1000:
            return hits
        page += 1


def step_search(net, get, out):
    dep = json.loads((out / "c_deposits.json").read_text())
    keys = json.loads((out / "c_keys.json").read_text())
    ids = {d["id"] for d in dep["deposits"]}
    found = defaultdict(list)
    cost = defaultdict(int)
    uncovered = []
    ekey = None
    for wname, w in dep["windows"].items():
        lo, hi = w["t_first"], w["t_last"] + FILL_SLACK
        for k in keys["solana_solver_keys"]:
            token, pages = None, 0
            while True:
                opts = {"transactionDetails": "full", "encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "limit": 100,
                        "sortOrder": "asc", "filters": {"blockTime": {"gte": lo, "lte": hi}}}
                if token:
                    opts["paginationToken"] = token
                res = net.post("https://mainnet.helius-rpc.com/", "getTransactionsForAddress", [k, opts], "search_sol")
                pages += 1; cost["helius_pages"] += 1; cost["solana_tx_scanned"] += len(res["data"])
                for tx in res["data"]:
                    for i in memo_ids(tx):
                        if i in ids:
                            r = recipient_of(tx, i, k)
                            found[i].append({"chain": SOLANA, "hash": tx["transaction"]["signatures"][0], "solver": k,
                                             "time": tx["blockTime"], "err": tx["meta"]["err"], **{x: r[x] for x in ("lamport_credited", "token_owner_credited")}})
                token = res.get("paginationToken")
                if not token or not res["data"]:
                    break
                if pages >= MAX_PAGES:
                    cost["solana_windows_truncated"] += 1; break
        for s in keys["evm_solvers"]:
            ekey = ekey or etherscan_key()
            c = s["chain"]
            try:
                hits = evm_window(get, ekey, s, c, lo, hi, ids, cost)
            except SystemExit as e:  # a refused explorer: this window and chain are not covered, nothing partial is kept
                uncovered.append([wname, c, s["address"], str(e)[:120]]); continue
            if hits is None:
                uncovered.append([wname, c, s["address"], "no explorer serves this chain"]); continue
            for i, h in hits:
                found[i].append(h)
    res = {"found": found, "cost": cost, "uncovered": uncovered, "calls": {"rpc": net.n, "get": get.n}, "bytes": net.bytes + get.bytes}
    p = out / "c_search.json"
    p.write_text(json.dumps(res, indent=1))
    print("ids with a chain-only fill", len(found), "collisions", sum(1 for v in found.values() if len(v) > 1), "sha256", sha(p.read_bytes()))


VERIFIABLE = ("hit", "wrong_fill", "miss")  # the only outcomes in the denominator of the hit rate
EXPECTED_SEARCH = Path(__file__).resolve().parent.parent / "results" / "experiment_c_search.SHA256"


def wilson(k, n, z=1.96):
    if not n:
        return None
    p, d = k / n, 1 + z * z / n
    c, h = p + z * z / (2 * n), z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5
    return [round((c - h) / d, 4), round((c + h) / d, 4)]


def archived_evm(raw):
    """hash -> (to, input) of every solver transaction in the archived txlist pages (chain data, identical across runs)."""
    tx = {}
    for f in raw.parent.glob("raw*/http/*_search_evm*.json"):
        if not f.name.endswith(".meta.json"):
            for t in json.loads(f.read_bytes()).get("result") or []:
                tx[t["hash"].lower()] = (t["to"].lower(), t["input"].lower())
    return tx


def recipient_agrees(r, g, evm):
    """True/False when the API recipient can be compared with the fill, None when it cannot."""
    want = r["recipient"]
    if not want:
        return None
    if g["chain"] == SOLANA:
        return want in g["lamport_credited"] or want in g["token_owner_credited"]
    if g["hash"] not in evm:
        return None
    to, inp = evm[g["hash"]]
    w = want.lower()
    words = {"0x" + inp[i + 24:i + 64] for i in range(10, len(inp) - 63, 64)}  # 32-byte arguments after the selector
    return w == to or w in words


def hkey(h, chain):
    """Comparable form of a transaction hash: hex is case-insensitive, a Solana signature (base58) is not."""
    return h if chain == SOLANA else h.lower()


def step_score(raw, out, expected=EXPECTED_SEARCH):
    dep = json.loads((out / "c_deposits.json").read_text())
    sp = out / "c_search.json"
    search, keys = json.loads(sp.read_text()), json.loads((out / "c_keys.json").read_text())
    want = expected.read_text().split()[0]
    if sha(sp.read_bytes()) != want:
        raise SystemExit(f"c_search.json is not the search hashed before the S2 truth ({want[:12]})")
    found, evm = search["found"], archived_evm(raw)
    refused = {(w, c) for w, c, *_ in search["uncovered"]}
    searched = ({SOLANA} if keys["solana_solver_keys"] else set()) | {e["chain"] for e in keys["evm_solvers"]}
    # shortcut: the search counts MAX_PAGES truncations without naming the window, so any truncation voids all Solana coverage
    sol_truncated = search["cost"].get("solana_windows_truncated", 0)
    fill_ids = defaultdict(set)
    for i, gs in found.items():
        for g in gs:
            fill_ids[hkey(g["hash"], g["chain"])].add(i)
    res = {}
    for sample in ("S1", "S2"):
        tp = out / f"c_truth_{sample}.json"
        truth = json.loads(tp.read_text()) if tp.exists() else {}
        by_tx = defaultdict(list)
        for d in dep["deposits"]:
            if d["sample"] == sample:
                by_tx[d["tx"]].append(d)
        rows, tally, why, rec = [], defaultdict(int), defaultdict(int), defaultdict(int)
        for tx, ds in sorted(by_tx.items()):
            reqs = [r for r in truth.get(tx, []) if tx in r["in_txs"]]
            o = ("truth_missing" if tx not in truth else "multi_deposit_tx" if len(ds) > 1 else
                 "no_relay_request" if not reqs else "multiple_requests" if len(reqs) > 1 else None)
            if o:
                tally[o] += len(ds)
                rows.append({"tx": tx, "deposits": len(ds), "requests": len(reqs), "outcome": o})
                continue
            d, r = ds[0], reqs[0]
            outs = {hkey(x["hash"], x["chain"]) for x in r["out_txs"] if x["chain"] == r["dest_chain"] and x["hash"]}
            got = found.get(d["id"], [])
            hashes = {hkey(g["hash"], g["chain"]) for g in got}
            c, cov = r["dest_chain"], None
            if c not in searched:
                cov = "no_learned_solver_on_chain"
            elif (d["window"], c) in refused:
                cov = "provider_refused_window"
            if r["status"] != "success":
                o = "not_success_found_fill" if got else "not_success_no_fill"
            elif not outs:
                o = "success_without_fill_hash"
            elif cov:
                o = "chain_not_covered"; why[f"{cov}:{c}"] += 1
            elif c == SOLANA and sol_truncated:
                o = "coverage_incomplete"
            elif hashes & outs:
                o = "hit"
            elif got:
                o = "wrong_fill"
            else:
                o = "miss"
            tally[o] += 1
            ok = None
            if o == "hit":
                ok = recipient_agrees(r, next(g for g in got if hkey(g["hash"], g["chain"]) in outs), evm)
                rec[{True: "agrees", False: "differs", None: "not_comparable"}[ok]] += 1
            rows.append({"tx": tx, "id": d["id"], "depositor": d["depositor"], "token": d["token"], "amount": d["amount"],
                         "status": r["status"], "dest_chain": c, "referrer": r["referrer"], "api_out": sorted(outs),
                         "api_recipient": r["recipient"], "chain_only": got, "collision": len(got) > 1,
                         "outcome": o, "recipient_agrees": ok})
        tally = dict(tally); n = lambda k: tally.get(k, 0)  # noqa: E731  (reading must not create zero categories)
        ids = [d["id"] for ds in by_tx.values() for d in ds]
        n_ops, cov_n = len(ids), sum(n(k) for k in VERIFIABLE)
        usable = cov_n + n("chain_not_covered") + n("coverage_incomplete")
        res[sample] = {
            "role": "independent validation" if sample == "S2" else "in-sample: solver keys were learned here, not a validation",
            "summary": {"operations": n_ops, "with_usable_truth": usable, "covered": cov_n,
                        "coverage_rate": round(cov_n / usable, 4) if usable else None,
                        "exact": n("hit"), "wrong": n("wrong_fill"), "not_found_with_full_coverage": n("miss"),
                        "not_covered": n("chain_not_covered") + n("coverage_incomplete"),
                        "hit_rate_on_covered": round(n("hit") / cov_n, 4) if cov_n else None,
                        "hit_rate_wilson95": wilson(n("hit"), cov_n),
                        "collisions": {"ids_with_several_fills": sum(1 for i in ids if len(found.get(i, [])) > 1),
                                       "fills_matching_several_ids": sum(1 for h, s in fill_ids.items() if len(s & set(ids)) > 1),
                                       "duplicate_deposit_ids": sum(1 for i in ids if i in dep["duplicate_ids"])},
                        "recipient_on_hits": dict(rec)},
            "tally": tally, "not_covered_by_reason": dict(why), "rows": rows}
        assert sum(tally.values()) == n_ops, (sample, dict(tally), n_ops)  # every operation lands in exactly one category
    # order proof: the S2 search was written before the first S2 ground-truth request (all raw folders of the experiment)
    metas = [json.loads(m.read_text())["fetched_utc"] for m in raw.parent.glob("raw*/http/*_relay_S2.meta.json")]
    written = datetime.fromtimestamp(sp.stat().st_mtime, timezone.utc)
    first = min(metas) if metas else None
    res["order"] = {"search_sha256": want, "search_written_utc": written.isoformat(), "first_s2_truth_request_utc": first,
                    "s2_truth_requests_archived": len(metas),
                    "search_before_s2_truth": first is None or written < datetime.fromisoformat(first)}
    res["search_coverage"] = {"chains_searched": sorted(searched), "refused_windows": search["uncovered"],
                              "solana_windows_truncated": sol_truncated}
    truth_cost = {}
    for s in ("S1", "S2"):
        m = [json.loads(f.read_text()) for f in raw.parent.glob(f"raw*/http/*_relay_{s}.meta.json")]
        truth_cost[s] = {"requests_archived": len(m), "bytes": sum(x["bytes"] for x in m)}
    steps = {}  # duration of each step, from the one-line summary main() prints into <step>.log
    for f in raw.parent.glob("*.log"):
        for w in (line.split() for line in f.read_text().splitlines()):
            if len(w) == 7 and w[1] == "calls" and w[5] == "seconds":
                steps[f.stem] = {"calls": int(w[2]), "bytes": int(w[4]), "seconds": float(w[6])}
    res["cost"] = {"search": search["cost"] | {"calls": search["calls"], "bytes": search["bytes"]}, "truth": truth_cost, "steps": steps}
    (out / "c_score.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k]["summary"] for k in ("S1", "S2")}, indent=1), res["order"])
    return res


def main():
    raw, out, step = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    out.mkdir(parents=True, exist_ok=True)
    net, get = Net(raw / "rpc"), Get(raw / "http")
    t0 = time.perf_counter()
    {"logs": lambda: step_logs(net, out), "truth-s1": lambda: step_truth(get, out, "S1"), "keys": lambda: step_keys(net, get, out),
     "search": lambda: step_search(net, get, out), "truth-s2": lambda: step_truth(get, out, "S2"),
     "score": lambda: step_score(raw, out)}[step]()
    print(step, "calls", net.n + get.n, "bytes", net.bytes + get.bytes, "seconds", round(time.perf_counter() - t0, 1))


if __name__ == "__main__":
    main()
