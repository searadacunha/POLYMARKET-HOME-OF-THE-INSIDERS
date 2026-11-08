"""Experiment A (live, forward direction): from a Polymarket withdrawal into Relay, find the unknown Solana recipient.

python3 -I experiment_a_forward.py <pr27_beneficiary_note_dir> <raw_out_dir> <result.json>
Inputs used for discovery: the archived Polygon receipts only (Depository log id, block number). The Polygon block time comes
from polygon.drpc.org (keyless); the solver's Solana transactions in [t, t + 180 s] come from Helius getTransactionsForAddress
(keys read from the local pool, never written). The recipient is the account, other than the solver, credited by the
transaction whose memo is the id. Scored afterwards against the archived beneficiary history. One worker; raw responses archived.
"""
import hashlib, json, re, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relay_onchain import MEMO_PROGRAMS, deposits_from_receipt, solana_fills  # noqa: E402

SOLVERS = ["F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe"]  # payer of every archived fill to the beneficiary; others exist
BENEFICIARY = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
_KEY = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
UA = {"content-type": "application/json", "user-agent": "polymarket-forensics-research/1.0"}


def helius_keys():
    cfg = json.loads((Path.home() / ".config/forensics_v2/helius_sources.json").read_text())
    ok, out = set(cfg["pool_fingerprints"]), []
    for s in cfg["sources"]:
        p = Path(s["path"]).expanduser()
        if p.exists():
            for k in _KEY.findall(p.read_text(errors="replace")):
                if hashlib.sha256(k.encode()).hexdigest()[:8] in ok and k not in out:
                    out.append(k)
    if not out:
        raise SystemExit("no pool key")
    return out


class Net:
    def __init__(self, raw: Path):
        self.raw, self.n, self.bytes, self.keys, self.i = raw, 0, 0, None, 0
        raw.mkdir(parents=True, exist_ok=True)

    def post(self, url, method, params, label):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        delay, last = 2.0, ""
        for _ in range(8):
            u = url
            if "helius" in url:
                self.keys = self.keys or helius_keys()
                u = f"{url}?api-key={self.keys[self.i % len(self.keys)]}"; self.i += 1
            try:
                with urllib.request.urlopen(urllib.request.Request(u, data=body, headers=UA), timeout=120) as r:
                    raw = r.read()
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code} {_KEY.sub('<KEY>', e.read()[:200].decode(errors='replace'))}"
                if e.code == 400:
                    raise SystemExit(f"{method}: {last}")
                time.sleep(delay); delay *= 2; continue
            except Exception as e:
                last = _KEY.sub("<KEY>", repr(e)); time.sleep(delay); delay *= 2; continue
            p = json.loads(raw)
            if "error" in p:
                last = _KEY.sub("<KEY>", json.dumps(p["error"])[:200]); time.sleep(delay); delay *= 2; continue
            self.n += 1; self.bytes += len(raw)
            name = f"{self.n:04d}_{label}"
            (self.raw / f"{name}.json").write_bytes(raw)
            (self.raw / f"{name}.meta.json").write_text(json.dumps({"endpoint": url + (" (key redacted)" if "helius" in url else ""),
                "method": method, "params": params, "fetched_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}))
            time.sleep(0.4)
            return p["result"]
        raise SystemExit(f"{method}: {last}")


def recipient_of(tx, relay_id, solver):
    """The account credited by a solver transaction whose memo is relay_id, or None."""
    memos = [i.get("parsed") for i in tx["transaction"]["message"]["instructions"] if i.get("programId") in MEMO_PROGRAMS]
    if relay_id not in [m.lower() for m in memos if isinstance(m, str)]:
        return None
    ak = [k["pubkey"] if isinstance(k, dict) else k for k in tx["transaction"]["message"]["accountKeys"]]
    m = tx["meta"]
    credited = [ak[i] for i in range(len(m["preBalances"])) if m["postBalances"][i] > m["preBalances"][i] and ak[i] != solver]
    owners = {b.get("owner") for b in (m.get("postTokenBalances") or [])
              if b.get("owner") != solver and int(b["uiTokenAmount"]["amount"]) > int(next((p["uiTokenAmount"]["amount"] for p in (m.get("preTokenBalances") or []) if p["accountIndex"] == b["accountIndex"]), 0))}
    return {"signature": tx["transaction"]["signatures"][0], "lamport_credited": credited, "token_owner_credited": sorted(o for o in owners if o)}


def main(note: Path, raw: Path, out: Path):
    ev = note / "evidence"
    deps = [d for f in sorted((ev / "polygon").glob("*.eth_getTransactionReceipt.json")) for d in deposits_from_receipt(json.loads(f.read_text())["result"])]
    net = Net(raw)
    t0 = time.perf_counter()
    rows = []
    for d in deps:
        blk = net.post("https://polygon.drpc.org", "eth_getBlockByNumber", [hex(d["block"]), False], "polygon_block")
        t = int(blk["timestamp"], 16)
        hit, pages = None, 0
        for solver in SOLVERS:
            token = None
            while hit is None:
                opts = {"transactionDetails": "full", "encoding": "jsonParsed", "maxSupportedTransactionVersion": 1, "limit": 100,
                        "sortOrder": "asc", "filters": {"blockTime": {"gte": t, "lte": t + 180}}}
                if token:
                    opts["paginationToken"] = token
                res = net.post("https://mainnet.helius-rpc.com/", "getTransactionsForAddress", [solver, opts], "solver_window")
                pages += 1
                for tx in res["data"]:
                    r = recipient_of(tx, d["id"], solver)
                    if r:
                        hit = {**r, "solver": solver, "fill_time": tx["blockTime"]}
                        break
                token = res.get("paginationToken")
                if not token or pages >= 10:  # shortcut: 10 pages = 1,000 solver tx per 180 s; widen if a fill is missed
                    break
        rows.append({"polygon_tx": d["tx"], "id": d["id"], "depositor": d["depositor"], "deposit_time": t, "solver_pages": pages, "found": hit})
    elapsed = time.perf_counter() - t0
    truth = {f["id"]: f["signature"] for f in solana_fills(ev / "sol" / BENEFICIARY, BENEFICIARY)}
    score = {"deposits": len(rows), "with_fill_found": sum(1 for r in rows if r["found"]),
             "beneficiary_deposits": sum(1 for r in rows if r["id"] in truth),
             "beneficiary_recipient_recovered": sum(1 for r in rows if r["id"] in truth and r["found"] and BENEFICIARY in r["found"]["lamport_credited"]
                                                     and r["found"]["signature"] == truth[r["id"]])}
    res = {"experiment": "A-forward", "score": score, "cost": {"calls": net.n, "bytes": net.bytes, "seconds": round(elapsed, 1)}, "rows": rows}
    out.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1))
    for x in r["rows"]:
        print(x["polygon_tx"][:12], x["depositor"][:10], "pages", x["solver_pages"], "->", (x["found"] or {}).get("lamport_credited"), (x["found"] or {}).get("token_owner_credited"))
