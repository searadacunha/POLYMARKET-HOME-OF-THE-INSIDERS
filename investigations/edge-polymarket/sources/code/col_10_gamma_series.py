#!/usr/bin/env python3
"""Liste tous les marchés fermés d'une série Gamma (crypto Up/Down) et écrit data/raw/gamma_<serie>.jsonl.

Une ligne par marché, champs bruts utiles : condition, jetons, issues, prix de résolution, horaires, frais.
Lève toute erreur réseau ou de format ; compte demandés / reçus / vides / 429 dans data/raw/gamma_<serie>.compte.json.

    python3 col_10_gamma_series.py 10114 btc_hourly
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ETUDE, "data", "raw")
UA = "edge-polymarket-recherche/1.0"
PAGE = 100  # Gamma plafonne à 100 par page même si on demande plus

CHAMPS = ["conditionId", "clobTokenIds", "outcomes", "outcomePrices", "eventStartTime", "endDate", "closedTime",
          "startDate", "volumeNum", "feesEnabled", "feeType", "takerBaseFee", "makerBaseFee", "question", "slug",
          "umaResolutionStatus", "orderPriceMinTickSize", "orderMinSize"]


def get(url, compte, essais=6):
    for i in range(essais):
        compte["demandes"] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                compte["429_ou_5xx"] += 1
                time.sleep(2 ** i)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            compte["erreurs_reseau"] += 1
            time.sleep(2 ** i)
    raise RuntimeError(f"échec après {essais} essais : {url}")


def main():
    serie, nom = sys.argv[1], sys.argv[2]
    compte = {"demandes": 0, "429_ou_5xx": 0, "erreurs_reseau": 0, "pages": 0, "evenements": 0,
              "marches": 0, "evenements_sans_marche": 0, "evenements_multi_marches": 0}
    sortie = os.path.join(RAW, f"gamma_{nom}.jsonl")
    vus = set()
    # Gamma refuse offset > 10 000 : on découpe par mois de endDate, chaque mois fait moins de 1 000 événements.
    mois = [(a, m) for a in (2025, 2026) for m in range(1, 13) if (2025, 5) <= (a, m) <= (2026, 10)]
    with open(sortie + ".tmp", "w") as f:
        for a, m in mois:
            debut = f"{a}-{m:02d}-01T00:00:00Z"
            a2, m2 = (a + 1, 1) if m == 12 else (a, m + 1)
            fin = f"{a2}-{m2:02d}-01T00:00:00Z"
            offset = 0
            while True:
                url = (f"https://gamma-api.polymarket.com/events?series_id={serie}&closed=true&limit={PAGE}"
                       f"&offset={offset}&order=endDate&ascending=true&end_date_min={debut}&end_date_max={fin}")
                page = get(url, compte)
                if not isinstance(page, list):
                    raise RuntimeError(f"réponse inattendue {debut} offset={offset}: {str(page)[:200]}")
                compte["pages"] += 1
                if not page:
                    break
                for ev in page:
                    compte["evenements"] += 1
                    ms = ev.get("markets") or []
                    if not ms:
                        compte["evenements_sans_marche"] += 1
                    if len(ms) > 1:
                        compte["evenements_multi_marches"] += 1
                    for mk in ms:
                        cid = mk.get("conditionId")
                        if not cid or cid in vus:
                            continue
                        vus.add(cid)
                        ligne = {k: mk.get(k) for k in CHAMPS}
                        ligne["event_slug"] = ev.get("slug")
                        f.write(json.dumps(ligne) + "\n")
                        compte["marches"] += 1
                # Avancer du nombre REÇU : avancer de PAGE sautait silencieusement des marchés (bug du 02/10).
                offset += len(page)
                if offset >= 9800:
                    raise RuntimeError(f"mois {debut} trop gros pour la pagination par offset")
                time.sleep(0.3)
            print(f"  {debut[:7]} : {compte['marches']} marchés cumulés", flush=True)
    os.replace(sortie + ".tmp", sortie)
    with open(os.path.join(RAW, f"gamma_{nom}.compte.json"), "w") as f:
        json.dump(compte, f, indent=1)
    print(json.dumps(compte))


if __name__ == "__main__":
    main()
