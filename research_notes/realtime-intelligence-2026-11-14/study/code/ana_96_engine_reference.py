"""ana_96: the two reference files of the live engine, written from the frozen table and from the verdicts.

  derived/export/engine/rarity_discovery.json.gz   the eight sorted feature lists of the discovery population (INFO
        entries with a history read) and the 99th percentile of the score there: the engine scores a live entry against
        exactly the population the study used. Values only, no wallet, no market.
  derived/export/engine/validation_status.json     what each class was worth on the validation set, in words and
        numbers, as carried by every alert. A class that is not SUPPORTED is marked EXPLORATORY.
No test is computed here."""
import gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ETUDE, "derived", *p)
STUDY = "frozen study of large purchases, 14 November 2026 (research_notes/realtime-intelligence-2026-11-14)"


def main():
    os.makedirs(D("export", "engine"), exist_ok=True)
    fit = [r["x"] for r in map(json.loads, open(D("analytic_table.jsonl"))) if r["evaluated"] and r["set"] == "DISCOVERY" and r["grp"] == "INFO"]
    model = {k: [round(v, 5) for v in vs] for k, vs in models.rarity_fit(fit).items()}
    cut = json.load(open(D("table_counts.json")))["m1_threshold"]
    with gzip.open(D("export", "engine", "rarity_discovery.json.gz"), "wt") as f:
        json.dump({"study": STUDY, "population": "discovery, INFO family, entries with a history read", "rows": len(fit), "threshold": cut, "model": model}, f)
    v = json.load(open(D("verdict.json"))); out = {"study": STUDY, "alpha_corrected": v["alpha_corrected"], "classes": {}}
    for cls, r in v["classes"].items():
        lo, hi = r["excess_ci"]
        num = (f"{r['alert_events']} alert events on the validation set (events whose scheduled ends fall from April to October 2026), excess over the price paid "
               f"{100 * r['excess']:+.1f} points (95 % interval {100 * lo:+.1f} to {100 * hi:+.1f})") if r["excess"] is not None else "no alert on the validation set"
        out["classes"][cls] = {"status": r["verdict"] if r["verdict"] == "SUPPORTED" else "EXPLORATORY", "study_verdict": r["verdict"],
                               "summary": f"{r['verdict']}: {num}", "alert_events": r["alert_events"], "excess": r["excess"], "excess_ci": r["excess_ci"],
                               "t1_p": r["t1_p"], "t2_p": r["t2_p"]}
    json.dump(out, open(D("export", "engine", "validation_status.json"), "w"), indent=1)
    print(len(fit), "discovery rows;", {c: x["study_verdict"] for c, x in out["classes"].items()})


if __name__ == "__main__":
    main()
