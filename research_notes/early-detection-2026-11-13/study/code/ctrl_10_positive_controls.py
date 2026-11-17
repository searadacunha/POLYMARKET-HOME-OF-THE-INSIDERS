"""ctrl_10: positive controls BEFORE the freeze. The same T1, T2 and verdict code runs on synthetic tables:
null effect, a general under-reaction shared by all ignitions (must stay silent), and planted effects of several sizes.
Writes controles/positive_controls.md and one registry line per cell, marked as synthetic data."""
import json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_TOTAL = 1500        # ignitions per synthetic table
N_PERM = 4000         # enough to resolve the corrected threshold used below
ALPHA_CORR = 0.05 / 20  # planned number of comparisons on real data: 18, rounded up
SEEDS = 60


def table(rnd, n_flag, delta_flag, delta_all):
    rows = []
    for i in range(N_TOTAL):
        p = min(0.9, max(0.03, rnd.betavariate(2.0, 3.0)))
        f = i < n_flag
        q = min(1.0, max(0.0, p + delta_all + (delta_flag if f else 0.0)))
        # events of 1 to 3 ignitions; flagged rows spread over distinct events
        rows.append({"win": int(rnd.random() < q), "p_alert": p, "event_slug": f"e{i if f else N_TOTAL + i // 2}",
                     "initiator": f"w{i}", "flag": f})
    return rows


def cell(n_flag, delta_flag, delta_all):
    out = {"SUPPORTED": 0, "NOT_SUPPORTED": 0, "INCONCLUSIVE": 0}
    for seed in range(SEEDS):
        rnd = random.Random(1000 * n_flag + 17 * seed + int(1000 * delta_flag) + int(7000 * delta_all))
        rows = table(rnd, n_flag, delta_flag, delta_all)
        t1 = stats.t1_exact([r for r in rows if r["flag"]]); t2 = stats.t2_permutation(rows, "flag", N_PERM, seed)
        out[stats.verdict(t1, t2, ALPHA_CORR)] += 1
    return out


def main():
    t0 = time.time(); lines = []; reg = []
    grid = [(n, d, a) for n in (8, 12, 20, 40, 80) for d, a in ((0.0, 0.0), (0.0, 0.10), (0.15, 0.0), (0.30, 0.0), (0.50, 0.0), (0.30, 0.10))]
    for n_flag, d, a in grid:
        c = cell(n_flag, d, a); lines.append((n_flag, d, a, c)); reg.append((n_flag, d, a, c))
        print(n_flag, d, a, c, f"{time.time() - t0:.0f}s", flush=True)
    os.makedirs(os.path.join(ETUDE, "controles"), exist_ok=True)
    rel = os.path.join("controles", "positive_controls.md")
    with open(os.path.join(ETUDE, rel), "w") as f:
        f.write("# Positive controls (synthetic tables, before the freeze)\n\n")
        f.write(f"Each cell: {SEEDS} synthetic tables of {N_TOTAL} ignitions, entry prices drawn from Beta(2,3) clipped to [0.03, 0.90]; "
                f"T1 exact, T2 with {N_PERM} permutations, verdict rule of `code/stats.py` at the corrected threshold {ALPHA_CORR:.4f}.\n"
                "`delta_class` is the planted excess win probability of the flagged class; `delta_all` is an excess shared by every "
                "ignition (a general under-reaction of the market), which must NOT produce a SUPPORTED verdict by itself.\n\n")
        f.write("| flagged rows | delta_class | delta_all | SUPPORTED | NOT_SUPPORTED | INCONCLUSIVE |\n|---:|---:|---:|---:|---:|---:|\n")
        for n_flag, d, a, c in lines:
            f.write(f"| {n_flag} | {d:.2f} | {a:.2f} | {c['SUPPORTED']}/{SEEDS} | {c['NOT_SUPPORTED']}/{SEEDS} | {c['INCONCLUSIVE']}/{SEEDS} |\n")
        nulls = [c["SUPPORTED"] for n, d, a, c in lines if d == 0.0]
        f.write(f"\nNull rows (delta_class = 0, with or without a shared excess): {sum(nulls)} SUPPORTED out of {len(nulls) * SEEDS} tables.\n")
        f.write("Fewer than 10 flagged rows always give INCONCLUSIVE by rule.\n")
    for n_flag, d, a, c in reg:
        enregistrer(ETUDE, test=f"CTRL_n{n_flag}_d{d}_a{a}", declare=True, n=N_TOTAL, agent="ctrl_10_positive_controls", n_comparaisons=SEEDS,
                    params={"n_flag": n_flag, "delta_class": d, "delta_all": a, "n_perm": N_PERM, "alpha_corr": ALPHA_CORR},
                    stat=c["SUPPORTED"] / SEEDS, donnees="synthetiques", sortie=rel)
    print("written", rel, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
