"""Analysis of analysis_plan.md, offline: per-population statistics, degree-preserving null, power, verdict.

python3 -I -B code/ana_50_stats.py

Reads only data/ of this study. Writes derived/results.json (statistics and collection accounting), then
one registry line per test. Stops before any test if the reference does not reproduce PR 27's published
counts (censored 37, S1 17, groups 9, 4, 2, 2), the positive control on real data.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (DATA, ETUDE, permutation_test, population_seed, power, recipients,  # noqa: E402
                    select_comparators, stats, verdict)
from registre import enregistrer  # noqa: E402

REF_POP = ETUDE.parent / "iran-cluster-e-network-2026-11-05" / "population.txt"
VARIANTS = ("primary", "A_known_groups_kept", "B_classes_ignored", "C_geopolitics_only", "D_contracts_as_service")


def exits(folder, wallets):
    """Visible wallets -> recipients, censored count, and why the population is incomplete if it is."""
    D, censored = {}, 0
    for w in wallets:
        p = DATA / folder / f"{w}.json"
        if not p.exists():
            return None, None, "wallet_not_collected"
        d = json.loads(p.read_text())
        if d["termination"] != "END":
            return None, None, "wallet_truncated_at_100_pages"
        rs = recipients(d["orders"], w)
        if rs:
            D[w] = rs
        else:
            censored += 1
    return D, censored, None


def run(name, folder, wallets, cls, seed_key, check_classes=True):
    D, censored, why = exits(folder, wallets)
    if D is None:
        return None, why
    holders = defaultdict(set)
    for w, rs in D.items():
        for x in rs:
            holders[x].add(w)
    missing = sorted(x for x, h in holders.items() if len(h) >= 2 and x not in cls)
    if check_classes and missing:  # a missing class is never read as CUSTOMER
        raise SystemExit(f"{name}: {len(missing)} shared recipients without a class, e.g. {missing[0]}")
    r = permutation_test(D, cls, population_seed(seed_key))
    return {"name": name, "population": len(wallets), "censored": censored, **r, "power": power(D, cls, seed_key)}, None


def accounting(kept, excluded, raw_cls):
    http, terms = Counter(), Counter()
    for folder in ("relay", "relay_reference"):
        for p in (DATA / folder).glob("*.json"):
            d = json.loads(p.read_text())
            terms[f"{folder}:{d['termination']}"] += 1
            http.update({f"relay_{k}": v for k, v in d.get("http", {}).items()})
    tapes = []
    for p in sorted((DATA / "populations").glob("*.json")):
        d = json.loads(p.read_text())
        http.update({f"trades_{k}": v for k, v in d.get("http", {}).items()})
        tapes.append({"condition": d["condition"], "pages": d["pages"], "termination": d["termination"],
                      "complete": d["complete"], "archive_rows_missing": len(d["archive_rows_missing_from_tape"]),
                      "wallets": len(d["wallets"])})
    for v in raw_cls.values():
        http.update({f"classes_{k}": n for k, n in v.get("http", {}).items()})
    return {"selection_excluded": excluded, "comparators_selected": len(kept), "tapes": tapes,
            "relay_files_by_termination": dict(terms), "http_counters": dict(http),
            "classes": dict(Counter(v["class"] for v in raw_cls.values())),
            "classes_with_contract_or_program_owner": sum(1 for v in raw_cls.values() if v["contract"]),
            "classes_with_unchecked_chains": sum(1 for v in raw_cls.values() if v["unchecked_chains"])}


def reference_control(ref_wallets):
    """Positive control on real data: the reference, classes ignored, must give PR 27's published counts."""
    D, censored, why = exits("relay_reference", ref_wallets)
    s = stats(D, {}) if D is not None else {}
    ok = D is not None and censored == 37 and s["S1"] == 17 and s["groups"] == [9, 4, 2, 2]
    return ok, {"censored": censored, "S1": s.get("S1"), "groups": s.get("groups"), "why": why}


def main():
    raw_cls = json.loads((DATA / "classes.json").read_text())
    cls = {r: v["class"] for r, v in raw_cls.items()}
    cls_d = {r: ("SERVICE" if v["class"] == "SERVICE" or v["contract"] else "CUSTOMER") for r, v in raw_cls.items()}
    kept, excluded = select_comparators()
    ref_wallets = REF_POP.read_text().split()
    ok, detail = reference_control(ref_wallets)
    if not ok:
        raise SystemExit(f"reference does not reproduce PR 27: {detail}")

    ref = {v: run("reference", "relay_reference", ref_wallets, c, f"reference|{v}", check_classes=v != "B_classes_ignored")[0]
           for v, c in (("primary", cls), ("B_classes_ignored", {}), ("D_contracts_as_service", cls_d))}
    variants = {}
    for v in VARIANTS:
        rows, skipped = [], Counter()
        c = {} if v == "B_classes_ignored" else (cls_d if v == "D_contracts_as_service" else cls)
        for m in kept:
            if v == "C_geopolitics_only" and m["cat"] != "geopolitics/war":
                continue
            ws = m["wallets_with_known"] if v == "A_known_groups_kept" else m["wallets"]
            r, why = run(m["condition"], "relay", ws, c, m["condition"] + "|" + v, check_classes=v != "B_classes_ignored")
            if r is None:
                skipped[why] += 1; continue
            rows.append({**r, "question": m["question"], "cat": m["cat"], "T_utc": m["T_utc"]})
        rref = ref.get(v, ref["primary"])
        variants[v] = {"reference": rref, "comparators": rows, "exit_incomplete": dict(skipped),
                       "verdict": verdict(rref, rows),
                       "descriptive": {f"L>={s}": sum(1 for x in rows if x["L"] >= s) for s in (2, 4, 9)}
                       | {"M>0": sum(1 for x in rows if x["M"] > 0)}}
    out = {"reference_control": detail, "accounting": accounting(kept, excluded, raw_cls), "variants": variants}
    (ETUDE / "derived").mkdir(exist_ok=True)
    (ETUDE / "derived" / "results.json").write_text(json.dumps(out, indent=1, default=list))
    prim = variants["primary"]
    enregistrer(str(ETUDE), test="P1_reference_excess_M", declare=True, n=ref["primary"]["visible"], agent="ana_50_stats",
                params={"alpha": 0.01, "permutations": ref["primary"]["draws"]}, stat=ref["primary"]["M"], p=ref["primary"]["p_M"],
                n_tirages=ref["primary"]["draws"], n_hits=ref["primary"]["hits"], sortie="derived/results.json")
    enregistrer(str(ETUDE), test="P2_comparator_rate_of_excess", declare=True, n=prim["verdict"]["n_comparators"],
                n_comparaisons=1 + len(prim["comparators"]), agent="ana_50_stats", params={"alpha": 0.01},
                stat=prim["verdict"]["rate"], sortie="derived/results.json")
    for v in VARIANTS[1:]:
        x = variants[v]
        enregistrer(str(ETUDE), test=f"S_{v}", declare=True, n=x["verdict"]["n_comparators"],
                    n_comparaisons=1 + len(x["comparators"]), agent="ana_50_stats", params={"alpha": 0.01},
                    stat=x["verdict"]["rate"], sortie="derived/results.json")
    print(json.dumps({k: v["verdict"] for k, v in variants.items()}, indent=1))


if __name__ == "__main__":
    main()
