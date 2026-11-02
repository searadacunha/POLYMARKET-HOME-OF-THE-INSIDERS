#!/usr/bin/env python3
"""Graphe de provenance des fonds (Polygon, jetons ERC-20) de chaque wallet de l'échantillon, sur 3 sauts.

Règles (fixées avant toute mesure) :
- Nœud racine = compte de trading Polymarket ; coupure = son premier trade p8 (seuls les afflux ANTÉRIEURS comptent).
- Afflux = transfert ERC-20 entrant de valeur > 0, hors contrats de trading Polymarket. Valeur en $ seulement pour
  les stablecoins (USDC.e, USDC, USDT, DAI) ; les autres jetons sont notés sans montant.
- Saut suivant : les 2 plus gros financeurs ($ stable) du nœud racine, puis le plus gros financeur de chacun ;
  coupure d'un financeur = heure de son dernier envoi au nœud enfant avant la coupure de l'enfant.
- Un nœud dont la 1re page (1 000 transferts) est pleine AVANT sa coupure est un « hub très actif » : on note
  son activité mais on ne remonte pas plus haut (service, CEX, bridge ou routeur probable, non nommé ici).
- Chaque adresse rencontrée est testée une fois (getsourcecode) : contrat vérifié et nom, ou EOA.
Sorties : data/graphe/<wallet>.json, data/contrats.json (cache), data/graphe.compte.json.
Lève sur toute erreur Etherscan persistante. Reprise automatique (fichiers existants sautés).

    python3 col_20_graphe_financement.py            # tout l'échantillon
    python3 col_20_graphe_financement.py 0 4        # part 0 sur 4 (exécutions parallèles)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ETUDE, "data")
GRAPHE = os.path.join(DATA, "graphe")
TRADING = {"0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e", "0xc5d563a36ae78145c45a50134d48a1215220f80a",
           "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296", "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
           "0xe111180000d2663c0091e4f400237545b87b996b", "0xe2222d279d744050d28e00520010520000310f59",
           "0x3a3bd7bb9528e159577f7c2e685cc81a765002e2"}  # WrappedCollateral : plomberie interne, pas une source
STABLES = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC.e", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC",
           "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": "USDT", "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063": "DAI"}
TOP_K = {0: 2, 1: 1, 2: 0}          # financeurs remontés selon la profondeur du nœud
# Contrats qui sont des portefeuilles d'utilisateur : on remonte à travers eux (la racine en est souvent un).
PORTEFEUILLES = {"GnosisSafeProxy", "SafeProxy", "GnosisSafe", "Safe", "SafeL2", "GnosisSafeL2", "ProxyWallet"}


def cle_api():
    for l in open(os.path.expanduser("~/Downloads/.env")):
        if l.startswith("ETHERSCAN_API_KEY="):
            return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("ETHERSCAN_API_KEY absente de ~/Downloads/.env")


EK = cle_api()
_dernier = [0.0]
COMPTE = {"appels": 0, "limite": 0, "erreurs_reseau": 0, "vides": 0}


def es(**params):
    params.update(chainid=137, apikey=EK)
    url = "https://api.etherscan.io/v2/api?" + urllib.parse.urlencode(params)
    for i in range(8):
        attente = 0.36 - (time.time() - _dernier[0])
        if attente > 0:
            time.sleep(attente)
        _dernier[0] = time.time()
        COMPTE["appels"] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                d = json.loads(r.read())
        except (urllib.error.URLError, TimeoutError):
            COMPTE["erreurs_reseau"] += 1
            time.sleep(2 * (i + 1))
            continue
        msg, res = str(d.get("message", "")), d.get("result")
        if d.get("status") == "1":
            return res
        if msg.startswith("No transactions found") or msg.startswith("No records found"):
            COMPTE["vides"] += 1
            return []
        if "rate limit" in str(res).lower() or "max calls" in str(res).lower() or "max rate" in str(res).lower():
            COMPTE["limite"] += 1
            time.sleep(2 * (i + 1))
            continue
        if params.get("action") == "getsourcecode" and isinstance(res, list):
            return res
        raise RuntimeError(f"Etherscan {params.get('action')} {params.get('address')}: {msg} {str(res)[:200]}")
    raise RuntimeError(f"Etherscan : échec répété {params.get('action')} {params.get('address')}")


def contrat(adr, cache):
    if adr not in cache:
        r = es(module="contract", action="getsourcecode", address=adr)
        x = r[0] if r else {}
        nom = x.get("ContractName") or ""
        # EOA : pas de bytecode vérifié ni de nom ; contrat non vérifié : nom vide mais ABI "not verified"
        cache[adr] = {"nom": nom, "proxy": x.get("Proxy") == "1", "impl": x.get("Implementation") or "",
                      "verifie": bool(nom)}
    return cache[adr]


def transferts(adr):
    return es(module="account", action="tokentx", address=adr, page=1, offset=1000, sort="asc")


def noeud(adr, coupure, cache):
    rows = transferts(adr)
    avant = [x for x in rows if int(x["timeStamp"]) < coupure]
    plein = len(rows) >= 1000 and int(rows[-1]["timeStamp"]) < coupure
    afflux, sorties = [], set()
    for x in avant:
        frm, to = x["from"].lower(), x["to"].lower()
        if to == adr and frm != adr and frm not in TRADING and int(x["value"]) > 0:
            ca = x["contractAddress"].lower()
            sym = STABLES.get(ca)
            usd = int(x["value"]) / 10 ** int(x["tokenDecimal"]) if sym else None
            afflux.append([int(x["timeStamp"]), frm, usd, sym or x.get("tokenSymbol", "?"), x["hash"]])
        elif frm == adr and to != adr:
            sorties.add(to)
    return {"adresse": adr, "coupure": coupure, "n_transferts_vus": len(rows), "hub_tres_actif": plein,
            "premier_ts": int(rows[0]["timeStamp"]) if rows else None, "afflux": afflux,
            "n_destinataires_avant": len(sorties), "contrat": contrat(adr, cache)}


def graphe(racine, coupure, cache):
    noeuds, file = {}, [(racine, coupure, 0, None)]
    while file:
        adr, cp, prof, enfant = file.pop(0)
        if (adr, cp) in noeuds:
            continue
        n = noeud(adr, cp, cache)
        n["profondeur"], n["enfant"] = prof, enfant
        noeuds[f"{adr}@{cp}"] = n
        bloque = n["contrat"]["verifie"] and n["contrat"]["nom"] not in PORTEFEUILLES and prof > 0
        if n["hub_tres_actif"] or bloque or TOP_K[prof] == 0:
            continue
        par_financeur = {}
        for ts, frm, usd, sym, h in n["afflux"]:
            f = par_financeur.setdefault(frm, {"usd": 0.0, "dernier": 0})
            f["usd"] += usd or 0.0
            f["dernier"] = max(f["dernier"], ts)
        tops = sorted(par_financeur.items(), key=lambda kv: -kv[1]["usd"])[:TOP_K[prof]]
        for frm, f in tops:
            if f["usd"] > 0:
                file.append((frm, f["dernier"] + 1, prof + 1, adr))
    return {"racine": racine, "coupure": coupure, "noeuds": list(noeuds.values())}


def main():
    part, nb = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    os.makedirs(GRAPHE, exist_ok=True)
    ech = json.load(open(os.path.join(DATA, "echantillon.json")))["wallets"]
    f_cache = os.path.join(DATA, f"contrats_{part}.json")
    cache = json.load(open(f_cache)) if os.path.exists(f_cache) else {}
    faits = 0
    for i, e in enumerate(ech):
        if i % nb != part:
            continue
        sortie = os.path.join(GRAPHE, e["wallet"] + ".json")
        if os.path.exists(sortie):
            continue
        g = graphe(e["wallet"], e["premier_trade_p8_ts"], cache)
        with open(sortie + ".tmp", "w") as f:
            json.dump(g, f)
        os.replace(sortie + ".tmp", sortie)
        faits += 1
        if faits % 25 == 0:
            json.dump(cache, open(f_cache, "w"))
            print(f"part {part}: {faits} graphes, {json.dumps(COMPTE)}", flush=True)
    json.dump(cache, open(f_cache, "w"))
    json.dump(COMPTE, open(os.path.join(DATA, f"graphe.compte_{part}.json"), "w"))
    print(f"part {part} terminée : {faits} graphes, {json.dumps(COMPTE)}")


if __name__ == "__main__":
    main()
