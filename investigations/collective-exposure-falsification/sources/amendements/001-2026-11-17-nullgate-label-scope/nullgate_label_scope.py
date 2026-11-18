#!/usr/bin/env python3
"""Amendment 001 (2026-11-17): run the frozen `ana_50_models.py nullgate` stage unchanged, except that the label
lookup covers every hold-out TEST market instead of only the markets that have an observed TEST unit.
Null panels (day-shifted fills) create COL units in TEST markets that had no observed unit; the frozen lookup
refused them ("9 units without a label"). No other line of the stage changes. TEST labels only.

usage: nullgate_label_scope.py <same arguments as `ana_50_models.py nullgate`> --holdout derived/holdout_markets.jsonl
"""
import json
import os
import sys

ETUDE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ETUDE, "code"))
import ana_50_models as A  # noqa: E402  frozen, unchanged

holdout = sys.argv[sys.argv.index("--holdout") + 1]
TEST_CIDS = {json.loads(l)["condition_id"].lower() for l in open(holdout) if json.loads(l)["split"] == "TEST"}
_frozen = A.load_labels
A.load_labels = lambda path, cids: _frozen(path, set(cids) | TEST_CIDS)
assert len(TEST_CIDS) == 1234, len(TEST_CIDS)
A.main()
