"""feat_10: apply the a-priori inclusion rules to the Gamma catalogue. Rules use tags, dates, volume and market shape only.
The outcome is written to a SEPARATE file (derived/labels.jsonl) that no feature code reads.
Every exclusion is counted (derived/universe_counts.json). A tag table is written for inspection of the vocabulary."""
import collections, datetime as dt, json, os

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ETUDE, "data", "universe_events.jsonl")
OUT = os.path.join(ETUDE, "derived")
# Event-level exclusions, by tag (fixed in the plan): outcomes produced in public, continuously or in play.
EXCLUDED_TAGS = {"games", "esports",                                   # match-level sports and e-sports events
                 "crypto-prices", "hit-price", "up-or-down", "multi-strikes",  # public price processes
                 "weather", "tweets-markets", "mention-markets"}       # public counters and meteorology
T_MIN = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp()
T_MAX = dt.datetime(2026, 10, 31, 23, 59, 59, tzinfo=dt.timezone.utc).timestamp()
MARKET_VOLUME_MIN = 10000.0


def ts(s):
    """Gamma timestamps come as '2025-10-10 12:11:22+00' or ISO with Z."""
    if not s: return None
    s = s.strip().replace(" ", "T").replace("Z", "+00:00")
    if s.endswith("+00"): s += ":00"
    return dt.datetime.fromisoformat(s).timestamp()


def main():
    os.makedirs(OUT, exist_ok=True)
    c = collections.Counter(); tags_all = collections.Counter(); tags_kept = collections.Counter()
    seen = set()
    with open(SRC) as f, open(os.path.join(OUT, "universe_markets.jsonl"), "w") as om, open(os.path.join(OUT, "labels.jsonl"), "w") as ol:
        for line in f:
            e = json.loads(line)  # a truncated last line raises: the catalogue must be complete
            c["events_read"] += 1
            tg = set(e.get("tags") or [])
            for t in tg: tags_all[t] += 1
            if tg & EXCLUDED_TAGS:
                c["events_excluded_by_tag"] += 1; c["markets_in_excluded_events"] += e.get("n_markets_not_copied", len(e["markets"])); continue
            c["events_tag_ok"] += 1
            kept_here = 0
            for m in e["markets"]:
                c["markets_seen"] += 1
                cid = m.get("conditionId")
                if not cid: c["m_no_condition"] += 1; continue
                if cid in seen: c["m_duplicate_condition"] += 1; continue
                try:
                    outs = json.loads(m.get("outcomes") or "[]"); toks = json.loads(m.get("clobTokenIds") or "[]")
                    prices = json.loads(m.get("outcomePrices") or "[]")
                except (TypeError, ValueError):
                    c["m_unparsable"] += 1; continue
                if outs != ["Yes", "No"] or len(toks) != 2: c["m_not_yes_no"] += 1; continue
                if float(m.get("volumeNum") or 0) < MARKET_VOLUME_MIN: c["m_volume_below_min"] += 1; continue
                closed = ts(m.get("closedTime"))
                if closed is None: c["m_no_closed_time"] += 1; continue
                if not (T_MIN <= closed <= T_MAX): c["m_closed_outside_period"] += 1; continue
                if prices == ["1", "0"]: win = "YES"
                elif prices == ["0", "1"]: win = "NO"
                else: c["m_not_resolved_to_0_or_1"] += 1; continue
                seen.add(cid); kept_here += 1; c["markets_kept"] += 1
                om.write(json.dumps({"event_id": e["id"], "event_slug": e["slug"], "tags": sorted(tg), "neg_risk": bool(m.get("negRisk")),
                                     "condition_id": cid, "yes_token": toks[0], "no_token": toks[1], "closed_ts": int(closed),
                                     "start_ts": ts(m.get("startDate") or m.get("createdAt")), "volume": float(m["volumeNum"])}) + "\n")
                ol.write(json.dumps({"condition_id": cid, "winner": win}) + "\n")
            if kept_here:
                c["events_with_kept_market"] += 1
                for t in tg: tags_kept[t] += 1
    json.dump(dict(c), open(os.path.join(OUT, "universe_counts.json"), "w"), indent=1)
    json.dump({"all_events": tags_all.most_common(), "kept_events": tags_kept.most_common()}, open(os.path.join(OUT, "tag_table.json"), "w"))
    print(json.dumps(dict(c), indent=1))
    print("top tags among kept events:", tags_kept.most_common(70))


if __name__ == "__main__":
    main()
