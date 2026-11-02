#!/usr/bin/env python3
"""Tirage de l'échantillon de wallets AVANT toute mesure de performance.

Cadre : wallets de l'univers p8 avec au moins 3 trades preneurs (>= 100 $) sur des marchés TRAIN
(clos avant 03/2026). Critère d'activité seulement, aucun résultat ni activité future.
Tirage uniforme, graine fixe. Écrit data/echantillon.json : [{wallet, premier_trade_p8_ts}].
"""
import csv
import json
import os
import random

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAINE, TAILLE, SEUIL = 20261002, 2500, 3


def main():
    cadre = [r for r in csv.DictReader(open(os.path.join(ETUDE, "derived", "p8_wallets.csv")))
             if int(r["n_train"]) >= SEUIL]
    cadre.sort(key=lambda r: r["wallet"])          # ordre stable avant tirage
    tirage = random.Random(GRAINE).sample(cadre, TAILLE)
    sortie = [{"wallet": r["wallet"], "premier_trade_p8_ts": int(float(r["first_ts"]))} for r in tirage]
    json.dump({"graine": GRAINE, "taille_cadre": len(cadre), "seuil_n_train": SEUIL, "wallets": sortie},
              open(os.path.join(ETUDE, "data", "echantillon.json"), "w"), indent=0)
    print(f"cadre {len(cadre)}, tirés {len(sortie)}")


if __name__ == "__main__":
    main()
