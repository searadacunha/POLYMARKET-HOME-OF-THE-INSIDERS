#!/usr/bin/env python3
"""Bougies 1 minute Binance spot (API publique, sans clé) sur toute la période d'étude.

Écrit data/raw/binance_<SYMBOLE>_1m.csv : open_time_ms,open,high,low,close,volume,close_time_ms,n_trades.
Vérifie la continuité (une bougie par minute) et compte les trous. Lève toute erreur réseau persistante.

    python3 col_20_binance_klines.py BTCUSDT
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ETUDE, "data", "raw")
DEBUT_MS = 1748390400000   # 2025-05-28 00:00 UTC
FIN_MS = 1791072000000     # 2026-10-04 00:00 UTC


def get(url, compte, essais=6):
    for i in range(essais):
        compte["demandes"] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "edge-recherche/1.0"}),
                                        timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (418, 429) or e.code >= 500:
                compte["429_ou_5xx"] += 1
                time.sleep(5 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            compte["erreurs_reseau"] += 1
            time.sleep(2 ** i)
    raise RuntimeError(f"échec : {url}")


def main():
    sym = sys.argv[1]
    compte = {"demandes": 0, "429_ou_5xx": 0, "erreurs_reseau": 0, "bougies": 0, "minutes_manquantes": 0}
    sortie = os.path.join(RAW, f"binance_{sym}_1m.csv")
    t, precedent = DEBUT_MS, None
    with open(sortie + ".tmp", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["open_time_ms", "open", "high", "low", "close", "volume", "close_time_ms", "n_trades"])
        while t < FIN_MS:
            url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1m&startTime={t}&limit=1000"
            lot = get(url, compte)
            if not lot:
                break
            for k in lot:
                ot = int(k[0])
                if ot >= FIN_MS:
                    break
                if precedent is not None and ot != precedent + 60000:
                    compte["minutes_manquantes"] += (ot - precedent) // 60000 - 1
                w.writerow([ot, k[1], k[2], k[3], k[4], k[5], k[6], k[8]])
                compte["bougies"] += 1
                precedent = ot
            t = int(lot[-1][0]) + 60000
            time.sleep(0.12)
    os.replace(sortie + ".tmp", sortie)
    with open(os.path.join(RAW, f"binance_{sym}_1m.compte.json"), "w") as f:
        json.dump(compte, f, indent=1)
    print(sym, json.dumps(compte))


if __name__ == "__main__":
    main()
