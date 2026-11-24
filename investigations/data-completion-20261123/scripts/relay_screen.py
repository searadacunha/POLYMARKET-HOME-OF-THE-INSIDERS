"""Offline: classify the Relay v2 history pages recorded by relay_v2_history.py, account by account.

Status of each of PR #110's 241 Ethereum recipients:
  EXHAUSTED            every page answered HTTP 200 and the last one carries no continuation (complete history)
  PARTIAL_RATE_LIMITED at least one request, but the history stops on HTTP 429 or an error before its last page
  NOT_REACHED          no request was sent before the endpoint's sunset (2026-11-24T00:00:00Z)
  STALLED_CURSOR / PAGE_CAP   the API repeated a continuation, or the safety cap of 100 pages was reached
A history that is not EXHAUSTED is never counted as an empty one.
"""

import argparse
import csv
import io
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


SCREEN_FROM = "2026-09-21T00:00:00Z"   # PR 110's screened weeks 2026-W39 .. W46 (bridge.json from_week, cutoff)
SCREEN_TO = "2026-11-16T00:00:00Z"


def in_screen(created):
    if not created:
        return False
    t = datetime.fromisoformat(created.replace("Z", "+00:00"))
    return datetime.fromisoformat(SCREEN_FROM.replace("Z", "+00:00")) <= t < datetime.fromisoformat(
        SCREEN_TO.replace("Z", "+00:00"))


def orders(plan, pages):
    """Every Relay request found in a counted page, with its legs, and whether it falls in PR 110's screened weeks."""
    out, seen = [], set()
    for r in pages:
        b = r.get("body")
        if r.get("http_status") != 200 or not isinstance(b, dict) or not isinstance(b.get("requests"), list):
            continue
        for q in b["requests"]:
            if q.get("id") in seen:
                continue
            seen.add(q.get("id"))
            d = q.get("data") or {}
            ins, outs = d.get("inTxs") or [], d.get("outTxs") or []
            created = q.get("createdAt") or ""
            out.append({"screened_address": r["address"], "request_id": q.get("id"), "status": q.get("status"),
                        "user": (q.get("user") or "").lower(), "recipient": (q.get("recipient") or "").lower(),
                        "origin_chain": ins[0].get("chainId") if ins else "", "origin_tx": ins[0].get("hash") if ins else "",
                        "destination_chain": outs[0].get("chainId") if outs else "",
                        "destination_tx": outs[0].get("hash") if outs else "", "created_utc": created,
                        "in_pr110_screened_weeks": in_screen(created)})
    return out


def classify(plan, pages):
    by = {}
    for r in pages:
        by.setdefault(r["address"], []).append(r)
    rows = []
    for a in plan["order"]:
        rs = by.get(a, [])
        ok = [r for r in rs if r.get("http_status") == 200 and isinstance(r.get("body"), dict)
              and isinstance(r["body"].get("requests"), list)]
        status, cursors, requests = None, [], []
        for r in ok:
            requests += r["body"]["requests"]
            nxt = r["body"].get("continuation")
            if not nxt:
                status = "EXHAUSTED"
            elif nxt in cursors:
                status = "STALLED_CURSOR"
            elif len(cursors) + 1 >= 100:
                status = "PAGE_CAP"
            else:
                cursors.append(nxt)
                status = None
        if status is None:
            if rs:
                status = "PARTIAL_RATE_LIMITED"
            elif plan["prior_status"][a] == "EXHAUSTED":
                status = "EXHAUSTED_IN_PR110_NOT_REREAD"   # PR 110 already read it to the end
            else:
                status = "NOT_REACHED"
        codes = Counter(str(r.get("http_status")) for r in rs)
        rows.append({
            "address": a, "pr110_status": plan["prior_status"][a], "status": status, "pages_200": len(ok),
            "http_429": codes.get("429", 0), "other_failures": sum(n for c, n in codes.items() if c not in ("200", "429")),
            "requests_found": len(requests),
            "requests_to_polygon": sum(1 for q in requests
                                       if any(str(t.get("chainId")) == "137" for t in (q.get("data") or {}).get("outTxs") or [])),
            "first_sent_utc": rs[0]["sent_utc"] if rs else "", "last_received_utc": rs[-1].get("received_utc", "") if rs else "",
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, required=True, help="relay_v2 directory (plan.json, pages.jsonl)")
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    plan = json.loads((a.raw / "plan.json").read_text())
    pages = [json.loads(line) for line in (a.raw / "pages.jsonl").read_text().splitlines() if line.strip()]
    rows = classify(plan, pages)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    a.results.mkdir(parents=True, exist_ok=True)
    (a.results / "relay_v2_screen.csv").write_text(buf.getvalue())
    found = orders(plan, pages)
    buf = io.StringIO()
    fields = ["screened_address", "request_id", "status", "user", "recipient", "origin_chain", "origin_tx",
              "destination_chain", "destination_tx", "created_utc", "in_pr110_screened_weeks"]
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(found)
    (a.results / "relay_v2_orders.csv").write_text(buf.getvalue())
    st = Counter(r["status"] for r in rows)
    before = Counter(plan["prior_status"].values())
    summary = {
        "source": plan["source"], "source_sha256": plan["source_sha256"], "accounts": len(rows),
        "pr110_status": dict(before), "status_now": dict(st),
        "requests_found_in_exhausted_histories": sum(r["requests_found"] for r in rows if r["status"] == "EXHAUSTED"),
        "transitions": dict(Counter(f"{r['pr110_status']}->{r['status']}" for r in rows)),
        "snapshot_note": "this file classifies all http_calls exchanges of the append-only page log, the last one at "
                         "last_call_utc; a history without a request in the log stays unknown, never empty",
        "requests_found_total": sum(r["requests_found"] for r in rows),
        "http_calls": len(pages), "http_429": sum(r["http_429"] for r in rows),
        "orders_found": len(orders(plan, pages)),
        "orders_in_pr110_screened_weeks": sum(o["in_pr110_screened_weeks"] for o in orders(plan, pages)),
        "accounts_with_orders": len({o["screened_address"] for o in orders(plan, pages)}),
        "first_call_utc": min((p["sent_utc"] for p in pages), default=""),
        "last_call_utc": max((p.get("received_utc", "") for p in pages), default=""),
        "reading": "EXHAUSTED histories are complete for originChainId=1 to destinationChainId=137; histories PR 110 "
                   "had exhausted and that were not re-read keep that status; every other status is an unknown, not a "
                   "zero",
    }
    ctl = a.raw / "control.json"
    if ctl.exists():  # the same endpoint and parameters must return a known order (PR 109 route R0, second leg)
        c = json.loads(ctl.read_text())
        summary["positive_control"] = {k: c.get(k) for k in ("url", "expected_order_id", "http_status", "requests",
                                                              "found", "received_utc", "body_sha256")}
    (a.results / "relay_v2_screen.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
