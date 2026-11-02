export PYTHONDONTWRITEBYTECODE=1
cd ~/Projects/PolySentinel-flow-trace
until grep -q FINAL_FINISHED state/run_final.log; do sleep 10; done
python3 -u tools/verify.py > state/verify2.log 2>&1
python3 -u tools/build_reports.py > state/reports.log 2>&1
python3 -u tests/test_forensics.py > state/test_forensics.log 2>&1
python3 -u tests/test_claims.py > state/test_claims.log 2>&1
tail -3 state/verify2.log | cut -c1-120
tail -12 state/test_forensics.log | cut -c1-200
tail -40 state/test_claims.log | cut -c1-120
