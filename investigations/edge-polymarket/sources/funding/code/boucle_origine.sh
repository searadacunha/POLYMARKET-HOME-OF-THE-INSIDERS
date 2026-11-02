#!/bin/bash
# Relance col_30 tant que la collecte des graphes tourne, puis une dernière fois.
cd "$(dirname "$0")"
while pgrep -f "col_20_graphe_financement.py" >/dev/null; do
  pgrep -f "col_30_origine_relay.py" >/dev/null || python3 col_30_origine_relay.py >> ../data/col_30.log 2>&1
  sleep 60
done
while pgrep -f "col_30_origine_relay.py" >/dev/null; do sleep 30; done
python3 col_30_origine_relay.py >> ../data/col_30.log 2>&1
echo "boucle terminée $(date)" >> ../data/col_30.log
