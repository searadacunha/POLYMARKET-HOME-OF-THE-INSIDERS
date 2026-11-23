"""Complete Polymarket v2 activity of a trading account, every type, ascending, all pages. Profile fields are dropped at read time."""
import gzip, json, sys, time
from pathlib import Path
from urllib.parse import urlencode
sys.path.insert(0, str(Path(__file__).parent))
from net import get_json

API = "https://data-api.polymarket.com/v2/activity?"
PRIVATE = {"name", "pseudonym", "bio", "profile_image", "profile_image_optimized", "profileImage", "profileImageOptimized"}


def activity(wallet, limit=500):
    wallet = wallet.lower()
    rows, pages, cursor = [], [], None
    while True:
        q = dict(user=wallet, limit=limit, sort_by="TIMESTAMP", sort_direction="ASC", exclude_deposits_withdrawals="false")
        if cursor:
            q["cursor"] = cursor
        url = API + urlencode(q)
        v = get_json(url)
        pg = v["pagination"]
        data = v["data"]
        for r in data:
            if r["proxy_wallet"].lower() != wallet:
                raise ValueError(f"activity row for another wallet: {r['proxy_wallet']}")
            rows.append({k: x for k, x in r.items() if k not in PRIVATE})
        pages.append({"cursor": cursor, "rows": len(data), "has_more": pg.get("has_more"), "next_cursor": pg.get("next_cursor")})
        if pg.get("has_more") != bool(pg.get("next_cursor")):
            raise ValueError("ambiguous pagination")
        if not pg.get("has_more"):
            break
        if not data:
            raise ValueError("empty page with a continuation")
        cursor = pg["next_cursor"]
        time.sleep(0.3)
    ts = [r["timestamp"] for r in rows]
    if ts != sorted(ts):
        raise ValueError("activity is not ascending")
    return {"wallet": wallet, "endpoint": API + "user=<wallet>&limit=%d&sort_by=TIMESTAMP&sort_direction=ASC&exclude_deposits_withdrawals=false" % limit,
            "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pages": pages, "rows": rows}


if __name__ == "__main__":
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    for w in sys.argv[2:]:
        res = activity(w)
        p = out / f"{w.lower()}.json.gz"
        with gzip.open(p, "wt", encoding="utf-8") as f:
            json.dump(res, f, sort_keys=True, separators=(",", ":"))
        types = {}
        for r in res["rows"]:
            k = r["type"] + ("/" + r["side"] if r.get("side") else "")
            types[k] = types.get(k, 0) + 1
        print(w, len(res["rows"]), "rows", len(res["pages"]), "pages", types)
