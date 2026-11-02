#!/usr/bin/env python3
"""Étiquettes publiques des explorateurs (titre de page PolygonScan / Etherscan / Arbiscan) pour les adresses qui
comptent dans les graphes : hubs très actifs, contrats, adresses vues chez >= 3 wallets,
expéditeurs d'origine Relay et leurs financeurs amont (Ethereum, Arbitrum).

Une étiquette = le nom affiché en titre de page (« OKX 1 | Address: 0x… | PolygonScan »). Sans nom : « aucune ».
Une page toutes les 3 s. Écrit data/etiquettes_publiques.json {chaine:adresse: {nom, url, date}}. Reprise automatique.
"""
import collections
import glob
import json
import os
import re
import time
import urllib.error
import urllib.request

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ETUDE, "data")
SITES = {137: "https://polygonscan.com/address/", 1: "https://etherscan.io/address/", 42161: "https://arbiscan.io/address/"}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"


def candidats():
    freq = collections.Counter()
    for fp in glob.glob(os.path.join(DATA, "graphe", "*.json")):
        g = json.load(open(fp))
        racine = g["noeuds"][0]["adresse"]
        vus = set()
        for n in g["noeuds"][1:]:
            vus.add(n["adresse"])
        for n in g["noeuds"]:
            if n["hub_tres_actif"] or (n["contrat"].get("verifie") and n["profondeur"] > 0
                                       and n["contrat"].get("nom") not in ("GnosisSafeProxy", "ProxyWallet")):
                continue  # les fournisseurs d'un hub ou d'un contrat ne disent rien du wallet étudié
            for a in n["afflux"]:
                vus.add(a[1])
        vus.discard(racine)
        for a in vus:
            freq[(137, a)] += 1
    for fp in glob.glob(os.path.join(DATA, "origine", "*.json")):
        d = (json.load(open(fp)).get("depot")) or {}
        ch, ex = d.get("chaine"), d.get("expediteur")
        if ch in (1, 42161) and ex:
            freq[(ch, ex)] += 2   # toujours retenu
            for a in (d.get("amont") or {}).get("afflux", []):
                freq[(ch, a[1])] += 1
    # hubs très actifs et contrats toujours ; les autres adresses seulement si elles reviennent chez >= 3 wallets
    # (un wallet personnel n'a pas d'étiquette publique, inutile de le visiter)
    hubs = set()
    for fp in glob.glob(os.path.join(DATA, "graphe", "*.json")):
        for n in json.load(open(fp))["noeuds"][1:]:
            if n["hub_tres_actif"] or n["contrat"].get("verifie"):
                hubs.add((137, n["adresse"]))
    return sorted({k for k, v in freq.items() if v >= 3} | hubs)


def titre(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                t = r.read(400_000).decode("utf-8", "replace")
            m = re.search(r"<title>\s*(.*?)\s*</title>", t, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):
                time.sleep(20 * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (i + 1))
    return None  # échec noté explicitement


def main():
    fichier = os.path.join(DATA, "etiquettes_publiques.json")
    deja = json.load(open(fichier)) if os.path.exists(fichier) else {}
    liste = [c for c in candidats() if f"{c[0]}:{c[1]}" not in deja or deja[f"{c[0]}:{c[1]}"]["nom"] is None]
    print(f"{len(liste)} adresses à étiqueter ({len(deja)} déjà faites)", flush=True)
    for i, (ch, adr) in enumerate(liste):
        url = SITES[ch] + adr
        t = titre(url)
        nom = None if t is None else ("aucune" if (not t or t.lower().startswith("address") or t.startswith("0x")
                                                   or " | " not in t) else t.split(" | ")[0].strip())
        deja[f"{ch}:{adr}"] = {"nom": nom, "titre": t, "url": url, "date": time.strftime("%Y-%m-%d")}
        if i % 20 == 0:
            json.dump(deja, open(fichier, "w"), indent=0)
            print(f"  {i}/{len(liste)}", flush=True)
        time.sleep(3)
    json.dump(deja, open(fichier, "w"), indent=0)
    noms = collections.Counter(v["nom"] for v in deja.values())
    print("terminé :", len(deja), "adresses ;", sum(1 for v in deja.values() if v["nom"] not in (None, "aucune")),
          "avec étiquette ;", noms.get(None, 0), "échecs")


if __name__ == "__main__":
    main()
