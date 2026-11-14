#!/bin/sh
# Fourth pass, after the second pre-freeze audit (code/PROVENANCE.md). No step reads an outcome. Stops at the first failure.
# Already run by hand on 14 November 2026 (end times): feat_10 15:14:20, feat_20 15:15:47, feat_30 pass 1 15:19:45 UTC; col_41 log reading
# started at 14:17:33 UTC on the list of that time (19,104 windows, of which the 18,780 of the current list).
cd "$(dirname "$0")/.." || exit 1
PY="python3 -I"
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*" >> logs/chain.log; }
step() { name=$1; shift; "$@"; rc=$?; log "$name: exit $rc"; [ $rc -eq 0 ] || { log "chain 4 stopped at $name"; exit $rc; }; }
log "chain 4 started"
while pgrep -f "code/col_41_inflows.py" > /dev/null; do sleep 30; done
step "col_41 (windows of the current list, pUSD mints, senders)" sh -c "$PY code/col_41_inflows.py >> logs/col_41.log 2>&1"
step "feat_30 pass 2 (chain inflows merged)" sh -c "$PY code/feat_30_wallet.py >> logs/feat_30.log 2>&1"
step "col_40 (deposits and chain inflows of the current list)" sh -c "$PY code/col_40_funding.py >> logs/col_40.log 2>&1"
step "feat_40" sh -c "$PY code/feat_40_groups.py >> logs/feat_40.log 2>&1"
log "chain 4 done"
