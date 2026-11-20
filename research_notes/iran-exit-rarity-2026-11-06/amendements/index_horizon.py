#!/usr/bin/env python3
"""Exploratory sensitivity from amendment 001. Not part of the frozen protocol.

Recomputes comparator recipient sets using only Relay orders created on or before
2026-11-05T23:59:59Z. Does not replace ana_50_stats.py.
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from ana_50_stats import REF_POP, reference_control  # noqa: E402
from common import (DATA, ETUDE, permutation_test, population_seed, power, recipients,  # noqa: E402
                    select_comparators, verdict)
from registre import enregistrer  # noqa: E402

CUTOFF = datetime(2026, 11, 5, 23, 59, 59, tzinfo=timezone.utc)


def parse_created(value):
    if not isinstance(value, str) or not value:
        raise SystemExit(f"missing created timestamp: {value!r}")
    text = value.replace("Z", "+00:00")
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SystemExit(f"unparseable created timestamp: {value}") from exc
    if stamp.tzinfo is None:
        raise SystemExit(f"naive created timestamp: {value}")
    return stamp.astimezone(timezone.utc)


def exits_cut(wallets):
    D, censored = {}, 0
    for w in wallets:
        path = DATA / "relay" / f"{w}.json"
        if not path.exists():
            return None, None, "wallet_not_collected"
        doc = json.loads(path.read_text())
        if doc["termination"] != "END":
            return None, None, "wallet_truncated_at_100_pages"
        kept = []
        for order in doc["orders"]:
            if parse_created(order["created"]) <= CUTOFF:
                kept.append(order)
        rs = recipients(kept, w)
        if rs:
            D[w] = rs
        else:
            censored += 1
    return D, censored, None


def run(name, wallets, cls, seed_key):
    D, censored, why = exits_cut(wallets)
    if D is None:
        return None, why
    holders = defaultdict(set)
    for w, rs in D.items():
        for recipient in rs:
            holders[recipient].add(w)
    missing = sorted(x for x, h in holders.items() if len(h) >= 2 and x not in cls)
    if missing:
        raise SystemExit(f"{name}: {len(missing)} shared recipients without a class, e.g. {missing[0]}")
    result = permutation_test(D, cls, population_seed(seed_key))
    return {"name": name, "population": len(wallets), "censored": censored, **result,
            "power": power(D, cls, seed_key)}, None


def assert_reference_within_cutoff():
    late = 0
    for path in (DATA / "relay_reference").glob("*.json"):
        doc = json.loads(path.read_text())
        for order in doc["orders"]:
            if parse_created(order["created"]) > CUTOFF:
                late += 1
    if late:
        raise SystemExit(f"reference archive has {late} orders after the cutoff; refusing to reuse it")


def main():
    raw_cls = json.loads((DATA / "classes.json").read_text())
    cls = {r: v["class"] for r, v in raw_cls.items()}
    kept, excluded = select_comparators()
    ok, detail = reference_control(REF_POP.read_text().split())
    if not ok:
        raise SystemExit(f"reference control failed: {detail}")
    assert_reference_within_cutoff()
    full = json.loads((ETUDE / "derived" / "results.json").read_text())
    ref = full["variants"]["primary"]["reference"]
    rows, skipped = [], Counter()
    for m in kept:
        result, why = run(m["condition"], m["wallets"], cls, m["condition"] + "|index_horizon")
        if result is None:
            skipped[why] += 1
            continue
        rows.append({**result, "question": m["question"], "cat": m["cat"], "T_utc": m["T_utc"]})
    out = {"amendment": "001-2026-11-19-collection-date", "cutoff_utc": CUTOFF.isoformat(),
           "excluded_at_selection": excluded, "exit_incomplete": dict(skipped),
           "reference_unchanged": True, "reference": ref, "comparators": rows,
           "verdict": verdict(ref, rows)}
    dest = ETUDE / "derived" / "index_horizon.json"
    dest.write_text(json.dumps(out, indent=1))
    enregistrer(str(ETUDE), test="S_INDEX_HORIZON", declare=True, n=out["verdict"]["n_comparators"],
                n_comparaisons=1 + len(rows), agent="amendement-001",
                params={"cutoff_utc": CUTOFF.isoformat(), "alpha": 0.01},
                stat=out["verdict"]["rate"], p=ref["p_M"], n_tirages=ref["draws"], n_hits=ref["hits"],
                sortie="derived/index_horizon.json",
                note="exploratory collection-date cutoff; primary verdict unchanged")
    print(json.dumps(out["verdict"], indent=1))


if __name__ == "__main__":
    main()
