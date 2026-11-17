"""Keyless read-only HTTP and JSON-RPC. Bounded retries with backoff, Retry-After honoured, gzip, per-host counters.
An HTTP error is never turned into an empty result: get_json and rpc raise."""
import gzip, json, time, urllib.error, urllib.request
from collections import Counter

UA = "Mozilla/5.0 (compatible; research-client/1.0)"
RETRY = (429, 500, 502, 503, 504, 529)
COUNTS = Counter()          # "<host>:<status>" -> n, shown by the status command
RPC_URLS = ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com", "https://gateway.tenderly.co/public/polygon",
            "https://1rpc.io/matic"]


class SourceError(RuntimeError):
    def __init__(self, msg, status=None):
        super().__init__(msg); self.status = status


def fetch(url, data=None, timeout=30, tries=4, sleep=time.sleep):
    """Return (status, body). HTTP errors are returned; a transport failure raises SourceError after `tries`."""
    host = url.split("/")[2]
    h = {"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"}
    body_out = None if data is None else json.dumps(data).encode()
    if body_out is not None:
        h["Content-Type"] = "application/json"
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body_out, headers=h), timeout=timeout) as r:
                body, status, rh = r.read(), r.status, r.headers
        except urllib.error.HTTPError as e:
            body, status, rh = (e.read() or b""), e.code, (e.headers or {})
        except Exception as e:  # DNS, TLS, timeout: counted, retried, finally raised
            last = repr(e); COUNTS[f"{host}:transport"] += 1
            sleep(1.5 * (attempt + 1)); continue
        if rh.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        COUNTS[f"{host}:{status}"] += 1
        if status in RETRY and attempt < tries - 1:
            ra = rh.get("Retry-After") or ""
            sleep(min(float(ra), 30.0) if ra.replace(".", "", 1).isdigit() else 2.0 * (attempt + 1)); continue
        return status, body
    raise SourceError(f"transport failure after {tries} tries: {url} :: {last}")


def get_json(url, **kw):
    status, body = fetch(url, **kw)
    if status != 200:
        raise SourceError(f"HTTP {status} for {url}: {body[:200]!r}", status)
    return json.loads(body)


def rpc(method, params, urls=None, **kw):
    """JSON-RPC call, falling back over the public endpoints. A JSON-RPC error object raises (never an empty result)."""
    err = None
    for url in (urls or RPC_URLS):
        try:
            j = get_json(url, data={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, **kw)
        except SourceError as e:
            err = e; continue
        if "error" in j:
            err = SourceError(f"{url} {method}: {j['error']}"); continue
        return j["result"]
    raise err or SourceError(f"no RPC endpoint answered {method}")
