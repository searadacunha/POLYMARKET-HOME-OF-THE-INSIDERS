#!/usr/bin/env python3
"""Summarise a run (units.jsonl, episodes.jsonl, missing_tape.jsonl) and write PARTITIONS.json. Reads no outcome.

usage: summarize.py --run out/full --frozen-splits ../../../splits.json --frozen-splits ../../../splits_expanded.json
                    --out-summary out/full/SUMMARY.json --out-partitions PARTITIONS.json
"""
import argparse, collections, hashlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger as L  # noqa: E402

IRAN = "0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--frozen-splits", action="append", default=[])
    ap.add_argument("--out-summary", required=True)
    ap.add_argument("--out-partitions", required=True)
    a = ap.parse_args()
    units = [json.loads(l) for l in open(os.path.join(a.run, "units.jsonl"))]
    names = [u["unit"] for u in units]
    dup_units = sorted({n for n in names if names.count(n) > 1})
    ck = [json.loads(l) for l in open(os.path.join(a.run, "checkpoint.jsonl"))]
    missing = [json.loads(l) for l in open(os.path.join(a.run, "missing_tape.jsonl"))]
    frozen = {}
    for p in a.frozen_splits:
        frozen.update(json.load(open(p)))

    tot = collections.Counter()
    tx = collections.Counter()
    xs = collections.Counter()
    fams = collections.Counter()
    fee_rates = collections.Counter()
    tape_status = collections.Counter()
    quarantine = collections.Counter()
    by_close = collections.Counter()
    flags = collections.Counter()
    cls = collections.defaultdict(collections.Counter)      # observation partition -> "type|class" -> n
    mism = []
    for u in units:
        f = u["family"]
        fams[f if not f.startswith("unproven") else "unproven: " + f.split(": ", 1)[1]] += 1
        for cid, m in u["markets"].items():
            tot["markets"] += 1
            tot["fill_rows"] += m["rows"]
            tape_status[m["status"]] += 1
            by_close[m["frozen_close_partition"]] += 1
            flags[f"fees_enabled={m['fees_enabled']}"] += 1
            flags[f"neg_risk={m['neg_risk']}"] += 1
            flags[f"gamma_version={m['gamma_version']}"] += 1
            fz = frozen.get(cid)
            if fz is not None and fz != m["frozen_close_partition"]:
                mism.append({"cid": cid, "frozen": fz, "recomputed": m["frozen_close_partition"]})
        tot["units"] += 1
        tot["events_applied"] += u["events_applied"]
        tot["events_in"] += u["events_in"]
        tot["wallet_market_pairs"] += u["wallet_market_pairs"]
        tot["pairs_with_proven_unobserved_inflow"] += u["pairs_with_proven_unobserved_inflow"]
        tot["rows_without_tx"] += u.get("rows_without_tx", 0)
        quarantine.update(u.get("quarantined", {}))
        tx.update(u["tx_checks"])
        xs.update(u["x_status_at_last_fill"])
        fee_rates.update(u.get("implied_fee_rates", {}))
        for k, n in u["classes"].items():
            p, t, c = k.split("|")
            cls[p][f"{t}|{c}"] += n
    eps = collections.Counter()
    for l in open(os.path.join(a.run, "episodes.jsonl")):
        e = json.loads(l)
        eps[f"{e['partition']}|{e['family']}|{e['class']}"] += 1
    obs = {p: sum(c.values()) for p, c in cls.items()}
    summary = {"units": tot["units"], "checkpointed_units": len(ck), "duplicate_units": dup_units,
               "markets_without_tape": len(missing), "totals": tot, "tape_status": tape_status,
               "families": fams, "flags": flags, "frozen_close_partition_of_markets": by_close,
               "tx_checks": tx, "implied_fee_rates": dict(sorted(fee_rates.items())), "quarantined": quarantine,
               "x_status_at_last_fill": xs, "observations_per_partition": obs,
               "classes_per_partition": {p: dict(sorted(c.items())) for p, c in sorted(cls.items())},
               "episodes": dict(sorted(eps.items())),
               "frozen_close_partition_mismatches": mism}
    json.dump(summary, open(a.out_summary, "w"), indent=1, sort_keys=True)

    parts = {
        "defined": "2026-11-17, mission 3, before any signal optimisation on this ledger",
        "unit": "an observation = (wallet, family, window (t0, t1]); it belongs to the partition containing t1",
        "bounds_utc": {n: [lo, hi] for n, lo, hi in L.BOUNDS},
        "why_not_market_close_time": "The frozen study assigned whole markets by close time. For 'by date' markets the "
                                      "close time depends on the outcome (an early YES closes early), so membership "
                                      "would carry label information, and trade periods of TRAIN and VALID markets "
                                      "overlap. The observation time t1 is fixed before any outcome.",
        "purge_rule_for_training": "an observation may be trained on only if its market closed by the end of its own "
                                   "partition (ledger.usable_for_training); otherwise its label did not exist yet",
        "exploratory_only": {"label": "EXPLORATORY_IRAN",
                             "rule": "observations of the 36 Iran cohort wallets (data/iran_cohort_wallets.json) that "
                                     "fall in VALID or TEST, plus every observation of the Iran 28 February market and "
                                     "of events whose slug starts with 'us-strikes-iran'; never in VALID or TEST"},
        "reference_frozen_rule": {"rule": "market close time (collective-exposure-shifts scripts/split.py)",
                                  "markets_per_partition": by_close,
                                  "agreement_with_frozen_splits_json": {
                                      "compared": sum(1 for u in units for c in u["markets"] if c in frozen),
                                      "mismatches": len(mism)}},
        "observations_per_partition": obs,
        "iran_observations_in_sample": "0: none of the 36 cohort wallets trades in the 1,579 sampled markets; the Iran "
                                       "market itself is read separately in out/iran_exploratory/",
        "caveat_test_already_read": "The TEST window (2026-07-01 to 2026-10-31) was read on 2026-11-16 by the S4 study "
                                    "(verdict NOT_SUPPORTED); missions 4 to 6, run in parallel today, may have read it too "
                                    "(not checked). Any new signal "
                                    "scored there re-uses a TEST window that has been looked at. A fresh holdout "
                                    "(markets closing after 2026-10-31, not yet collected) is a decision for Benjamin.",
        "code_sha256": hashlib.sha256(open(L.__file__, "rb").read()).hexdigest(),
    }
    json.dump(parts, open(a.out_partitions, "w"), indent=1)
    print(json.dumps({k: summary[k] for k in ("units", "checkpointed_units", "duplicate_units", "markets_without_tape",
                                               "totals", "tape_status", "families", "flags", "tx_checks",
                                               "implied_fee_rates", "quarantined", "x_status_at_last_fill",
                                               "observations_per_partition", "episodes",
                                               "frozen_close_partition_of_markets")}, indent=1))
    print("frozen-close mismatches:", len(mism))


if __name__ == "__main__":
    main()
