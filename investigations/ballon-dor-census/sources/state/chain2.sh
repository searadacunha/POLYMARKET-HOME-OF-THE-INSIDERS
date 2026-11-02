#!/bin/zsh
cd ~/Projects/PolySentinel-ballon-dor-2026/code
export PYTHONDONTWRITEBYTECODE=1
export WALK_SKIP_DONE=1
echo "$(date -u) walk13" ; nice -n 12 python3 col_60_walk.py $(cat ../state/main13.txt)
echo "$(date -u) walk17" ; WALK_HOPS=2 WALK_NODES=15 WALK_TOP=5 WALK_RELAY_CAP=5 nice -n 12 python3 col_60_walk.py $(cat ../state/lookalikes17.txt)
echo "$(date -u) END"
