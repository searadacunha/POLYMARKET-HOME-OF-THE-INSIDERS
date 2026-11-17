"""Offline consistency checks of this exported TriAgent campaign registry. No network. Exit code 1 on any failure.

A  every lead id is "L-" + the first 10 hex digits of the SHA-256 of its dedup key, and ids and keys are unique
B  an X lead's key, URL and post id agree; when the supervisor re-read the post, its author matches the URL
C  every lead that is closed, a duplicate, deferred or unresolved carries its reason
D  every "duplicate of L-..." points to a lead or a known case listed here
E  each search's count of new leads equals the leads it registered first (source_job)
"""
import csv
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POST = re.compile(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status(?:es)?/(\d{5,25})")
FAILS = []


def rows(name):
    with open(HERE / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    leads, known, searches = rows("LEADS.csv"), rows("KNOWN_CASES.csv"), rows("SEARCHES.csv")
    ids = [r["id"] for r in leads + known]
    keys = [r["dedup_key"] for r in leads + known]
    if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
        FAILS.append("A: duplicate id or dedup key")
    for r in leads + known:
        if r["id"] != "L-" + hashlib.sha256(r["dedup_key"].encode()).hexdigest()[:10]:
            FAILS.append(f"A: {r['id']} does not derive from {r['dedup_key'][:60]}")
    for r in leads:
        if r["dedup_key"].startswith("x:"):
            m = POST.search(r["post_url"])
            if not m or m.group(2) != r["dedup_key"][2:]:
                FAILS.append(f"B: {r['id']} key and URL disagree")
            elif r["post_reread"] == "yes" and r["post_author"].lower() != m.group(1).lower():
                FAILS.append(f"B: {r['id']} re-read author differs from the URL")
        if r["state"] in ("closed", "duplicate", "deferred", "unresolved") and not r["closure_reason"].strip():
            FAILS.append(f"C: {r['id']} {r['state']} without a reason")
        m = re.match(r"duplicate of (L-[0-9a-f]{10})", r["closure_reason"])
        if r["state"] == "duplicate" and m and m.group(1) not in ids:
            FAILS.append(f"D: {r['id']} points to unknown {m.group(1)}")
    for s in searches:
        first = sum(r["source_job"] == s["job_id"] for r in leads)
        if s["new_leads"] and int(s["new_leads"]) != first:
            FAILS.append(f"E: search {s['cell']} says {s['new_leads']} new leads, {first} found")
    print(f"leads {len(leads)}, known cases {len(known)}, searches {len(searches)}: {len(FAILS)} failure(s)")
    for line in FAILS:
        print("FAIL", line)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
