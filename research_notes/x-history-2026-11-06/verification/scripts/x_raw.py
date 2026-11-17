"""Archive the full public embed object of X posts by ID (same endpoint and user agent as agent-reach `tweet`).

Saves raw bytes plus a meta file with sha256 and fetch time. Proves the text, entities and edit_control the
embed endpoint returns today; it does not prove authorship of a wallet or the absence of later deletions.
Usage: python3 -I x_raw.py OUTDIR ID...
"""
import hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests

UA = "research-script/0.1 (agent-reach; local user)"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for tid in sys.argv[2:]:
    r = requests.get("https://cdn.syndication.twimg.com/tweet-result", params={"id": tid, "token": "a"},
                     headers={"User-Agent": UA}, timeout=30)
    body = r.content
    (out / f"{tid}.json").write_bytes(body)
    (out / f"{tid}.meta.json").write_text(json.dumps({
        "url": f"https://cdn.syndication.twimg.com/tweet-result?id={tid}&token=a", "http_status": r.status_code,
        "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
        "fetched_utc": datetime.now(timezone.utc).isoformat()}, indent=1))
    if r.status_code != 200 or not body.strip().startswith(b"{"):
        print(tid, "HTTP", r.status_code, file=sys.stderr); continue
    t = r.json()
    print(tid, t.get("__typename"), (t.get("user") or {}).get("screen_name"), t.get("created_at"),
          "edit:", json.dumps(t.get("edit_control")), "reply_to:", t.get("in_reply_to_status_id_str"))
    time.sleep(2)
