"""Titles and dates of the events where the strict C4 fires, from the public Gamma API, for the report's table.

    python3 -I -B event_titles.py STRICT_SUMMARY_JSON OUT_JSON"""
import hashlib, json, sys, time, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; research-client/1.0)", "Accept": "application/json"}


def main(summary, out):
    ids = sorted(json.load(open(summary))["c4_events_strict"])
    res = {}
    for i in ids:
        with urllib.request.urlopen(urllib.request.Request(f"https://gamma-api.polymarket.com/events/{i}", headers=UA), timeout=30) as r:
            body = r.read()
        j = json.loads(body)
        res[i] = {"title": (j.get("title") or "").strip(), "start": (j.get("startDate") or "")[:10], "end": (j.get("endDate") or "")[:10],
                  "response_sha256": hashlib.sha256(body).hexdigest(), "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(res, open(out, "w"), indent=1, sort_keys=True)
    print(json.dumps({k: v["title"] for k, v in res.items()}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
