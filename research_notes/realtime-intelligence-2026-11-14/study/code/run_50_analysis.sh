#!/bin/sh
# The analysis, in order, on the frozen table. Entry point of the computation and of its reproduction.
#   ana_50  every declared test, then one registry line per test
#   ana_90  the verdict of each class, by code
#   ana_70  what the classes say on the documented cases (a listing, no test)
#   ana_95  the small tables that let anybody recompute the results (no wallet address)
#   ana_96  the two reference files of the live engine
#   ana_97  the funding links that involve more than one wallet, with their evidence (reads no outcome)
set -e
cd "$(dirname "$0")/.."
python3 -I code/ana_50_tests.py > derived/ana_50.log
python3 -I code/ana_90_verdict.py > derived/ana_90.log
python3 -I code/ana_70_cases.py > derived/ana_70.log
python3 -I code/ana_95_export.py > derived/ana_95.log
python3 -I code/ana_96_engine_reference.py > derived/ana_96.log
python3 -I code/ana_97_links.py > derived/ana_97.log
echo "analysis done"
