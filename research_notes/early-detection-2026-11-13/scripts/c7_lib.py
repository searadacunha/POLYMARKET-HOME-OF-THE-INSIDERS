"""Shared helpers for the c7-chain scripts (rebuilt 2026-11-13 evening to the API the s1..s9 scripts use: P, r1, rpc->(result,url), hexint, pad).
Every HTTP call goes through net.fetch (archived under agents/c7-chain/raw with INDEX.jsonl)."""
import sys, os, json, time, gzip
ROOT = "/Volumes/PHI-Data/Projects/Polymarket-early-detection-raw-20261113"
sys.path.insert(0, ROOT)
os.environ.setdefault("RAW_DIR", "agents/c7-chain/raw")
import net
HERE = os.path.dirname(os.path.abspath(__file__))
def P(name): return os.path.join(HERE, name)
RPCS = ["https://polygon.drpc.org", "https://gateway.tenderly.co/public/polygon", "https://1rpc.io/matic", "https://polygon-bor-rpc.publicnode.com"]
FUNDER = "0xe206961002feebd9edb152eed9b630a351874043"
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def pad(a): return "0x" + "0" * 24 + a.lower()[2:]
def hexint(x): return int(x, 16)
_id = [0]
def rpc(method, params, urls=None, tries=2):
    """Try each url in turn; return (result, url_that_answered). Raises RuntimeError if none answers."""
    last = None
    for u in (urls or RPCS):
        for _ in range(tries):
            _id[0] += 1
            try:
                s, b, m = net.fetch(u, data={"jsonrpc": "2.0", "id": _id[0], "method": method, "params": params}, tag="c7", tries=2)
                if b[:2] == b"\x1f\x8b": b = gzip.decompress(b)
                j = json.loads(b)
                if "result" in j: return j["result"], u
                last = str(j.get("error", j))[:300]
                if "range" in last.lower() or "archive" in last.lower() or "limit" in last.lower(): break
            except Exception as e: last = repr(e)[:300]
            time.sleep(0.5)
    raise RuntimeError(f"rpc fail {method} {last}")
def r1(method, params, urls=None): return rpc(method, params, urls)[0]
