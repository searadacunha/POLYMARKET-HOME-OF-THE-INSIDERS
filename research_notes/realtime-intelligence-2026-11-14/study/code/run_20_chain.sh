#!/bin/sh
# Second pass after the 16 markets were read and the funding reader was extended. No step reads an outcome. Resumable.
cd "$(dirname "$0")/.." || exit 1
PY="python3 -I"
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*"; }
log "chain 2 started"
# feat_20 and col_30 already ran on the full universe at 12:27 UTC on 14 November 2026 (logs/chain.log)
# col_31 and feat_30 ran at 12:41 UTC on 14 November 2026 (logs/chain.log)
$PY code/col_40_funding.py > logs/col_40.log 2>&1; log "col_40: exit $?"
$PY code/feat_40_groups.py > logs/feat_40.log 2>&1; log "feat_40: exit $?"
log "chain 2 done"
