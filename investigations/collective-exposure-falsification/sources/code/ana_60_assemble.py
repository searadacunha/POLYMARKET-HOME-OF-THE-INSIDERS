#!/usr/bin/env python3
"""Assemble STATISTICAL_RESULTS.json from the study outputs. Computes nothing new: every number is copied from a
file written by ana_50 / feat_30 / col_30 / ctl_45, with that file's sha256.

usage: ana_60_assemble.py OUT.json
"""
import hashlib
import json
import os
import sys

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {
    "coverage_and_units": "out/base/stats.json",
    "funding_counts": "out/funding/funding.json",
    "models_train": "out/models/models_train.json",
    "models_trainvalid": "out/models/models_trainvalid.json",
    "valid": "out/models/results_valid.json",
    "test": "out/models/results_test.json",
    "sensitivity_test": "out/models/sensitivity_test.json",
    "nullgate": "out/models/nullgate.json",
    "controls": "controles/summary.json",
    "verdict": "out/models/verdict.json",
}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    out, prov = {}, {}
    for k, rel in SRC.items():
        p = os.path.join(ETUDE, rel)
        if not os.path.exists(p):
            out[k] = {"status": "MISSING", "file": rel}
            continue
        d = json.load(open(p))
        if k == "funding_counts":
            d = {"counts": d["counts"], "window": d.get("window")}
        if k in ("models_train", "models_trainvalid"):
            d = {kk: v for kk, v in d.items() if kk != "models"} | {
                "converged": {m: v.get("converged") for m, v in d["models"].items()},
                "n_coefficients": {m: len(v["beta"]) for m, v in d["models"].items()}}
        out[k] = d
        prov[k] = {"file": rel, "sha256": sha(p)}
    lock = os.path.join(ETUDE, "PROTOCOL.lock")
    out["provenance"] = prov
    out["protocol_lock_sha256"] = sha(lock) if os.path.exists(lock) else None
    json.dump(out, open(sys.argv[1], "w"), indent=1, sort_keys=True, default=float)
    print(json.dumps({k: (v.get("status") if isinstance(v, dict) else None) for k, v in out.items()
                      if isinstance(v, dict) and v.get("status") == "MISSING"}))


if __name__ == "__main__":
    main()
