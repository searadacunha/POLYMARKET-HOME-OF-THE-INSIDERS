"""Acquire the frozen MLB sample, or check and summarize the committed normalized public records."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlencode

from pilot import get, values

HERE = Path(__file__).resolve().parent
START, END = "2026-09-01T00:00:00Z", "2026-09-08T00:00:00Z"
GAME = re.compile(r"mlb-[a-z0-9]+-[a-z0-9]+-\d{4}-\d{2}-\d{2}(?:-(?:game-)?[12])?$")


def ts(value):
    if not value:
        return None
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return int((d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp())


def collect(output, by_game_start=False):
    lower, upper = (END, "2026-09-15T00:00:00Z") if by_game_start else (START, END)
    receipts, games, events = [], {}, set()
    offset = 0
    while True:
        query = urlencode(dict(tag_slug="mlb", closed="true", end_date_min=lower, end_date_max=upper,
                               order="id", ascending="true", limit=50, offset=offset))
        receipt, page = get("https://gamma-api.polymarket.com/events?" + query)
        if not isinstance(page, list):
            raise RuntimeError(f"catalogue page unavailable at {offset}: {receipt}")
        receipts.append(receipt)
        for event in page:
            if event["id"] in events:
                raise ValueError("duplicate event across catalogue pages")
            events.add(event["id"])
            if not (ts(lower) <= ts(event["endDate"]) < ts(upper) and GAME.fullmatch(event["slug"])
                    and "mlb" in {r.get("slug") for r in event.get("tags", [])}):
                continue
            for m in event.get("markets", []):
                sides = values(m.get("outcomes"))
                if m.get("sportsMarketType") != "moneyline" or len(sides) != 2 or any(s.lower() in {"yes", "no"} for s in sides):
                    continue
                token_ids = values(m.get("positionIds") if m.get("version") == "v2" else m.get("clobTokenIds"))
                prices = values(m.get("outcomePrices"))
                cid = m["conditionId"]
                row = {"event": event["id"], "slug": event["slug"], "condition": cid, "end": event["endDate"],
                       "game_start": m.get("gameStartTime"), "created": m.get("createdAt"), "closed": m.get("closedTime"),
                       "first_team": sides[0], "token": str(token_ids[0]) if len(token_ids) == 2 else None,
                       "payout_first": int(float(prices[0])) if m.get("closed") and sorted(map(float, prices)) == [0, 1] else None}
                if cid in games and row != games[cid]:
                    raise ValueError("conflicting facts for the same condition")
                games[cid] = row
        if len(page) < 50:
            break
        offset += len(page)
    before_filter = len(games)
    if by_game_start:
        games = {cid: r for cid, r in games.items() if r["game_start"] and ts(START) <= ts(r["game_start"]) < ts(END)}
    for row in games.values():
        target = ts(row["game_start"] or row["end"]) - 7 * 86400
        if row["token"] and row["created"] and ts(row["created"]) <= target and (not row["closed"] or ts(row["closed"]) > target):
            q = urlencode(dict(market=row["token"], startTs=target-600, endTs=target, fidelity=1))
            receipt, chart = get("https://clob.polymarket.com/prices-history?" + q)
            row["history_request"] = receipt
            row["points"] = chart.get("history") if isinstance(chart, dict) else None
    data = {"catalogue": receipts, "event_records": len(events), "games": list(games.values())}
    if by_game_start:
        data.update(game_start_filter=[START, END], moneylines_before_game_start_filter=before_filter)
    with output.open("x") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return data


def summarize(data):
    counts = Counter()
    seen = set()
    for row in data["games"]:
        cid = row["condition"]
        if cid in seen:
            raise ValueError("duplicate condition")
        seen.add(cid)
        counts["moneylines"] += 1
        start = ts(row["game_start"] or row["end"])
        target = start - 7 * 86400
        counts["missing_game_start_fallback"] += int(not row["game_start"])
        counts["game_start_outside_event_end_window"] += int(not ts(START) <= start < ts(END))
        if not row["created"] or not row["token"]:
            counts["missing_metadata"] += 1
        elif ts(row["created"]) > target:
            counts["listed_after_target"] += 1
        elif row["closed"] and ts(row["closed"]) <= target:
            counts["closed_before_target"] += 1
        elif row["points"] is None:
            counts["history_error"] += 1
        else:
            points = [(int(p["t"]), float(p["p"])) for p in row["points"] if target-600 <= int(p["t"]) <= target]
            if not points:
                counts["history_empty"] += 1
                continue
            latest = max(t for t, _ in points)
            values_at_time = {v for t, v in points if t == latest}
            if len(values_at_time) != 1:
                counts["price_conflict"] += 1
                continue
            price = values_at_time.pop()
            if not 0 <= price <= 1:
                raise ValueError("invalid probability")
            counts["priced"] += 1
            if 0.55 <= price < 0.60:
                counts["bucket"] += 1
                if row["payout_first"] is not None:
                    counts["bucket_settled"] += 1
                    counts["bucket_wins"] += row["payout_first"]
    counts["end_minus_start_exactly_7d"] = sum(ts(r["end"]) - ts(r["game_start"]) == 604800 for r in data["games"] if r["game_start"])
    return {"catalogue_pages": len(data["catalogue"]), "catalogue_events": data["event_records"], **dict(counts)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collect", type=Path, help="fetch the fixed window into a new file")
    ap.add_argument("--game-start", action="store_true", help="use the registered follow-up game-date window")
    args = ap.parse_args()
    filename = "sports_game_start.json" if args.game_start else "sports.json"
    data = collect(args.collect, args.game_start) if args.collect else json.loads((HERE / filename).read_text())
    print(json.dumps(summarize(data), sort_keys=True))
