"""Resume PR #110's Ethereum-to-Polygon Relay history screen on GET /requests/v2 before its sunset.

PR #110 queried 241 Ethereum payees; 222 histories stopped on HTTP 429 (snapshot/bridge.json.gz at
8b63304). This collector re-reads those histories one call at a time with the same query
(user, originChainId=1, destinationChainId=137, limit=50, continuation) and no page cap.

Every HTTP exchange is appended to pages.jsonl (status, Retry-After, receipt time, body SHA-256 and
body), so a run resumes where it stopped and a rate-limited history is never read as an empty one.
Classification of the recorded pages is offline (relay_screen.py).
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.relay.link/requests/v2"
SUNSET = 1795478400  # 2026-11-24T00:00:00Z, the endpoint's own Sunset header
PR110 = "8b633048290e7174945bc811b16cf0b11b4d8ceb"
BRIDGE = "investigations/weekly-funding-intelligence/snapshot/bridge.json.gz"
TRADERS = "investigations/changenow-polymarket/sources/state/pm_traders.csv"
TRADES = "investigations/ballon-dor-census/sources/TRADES.csv"
PAGE_SAFETY_CAP = 100
UA = "research-client/1.0"


def utc(ts=None):
    return datetime.fromtimestamp(time.time() if ts is None else ts, timezone.utc).isoformat()


def git_bytes(repo, rev, path):
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{rev}:{path}"], check=True, capture_output=True
    ).stdout


def plan(repo):
    """Accounts of PR #110's screen: unfinished first, known trading endpoints before samples."""
    raw = git_bytes(repo, PR110, BRIDGE)
    accounts = json.loads(gzip.decompress(raw))["accounts"]
    members = set()
    for path, col in ((TRADERS, "account"), (TRADES, "wallet")):
        for r in csv.DictReader(io.StringIO(git_bytes(repo, PR110, path).decode())):
            members.add(r[col].lower())
    rank = lambda a: (accounts[a]["status"] == "EXHAUSTED", a not in members, a)
    order = sorted(accounts, key=rank)
    return dict(
        source=f"{PR110}:{BRIDGE}",
        source_sha256=hashlib.sha256(raw).hexdigest(),
        rule="PR110 status!=EXHAUSTED first; then pm_traders.csv/TRADES.csv members; then address",
        prior_status={a: accounts[a]["status"] for a in order},
        member={a: a in members for a in order},
        order=order,
    )


def state(log):
    """Per address: next continuation, or a terminal state recorded in the log."""
    out = {}
    if not log.exists():
        return out
    for line in log.open():
        r = json.loads(line)
        a = r["address"]
        s = out.setdefault(a, {"cursor": None, "pages": 0, "done": None, "cursors": []})
        if r["http_status"] != 200 or not isinstance(r.get("body"), dict):
            continue
        s["pages"] += 1
        nxt = r["body"].get("continuation")
        if not nxt:
            s["done"] = "EXHAUSTED"
        elif nxt in s["cursors"]:
            s["done"] = "STALLED_CURSOR"
        elif s["pages"] >= PAGE_SAFETY_CAP:
            s["done"] = "PAGE_CAP"
        else:
            s["cursors"].append(nxt)
            s["cursor"] = nxt
    return out


def fetch(address, cursor, timeout=20):
    q = {"user": address, "originChainId": 1, "destinationChainId": 137, "limit": 50}
    if cursor:
        q["continuation"] = cursor
    url = API + "?" + urllib.parse.urlencode(q)
    t0 = time.time()
    rec = dict(address=address, cursor=cursor, url=url, sent_utc=utc(t0))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, headers, body = resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as e:
        status, headers, body = e.code, e.headers, e.read()
    except Exception as e:  # network failure is recorded, never treated as an empty history
        rec.update(http_status=None, error=f"{type(e).__name__}: {e}"[:300], received_utc=utc())
        return rec
    rec.update(
        http_status=status,
        retry_after=headers.get("Retry-After"),
        sunset=headers.get("Sunset"),
        received_utc=utc(),
        elapsed_s=round(time.time() - t0, 3),
        body_sha256=hashlib.sha256(body).hexdigest(),
    )
    try:
        rec["body"] = json.loads(body)
    except ValueError:
        rec["body_text"] = body[:2000].decode("utf-8", "replace")
    return rec


def run(repo, out, interval, stop_at, lo=15.0, hi=600.0):
    out.mkdir(parents=True, exist_ok=True)
    p = plan(repo)
    (out / "plan.json").write_text(json.dumps(p, indent=1) + "\n")
    log, runlog = out / "pages.jsonl", (out / "run.log").open("a")
    say = lambda m: (runlog.write(f"{utc()} {m}\n"), runlog.flush())
    st = state(log)
    ok_streak, fails = 0, {}
    say(f"start interval={interval:.0f}s accounts={len(p['order'])}")
    while True:
        todo = [a for a in p["order"] if not st.get(a, {}).get("done") and fails.get(a, 0) < 6]
        if not todo:
            say("no account left")
            break
        if time.time() + interval > stop_at or (out / "STOP").exists():
            say(f"stop before sunset or on STOP; {len(todo)} accounts unfinished")
            break
        a = todo[0]
        s = st.setdefault(a, {"cursor": None, "pages": 0, "done": None, "cursors": []})
        rec = fetch(a, s["cursor"])
        with log.open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        code = rec["http_status"]
        if code == 200 and isinstance(rec.get("body"), dict):
            st = state(log)
            ok_streak += 1
            fails.pop(a, None)
            if ok_streak >= 3:
                interval = max(lo, interval * 0.85)
            wait = interval
        else:
            ok_streak = 0
            fails[a] = fails.get(a, 0) + (0 if code == 429 else 1)
            interval = min(hi, interval * 1.5)
            ra = rec.get("retry_after")
            wait = max(interval, float(ra) if ra and str(ra).isdigit() else 0.0)
        done = sum(1 for x in p["order"] if st.get(x, {}).get("done"))
        say(f"{a} cursor={'y' if s['cursor'] else 'n'} http={code} done={done} next_wait={wait:.0f}s")
        time.sleep(wait)
    runlog.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True, help="clone holding PR #110's Git objects")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--interval", type=float, default=60.0)
    ap.add_argument("--stop-at", type=float, default=SUNSET - 60)
    ap.add_argument("--min-interval", type=float, default=15.0)
    ap.add_argument("--max-interval", type=float, default=600.0, help="backoff ceiling after HTTP 429")
    ap.add_argument("--plan-only", action="store_true")
    a = ap.parse_args()
    if a.plan_only:
        p = plan(a.repo)
        print(len(p["order"]), sum(p["member"].values()), p["source_sha256"][:16])
        print(sum(1 for x in p["order"] if p["prior_status"][x] != "EXHAUSTED"), "unfinished")
    else:
        run(a.repo, a.out, a.interval, a.stop_at, a.min_interval, a.max_interval)
