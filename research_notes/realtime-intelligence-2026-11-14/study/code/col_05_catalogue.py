"""col_05: market catalogue for the study, slim records only.

Two sources, both event listings of Gamma with an event volume of 50,000 USD or more:
  1. the catalogue of CLOSED events collected on 2026-11-13 for the previous frozen study (read in place, never modified);
  2. a fresh listing of events still OPEN, read now: their already closed markets are absent from source 1, and leaving
     them out would keep a "by date" market only when its whole event has ended, which depends on the outcome.
Nothing is filtered on an outcome here. Raises on any schema surprise; counts are written to data/catalogue_counts.json."""
import hashlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOSED_SRC = "/Volumes/PHI-Data/Projects/Polymarket-early-detection-study-20261113/data/universe_events.jsonl"
OUT = os.path.join(ETUDE, "data", "catalogue.jsonl")
VOLUME_MIN = 50000
EXCLUDED_TAGS = {"games", "esports", "crypto-prices", "hit-price", "up-or-down", "multi-strikes", "weather", "tweets-markets",
                 "mention-markets"}     # same list as the previous study: their markets were not copied in source 1
MK = ("id", "conditionId", "question", "clobTokenIds", "outcomes", "outcomePrices", "volumeNum", "closedTime", "createdAt", "startDate",
      "endDate", "negRisk", "closed", "umaResolutionStatus", "version")
EK = ("id", "slug", "volume", "closedTime", "endDate", "startDate", "createdAt", "negRisk", "closed")


def main():
    c = {"closed_lines": 0, "closed_events": 0, "closed_duplicates": 0, "open_pages": 0, "open_events": 0, "open_also_in_closed": 0,
         "markets_written": 0, "events_excluded_tag": 0}
    seen, h = set(), hashlib.sha256()
    with open(OUT + ".tmp", "w") as out:
        with open(CLOSED_SRC, "rb") as f:
            for raw in f:
                h.update(raw); c["closed_lines"] += 1
                e = json.loads(raw)                     # a truncated line raises: the source must be whole
                if e["id"] in seen:
                    c["closed_duplicates"] += 1; continue
                seen.add(e["id"]); c["closed_events"] += 1
                c["events_excluded_tag"] += bool(set(e.get("tags") or []) & EXCLUDED_TAGS)
                e["markets"] = [{k: m.get(k) for k in MK} for m in e.get("markets") or []]
                e["src"] = "closed_20261113"; e.pop("title", None)
                c["markets_written"] += len(e["markets"]); out.write(json.dumps(e) + "\n")
        c["closed_sha256"] = h.hexdigest()
        cursor, pace = None, net.Pace(0.3)
        while True:
            url = (f"https://gamma-api.polymarket.com/events/keyset?closed=false&limit=100&order=volume&ascending=false&volume_min={VOLUME_MIN}"
                   + (f"&after_cursor={cursor}" if cursor else ""))
            j, _ = net.get(url, timeout=120, pace=pace)
            if not isinstance(j, dict) or not isinstance(j.get("events"), list):
                raise net.SourceError(f"unexpected keyset schema at open page {c['open_pages']}")
            for e in j["events"]:
                if float(e.get("volume") or 0) < VOLUME_MIN or e.get("closed"):
                    raise net.SourceError(f"filter not honoured: event {e.get('id')} volume {e.get('volume')} closed {e.get('closed')}")
                if e["id"] in seen:
                    c["open_also_in_closed"] += 1; continue
                seen.add(e["id"]); c["open_events"] += 1
                rec = {k: e.get(k) for k in EK}
                rec["tags"] = [t.get("slug") for t in (e.get("tags") or [])]
                excluded = bool(set(rec["tags"]) & EXCLUDED_TAGS); c["events_excluded_tag"] += excluded
                rec["markets"] = [] if excluded else [{k: m.get(k) for k in MK} for m in (e.get("markets") or [])]
                rec["src"] = "open_" + time.strftime("%Y%m%d", time.gmtime())
                c["markets_written"] += len(rec["markets"]); out.write(json.dumps(rec) + "\n")
            c["open_pages"] += 1
            nxt = j.get("next_cursor")
            if nxt and nxt == cursor:
                raise net.SourceError("cursor did not advance")
            cursor = nxt
            if not nxt:
                break
    os.replace(OUT + ".tmp", OUT)
    c["requests"] = dict(net.COUNTS); c["read_at"] = int(time.time())
    json.dump(c, open(os.path.join(ETUDE, "data", "catalogue_counts.json"), "w"), indent=1)
    print(json.dumps(c, indent=1))


if __name__ == "__main__":
    main()
