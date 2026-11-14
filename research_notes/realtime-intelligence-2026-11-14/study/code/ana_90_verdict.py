"""ana_90: the verdict of each class, by code, from derived/results_tests.json and the registry count of comparisons.
Wording and thresholds are those of the plan (tests_lib.verdict)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tests_lib as T

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def comparisons(etude):
    """Comparisons made on real data, all scripts and all agents, as the registry counts them."""
    n = 0
    for line in open(os.path.join(etude, "registre", "tests.jsonl")):
        if line.strip():
            x = json.loads(line)
            if x.get("donnees") == "reelles":
                n += int(x.get("n_comparaisons") or 1)
    return n


def main():
    res = json.load(open(os.path.join(ETUDE, "derived", "results_tests.json")))
    n = comparisons(ETUDE); alpha = 0.05 / n
    out = {"comparisons_on_real_data": n, "alpha_corrected": alpha, "classes": {}}
    for cls, r in res["primary"].items():
        nc = (res["negative_control"].get(cls) or {}).get("t1", {}).get("p")
        out["classes"][cls] = {"verdict": T.verdict(r, alpha, nc_p=nc), "alert_events": r["alert_events"], "excess": r["t1"]["excess"],
                               "excess_ci": r["excess_ci"], "t1_p": r["t1"]["p"], "t2_p": (r.get("t2") or {}).get("p"),
                               "t2_diff": (r.get("t2") or {}).get("diff"), "negative_control_t1_p": nc}
    json.dump(out, open(os.path.join(ETUDE, "derived", "verdict.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
