#!/bin/zsh
cd ~/Projects/PolySentinel-ballon-dor-2026/code
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f col_50_relay >/dev/null; do sleep 20; done
echo "$(date -u) wallets" ; nice -n 12 python3 col_40_wallets.py | tail -18 | cut -c1-150
echo "$(date -u) relay2" ; nice -n 12 python3 col_50_relay.py | tail -2 | cut -c1-100
echo "$(date -u) ledger" ; nice -n 12 python3 ana_20_ledger.py | wc -l
echo "$(date -u) walk13" ; nice -n 12 python3 col_60_walk.py $(cat ../state/main13.txt)
echo "$(date -u) walk17" ; WALK_HOPS=2 WALK_NODES=15 WALK_TOP=5 nice -n 12 python3 col_60_walk.py $(cat ../state/lookalikes17.txt)
echo "$(date -u) END"
