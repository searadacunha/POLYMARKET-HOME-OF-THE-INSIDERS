#!/bin/bash
# Phase 13 : paper trading de SIG_HIST V1 (PAPER ONLY, aucun ordre). Processus séparé des phases 11 et 12.
# Usage : nohup scripts/p13_run.sh >/dev/null 2>&1 &   ; arrêt : créer donnees/brut_p13/STOP puis pkill -f "Python p13_paper.py"
cd "$(dirname "$0")"
mkdir -p ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p13
LOG=~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p13/run_paper.log
while true; do
  echo "$(date -u +%FT%TZ) démarrage" >> "$LOG"
  caffeinate -is python3 p13_paper.py >> "$LOG" 2>&1
  echo "$(date -u +%FT%TZ) arrêt code $?" >> "$LOG"
  if [ -f ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p13/STOP ]; then exit 0; fi
  sleep 10
done
