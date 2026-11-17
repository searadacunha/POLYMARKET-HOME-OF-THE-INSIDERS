"""Keyless read-only HTTP helper for the study. Standard library only.

Every request is indexed in data/<RAW_DIR>/INDEX.jsonl (url, status, elapsed, bytes, sha256), success or failure.
Bodies are archived as gzip files named by their SHA-256 unless archive=False (then only the hash is kept, so a later
re-fetch can still be compared). An HTTP error is never turned into an empty result: get_json raises.
"""
import gzip, hashlib, json, os, pathlib, threading, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent  # study root
RAW = ROOT / "data" / os.environ.get("RAW_DIR", "raw")
INDEX = RAW / "INDEX.jsonl"
UA = "Mozilla/5.0 (compatible; research-client/1.0)"
COUNTS = {"requests": 0, "ok": 0, "http_error": 0, "http_429": 0, "transport_error": 0}
_LOCK = threading.Lock()
RETRY = (429, 500, 502, 503, 504, 529)


def fetch(url, data=None, headers=None, timeout=30, tries=5, pause=0.0, tag="", archive=True):
    """Return (status, body_bytes, meta). HTTP errors are returned, not raised; transport failure raises after `tries`."""
    h = {"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"}
    if headers:
        h.update(headers)
    body_out = None if data is None else (data if isinstance(data, bytes) else json.dumps(data).encode())
    if body_out is not None:
        h.setdefault("Content-Type", "application/json")
    last = None
    for attempt in range(tries):
        if pause:
            time.sleep(pause)
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=body_out, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body, status, rh = r.read(), r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            body, status, rh = (e.read() or b""), e.code, dict(e.headers or {})
        except Exception as e:  # transport failure: logged, retried, finally raised
            last = repr(e)
            _log(url, body_out, None, time.time() - t0, t0, b"", {}, tag, archive, err=last)
            time.sleep(1.5 * (attempt + 1))
            continue
        if rh.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        meta = _log(url, body_out, status, time.time() - t0, t0, body, rh, tag, archive)
        if status in RETRY and attempt < tries - 1:
            ra = rh.get("Retry-After") or ""
            time.sleep(min(float(ra), 30.0) if ra.replace(".", "", 1).isdigit() else 2.0 * (attempt + 1))
            continue
        return status, body, meta
    raise RuntimeError(f"transport failure after {tries} tries: {url} :: {last}")


def _log(url, body_out, status, elapsed, t0, body, rh, tag, archive, err=None):
    sha = hashlib.sha256(body).hexdigest() if body else None
    meta = {"t": round(t0, 3), "url": url, "post": body_out.decode()[:2000] if body_out else None, "status": status,
            "elapsed": round(elapsed, 3), "bytes": len(body), "sha256": sha, "archived": bool(archive and body), "tag": tag,
            "err": err, "date_hdr": rh.get("Date"), "cache": rh.get("Cache-Control")}
    with _LOCK:
        RAW.mkdir(parents=True, exist_ok=True)
        COUNTS["requests"] += 1
        if err:
            COUNTS["transport_error"] += 1
        elif status == 200:
            COUNTS["ok"] += 1
        else:
            COUNTS["http_error"] += 1
            if status == 429:
                COUNTS["http_429"] += 1
        if archive and body:
            p = RAW / f"{sha}.gz"
            if not p.exists():
                with gzip.open(p, "wb") as f:
                    f.write(body)
        with INDEX.open("a") as f:
            f.write(json.dumps(meta) + "\n")
    return meta


def get_json(url, **kw):
    """JSON body of a 200 response; anything else raises (an error is never an empty result)."""
    s, b, m = fetch(url, **kw)
    if s != 200:
        raise RuntimeError(f"HTTP {s} for {url}: {b[:300]!r}")
    return json.loads(b), m
