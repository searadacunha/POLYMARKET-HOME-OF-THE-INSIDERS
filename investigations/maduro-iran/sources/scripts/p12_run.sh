#!/bin/bash
# Phase 12 : journal PAPER ONLY du détecteur sans wallet (aucun ordre). Processus séparé de la phase 11.
# Usage : nohup scripts/p12_run.sh >/dev/null 2>&1 &   ; arrêt : créer donnees/brut_p12/STOP puis pkill -f "Python p12_live.py"
cd "$(dirname "$0")"
mkdir -p ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p12
LOG=~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p12/run_live.log
while true; do
  echo "$(date -u +%FT%TZ) démarrage" >> "$LOG"
  caffeinate -is python3 p12_live.py >> "$LOG" 2>&1
  echo "$(date -u +%FT%TZ) arrêt code $?" >> "$LOG"
  if [ -f ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p12/STOP ]; then exit 0; fi
  sleep 10
done
