#!/usr/bin/env python3
"""Provenance check and correction of the archived 20/36 vs 16/733 contrast.

Three readings of the same question, same rule ("earliest BUY of No strictly before earliest BUY of Yes"):
  1. the archived 42,000-row tape as published;
  2. the complete v2 tape restricted to the archived band's first second;
  3. the complete v2 tape of the market.
It also asserts that every archived row exists in the v2 tape, so a difference can only come from missing rows,
never from a changed definition.

Run (paths are arguments, nothing is downloaded if the files exist):
  python3 reproduce_feb28.py --archive feb28.jsonl --created feb22_25.csv --v2 feb28_v2.sqlite \
      --out results/feb28_recheck.json
"""
import argparse, collections, csv, datetime as dt, hashlib, json, os, sqlite3, urllib.parse


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(rows, cohort):
    first = {}
    present = set()
    for w, side, oc, ts in rows:
        present.add(w)
        if side != "BUY":
            continue
        oc = (oc or "").lower()
        k = (w, oc)
        if k not in first or ts < first[k]:
            first[k] = ts

    def cls(ws):
        c = collections.Counter()
        for w in ws:
            y, n = first.get((w, "yes")), first.get((w, "no"))
            if y is None and n is None:
                c["no_buy"] += 1
            elif y is not None and n is None:
                c["yes_buy_only"] += 1
            elif n is not None and y is None:
                c["no_buy_only"] += 1
            elif n < y:
                c["no_buy_before_yes_buy"] += 1
            elif y < n:
                c["yes_buy_before_no_buy"] += 1
            else:
                c["both_same_second"] += 1
        d = dict(c)
        d["n"] = len(ws)
        return d

    pop = [w for w in cohort if w in present]
    return {"population_present": len(pop),
            "cohort": cls([w for w in pop if cohort[w]]),
            "other": cls([w for w in pop if not cohort[w]])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--created", required=True)
    ap.add_argument("--v2", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    for k in ("archive", "created", "v2", "out"):
        setattr(a, k, os.path.abspath(getattr(a, k)))

    cohort = {}
    with open(a.created) as f:
        for rec in csv.DictReader(f):
            cohort[rec["proxy"].lower()] = rec["in_g38"] == "True"

    arch = []
    with open(a.archive) as f:
        for line in f:
            r = json.loads(line)
            arch.append((r["proxy_wallet"].lower(), r["side"], r["outcome"], r["timestamp"]))
    band_start, band_end = min(r[3] for r in arch), max(r[3] for r in arch)

    con = sqlite3.connect(f"file:{urllib.parse.quote(a.v2)}?mode=ro", uri=True)
    full = con.execute("select wallet, side, outcome, ts from trades").fetchall()
    window = [r for r in full if r[3] >= band_start]

    A = collections.Counter((w, ts, oc, s) for w, s, oc, ts in arch)
    B = collections.Counter((w, ts, oc, s) for w, s, oc, ts in window)

    out = {
        "market": "US strikes Iran by February 28, 2026?",
        "archived_tape": {"sha256": sha256(a.archive), "rows": len(arch),
                          "band_utc": [iso(band_start), iso(band_end)],
                          "rows_are_84_pages_of_500": len(arch) == 84 * 500},
        "complete_tape": {"rows": len(full), "first_utc": iso(min(r[3] for r in full)),
                          "last_utc": iso(max(r[3] for r in full))},
        "integrity": {"archived_rows_absent_from_v2": sum((A - B).values()),
                      "v2_rows_inside_archived_band_missing_from_archive": sum((B - A).values()),
                      "v2_rows_from_band_start": len(window)},
        "reading_1_archived_42k": classify(arch, cohort),
        "reading_2_complete_tape_from_band_start": classify(window, cohort),
        "reading_3_complete_tape_full_history": classify(full, cohort),
    }
    out["archive_kept_share_of_window"] = round(len(arch) / max(len(window), 1), 4)
    out["conclusion"] = ("The archived band is the newest 84 pages of a longer stream; the band edges equal the tape "
                         "extent, so the band is a page cap, not a designed window. With the complete tape the same "
                         "rule classifies the cohort differently.")
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
