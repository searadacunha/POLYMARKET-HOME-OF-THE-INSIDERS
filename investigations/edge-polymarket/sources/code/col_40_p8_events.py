#!/usr/bin/env python3
"""Identifiant d'événement Gamma de chaque marché de l'univers p8 (pour grouper les marchés liés d'un même événement).

Lit l'univers p8 de l'enquête Maduro/Iran (lecture seule) et écrit data/raw/p8_events.json {conditionId: event_id}.
Lève si un marché n'est pas retrouvé ; compte demandés / trouvés / sans événement.
"""
import json
import os
import time
import urllib.parse
import urllib.request

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P8 = os.path.expanduser("~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8/universe.json")


def main():
    u = json.load(open(P8))
    cids = [m["conditionId"] for m in u]
    out, compte = {}, {"demandes": 0, "trouves": 0, "sans_evenement": 0}
    for i in range(0, len(cids), 20):
        lot = cids[i:i + 20]
        q = "&".join("condition_ids=" + urllib.parse.quote(c) for c in lot)
        url = f"https://gamma-api.polymarket.com/markets?{q}&closed=true&limit=100"
        compte["demandes"] += 1
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "edge-recherche/1.0"}),
                                    timeout=30) as r:
            d = json.loads(r.read())
        for m in d:
            evs = m.get("events") or []
            if evs:
                out[m["conditionId"]] = {"event_id": evs[0].get("id"), "event_slug": evs[0].get("slug")}
                compte["trouves"] += 1
            else:
                compte["sans_evenement"] += 1
        time.sleep(0.3)
    manquants = [c for c in cids if c not in out]
    compte["manquants"] = len(manquants)
    json.dump(out, open(os.path.join(ETUDE, "data", "raw", "p8_events.json"), "w"))
    print(json.dumps(compte))
    if len(manquants) > 0.02 * len(cids):
        raise RuntimeError(f"{len(manquants)} marchés sans événement retrouvé")


if __name__ == "__main__":
    main()
