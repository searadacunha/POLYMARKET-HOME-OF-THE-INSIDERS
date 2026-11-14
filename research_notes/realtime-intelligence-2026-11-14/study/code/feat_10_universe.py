"""feat_10: apply the a-priori inclusion rules to the catalogue. Rules use tags, the SCHEDULED end date, volume and market
shape only. The outcome and the real closing time go to a SEPARATE file (derived/labels.jsonl) that no feature code reads.
Every exclusion is counted (derived/universe_counts.json)."""
import collections, datetime as dt, json, os

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ETUDE, "data", "catalogue.jsonl")
CASES = os.path.join(ETUDE, "data", "documented_cases_20261113.json")
OUT = os.path.join(ETUDE, "derived")
EXCLUDED_TAGS = {"games", "esports", "crypto-prices", "hit-price", "up-or-down", "multi-strikes", "weather", "tweets-markets",
                 "mention-markets"}       # outcomes produced in public view, continuously or in play (same list as the previous study)
# Markets kept but analysed apart, as a negative-control family: the outcome is a public process (season-long sports,
# listed prices, public counters). Fixed from the tag vocabulary alone.
PUBLIC_PROCESS_TAGS = {"sports", "soccer", "nfl", "nba", "basketball", "golf", "tennis", "formula1", "f1", "football", "hockey",
                       "olympics", "fifa-world-cup", "2026-fifa-world-cup", "world-cup", "pga", "pga-tour", "baseball", "mlb", "nhl",
                       "ufc", "boxing", "cricket", "chess", "equities", "stocks", "commodities", "pre-market", "monthly-hit",
                       "youtube", "mrbeast", "box-office"}
T_MIN = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp()
T_MAX = dt.datetime(2026, 10, 31, 23, 59, 59, tzinfo=dt.timezone.utc).timestamp()       # scheduled end date of the market
T_SPLIT = dt.datetime(2026, 3, 31, 23, 59, 59, tzinfo=dt.timezone.utc).timestamp()      # events ending later are VALIDATION
MARKET_VOLUME_MIN = 10000.0


def ts(s):
    """Gamma timestamps come as '2025-10-10 12:11:22+00' or ISO with Z."""
    if not s:
        return None
    s = s.strip().replace(" ", "T").replace("Z", "+00:00")
    if s.endswith("+00"):
        s += ":00"
    return dt.datetime.fromisoformat(s).timestamp()


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = json.load(open(CASES))
    case_slugs, case_conditions = set(cases["event_slugs"]), set(cases["condition_ids"])
    c = collections.Counter(); seen = set(); events = {}
    with open(SRC) as f, open(os.path.join(OUT, "universe_markets.jsonl"), "w") as om, open(os.path.join(OUT, "labels.jsonl"), "w") as ol, \
            open(os.path.join(OUT, "universe_unresolved.jsonl"), "w") as ou:
        for line in f:
            e = json.loads(line)
            c["events_read"] += 1
            tg = set(e.get("tags") or [])
            if tg & EXCLUDED_TAGS:
                c["events_excluded_by_tag"] += 1; continue
            group = "PUBLIC_PROCESS" if tg & PUBLIC_PROCESS_TAGS else "INFO"
            for m in e["markets"]:
                c["markets_seen"] += 1
                cid = m.get("conditionId")
                if not cid:
                    c["m_no_condition"] += 1; continue
                if cid in seen:
                    c["m_duplicate_condition"] += 1; continue
                try:
                    outs = json.loads(m.get("outcomes") or "[]"); toks = json.loads(m.get("clobTokenIds") or "[]")
                    prices = json.loads(m.get("outcomePrices") or "[]")
                except (TypeError, ValueError):
                    c["m_unparsable"] += 1; continue
                if outs != ["Yes", "No"] or len(toks) != 2:
                    c["m_not_yes_no"] += 1; continue
                if float(m.get("volumeNum") or 0) < MARKET_VOLUME_MIN:
                    c["m_volume_below_min"] += 1; continue
                end = ts(m.get("endDate"))
                if end is None:
                    c["m_no_end_date"] += 1; continue
                if not (T_MIN <= end <= T_MAX):
                    c["m_end_outside_period"] += 1; continue
                seen.add(cid); c["markets_in_period"] += 1
                # the last scheduled end of an event is taken over its markets in the period whatever their resolution, so that the
                # split does not depend on which markets have resolved; the documented cases are those listed, nothing else
                ev = events.setdefault(e["id"], {"slug": e["slug"], "end": 0, "group": group, "n": 0, "case": False})
                ev["end"] = max(ev["end"], int(end))
                ev["case"] = ev["case"] or e["slug"] in case_slugs or cid in case_conditions
                rec = {"event_id": e["id"], "event_slug": e["slug"], "tags": sorted(tg), "group": group, "neg_risk": bool(m.get("negRisk")),
                       "condition_id": cid, "yes_token": toks[0], "no_token": toks[1], "end_ts": int(end),
                       "start_ts": ts(m.get("startDate") or m.get("createdAt")), "volume": float(m["volumeNum"]), "src": e["src"]}
                closed = ts(m.get("closedTime")) if m.get("closed") else None
                win = "YES" if prices == ["1", "0"] else "NO" if prices == ["0", "1"] else None
                if closed is None or win is None:            # still open, or resolved otherwise: counted, never scored
                    c["m_unresolved_or_not_0_1"] += 1; ou.write(json.dumps(dict(rec, closed=bool(m.get("closed")))) + "\n"); continue
                c["markets_kept"] += 1; c["markets_kept_" + group] += 1
                om.write(json.dumps(rec) + "\n")
                ol.write(json.dumps({"condition_id": cid, "winner": win, "closed_ts": int(closed)}) + "\n")
                ev["n"] += 1
    sets = {}
    for eid, ev in events.items():
        if ev["n"] == 0:                                   # no market of the event is scored
            continue
        s = "DISCOVERY" if (ev["case"] or ev["end"] <= T_SPLIT) else "VALIDATION"
        sets[eid] = {"set": s, "documented_case": ev["case"], "slug": ev["slug"], "group": ev["group"], "markets": ev["n"]}
        c[f"events_{s}"] += 1; c[f"markets_{s}"] += ev["n"]; c[f"events_{s}_{ev['group']}"] += 1
        c["events_documented_case"] += ev["case"]
    json.dump(sets, open(os.path.join(OUT, "sets.json"), "w"))
    json.dump(dict(c), open(os.path.join(OUT, "universe_counts.json"), "w"), indent=1)
    print(json.dumps(dict(c), indent=1))


if __name__ == "__main__":
    main()
