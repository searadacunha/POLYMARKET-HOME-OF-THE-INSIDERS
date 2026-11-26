"""Bounded public-data collection. Drops profile fields. Not used by the offline tests.

Same-day tapes stop once a page is older than the alert's UTC day, or after
``--page-cap`` pages. An alert that never reaches that day is marked incomplete
and is not used as a control.
"""

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

NOTE = Path(__file__).resolve().parents[1]
REPO = NOTE.parents[1]
TRADES = "https://data-api.polymarket.com/v2/trades?condition={condition}&limit=1000"
ACTIVITY = "https://data-api.polymarket.com/v2/activity"
KEEP_TRADE = ("timestamp", "price", "size", "side", "outcome", "proxy_wallet", "transaction_hash")
KEEP_ACTIVITY = KEEP_TRADE + ("type", "usdc_size", "condition_id", "title")
INCA = (
    "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a",
    "0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a",
    "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2",
    "0xcb18ea2923d957bd9cf049cce60a87638722f867",
    "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44",
)


def get_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "research-client/1.0", "Accept": "application/json"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 503) and attempt < 3:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise
    raise last


def day_start(ts: int) -> int:
    day = datetime.fromtimestamp(ts, timezone.utc).date()
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())


def slim(row: dict, keys) -> dict:
    return {key: row.get(key) for key in keys}


def fetch_alert(alert: dict, page_cap: int, pause: float) -> dict:
    start = day_start(int(alert["t_alert"]))
    cursor = None
    pages = 0
    peers = []
    complete = False
    oldest = None
    while pages < page_cap:
        url = TRADES.format(condition=urllib.parse.quote(alert["condition_id"], safe=""))
        if cursor:
            url += "&cursor=" + urllib.parse.quote(cursor, safe="")
        payload = get_json(url)
        rows = payload.get("data") or []
        pages += 1
        if not rows:
            complete = True
            break
        stamps = [int(row["timestamp"]) for row in rows]
        oldest = min(stamps)
        for row in rows:
            stamp = int(row["timestamp"])
            if not start <= stamp < start + 86400:
                continue
            if str(row.get("side", "")).upper() != "BUY":
                continue
            if str(row.get("outcome", "")).upper() != str(alert["side"]).upper():
                continue
            if str(row.get("proxy_wallet", "")).lower() == alert["initiator"].lower():
                continue
            peers.append(slim(row, KEEP_TRADE))
        pagination = payload.get("pagination") or {}
        if oldest < start or not pagination.get("has_more"):
            complete = True
            break
        cursor = pagination.get("next_cursor")
        if not cursor:
            complete = True
            break
        time.sleep(pause)
    return {
        "condition_id": alert["condition_id"],
        "event_slug": alert["event_slug"],
        "side": alert["side"],
        "t_alert": alert["t_alert"],
        "p_alert": alert["p_alert"],
        "win": alert["win"],
        "initiator": alert["initiator"],
        "day_start": start,
        "pages": pages,
        "oldest_timestamp": oldest,
        "complete": complete,
        "peers": peers,
    }


def alerts():
    path = REPO / "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [row for row in rows if row.get("eval_set") == "VALIDATION" and row.get("lonely_thin")]


def fetch_activity(address: str, page_cap: int, pause: float) -> dict:
    rows = []
    cursor = None
    pages = 0
    complete = False
    while pages < page_cap:
        params = {"user": address, "limit": 500, "sort_by": "TIMESTAMP", "sort_direction": "ASC"}
        if cursor:
            params["cursor"] = cursor
        payload = get_json(ACTIVITY + "?" + urllib.parse.urlencode(params))
        batch = payload.get("data") or []
        pages += 1
        rows.extend(slim(row, KEEP_ACTIVITY) for row in batch)
        pagination = payload.get("pagination") or {}
        if not pagination.get("has_more"):
            complete = True
            break
        cursor = pagination.get("next_cursor")
        if not cursor:
            complete = True
            break
        time.sleep(pause)
    return {"address": address, "pages": pages, "complete": complete, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-cap", type=int, default=12)
    parser.add_argument("--activity-cap", type=int, default=40)
    parser.add_argument("--pause", type=float, default=0.2)
    args = parser.parse_args()
    out_dir = NOTE / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    collected = [fetch_alert(alert, args.page_cap, args.pause) for alert in alerts()]
    (out_dir / "same_cell.json").write_text(json.dumps({"alerts": collected}, separators=(",", ":")) + "\n")
    wallets = [fetch_activity(address, args.activity_cap, args.pause) for address in INCA]
    (out_dir / "inca_activity.json").write_text(json.dumps({"wallets": wallets}, separators=(",", ":")) + "\n")
    done = sum(1 for row in collected if row["complete"])
    print(json.dumps({"alerts": len(collected), "complete": done, "wallets": len(wallets)}))


if __name__ == "__main__":
    main()
