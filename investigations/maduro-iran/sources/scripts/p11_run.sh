#!/bin/bash
# Phase 11 : lance et relance (en cas d'arrêt anormal) le collecteur ou le listener. Recherche uniquement, aucun ordre.
# Usage : nohup scripts/p11_run.sh collector|listener &   (détaché ; caffeinate empêche la mise en veille)
cd "$(dirname "$0")"
mkdir -p ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p11/meta
LOG=~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p11/meta/run_$1.log
while true; do
  echo "$(date -u +%FT%TZ) démarrage $1" >> "$LOG"
  if [ "$1" = "collector" ]; then caffeinate -is python3 p11_clob_collector.py >> "$LOG" 2>&1; fi
  if [ "$1" = "listener" ]; then caffeinate -is python3 p11_signal_listener.py >> "$LOG" 2>&1; fi
  code=$?
  echo "$(date -u +%FT%TZ) arrêt $1 code $code" >> "$LOG"
  if [ -f ~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p11/meta/STOP ]; then exit 0; fi
  sleep 10
done
