"""Collect a small, read-only tennis price-history pilot into a new file."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def get(url):
    start = time.time()
    try:
        with urlopen(Request(url, headers={"User-Agent": "Polymarket-public-research/1"}), timeout=15) as response:
            body = response.read()
            stamp = time.time()
            return {"url": url, "request": start, "response": stamp, "status": response.status,
                    "sha256": hashlib.sha256(body).hexdigest()}, json.loads(body)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return {"url": url, "request": start, "response": time.time(), "error": str(exc)}, None


def values(field):
    return json.loads(field) if isinstance(field, str) else field or []


def select():
    pages = []
    for offset in range(0, 1000, 5):
        query = urlencode({"closed": "false", "active": "true", "tag_slug": "tennis", "limit": 5, "offset": offset})
        receipt, events = get("https://gamma-api.polymarket.com/events?" + query)
        pages.append(receipt)
        if not events:
            break
        for event in events:
            if "tennis" not in {t.get("slug") for t in event.get("tags", [])}:
                continue
            for m in event["markets"]:
                ids = values(m.get("positionIds") if m.get("version") == "v2" else m.get("clobTokenIds"))
                outcomes = values(m.get("outcomes"))
                if (m.get("active") and m.get("acceptingOrders") and not m.get("closed")
                        and m.get("bestAsk") is not None and m.get("bestBid") is not None
                        and len(ids) == len(outcomes) == 2):
                    return pages, {"condition": m["conditionId"], "token": str(ids[0]), "outcome": outcomes[0],
                                   "question": m["question"], "event": event["slug"]}
    return pages, None


def collect(path):
    pages, market = select()
    report = {"catalogue_requests": pages, "market": market, "observations": []}
    with path.open("x", encoding="utf-8") as out:
        json.dump(report, out, indent=2)
    if market:
        for i in range(3):
            if i:
                time.sleep(30)
            cutoff = int(time.time())
            q = urlencode({"token_id": market["token"], "as_of": cutoff})
            r, data = get("https://data-api.polymarket.com/v2/prices-history?" + q)
            r["as_of"] = cutoff
            r["points"] = data.get("data") if isinstance(data, dict) else None
            report["observations"].append(r)
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            temp.replace(path)
            print(datetime.now(timezone.utc).isoformat(), r.get("status", r.get("error")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    collect(parser.parse_args().output)
