#!/bin/sh
# Third pass, after the pre-freeze code audit of 14 November 2026 (audit/sfh_collecteurs_20261114.txt). No step reads an outcome.
# feat_30 pass 1 (activity rows only) ran by hand at 14:17:12 UTC and wrote derived/inflow_todo.jsonl; col_41 was started by hand at
# 14:17:33 UTC. This chain was started at 14:20:08 UTC and STOPPED at about 15:12 UTC while it was still waiting for col_41: none of its
# steps ran. The second pre-freeze audit (audit/sfh2_code_corrige_20261114.txt, audit/protocole_avant_gel_20261114.txt,
# audit/fuites_avant_gel_20261114.txt) led to the corrections listed in code/PROVENANCE.md; the steps were then run by run_40_chain.sh.
cd "$(dirname "$0")/.." || exit 1
PY="python3 -I"
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*" >> logs/chain.log; }
log "chain 3 started"
while pgrep -f "code/col_41_inflows.py" > /dev/null; do sleep 30; done
$PY code/col_41_inflows.py >> logs/col_41.log 2>&1; log "col_41 (resume, retries errors): exit $?"
$PY code/feat_30_wallet.py >> logs/feat_30.log 2>&1; log "feat_30 pass 2 (chain inflows merged): exit $?"
$PY code/col_40_funding.py >> logs/col_40.log 2>&1; log "col_40 (new deposits and chain inflows): exit $?"
$PY code/feat_40_groups.py >> logs/feat_40.log 2>&1; log "feat_40: exit $?"
log "chain 3 done"
