"""Sequential collector (1 network worker) of Polymarket Data API v2 activity rows of type TIP.

The default activity feed omits TIP (docs: "Omitted, the feed returns every type except TIP").
python3 -I collect_tip.py <out_dir> <addresses.txt>
Every raw page is archived with a .meta.json (url, UTC time, sha256, status). Identical filters on every page.
"""
import hashlib, json, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://data-api.polymarket.com/v2/activity?user={u}&type=TIP&start=1&limit=1000&sort_by=TIMESTAMP&sort_direction=ASC"
UA = {"user-agent": "polymarket-forensics-research/1.0"}


def get(url, tries=6):
    delay = 2.0
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(delay); delay *= 2; continue
            return e.code, e.read()
        except Exception:
            time.sleep(delay); delay *= 2
    raise SystemExit(f"failed after {tries} tries: {url}")


def main(out, addrs):
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for a in addrs:
        url, page, rows = BASE.format(u=a), 0, 0
        while True:
            f = out / f"{a}_p{page:03d}.json"
            if f.exists():
                body = f.read_bytes(); status = json.loads(f.with_suffix(".meta.json").read_text())["http_status"]
            else:
                status, body = get(url)
                f.write_bytes(body)
                f.with_suffix(".meta.json").write_text(json.dumps({"url": url, "http_status": status,
                    "fetched_utc": datetime.now(timezone.utc).isoformat(), "sha256": hashlib.sha256(body).hexdigest(),
                    "bytes": len(body)}, indent=1))
                time.sleep(1.5)
            if status != 200:
                summary[a] = {"error": status}; break
            p = json.loads(body)
            rows += len(p["data"])
            nc, more = p["pagination"].get("next_cursor"), p["pagination"].get("has_more")
            if bool(nc) != bool(more):
                raise SystemExit(f"inconsistent pagination envelope for {a} page {page}")
            if not more:
                summary[a] = {"rows": rows, "pages": page + 1}; break
            url, page = BASE.format(u=a) + f"&cursor={nc}", page + 1
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    s = main(Path(sys.argv[1]), [l.strip().lower() for l in open(sys.argv[2]) if l.strip().startswith("0x")])
    print(sum(1 for v in s.values() if v.get("rows")), "of", len(s), "addresses have TIP rows;",
          sum(v.get("rows", 0) for v in s.values()), "rows;", sum(1 for v in s.values() if "error" in v), "errors")
