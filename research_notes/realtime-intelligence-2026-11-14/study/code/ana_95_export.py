"""ana_95: the small tables that let anybody recompute the results without the raw data and without any wallet address.

  derived/export/alerts.jsonl       one row per population, class and event: the alert that enters the tests
  derived/export/base_cells.jsonl   VALIDATION x INFO: per event and stratum, the entries that can serve as controls
  derived/export/class_cells.jsonl  VALIDATION x INFO: per class, event and stratum, the entries to take out of the base
                                    (alerts of the class, and alerts refused for price or date)
A control of a class is a base entry that is not in the class cells: the published verify.py recomputes T1 exactly and
the difference of T2 from these three files. No test is computed here."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats, tests_lib as T

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ETUDE, "derived", *p)
POPS = {"validation_info": ("VALIDATION", "INFO"), "validation_public_process": ("VALIDATION", "PUBLIC_PROCESS"), "discovery_info": ("DISCOVERY", "INFO")}


def main():
    rows = [json.loads(l) for l in open(D("analytic_table.jsonl"))]
    T.fit_m3(rows)
    os.makedirs(D("export"), exist_ok=True)
    n = {"alerts": 0, "base_cells": 0, "class_cells": 0}
    with open(D("export", "alerts.jsonl"), "w") as fa, open(D("export", "base_cells.jsonl"), "w") as fb, open(D("export", "class_cells.jsonl"), "w") as fc:
        for pop, (s, g) in POPS.items():
            part = [r for r in rows if r["set"] == s and r["grp"] == g]
            for cls in T.TESTED + T.BASELINES:
                if pop != "validation_info" and cls in T.BASELINES:
                    continue
                alerts, _, _ = T.split(part, cls)
                for a in stats.first_per_event(alerts):
                    fa.write(json.dumps({"population": pop, "class": cls, "event": a["event"], "t": a["t"], "price": round(a["price"], 6), "win": a["win"],
                                         "hours_to_end": round(a["hours_to_end"], 3), "hours_before_real_close": round((a["closed_ts"] - a["t"]) / 3600.0, 2),
                                         "entry_usd": round(a["cash"], 2), "follow_price": a["follow_price"]}) + "\n"); n["alerts"] += 1
            if pop != "validation_info":
                continue
            base = {}
            for r in part:
                if not r["tier1"] or r["evaluated"]:
                    k = (r["event_id"],) + stats.stratum(r["price"], (r["end_ts"] - r["t"]) / 3600.0)
                    x = base.setdefault(k, [0, 0.0]); x[0] += 1; x[1] += r["win"] - r["price"]
            for (ev, sp, sh), (cnt, tot) in sorted(base.items()):
                fb.write(json.dumps({"event": ev, "price_band": sp, "horizon_band": sh, "n": cnt, "sum_excess": round(tot, 6)}) + "\n"); n["base_cells"] += 1
            for cls in T.TESTED + T.BASELINES:
                cells = {}
                for r in part:
                    if cls in r.get("unknown", ()):
                        continue
                    a, why = T.alert_of(r, cls)
                    if (a is not None or why is not None) and (not r["tier1"] or r["evaluated"]):
                        k = (r["event_id"],) + stats.stratum(r["price"], (r["end_ts"] - r["t"]) / 3600.0)
                        x = cells.setdefault(k, [0, 0.0]); x[0] += 1; x[1] += r["win"] - r["price"]
                for (ev, sp, sh), (cnt, tot) in sorted(cells.items()):
                    fc.write(json.dumps({"class": cls, "event": ev, "price_band": sp, "horizon_band": sh, "n": cnt, "sum_excess": round(tot, 6)}) + "\n"); n["class_cells"] += 1
    print(json.dumps(n))


if __name__ == "__main__":
    main()
