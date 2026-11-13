"""Keyless read-only HTTP helper with raw archival. Every response (success or failure) is indexed.
Raw bodies are gzip files named by SHA-256 of the body; INDEX.jsonl records url, status, elapsed, time."""
import gzip, hashlib, json, os, time, urllib.request, urllib.error, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / os.environ.get("RAW_DIR", "raw")  # per-agent raw dirs avoid interleaved index writes
INDEX = RAW / "INDEX.jsonl"
UA = "Mozilla/5.0 (compatible; research-client/1.0)"

def fetch(url, data=None, headers=None, timeout=30, tries=4, pause=0.0, tag=""):
    """Return (status, body_bytes, meta). Never raises on HTTP errors; raises only after all tries fail at transport."""
    h = {"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"}
    if headers: h.update(headers)
    body_out = None if data is None else (data if isinstance(data, bytes) else json.dumps(data).encode())
    if body_out is not None: h.setdefault("Content-Type", "application/json")
    last = None
    for attempt in range(tries):
        if pause: time.sleep(pause)
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=body_out, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read(); status = r.status; rh = dict(r.headers)
                if rh.get("Content-Encoding") == "gzip": body = gzip.decompress(body)
        except urllib.error.HTTPError as e:
            body = e.read() or b""; status = e.code; rh = dict(e.headers or {})
            if rh.get("Content-Encoding") == "gzip": body = gzip.decompress(body)
        except Exception as e:  # transport failure: recorded, retried
            last = repr(e)
            _log(url, body_out, None, time.time() - t0, t0, b"", {}, tag, err=last)
            time.sleep(1.5 * (attempt + 1)); continue
        meta = _log(url, body_out, status, time.time() - t0, t0, body, rh, tag)
        if status in (429, 500, 502, 503, 504, 529) and attempt < tries - 1:
            ra = rh.get("Retry-After")
            time.sleep(min(float(ra), 30) if ra and ra.replace(".", "").isdigit() else 2.0 * (attempt + 1)); continue
        return status, body, meta
    raise RuntimeError(f"transport failure after {tries} tries: {url} :: {last}")

def _log(url, body_out, status, elapsed, t0, body, rh, tag, err=None):
    RAW.mkdir(exist_ok=True)
    sha = hashlib.sha256(body).hexdigest() if body else None
    if body:
        p = RAW / f"{sha}.gz"
        if not p.exists():
            with gzip.open(p, "wb") as f: f.write(body)
    meta = {"t": round(t0, 3), "url": url, "post": body_out.decode()[:2000] if body_out else None, "status": status,
            "elapsed": round(elapsed, 3), "bytes": len(body), "sha256": sha, "tag": tag, "err": err,
            "date_hdr": rh.get("Date"), "cache": rh.get("Cache-Control"), "age": rh.get("Age")}
    with INDEX.open("a") as f: f.write(json.dumps(meta) + "\n")
    return meta

def get_json(url, **kw):
    s, b, m = fetch(url, **kw)
    if s != 200: raise RuntimeError(f"HTTP {s} for {url}: {b[:300]!r}")
    return json.loads(b), m
