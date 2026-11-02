#!/usr/bin/env python3
"""Historique de prix minute (CLOB /prices-history, fidelity=1) du jeton « Up » de chaque marché d'une série.

Fenêtre : [eventStartTime - 10 min, endDate + 2 min]. Écrit data/raw/ph_<serie>.jsonl (une ligne par marché,
reprise possible : les marchés déjà écrits sont sautés). Compte demandés / reçus / vides / 429 / erreurs.

    python3 col_30_prices_history.py btc_hourly
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ETUDE, "data", "raw")


def ts(iso):
    return int(dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def get(url, compte, essais=6):
    for i in range(essais):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "edge-recherche/1.0"}),
                                        timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                compte["429_ou_5xx"] += 1
                time.sleep(3 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            compte["erreurs_reseau"] += 1
            time.sleep(2 ** i)
    raise RuntimeError(f"échec : {url}")


def main():
    nom = sys.argv[1]
    marches = [json.loads(l) for l in open(os.path.join(RAW, f"gamma_{nom}.jsonl"))]
    sortie = os.path.join(RAW, f"ph_{nom}.jsonl")
    faits = set()
    if os.path.exists(sortie):
        faits = {json.loads(l)["conditionId"] for l in open(sortie)}
    a_faire = [m for m in marches if m["conditionId"] not in faits and m.get("eventStartTime")]
    compte = {"a_faire": len(a_faire), "deja": len(faits), "recus": 0, "vides": 0, "429_ou_5xx": 0,
              "erreurs_reseau": 0, "sans_eventStartTime": sum(1 for m in marches if not m.get("eventStartTime"))}
    print(json.dumps(compte), flush=True)

    def un(m):
        tok_up = json.loads(m["clobTokenIds"])[json.loads(m["outcomes"]).index("Up")]
        a, b = ts(m["eventStartTime"]) - 600, ts(m["endDate"]) + 120
        url = f"https://clob.polymarket.com/prices-history?market={tok_up}&startTs={a}&endTs={b}&fidelity=1"
        d = get(url, compte)
        if "history" not in d:
            raise RuntimeError(f"réponse sans history pour {m['conditionId']}: {str(d)[:200]}")
        time.sleep(0.4)
        return {"conditionId": m["conditionId"], "token_up": tok_up, "history": d["history"]}

    with open(sortie, "a") as f, ThreadPoolExecutor(3) as pool:
        for i, r in enumerate(pool.map(un, a_faire)):
            compte["recus"] += 1
            compte["vides"] += not r["history"]
            f.write(json.dumps(r) + "\n")
            if i % 500 == 0:
                f.flush()
                print(f"  {i}/{len(a_faire)} vides={compte['vides']} 429={compte['429_ou_5xx']}", flush=True)
    with open(os.path.join(RAW, f"ph_{nom}.compte.json"), "w") as f:
        json.dump(compte, f, indent=1)
    print(json.dumps(compte))


if __name__ == "__main__":
    main()
