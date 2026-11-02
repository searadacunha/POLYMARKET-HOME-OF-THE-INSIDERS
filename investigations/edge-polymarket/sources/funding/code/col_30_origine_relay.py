#!/usr/bin/env python3
"""Origine hors Polygon des dépôts arrivés par Relay, pour chaque wallet dont le graphe est collecté.

Pour le plus gros afflux de la racine venant du solveur Relay (0xf70da978) ou d'un contrat nommé Relay* (avant coupure) :
1. API Relay requests/v2?hash= : on garde la requête dont le destinataire est la racine (sinon « non apparié ») ;
   chaîne d'origine, jeton d'entrée, expéditeur d'origine.
2. Si la chaîne d'origine est Ethereum (1) ou Arbitrum (42161), un saut en amont via Etherscan V2 : afflux ERC-20 et
   natifs de l'expéditeur d'origine avant l'heure du dépôt, hub très actif si 1 000 transferts avant cette heure.
   Autres chaînes (BSC, Base, Solana…) : chaîne et expéditeur notés, amont non suivi (pas d'accès gratuit).
Écrit data/origine/<wallet>.json. Lève sur erreur persistante. Reprise automatique.
"""
import glob
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ETUDE, "data")
SOLVEUR = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
CHAINES_SUIVIES = {1, 42161}
PLAFOND_RELAY = 500   # sous-échantillon : les 500 premiers wallets financés par Relay dans l'ordre du tirage aléatoire
EK = [l.split("=", 1)[1].strip().strip('"').strip("'") for l in open(os.path.expanduser("~/Downloads/.env"))
      if l.startswith("ETHERSCAN_API_KEY=")][0]
COMPTE = {"relay_appels": 0, "relay_429": 0, "relay_sans_requete": 0, "relay_non_apparie": 0, "es_appels": 0,
          "es_limite": 0, "wallets": 0, "sans_depot_relay": 0}
_t = {"relay": 0.0, "es": 0.0}


class Refus429(Exception):
    pass


def http_json(url, cle, gap, compteur_429=None, essais=8, pause_429=15):
    for i in range(essais):
        attente = gap - (time.time() - _t[cle])
        if attente > 0:
            time.sleep(attente)
        _t[cle] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                if compteur_429:
                    COMPTE[compteur_429] += 1
                time.sleep(pause_429 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(5 * (i + 1))
    raise Refus429(f"échec répété : {url[:120]}")


def es(chainid, **p):
    p.update(chainid=chainid, apikey=EK)
    url = "https://api.etherscan.io/v2/api?" + urllib.parse.urlencode(p)
    for i in range(8):
        COMPTE["es_appels"] += 1
        d = http_json(url, "es", 0.4)
        msg, res = str(d.get("message", "")), d.get("result")
        if d.get("status") == "1":
            return res
        if msg.startswith("No transactions found") or msg.startswith("No records found"):
            return []
        if "rate limit" in str(res).lower() or "max calls" in str(res).lower():
            COMPTE["es_limite"] += 1
            time.sleep(2 * (i + 1))
            continue
        raise RuntimeError(f"Etherscan {chainid} {p.get('action')} {p.get('address')}: {msg} {str(res)[:150]}")
    raise RuntimeError("Etherscan : limite répétée")


def amont(chainid, adr, avant_ts):
    afflux, plein = [], False
    for action in ("tokentx", "txlist"):
        rows = es(chainid, module="account", action=action, address=adr, page=1, offset=1000, sort="asc")
        vus = [x for x in rows if int(x["timeStamp"]) < avant_ts]
        plein = plein or (len(rows) >= 1000 and int(rows[-1]["timeStamp"]) < avant_ts)
        for x in vus:
            if x["to"].lower() == adr and int(x["value"]) > 0:
                dec = int(x.get("tokenDecimal") or 18)
                afflux.append([int(x["timeStamp"]), x["from"].lower(), int(x["value"]) / 10 ** dec,
                               x.get("tokenSymbol") or "natif", x["hash"]])
    afflux.sort()
    return {"afflux": afflux, "hub_tres_actif": plein}


def main():
    os.makedirs(os.path.join(DATA, "origine"), exist_ok=True)
    ordre = [e["wallet"] for e in json.load(open(os.path.join(DATA, "echantillon.json")))["wallets"]]
    deja_interroges = sum(1 for f in glob.glob(os.path.join(DATA, "origine", "*.json"))
                          if (json.load(open(f)).get("depot") or {}).get("hash"))
    for w in ordre:
        fp = os.path.join(DATA, "graphe", w + ".json")
        if not os.path.exists(fp):
            continue
        g = json.load(open(fp))
        racine = g["noeuds"][0]
        sortie = os.path.join(DATA, "origine", g["racine"] + ".json")
        if os.path.exists(sortie) and "erreur" not in ((json.load(open(sortie)).get("depot")) or {}):
            continue
        COMPTE["wallets"] += 1
        relays = {n["adresse"] for n in g["noeuds"][1:] if "relay" in (n["contrat"].get("nom") or "").lower()} | {SOLVEUR}
        depots = [a for a in racine["afflux"] if a[1] in relays and (a[2] or 0) > 0]
        res = {"racine": g["racine"], "depot": None}
        if not depots:
            COMPTE["sans_depot_relay"] += 1
        elif deja_interroges >= PLAFOND_RELAY:
            res["depot"] = {"hors_sous_echantillon": True}
            COMPTE["hors_sous_echantillon"] = COMPTE.get("hors_sous_echantillon", 0) + 1
        else:
            deja_interroges += 1
            d = max(depots, key=lambda a: a[2])
            COMPTE["relay_appels"] += 1
            try:
                rep = http_json(f"https://api.relay.link/requests/v2?hash={d[4]}", "relay", 10.0, "relay_429",
                                essais=6, pause_429=30)
            except Refus429 as e:
                # échec écrit et compté, jamais avalé : la relance reprend ces fichiers
                COMPTE["relay_echec"] = COMPTE.get("relay_echec", 0) + 1
                res["depot"] = {"ts": d[0], "usd": d[2], "hash": d[4], "erreur": str(e)[:120]}
                with open(sortie + ".tmp", "w") as f:
                    json.dump(res, f)
                os.replace(sortie + ".tmp", sortie)
                continue
            reqs = rep.get("requests") or []
            q = next((r for r in reqs if (r.get("recipient") or "").lower() == g["racine"]), None)
            if not reqs:
                COMPTE["relay_sans_requete"] += 1
            elif q is None:
                COMPTE["relay_non_apparie"] += 1
            info = {"ts": d[0], "usd": d[2], "hash": d[4], "apparie": q is not None, "n_requetes": len(reqs)}
            if q:
                cin = q["data"].get("metadata", {}).get("currencyIn", {}).get("currency", {})
                info.update(chaine=cin.get("chainId"), jeton=cin.get("symbol"), expediteur=(q.get("user") or "").lower())
                if info["chaine"] in CHAINES_SUIVIES and info["expediteur"].startswith("0x"):
                    info["amont"] = amont(info["chaine"], info["expediteur"], d[0])
            res["depot"] = info
        with open(sortie + ".tmp", "w") as f:
            json.dump(res, f)
        os.replace(sortie + ".tmp", sortie)
        if COMPTE["wallets"] % 25 == 0:
            print(json.dumps(COMPTE), flush=True)
    json.dump(COMPTE, open(os.path.join(DATA, "origine.compte.json"), "w"))
    print("terminé", json.dumps(COMPTE))


if __name__ == "__main__":
    main()
