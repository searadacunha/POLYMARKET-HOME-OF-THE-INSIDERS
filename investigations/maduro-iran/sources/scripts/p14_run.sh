#!/bin/bash
# Phase 14 : journal papier des 2e achats (PAPER ONLY, aucun ordre). Processus séparé des phases 11 à 13.
# Usage : nohup scripts/p14_run.sh >/dev/null 2>&1 &   ; arrêt : créer donnees/brut_p14/STOP puis pkill -f "Python p14_paper.py"
cd "$(dirname "$0")"
mkdir -p ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p14
LOG=~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p14/run_paper.log
while true; do
  echo "$(date -u +%FT%TZ) démarrage" >> "$LOG"
  caffeinate -is python3 p14_paper.py >> "$LOG" 2>&1
  echo "$(date -u +%FT%TZ) arrêt code $?" >> "$LOG"
  if [ -f ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p14/STOP ]; then exit 0; fi
  sleep 10
done
