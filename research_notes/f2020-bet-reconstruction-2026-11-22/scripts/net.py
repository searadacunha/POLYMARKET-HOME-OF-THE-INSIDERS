"""HTTP and JSON-RPC reads with retries. Standard library only. Every failure raises: an empty answer is never a zero."""
import json
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "phi-research/1.0", "Accept": "application/json"}
RPC_URLS = ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com",
            "https://gateway.tenderly.co/public/polygon", "https://1rpc.io/matic"]


class SourceError(RuntimeError):
    pass


def get_json(url, tries=4, timeout=40, pause=1.5):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 404, 410):
                break
        except Exception as e:  # network, timeout, bad JSON
            last = str(e)[:200]
        time.sleep(pause * (i + 1))
    raise SourceError(f"{url[:160]} -> {last}")


def rpc(method, params, urls=None, tries=2):
    last = None
    for u in urls or RPC_URLS:
        for i in range(tries):
            try:
                body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
                req = urllib.request.Request(u, data=body, headers={**UA, "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    v = json.load(r)
                if "error" in v:
                    last = f"{u}: {str(v['error'])[:200]}"
                    break  # a JSON-RPC error is deterministic for this node: try the next node
                if v.get("result") is None:
                    last = f"{u}: null result"
                    break
                return v["result"], u
            except Exception as e:
                last = f"{u}: {str(e)[:200]}"
                time.sleep(1 + i)
    raise SourceError(f"{method} failed on every node: {last}")


def rpc_batch(calls, urls=None, tries=2):
    """[(method, params)] -> [result] in order, one HTTP request. Any error or missing id fails the whole batch on that node."""
    last = None
    body = json.dumps([{"jsonrpc": "2.0", "id": i, "method": m, "params": p} for i, (m, p) in enumerate(calls)]).encode()
    for u in urls or RPC_URLS:
        for i in range(tries):
            try:
                req = urllib.request.Request(u, data=body, headers={**UA, "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    v = json.load(r)
                if not isinstance(v, list):
                    last = f"{u}: not a batch answer"
                    break
                got = {x.get("id"): x for x in v}
                if len(got) != len(calls) or any("error" in got.get(k, {"error": 1}) or got[k].get("result") is None
                                                  for k in range(len(calls))):
                    last = f"{u}: incomplete batch"
                    break
                return [got[k]["result"] for k in range(len(calls))], u
            except Exception as e:
                last = f"{u}: {str(e)[:200]}"
                time.sleep(1 + i)
    raise SourceError(f"batch of {len(calls)} failed on every node: {last}")
