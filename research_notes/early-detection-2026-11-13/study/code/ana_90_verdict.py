"""ana_90: the verdict, computed by code from the primary tests and the registry count of comparisons on real data."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats
from registre import lire

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    res = json.load(open(os.path.join(ETUDE, "derived", "results_tests.json")))
    lines, errors = lire(ETUDE)
    if errors: raise SystemExit(f"registry errors: {errors[:3]}")
    k = sum(int(l.get("n_comparaisons") or 1) for l in lines if l.get("donnees", "reelles") == "reelles")
    if k < 2: raise SystemExit("the registry holds fewer than the two primary tests on real data")
    alpha = 0.05 / k
    p = res["tests"]["PRIMARY_lonely_thin"]
    v = stats.verdict(p["t1"], p["t2"], alpha)
    out = {"verdict": v, "alpha": 0.05, "comparisons_on_real_data": k, "alpha_corrected": alpha,
           "primary_T1": {x: p["t1"][x] for x in ("n", "n_events", "n_initiators", "wins", "win_rate", "mean_p", "excess", "p", "ci95_excess_cluster")},
           "primary_T2": p["t2"], "rule": {"min_n": stats.MIN_N, "min_events": stats.MIN_EVENTS, "min_excess": stats.MIN_EXCESS}}
    json.dump(out, open(os.path.join(ETUDE, "derived", "verdict.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
