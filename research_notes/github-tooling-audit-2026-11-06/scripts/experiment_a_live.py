"""Experiment A (live, bounded): find each Relay origin deposit from the Solana side only, through Polygon logs, no Relay API.

python3 -I experiment_a_live.py <pr27_beneficiary_note_dir> <raw_out_dir> <result.json> [rpc_url]
Inputs used for discovery: each fill's memo id and block time, read from the archived Solana history. The archived Polygon
receipts are read only afterwards, to score the result. One network worker; every RPC response is archived with sha256.
"""
import hashlib, json, resource, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relay_onchain import find_origin, solana_fills, deposits_from_receipt  # noqa: E402

BENEFICIARY = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"


class Rpc:
    def __init__(self, url, raw: Path):
        self.url, self.raw, self.calls, self.bytes = url, raw, 0, 0
        raw.mkdir(parents=True, exist_ok=True)

    def __call__(self, method, params):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        delay = 2.0
        for _ in range(8):
            try:
                req = urllib.request.Request(self.url, data=body, headers={"content-type": "application/json", "user-agent": "polymarket-forensics-research/1.0"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    raw = r.read()
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code} {e.read()[:300]!r}"
                if e.code == 400:
                    raise SystemExit(f"{method}: {last}")  # a malformed or over-limit request will not succeed on retry
                time.sleep(delay); delay *= 2; continue
            except (urllib.error.URLError, TimeoutError) as e:
                time.sleep(delay); delay *= 2; last = repr(e); continue
            p = json.loads(raw)
            if "error" in p:
                last = json.dumps(p["error"])[:300]
                if "not supported" in last or "require" in last:
                    raise SystemExit(f"{method}: {last}")  # plan limit, not a transient error
                time.sleep(delay); delay *= 2; continue
            self.calls += 1; self.bytes += len(raw)
            name = f"{self.calls:04d}_{method}"
            (self.raw / f"{name}.json").write_bytes(raw)
            (self.raw / f"{name}.meta.json").write_text(json.dumps({"endpoint": self.url, "method": method, "params": params,
                "fetched_utc": datetime.now(timezone.utc).isoformat(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}))
            time.sleep(0.6)
            return p["result"]
        raise SystemExit(f"{method} failed: {last}")


def make_block_at(rpc):
    pts = {}

    def ts(b):
        if b not in pts:
            pts[b] = int(rpc("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16)
        return pts[b]

    def block_at(t):
        """Highest block with timestamp <= t (secant steps, then bisection)."""
        hi = int(rpc("eth_blockNumber", []), 16) if not pts else max(pts)
        known = sorted(pts.items())
        lo = max([b for b, x in known if x <= t], default=hi - 50_000_000)
        up = min([b for b, x in known if x > t], default=hi)
        while up - lo > 1:
            tl, tu = ts(lo), ts(up)
            guess = lo + int((t - tl) * (up - lo) / max(tu - tl, 1))
            guess = min(max(guess, lo + 1), up - 1)
            if ts(guess) <= t:
                lo = guess
            else:
                up = guess
            if up - lo > 1 and up - lo < 64:  # converge by bisection once close
                mid = (lo + up) // 2
                lo, up = (mid, up) if ts(mid) <= t else (lo, mid)
        return lo
    return block_at


def main(note: Path, raw: Path, out: Path, url: str):
    ev = note / "evidence"
    fills = solana_fills(ev / "sol" / BENEFICIARY, BENEFICIARY)
    rpc = Rpc(url, raw)
    block_at = make_block_at(rpc)
    t0 = time.perf_counter()
    found = []
    for f in fills:
        d, calls, scanned = find_origin(rpc, f["id"], f["block_time"], block_at, window_blocks=100, max_windows=3)  # drpc free plan: < 200 blocks per getLogs
        found.append({"fill": f["signature"], "id": f["id"], "fill_time": f["block_time"], "origin": d, "getlogs_calls": calls, "logs_scanned": scanned})
    elapsed = time.perf_counter() - t0
    truth = {d["id"]: d for p in sorted((ev / "polygon").glob("*.eth_getTransactionReceipt.json"))
             for d in deposits_from_receipt(json.loads(p.read_text())["result"])}
    score = {"fills": len(fills), "origin_found": sum(1 for x in found if x["origin"]),
             "tx_matches_archive": sum(1 for x in found if x["origin"] and truth.get(x["id"], {}).get("tx") == x["origin"]["tx"]),
             "depositor_matches_archive": sum(1 for x in found if x["origin"] and truth.get(x["id"], {}).get("depositor") == x["origin"]["depositor"]),
             "amount_matches_archive": sum(1 for x in found if x["origin"] and truth.get(x["id"], {}).get("amount") == x["origin"]["amount"])}
    res = {"experiment": "A-live", "rpc": url, "score": score,
           "cost": {"rpc_calls": rpc.calls, "bytes_downloaded": rpc.bytes, "seconds": round(elapsed, 1),
                    "logs_scanned": sum(x["logs_scanned"] for x in found), "process_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
           "rows": found}
    out.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else "https://polygon.drpc.org")
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1))
