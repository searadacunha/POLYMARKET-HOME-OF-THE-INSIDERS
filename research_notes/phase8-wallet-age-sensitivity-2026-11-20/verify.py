#!/usr/bin/env python3
"""Offline verifier of the phase 8 wallet-age sensitivity note (EXPLORATORY, post hoc).

Checks the SHA-256 list, re-runs sensitivity.py, compares every headline and table figure of README.md with the recomputed value
under a named check, re-reads the frozen protocol and code lines the note cites, and runs one negative self-test.
Prints PASS or FAIL per check and "N/M checks pass"; exits 1 on any failure. Writes nothing.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "investigations/maduro-iran/sources"
PUSD_TOKEN = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def fmt(x):
    return f"{x:+.2f}"


def ci(c):
    return f"[{c[0]:+.2f}, {c[1]:+.2f}]"


def lines(path):
    return path.read_text(encoding="utf-8").splitlines()


def main():
    raw = (HERE / "README.md").read_text(encoding="utf-8")
    text = " ".join(raw.split())

    def quoted(name, phrase, ok=True):
        check(name, ok and phrase in text, phrase)

    for line in lines(HERE / "data/SHA256SUMS"):
        digest, rel = line.split("  ", 1)
        path = ROOT / rel
        got = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
        check(f"sha256:{rel}", got == digest, got[:16])

    run = subprocess.run([sys.executable, "-B", str(HERE / "sensitivity.py")], capture_output=True, text=True)
    check("sensitivity_runs", run.returncode == 0, run.stderr[-300:])
    if run.returncode:
        return
    R = json.loads(run.stdout)
    C, E, P, F = R["counts"], R["estimates"], R["published"], R["flips"]
    fr = R["frozen_reproduction"]

    quoted("frozen_flags_reproduced", f"0 flag mismatches on {fr['events']:,} events and 0 age mismatches on the "
           f"{fr['fund_sample_events']:,} funding-sample events", fr["flag_mismatch"] == 0 and fr["age_mismatch"] == 0)
    quoted("frozen_counts_equal_published", "/".join(str(C[s]["fresh_published"]) for s in C),
           all(C[s]["fresh_frozen"] == C[s]["fresh_published"] for s in C))
    quoted("published_effects_reproduced", f"{fmt(E['TRAIN']['frozen']['effect_pts'])} (TRAIN), "
           f"{fmt(E['VALID']['frozen']['effect_pts'])} (VALID) and {fmt(E['TEST']['frozen']['effect_pts'])} (TEST)",
           all(E[s]["frozen"]["effect_pts"] == P[s]["effect_pts"] and E[s]["frozen"]["n_sig"] == P[s]["n_sig"]
               for s in P))
    quoted("counts_headline", "from " + "/".join(str(C[s]["fresh_frozen"]) for s in C) + " to " +
           "/".join(str(C[s]["fresh_pusd"]) for s in C) + " (TRAIN/VALID/TEST)")
    for s, c in C.items():
        quoted(f"count_table_{s}", f"| {s} | {c['fresh_frozen']} | {c['fresh_pusd']} | {c['flips_not_fresh_to_fresh']} | "
               f"{c['flips_fresh_to_not_fresh']} | {c['events_pusd_before_T']} | {c['age_unknown_frozen_candidates']} |")
    quoted("only_not_fresh_to_fresh", "Every change is from not fresh to fresh",
           all(c["flips_fresh_to_not_fresh"] == 0 for c in C.values()))
    quoted("no_unknown_age_with_pusd", "With pUSD counted, no candidate keeps an unknown age",
           all(c["age_unknown_pusd_candidates"] == 0 for c in C.values()))
    quoted("changes_in_valid_and_test", f"it reaches the end of VALID too ({C['VALID']['flips_not_fresh_to_fresh']} "
           "changed events)", C["VALID"]["flips_not_fresh_to_fresh"] > 0 and C["TEST"]["flips_not_fresh_to_fresh"] > 0
           and C["TRAIN"]["flips_not_fresh_to_fresh"] == 0)
    for mo, m in R["pusd_timeline"]["candidates_by_trade_month"].items():
        quoted(f"month_table_{mo}", f"| {mo} | {m['candidates']} | {m['age_unknown_frozen']} | {m['fresh_frozen']} | "
               f"{m['fresh_pusd']} |")
    T = R["pusd_timeline"]
    quoted("earliest_pusd", f"dated {T['earliest_first_pusd_utc']} UTC")
    quoted("pusd_wallet_count", f"{T['wallets_with_a_pusd_transfer']} of the {T['wallets']:,} wallets have a pUSD "
           "transfer")
    quoted("sample_size", f"each of the {T['wallets']:,} funding-sample wallets")
    quoted("flips_summary", f"{F['n']} events change, in {F['wallets']} wallets and {F['markets']} markets, all traded "
           f"between {F['trades_utc'][0]} and {F['trades_utc'][1]} UTC", F["n"] == sum(
               c["flips_not_fresh_to_fresh"] + c["flips_fresh_to_not_fresh"] for c in C.values()))
    quoted("flips_all_unknown_age", f"All {F['n']} had an unknown age under the frozen rule",
           F["age_unknown_under_frozen_rule"] == F["n"])
    quoted("flips_usdc_history", f"For {F['usdc_never']} of them the wallet never has a USDC.e or USDC transfer, and "
           f"for the other {F['usdc_first_after_T']} its first one comes after the trade",
           F["usdc_never"] + F["usdc_first_after_T"] == F["n"])
    quoted("flips_on_mint", f"{F['first_pusd_is_mint']} of the {F['n']} changed events rest on a first pUSD transfer "
           "that is a mint")
    quoted("flips_on_mint_result", f"{F['first_pusd_is_mint']} of the {F['n']} changed events rest on a pUSD mint")
    tot = [C[s]["fresh_pusd"] for s in C]
    quoted("flagged_total", f"{sum(tot)} events are flagged in total ({' + '.join(map(str, tot))})")
    for s, e in E.items():
        for rule, label in (("frozen", "frozen"), ("pusd", "pUSD counted")):
            x = e[rule]
            quoted(f"estimate_table_{s}_{rule}", f"| {s} | {label} | {x['n_sig']} ({x['n_sig_in_used_strata']}) | "
                   f"{x['sig_markets']} | {x['sig_wallets']} | {fmt(x['effect_pts'])} | {ci(x['ci95_market'])} | "
                   f"{x['kish_neff_market']} / {x['kish_neff_wallet']} |", x["draws_kept"] == R["bootstrap"]["draws"])
        quoted(f"published_table_{s}", f"| {s} | {fmt(P[s]['effect_pts'])} | {ci(P[s]['ci95'])} | {P[s]['n_sig']} |")
    t0, t1 = E["TEST"]["frozen"], E["TEST"]["pusd"]
    quoted("headline_test_estimate", f"from {fmt(t0['effect_pts'])} points (n = {t0['n_sig']}) to "
           f"{fmt(t1['effect_pts'])} points (n = {t1['n_sig']}, {t1['sig_markets']} markets)")
    zero = [t0["ci95_market"], t1["ci95_market"], P["TEST"]["ci95"]]
    quoted("test_intervals_include_zero", "Neither TEST interval excludes zero", all(a < 0 < b for a, b in zero))
    quoted("n_eff_published", f"rests on about {round(t0['kish_neff_market'])} to {round(t0['kish_neff_wallet'])} "
           "effectively independent events")
    quoted("n_eff_pusd", f"the pUSD-counted one on about {round(t1['kish_neff_market'])} to "
           f"{round(t1['kish_neff_wallet'])}")
    ft = R["flipped_test_with_outcome"]
    quoted("flipped_test_outcome", f"The {ft['n']} TEST events that change and have an outcome sit in {ft['markets']} "
           f"markets and {ft['wallets']} wallets, with a mean gross `ret_res` of {ft['mean_gross_ret_res_pts']:.2f} "
           "points", ft["n"] == t1["n_sig"] - t0["n_sig"])
    quoted("mde", f"about {t0['mde80_pts']} points with the frozen flags and about {t1['mde80_pts']} points with pUSD "
           "counted")
    quoted("mde_range", f"roughly {round(t1['mde80_pts'])} to {round(t0['mde80_pts'])} points")
    v0, v1 = E["VALID"]["frozen"], E["VALID"]["pusd"]
    quoted("valid_move", f"VALID moves from {fmt(v0['effect_pts'])} to {fmt(v1['effect_pts'])} points")
    quoted("train_unchanged", "TRAIN is unchanged", E["TRAIN"]["frozen"]["effect_pts"] == E["TRAIN"]["pusd"][
        "effect_pts"] and C["TRAIN"]["fresh_frozen"] == C["TRAIN"]["fresh_pusd"])
    B = R["bootstrap"]
    quoted("bootstrap_settings", f"{B['draws']:,} draws, seed {B['seed']}")

    rapport = (SRC / "phase8/RAPPORT_PHASE8.md").read_text(encoding="utf-8")
    proto = lines(SRC / "phase8/PROTOCOLE_PREENREGISTRE.md")
    quoted("multiplicity_family", "288 + 36 = 324 comparisons (Bonferroni threshold "
           f"{0.05 / 324:.2e}".replace("e-04", "e-4") + "), of which 48 + 6 = 54 primary (threshold "
           f"{0.05 / 54:.1e}".replace("e-04", "e-4") + ")", "288 comparaisons" in rapport and "48 principales" in rapport)
    row = [l for l in proto if l.startswith("| `wallet_age_h`")]
    check("protocol_definition", len(row) == 1 and "premier afflux USDC (USDC.e ou natif) non lié au trading" in row[0],
          row[0][:90] if row else "row missing")
    check("protocol_written_30_09_2026", "Rédigé le 30/09/2026" in "\n".join(proto) and "written on 30/09/2026" in text)
    fund = lines(SRC / "scripts/p8_funding.py")
    check("code_token_set_line6", fund[5].startswith("TOK={") and fund[5].count("0x") == 2 and "USDC.e" in fund[5]
          and PUSD_TOKEN not in "\n".join(fund).lower())
    inflow = next(i for i, l in enumerate(fund) if "x['to'].lower()==w" in l)
    check("code_first_any_any_kind_line18", "t0=int(r[0]['timeStamp'])" in fund[17] and "first_any" in fund[17]
          and inflow > 17)
    feat = lines(SRC / "scripts/p8_fundfeat.py")
    check("code_age_line24", "age=(r.ts-f['first_any'])/3600" in feat[23])
    check("code_s_fresh_line32", "FF['S_FRESH']=(FF.wallet_age_h<=48)&(FF.prior_trades_univ<=2)" in feat[31])
    low = rapport.lower()
    check("report_silent_on_gap", "first_any" not in low and "pusd" not in low)

    # negative self-test: one changed wallet's first pUSD transfer moved after all its trades must change the count
    sys.path.insert(0, str(HERE))
    import sensitivity
    pusd = sensitivity.load_pusd()
    rows = sensitivity.flag_events(sensitivity.load_events(), sensitivity.load_first_usdc(), pusd)
    w = next(r["wallet"] for r in rows if r["split"] == "TEST" and r["F1"] and not r["F0"])
    last = max(r["ts"] for r in rows if r["wallet"] == w)
    moved = dict(pusd)
    moved[w] = dict(pusd[w], pusd_first_ts=last + 1)
    M = sensitivity.compute(moved, bootstrap=False)["counts"]
    check("negative_selftest_moved_pusd_changes_count", M["TEST"]["fresh_pusd"] < C["TEST"]["fresh_pusd"] and
          M["TEST"]["fresh_frozen"] == C["TEST"]["fresh_frozen"],
          f"TEST pUSD count {C['TEST']['fresh_pusd']} -> {M['TEST']['fresh_pusd']}")

    for p in sorted(HERE.rglob("*")):
        if p.is_file() and p.suffix in (".md", ".py", ".txt") or p.name == "SHA256SUMS":
            body = p.read_text(encoding="utf-8")
            check(f"hygiene:{p.relative_to(HERE)}", chr(0x2014) not in body and ("/" + "Users/") not in body)


if __name__ == "__main__":
    main()
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok or not detail else f"  [{detail}]"))
    n = sum(ok for _, ok, _ in RESULTS)
    print(f"{n}/{len(RESULTS)} checks pass")
    sys.exit(0 if RESULTS and n == len(RESULTS) else 1)
