"""ana_98: the cells of the entries that are neither alerts nor controls of a class, so that the published verify.py
recomputes the T2 difference of every class from the exported cells. Added after the freeze (amendements/001-2026-11-14.md).

  derived/export/excluded_cells.jsonl  VALIDATION x INFO: per class, event and stratum, the base entries left out of the
                                       controls although they are not in the class cells of ana_95: an entry whose
                                       membership of the class is unknown (tests_lib.split), and for C7 an entry of C1
                                       that did not turn heavy (tests_lib.NOT_A_CONTROL).
The rule is the one of tests_lib.split, applied to the same rows as ana_95. No test is computed here."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats, tests_lib as T

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ETUDE, "derived", *p)


def excluded(r, cls):
    """A base entry that tests_lib.split keeps out of both the alerts and the controls of `cls`, and that ana_95 did not
    already put in the class cells (those hold alerts and refused alerts, never an entry of unknown membership)."""
    if not (not r["tier1"] or r["evaluated"]):
        return False                                   # not in the base cells either
    if cls in r.get("unknown", ()):
        return True
    a, why = T.alert_of(r, cls)
    return a is None and why is None and cls in T.NOT_A_CONTROL and bool(r.get(T.NOT_A_CONTROL[cls]))


def main():
    rows = [json.loads(l) for l in open(D("analytic_table.jsonl"))]
    T.fit_m3(rows)
    part = [r for r in rows if r["set"] == "VALIDATION" and r["grp"] == "INFO"]
    n = 0
    with open(D("export", "excluded_cells.jsonl"), "w") as f:
        for cls in T.TESTED + T.BASELINES:
            cells = {}
            for r in part:
                if excluded(r, cls):
                    k = (r["event_id"],) + stats.stratum(r["price"], (r["end_ts"] - r["t"]) / 3600.0)
                    x = cells.setdefault(k, [0, 0.0]); x[0] += 1; x[1] += r["win"] - r["price"]
            for (ev, sp, sh), (cnt, tot) in sorted(cells.items()):
                f.write(json.dumps({"class": cls, "event": ev, "price_band": sp, "horizon_band": sh, "n": cnt, "sum_excess": round(tot, 6)}) + "\n"); n += 1
    print(json.dumps({"excluded_cells": n}))


if __name__ == "__main__":
    main()
