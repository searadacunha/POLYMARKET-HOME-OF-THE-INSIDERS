"""Keyless read-only HTTP for the study collectors. Bounded retries, Retry-After honoured, gzip, counters.
An HTTP error or a transport failure is never turned into an empty result: get() raises SourceError."""
import atexit, gzip, hashlib, json, time, urllib.error, urllib.request
from collections import Counter

UA = {"User-Agent": "Mozilla/5.0 (compatible; research-client/1.0)", "Accept": "application/json", "Accept-Encoding": "gzip"}
RETRY = (429, 500, 502, 503, 504, 520, 522, 524, 529)
COUNTS = Counter()      # requested / ok / retry_<status> / transport / failed


def _keep_counts():         # one line per run of a collector, appended, so a later run does not erase an earlier one
    import os, sys
    if COUNTS and sys.argv[0] not in ("-", "", "-c"):      # a one-off probe typed at the prompt is not a collection run
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "collect_counts.jsonl"), "a") as f:
            f.write(json.dumps({"script": os.path.basename(sys.argv[0]), "args": sys.argv[1:], "ended": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "counts": dict(COUNTS)}) + "\n")


atexit.register(_keep_counts)


class SourceError(RuntimeError):
    pass


def get(url, data=None, timeout=45, tries=7, pace=None):
    """Return (parsed JSON, sha256 of the raw body). Raises SourceError after `tries` failed attempts."""
    last = None
    body_out = None if data is None else json.dumps(data).encode()
    headers = dict(UA, **({"Content-Type": "application/json"} if data is not None else {}))
    for attempt in range(tries):
        if pace:
            pace()
        COUNTS["requested"] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body_out, headers=headers), timeout=timeout) as r:
                raw, status, rh = r.read(), r.status, r.headers
        except urllib.error.HTTPError as e:
            raw, status, rh = (e.read() or b""), e.code, (e.headers or {})
        except Exception as e:                       # DNS, TLS, timeout
            last = repr(e); COUNTS["transport"] += 1
            time.sleep(min(60, 3 * 2 ** attempt)); continue
        if status == 200:
            if rh.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            COUNTS["ok"] += 1
            return json.loads(raw), hashlib.sha256(raw).hexdigest()
        COUNTS[f"http_{status}"] += 1
        last = f"HTTP {status}: {raw[:160]!r}"
        if status not in RETRY:
            break
        ra = (rh.get("Retry-After") or "") if rh else ""
        time.sleep(min(float(ra), 120.0) if ra.replace(".", "", 1).isdigit() else min(90, 4 * 2 ** attempt))
    COUNTS["failed"] += 1
    raise SourceError(f"{url[:160]} :: {last}")


class Pace:
    """Minimum spacing between requests of one collector."""
    def __init__(self, interval):
        self.interval, self._next = interval, 0.0

    def __call__(self):
        d = self._next - time.time()
        if d > 0:
            time.sleep(d)
        self._next = time.time() + self.interval
