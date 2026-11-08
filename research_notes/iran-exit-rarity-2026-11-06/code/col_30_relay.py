"""Exit data: every Relay request of each population wallet. Network, one worker, 13 s per request.

python3 -I -B code/col_30_relay.py            # comparator populations, in the order fixed by the plan
python3 -I -B code/col_30_relay.py reference  # reference wallets from PR 27's archived pages, offline

Comparators: raw pages to RAW/relay/, reduced files to data/relay/<wallet>.json (requests whose user is the
wallet, reduced by common.flat, page hashes, request counters, termination). Reference: data/relay_reference/,
from the pages PR 27 committed, each checked against that note's SHA256SUMS.txt and DONE counts. The two
folders never overwrite each other. Resumable: a wallet already at END is skipped.

Every page must hold a list of requests, and an empty page may not carry a continuation (common.relay_page).
Every 50 wallets a sentinel re-reads a reference wallet whose single archived page is known; if the ids
archived on 5 November are not all returned, the endpoint is degraded and the run stops. The run also stops
after 22 November 2026 23:59 UTC (plan, stopping rule).
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (DATA, ETUDE, MAX_RELAY_PAGES, RAW, fetch, flat, relay_page, select_comparators,  # noqa: E402
                    sha256, write_atomic)

NET = ETUDE.parent / "iran-cluster-e-network-2026-11-05"
STOP = datetime(2026, 11, 22, 23, 59, tzinfo=timezone.utc).timestamp()
SENTINEL_EVERY = 50


def write(folder, w, pages, shas, term, requests, source, counters):
    orders = sorted((flat(r) for r in requests if flat(r)["user"] == w), key=lambda o: (o["created"], o["id"]))
    write_atomic(DATA / folder / f"{w}.json", json.dumps(
        {"wallet": w, "pages": pages, "termination": term, "page_sha256": shas, "source": source,
         "requests_read": len(requests), "http": counters, "orders": orders}, indent=1).encode())


def pages_of(w, tag, counters):
    cur, n, reqs, shas = None, 0, {}, []
    while True:
        u = f"https://api.relay.link/requests/v2?user={w}&limit=50" + (f"&continuation={cur}" if cur else "")
        out = RAW / "relay" / f"{w}{tag}_p{n:03d}.json"
        rs, cur = relay_page(fetch(u, out, counters), f"{w} page {n}")
        shas.append(json.loads(out.with_suffix(".meta.json").read_text())["sha256"]); n += 1
        for r in rs:
            reqs[r["id"]] = r
        time.sleep(13)
        if not cur:
            return n, shas, "END", reqs
        if n >= MAX_RELAY_PAGES:
            return n, shas, "MAX_PAGES", reqs


def collect(w):
    out = DATA / "relay" / f"{w}.json"
    if out.exists() and json.loads(out.read_text())["termination"] == "END":
        return "skip"
    counters = {}
    n, shas, term, reqs = pages_of(w, "", counters)
    write("relay", w, n, shas, term, list(reqs.values()), "api.relay.link requests/v2?user=", counters)
    return term


def sentinel():
    """A reference wallet with one archived page of 5 to 40 requests: its archived ids must all come back."""
    for w in (NET / "population.txt").read_text().split():
        done = json.loads((NET / "evidence/relay" / f"relay_user_{w}_DONE.json").read_text())
        if done["pages"] == 1 and 5 <= done["requests"] <= 40:
            ids = {r["id"] for r in json.loads((NET / "evidence/relay" / f"relay_user_{w}_p000.json").read_text())["requests"]}
            n, _, term, reqs = pages_of(w, f"_sentinel_{int(time.time())}", {})
            if not ids <= set(reqs):
                raise SystemExit(f"sentinel {w}: {len(ids - set(reqs))} of {len(ids)} archived requests missing; endpoint degraded")
            return w
    raise SystemExit("no sentinel wallet")


def reference():
    sums = {}
    for line in (NET / "SHA256SUMS.txt").read_text().splitlines():
        h, p = line.split(maxsplit=1)
        sums[p.lstrip("./")] = h
    pop = (NET / "population.txt").read_text().split()
    for w in pop:
        done = json.loads((NET / "evidence/relay" / f"relay_user_{w}_DONE.json").read_text())
        pages = sorted(p for p in (NET / "evidence/relay").glob(f"relay_user_{w}_p*.json") if not p.name.endswith(".meta.json"))
        reqs, shas, rows = {}, [], 0
        for p in pages:
            b = p.read_bytes(); h = sha256(b)
            if sums.get(f"evidence/relay/{p.name}") != h:
                raise SystemExit(f"{p.name}: SHA-256 differs from PR 27's SHA256SUMS.txt")
            shas.append(h)
            rs, _ = relay_page(json.loads(b), p.name)
            rows += len(rs)
            for r in rs:
                reqs[r["id"]] = r
        if len(pages) != done["pages"] or rows != done["requests"]:
            raise SystemExit(f"{w}: {len(pages)} pages and {rows} rows archived, DONE says {done['pages']} and {done['requests']}")
        write("relay_reference", w, len(pages), shas, done["termination"], list(reqs.values()),
              "PR 27 archive, iran-cluster-e-network-2026-11-05/evidence/relay, fetched 5 November 2026", {})
    print("reference wallets", len(pop))


def order():
    """Comparator wallets: selected populations by distance of T to the reference event, wallets by first buy.
    Known-group wallets are read too (sensitivity A keeps them)."""
    kept, _ = select_comparators()
    seen, out = set(), []
    for m in kept:
        for w in m["wallets_with_known"]:
            if w not in seen:
                seen.add(w); out.append((m["condition"], w))
    return out


if __name__ == "__main__":
    if sys.argv[1:] == ["reference"]:
        reference(); sys.exit()
    todo = order()
    print("wallets to read", len(todo), "sentinel", sentinel(), flush=True)
    for i, (c, w) in enumerate(todo):
        if time.time() > STOP:
            print("stopping rule reached: 22 November 2026 23:59 UTC", flush=True); break
        if i and i % SENTINEL_EVERY == 0:
            sentinel()
        print(i, c[:10], w, collect(w), flush=True)
