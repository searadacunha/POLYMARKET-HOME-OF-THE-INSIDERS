#!/bin/sh
# Continuation of the data pipeline, one step after the other. No step reads an outcome. Every collector is resumable:
# run this script again after an interruption. Progress: logs/chain.log and the log of each step.
cd "$(dirname "$0")/.." || exit 1
PY="python3 -I"
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*"; }
log "chain started"
while ps -Ao command | grep -q "[c]ol_20_fills.py all"; do sleep 30; done      # the pass already running
log "col_20 all: $(tail -1 logs/col_20_all.log)"
$PY code/col_20_fills.py all >> logs/col_20_all.log 2>&1; log "col_20 all, retry of failed markets: exit $?"
$PY code/feat_20_entries.py > logs/feat_20.log 2>&1 || { log "feat_20 failed, chain stopped"; exit 1; }
log "feat_20 done"
$PY code/col_30_activity.py >> logs/col_30.log 2>&1; log "col_30: exit $?"
$PY code/col_31_asof.py > logs/col_31.log 2>&1; log "col_31 (first real run, a failure does not stop the chain): exit $?"
$PY code/feat_30_wallet.py > logs/feat_30.log 2>&1 || { log "feat_30 failed, chain stopped"; exit 1; }
log "feat_30 done"
$PY code/col_40_funding.py > logs/col_40.log 2>&1; log "col_40: exit $?"
$PY code/feat_40_groups.py > logs/feat_40.log 2>&1; log "feat_40: exit $?"
$PY code/col_20_fills.py taker > logs/col_20_taker_universe.log 2>&1; log "col_20 taker: exit $?"
log "chain done"
