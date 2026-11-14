"""ana_50: every declared test, once, on the frozen analytic table. Writes derived/results_tests.json, then one registry
line per test (registre.py). Nothing here chooses anything: classes, populations and tests are those of the plan.

Populations: VALIDATION x INFO (primary), VALIDATION x PUBLIC_PROCESS (negative control), DISCOVERY x INFO (the set the
scores were fitted on, description only)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tests_lib as T

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join("derived", "results_tests.json")


def run(rows, steps=(2000, 20000, 100000, 500000), seed=20261114):
    m3 = T.fit_m3(rows)
    pop = lambda s, g: [r for r in rows if r["set"] == s and r["grp"] == g]
    vi, vp, di = pop("VALIDATION", "INFO"), pop("VALIDATION", "PUBLIC_PROCESS"), pop("DISCOVERY", "INFO")
    res = {"populations": {"validation_info": len(vi), "validation_public_process": len(vp), "discovery_info": len(di)}, "m3": m3,
           "primary": {}, "negative_control": {}, "discovery": {}, "robustness": {}}
    for cls in T.TESTED + T.BASELINES:
        res["primary"][cls] = T.class_tests(vi, cls, with_t2=True, seed=seed, steps=steps)
    for cls in T.TESTED:
        res["negative_control"][cls] = T.class_tests(vp, cls, with_t2=False, seed=seed)
        res["discovery"][cls] = T.class_tests(di, cls, with_t2=False, seed=seed)
        res["robustness"][cls] = T.robustness(vi, cls, seed=seed)
    res["sweep_c1"] = T.sweep_c1(vi); res["placebo_c1"] = T.placebo(vi, seed=seed)
    return res


def main():
    from registre import enregistrer
    rows = [json.loads(l) for l in open(os.path.join(ETUDE, "derived", "analytic_table.jsonl"))]
    res = run(rows)
    json.dump(res, open(os.path.join(ETUDE, OUT), "w"), indent=1)
    reg = lambda **k: enregistrer(ETUDE, declare=True, agent="analyse-principale", sortie=OUT, **k)
    for cls, r in res["primary"].items():
        t1, t2 = r["t1"], r.get("t2") or {}
        reg(test=f"T1_{cls}_validation_info", n=r["entries_alerted"], n_effectif=r["alert_events"], stat=t1["excess"], p=t1["p"],
            params={"test": "exact Poisson-binomial, one alert per event", "wins": t1["wins"], "expected": t1["expected"]})
        reg(test=f"T2_{cls}_validation_info", n=r["entries_alerted"], n_effectif=r["alert_events"], stat=t2.get("diff"), p=t2.get("p"),
            n_tirages=t2.get("draws") or None, n_hits=t2.get("hits") if t2.get("draws") else None,
            params={"test": "stratified difference to control entries, events resampled", "controls": r["controls"]})
    for part, label in (("negative_control", "validation_public_process"), ("discovery", "discovery_info")):
        for cls, r in res[part].items():
            t1 = r["t1"]
            reg(test=f"T1_{cls}_{label}", n=r["entries_alerted"], n_effectif=r["alert_events"], stat=t1["excess"], p=t1["p"],
                params={"test": "exact Poisson-binomial, one alert per event", "wins": t1["wins"], "expected": t1["expected"]})
    cells = res["sweep_c1"]
    best = min((c["p"] for c in cells.values() if c["p"] is not None), default=None)
    reg(test="X1_sweep_C1_cells", n=sum(c["n"] for c in cells.values()), n_comparaisons=len(cells), p=best,
        params={"cells": sorted(cells), "p": "smallest of the cells"})
    reg(test="X2_placebo_C1", n=res["placebo_c1"]["placebos"], stat=res["placebo_c1"]["share_p_below_0.05"],
        params={"what": "share of random classes of the size of C1 with p < 0.05: one diagnostic number"})
    reg(test="X3_robustness_variants", n=len(res["robustness"]), params={"what": "estimates and intervals only, no p-value computed"})
    print(json.dumps({k: {c: (v["alert_events"], v["t1"]["excess"], v["t1"]["p"], (v.get("t2") or {}).get("p")) for c, v in res[k].items()}
                      for k in ("primary", "negative_control", "discovery")}, indent=1))


if __name__ == "__main__":
    main()
