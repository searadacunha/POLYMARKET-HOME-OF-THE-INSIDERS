#!/usr/bin/env python3
"""Échantillon ciblé ChangeNOW (analysis_plan.md, si ECH < 30 dans le tirage aléatoire).

Pour chaque adresse ChangeNOW de data/etiquettes.json (étiquette publique, et f2020 « fortement compatible », noté à
part) : tous ses envois ERC-20 sur Polygon (pagination par bloc), destinataires = comptes de trading de l'univers p8
qui reçoivent un envoi AVANT leur premier trade p8. Population définie par le financement seul.
Écrit data/cible_changenow.json : [{wallet, premier_trade_p8_ts, envois: [[ts, hub, usd, hash]], preuve}].
Lève sur toute erreur Etherscan persistante.
"""
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import col_20_graphe_financement as c20  # noqa: E402  (même accès Etherscan, même limiteur, mêmes jetons stables)

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def envois_hub(hub):
    """Tous les transferts ERC-20 sortants du hub, par pages de 10 000, découpées par bloc."""
    out, debut = [], 0
    while True:
        r = c20.es(module="account", action="tokentx", address=hub, startblock=debut, endblock=99999999,
                   page=1, offset=10000, sort="asc")
        out += r
        if len(r) < 10000:
            break
        debut = int(r[-1]["blockNumber"])
        out = [x for x in out if int(x["blockNumber"]) < debut]   # le dernier bloc est repris en entier
        print(f"  {hub[:10]} : {len(out)} transferts, bloc {debut}", flush=True)
    vus, ded = set(), []
    for x in out:
        k = (x["hash"], x.get("logIndex"), x["to"], x["value"])
        if k not in vus:
            vus.add(k)
            ded.append(x)
    return [x for x in ded if x["from"].lower() == hub]


def main():
    etiq = json.load(open(os.path.join(ETUDE, "data", "etiquettes.json")))["etiquettes"]
    hubs = {a: v for a, v in etiq.items() if v["famille"] == "echange_instantane" and "ChangeNOW" in v["entite"]
            and v["preuve"] in ("observe_etiquette_publique", "fortement_compatible")}
    premier = {r["wallet"]: int(float(r["first_ts"])) for r in csv.DictReader(open(os.path.join(ETUDE, "derived", "p8_wallets.csv")))}
    cible = {}
    compte = {"hubs": len(hubs), "envois": 0, "destinataires": 0, "dans_p8": 0, "avant_premier_trade": 0}
    for hub, v in hubs.items():
        rows = envois_hub(hub)
        compte["envois"] += len(rows)
        dest = {}
        for x in rows:
            dest.setdefault(x["to"].lower(), []).append(x)
        compte["destinataires"] += len(dest)
        for w, xs in dest.items():
            if w not in premier:
                continue
            compte["dans_p8"] += 1
            avant = [x for x in xs if int(x["timeStamp"]) < premier[w]]
            if not avant:
                continue
            compte["avant_premier_trade"] += 1
            e = cible.setdefault(w, {"wallet": w, "premier_trade_p8_ts": premier[w], "envois": [], "preuves": set()})
            for x in avant:
                sym = c20.STABLES.get(x["contractAddress"].lower())
                usd = int(x["value"]) / 10 ** int(x["tokenDecimal"]) if sym else None
                e["envois"].append([int(x["timeStamp"]), hub, usd, x["hash"]])
            e["preuves"].add(v["preuve"])
        print(f"{v['entite']} : {len(rows)} envois, {len(dest)} destinataires", flush=True)
    sortie = []
    for e in cible.values():
        e["preuve"] = "observe_etiquette_publique" if "observe_etiquette_publique" in e["preuves"] else "fortement_compatible"
        del e["preuves"]
        sortie.append(e)
    json.dump({"compte": compte, "wallets": sortie}, open(os.path.join(ETUDE, "data", "cible_changenow.json"), "w"))
    print(json.dumps(compte))


if __name__ == "__main__":
    main()
