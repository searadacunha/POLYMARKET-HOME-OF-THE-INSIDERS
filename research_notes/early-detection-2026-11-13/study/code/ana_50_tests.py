"""ana_50: every test of the plan on the frozen analytic table. Each test is written to derived/results_tests.json first,
then recorded in the registry (one line per test; the threshold sweep is one line with its number of comparisons)."""
import json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats, tapefeat
from col_20_prices import unpack
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join("derived", "results_tests.json")
N_PERM = 200_000
SPLIT_TS = 1772323200  # 2026-03-01T00:00:00Z, chronological halves
AGENT = "ana_50_tests"


def load():
    return [json.loads(l) for l in open(os.path.join(ETUDE, "derived", "analytic_table.jsonl"))]


def pair(rows, flag, seed):
    sel = [r for r in rows if r[flag]]
    t1 = stats.t1_exact(sel); t1["ci95_excess_cluster"] = stats.cluster_ci(sel, 5000, seed) if sel else None
    return t1, stats.t2_permutation(rows, flag, N_PERM, seed)


def lead_times(rows):
    """Label-side description: seconds from the alert to the first 10-minute point where the ignited side is priced >= 0.95."""
    con = sqlite3.connect(os.path.join(ETUDE, "data", "prices.sqlite")); out = []
    for r in rows:
        b = con.execute("select blob from series where condition_id=?", (r["condition_id"],)).fetchone()
        lt = None
        for t, p in sorted(unpack(b[0])):
            x = p if r["side"] == "YES" else 1 - p
            if t >= r["t_alert"] and x >= 0.95: lt = t - r["t_alert"]; break
        out.append(lt)
    return out


def main():
    table = load()
    val = [r for r in table if r["eval_set"] == "VALIDATION"]; disc = [r for r in table if r["eval_set"] == "DISCOVERY"]
    res = {"n_table": len(table), "n_validation": len(val), "n_discovery": len(disc), "n_perm": N_PERM, "tests": {}, "describe": {}}
    reg = []

    def test(name, declare, t1, t2=None, n_comp=1, note=""):
        res["tests"][name] = {"t1": t1, "t2": t2, "declared": declare}
        reg.append((name + "_T1", declare, t1["n"], t1["n_events"], t1.get("excess"), t1.get("p"), None, None, n_comp, note))
        if t2 is not None:
            reg.append((name + "_T2", declare, t2["n_flag"] + t2["n_other"], t1["n_events"], t2["diff"], t2["p"], t2["n_perm"], t2["hits"], n_comp, note))

    t1, t2 = pair(val, "lonely_thin", 11); test("PRIMARY_lonely_thin", True, t1, t2)
    t1, t2 = pair(val, "lonely", 12); test("S1_lonely", True, t1, t2)
    t1, t2 = pair(val, "thin", 13); test("S2_thin", True, t1, t2)
    early = [r for r in val if r["t_first"] < SPLIT_TS]; late = [r for r in val if r["t_first"] >= SPLIT_TS]
    test("S3_lonely_thin_early", True, stats.t1_exact([r for r in early if r["lonely_thin"]]))
    test("S3_lonely_thin_late", True, stats.t1_exact([r for r in late if r["lonely_thin"]]))
    test("S4_all_ignitions", True, stats.t1_exact(val))
    sweep = {}
    for share in (0.3, 0.5, 0.7):
        for thin in (0, 2, 5):
            sel = [r for r in val if r["share15"] >= share and r["prior_markets"] <= thin]
            sweep[f"share>={share}|markets<={thin}"] = stats.t1_exact(sel)
    res["tests"]["X1_threshold_sweep"] = {"declared": False, "cells": sweep}
    # description (no test): class sizes and hit rates, discovery cases, lead time, alert load
    for name, sel in (("validation_all", val), ("validation_lonely_thin", [r for r in val if r["lonely_thin"]]),
                      ("validation_lonely_not_thin", [r for r in val if r["lonely"] and not r["thin"]]),
                      ("validation_thin_not_lonely", [r for r in val if r["thin"] and not r["lonely"]]),
                      ("validation_neither", [r for r in val if not r["lonely"] and not r["thin"]]),
                      ("discovery_all", disc), ("discovery_lonely_thin", [r for r in disc if r["lonely_thin"]])):
        res["describe"][name] = stats.summary(sel)
    lt_rows = [r for r in val if r["lonely_thin"]]
    lts = lead_times(lt_rows)
    res["describe"]["lonely_thin_lead_seconds_to_0.95"] = {"n": len(lts), "never": sum(1 for x in lts if x is None),
                                                           "sorted": sorted(x for x in lts if x is not None)}
    loo = []
    for ev in sorted({r["event_slug"] for r in lt_rows}):
        t = stats.t1_exact([r for r in lt_rows if r["event_slug"] != ev]); loo.append({"removed": ev, "n": t["n"], "excess": t["excess"], "p": t["p"]})
    res["describe"]["lonely_thin_leave_one_event_out"] = {"largest_p": max((x["p"] for x in loo if x["p"] is not None), default=None),
                                                          "smallest_excess": min((x["excess"] for x in loo if x["excess"] is not None), default=None),
                                                          "cells": loo}
    span = (max(r["t_alert"] for r in val) - min(r["t_alert"] for r in val)) / 86400 if val else 0
    res["describe"]["alert_load"] = {"days_spanned": span, "lonely_thin_alerts": len(lt_rows),
                                     "per_week": 7 * len(lt_rows) / span if span else None}
    res["describe"]["lonely_thin_rows"] = [{k: r[k] for k in ("event_slug", "condition_id", "side", "t_first", "t_alert", "p_alert", "share15",
                                           "n_buyers15", "initiator", "initiator_cash", "escalation", "prior_markets", "first_activity_age_h",
                                           "deposit_72h_usdc", "win")} for r in lt_rows]
    res["describe"]["discovery_rows"] = [{k: r[k] for k in ("event_slug", "condition_id", "side", "t_first", "t_alert", "p_alert", "share15",
                                         "n_buyers15", "initiator", "initiator_cash", "escalation", "prior_markets", "lonely", "thin", "win")} for r in disc]
    json.dump(res, open(os.path.join(ETUDE, OUT), "w"), indent=1)
    for name, declare, n, n_eff, stat, p, n_tir, n_hits, n_comp, note in reg:
        enregistrer(ETUDE, test=name, declare=declare, n=n, n_effectif=n_eff, agent=AGENT, n_comparaisons=n_comp,
                    params={"lonely_share": tapefeat.LONELY_SHARE, "thin_markets": tapefeat.THIN_MARKETS, "set": "VALIDATION"},
                    stat=stat, p=p, n_tirages=n_tir, n_hits=n_hits, sortie=OUT, note=note)
    enregistrer(ETUDE, test="X1_threshold_sweep_T1", declare=False, n=len(val), agent=AGENT, n_comparaisons=9,
                params={"share": [0.3, 0.5, 0.7], "thin_markets": [0, 2, 5]}, sortie=OUT, note="exploratory sweep, never used for the verdict")
    print("written", OUT, "| registry lines:", len(reg) + 1)


if __name__ == "__main__":
    main()
