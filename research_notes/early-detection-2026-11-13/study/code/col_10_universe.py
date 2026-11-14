"""col_10: catalogue of closed Polymarket events (Gamma keyset), slim records only.
Raises on any HTTP error or schema surprise; counts requested / received pages and rows. No outcome-based filtering here."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ETUDE, "data", "universe_events.jsonl")
STATE = os.path.join(ETUDE, "data", "universe_state.json")
VOLUME_MIN = 50000  # event-level volume floor (USD), fixed before any outcome is read
MK = ("id", "conditionId", "question", "groupItemTitle", "clobTokenIds", "outcomes", "outcomePrices", "volumeNum", "closedTime",
      "umaEndDate", "createdAt", "startDate", "endDate", "negRisk", "closed", "umaResolutionStatus", "feesEnabled")
EXCLUDED_TAGS = {"games", "esports", "crypto-prices", "hit-price", "up-or-down", "multi-strikes", "weather", "tweets-markets",
                 "mention-markets"}  # same list as feat_10_universe.py and the plan
EK = ("id", "slug", "title", "volume", "closedTime", "endDate", "startDate", "createdAt", "negRisk", "closed")

def main():
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"cursor": None, "pages": 0, "events": 0, "markets": 0, "complete": False}
    if st["complete"]:
        print("already complete", st); return
    mode = "a" if st["pages"] else "w"
    with open(OUT, mode) as out:
        while True:
            url = (f"https://gamma-api.polymarket.com/events/keyset?closed=true&limit=100&order=volume&ascending=false&volume_min={VOLUME_MIN}"
                   + (f"&after_cursor={st['cursor']}" if st["cursor"] else ""))
            j, m = net.get_json(url, tag="universe", timeout=120, pause=0.2)
            if not isinstance(j, dict) or not isinstance(j.get("events"), list):
                raise RuntimeError(f"unexpected keyset schema at page {st['pages']}")
            for e in j["events"]:
                if float(e.get("volume") or 0) < VOLUME_MIN:
                    raise RuntimeError(f"volume_min not honoured: event {e.get('id')} volume {e.get('volume')}")
                rec = {k: e.get(k) for k in EK}
                rec["tags"] = [t.get("slug") for t in (e.get("tags") or [])]
                # markets of events excluded by tag are not copied (their count is kept; the raw page is archived anyway)
                if set(rec["tags"]) & EXCLUDED_TAGS:
                    rec["markets"] = []; rec["n_markets_not_copied"] = len(e.get("markets") or [])
                else:
                    rec["markets"] = [{k: mk.get(k) for k in MK} for mk in (e.get("markets") or [])]
                out.write(json.dumps(rec) + "\n")
                st["events"] += 1; st["markets"] += len(e.get("markets") or [])
            out.flush()
            st["pages"] += 1
            nxt = j.get("next_cursor")
            if nxt and nxt == st["cursor"]: raise RuntimeError("cursor did not advance")
            st["cursor"] = nxt
            if not nxt: st["complete"] = True
            json.dump(st, open(STATE, "w"))
            if st["pages"] % 10 == 0: print(time.strftime("%H:%M:%S"), st["pages"], "pages", st["events"], "events", st["markets"], "markets", net.COUNTS, flush=True)
            if st["complete"]: break
    print("DONE", st, net.COUNTS)

if __name__ == "__main__":
    main()
