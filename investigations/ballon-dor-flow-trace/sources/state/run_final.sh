export PYTHONDONTWRITEBYTECODE=1
cd ~/Projects/PolySentinel-flow-trace
python3 -u tools/walk.py | tail -1
python3 -u tools/pairs.py
python3 -u tools/bridges.py | head -1
python3 -u tools/reconcile.py | tail -1 | cut -c1-120
python3 -u tools/followups.py > state/followups.log 2>&1
python3 -u tools/build_data.py
python3 -u tools/verify.py
python3 -u tools/build_reports.py
python3 -u tests/test_forensics.py > state/test_forensics.log 2>&1
tail -1 state/test_forensics.log
grep -E "^FAIL" state/test_forensics.log | cut -c1-200
python3 -u tests/test_claims.py > state/test_claims.log 2>&1
tail -12 state/test_claims.log | cut -c1-100
echo FINAL_FINISHED
