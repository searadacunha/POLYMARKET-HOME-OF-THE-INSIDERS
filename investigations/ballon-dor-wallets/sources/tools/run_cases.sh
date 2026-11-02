#!/bin/zsh
# One wallet at a time, one checkpoint per wallet: a stopped run resumes from the cache.
cd ~/Projects/PolySentinel-investigation
PY=~/Projects/PolySentinel/.venv/bin/python
export SIGNAL_ENGINE_STATE="$PWD/state/fund_flow_engine" PYTHONDONTWRITEBYTECODE=1
for s in "$@"; do
  [ -f "state/done_$s" ] && continue
  addr=$($PY -I -c "import sys;sys.path.insert(0,'tools');import identities as I;print((I.IDS.get('$s') or dict(address=I.NOT_HIGHLIGHTED.get('$s')))['address'])")
  ( cd ~/Projects/PolySentinel && $PY -m signal_engine.fund_flow.trace "$addr" --pages 8 --rpc 250 --http 30 --out ~/Projects/PolySentinel-investigation/evidence/traces/$s.json ) || { echo "$s trace failed"; continue; }
  $PY -I -u tools/case_build.py "$s" || { echo "$s build failed"; continue; }
  $PY -I -u tools/case_chain.py "$s" || { echo "$s chain failed"; continue; }
  $PY -I tools/case_report.py "$s" && touch "state/done_$s"
done
echo finished
