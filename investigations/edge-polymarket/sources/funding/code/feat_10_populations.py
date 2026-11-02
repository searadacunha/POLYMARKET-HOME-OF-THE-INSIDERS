#!/usr/bin/env python3
"""Populations de financement de chaque wallet, selon analysis_plan.md (graphe seul, aucun résultat de trading).

Lit data/graphe/*.json, data/etiquettes.json et les noms de contrats rencontrés. Écrit derived/populations.csv
(une ligne par wallet) et derived/grappes.csv (paires de wallets partageant un financeur EOA non hub, avec la classe
de preuve du lien). Aucune lecture de prix, de trade ni de résolution.
"""
import collections
import csv
import glob
import json
import os

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import re
ETIQ = json.load(open(os.path.join(ETUDE, "data", "etiquettes.json")))["etiquettes"]
_pub = os.path.join(ETUDE, "data", "etiquettes_publiques.json")
PUB = json.load(open(_pub)) if os.path.exists(_pub) else {}
# Nom public (titre d'explorateur) -> famille. Ordre des tests fixé avant toute mesure.
FAMILLES_PUB = [
    ("melangeur", r"tornado|railgun|mixer|privacy pool|blender"),
    ("echange_instantane", r"changenow|fixedfloat|fixed float|simpleswap|changehero|exolix|stealthex|sideshift|n\.exchange|"
                           r"trocador|letsexchange|godex|swapzone|majestic|wizardswap"),
    ("rampe_fiat", r"moonpay|transak|ramp network|banxa|mercuryo|onramper|coinbase pay|checkout"),
    ("bridge", r"relay|across|stargate|hop protocol|synapse|debridge|wormhole|bridge|li\.fi|lifi|socket|orbiter|rhino|"
               r"cctp|token messenger|layerzero|axelar|squid"),
    ("dex", r"router|swap|pool|vault|aggregat|uniswap|1inch|paraswap|odos|kyber|curve|balancer|sushi|quickswap|dex"),
    ("cex", r"binance|coinbase|okx|kraken|bybit|kucoin|gate\.io|gate |mexc|bitget|htx|huobi|crypto\.com|bitfinex|"
            r"bitstamp|gemini|robinhood|upbit|bithumb|bitpanda|bitvavo|revolut|paxos|bitmart|lbank|poloniex|whitebit"),
    ("polymarket", r"polymarket"),
]


def famille_publique(nom):
    nl = nom.lower()
    for fam, motif in FAMILLES_PUB:
        if re.search(motif, nl):
            return fam
    return "etiquete_autre"


def etiquette_publique(chaine, adr):
    v = PUB.get(f"{chaine}:{adr}")
    if v and v.get("nom") not in (None, "aucune"):
        return famille_publique(v["nom"]), v["nom"]
    return None
MOTS_BRIDGE = ("relay", "bridge", "across", "stargate", "lifi", "socket", "debridge", "cctp", "tokenmessenger")
MOTS_DEX = ("router", "swap", "pool", "aggregat", "augustus", "odos", "exchangeproxy", "pair", "vault")
PORTEFEUILLES = {"GnosisSafeProxy", "SafeProxy", "GnosisSafe", "Safe", "SafeL2", "GnosisSafeL2", "ProxyWallet"}


def nature(n):
    """Nature d'un nœud : étiquette du disque d'abord, puis nom de contrat, puis comportement."""
    adr = n["adresse"]
    if adr in ETIQ:
        return ETIQ[adr]["famille"], ETIQ[adr]["preuve"], ETIQ[adr]["entite"]
    pub = etiquette_publique(137, adr)
    if pub:
        return pub[0], "observe_etiquette_publique", pub[1]
    if n.get("non_remonte"):
        return "non_remonte", "aucune", "financeur secondaire non récupéré"
    nom = (n["contrat"].get("nom") or "")
    nl = nom.lower()
    if nom and nom not in PORTEFEUILLES:
        if any(m in nl for m in MOTS_BRIDGE):
            return "bridge", "observe_nom_contrat", nom
        if any(m in nl for m in MOTS_DEX):
            return "dex", "observe_nom_contrat", nom
        return "contrat_autre", "observe_nom_contrat", nom
    if n["hub_tres_actif"]:
        return "hub_non_nomme", "observe_comportement", "hub très actif (CEX, service ou bridge probable)"
    if nom in PORTEFEUILLES:
        return "portefeuille", "observe_nom_contrat", nom
    return "eoa", "observe_direct", "EOA ou contrat non vérifié"


TOP_K = {0: 2, 1: 1, 2: 0}


def remonte(n):
    """Même règle que le collecteur : ce nœud a-t-il été remonté vers ses financeurs ?"""
    nom = n["contrat"].get("nom") or ""
    bloque = n["contrat"].get("verifie") and nom not in PORTEFEUILLES and n["profondeur"] > 0
    return not (n["hub_tres_actif"] or bloque or TOP_K[n["profondeur"]] == 0)


def origine(racine):
    """Résumé de data/origine/<racine>.json : chaîne, part du dépôt, nature de l'expéditeur et de ses financeurs."""
    fp = os.path.join(ETUDE, "data", "origine", racine + ".json")
    if not os.path.exists(fp):
        return None
    d = json.load(open(fp)).get("depot") or {}
    if not d.get("apparie"):
        return None
    ch, ex = d.get("chaine"), d.get("expediteur") or ""
    out = {"chaine": ch, "usd": d.get("usd") or 0.0, "expediteur": ex, "expediteur_famille": None,
           "expediteur_hub": None, "expediteur_age_j": None, "familles_amont": []}
    pub = etiquette_publique(ch, ex) if ch in (1, 42161) else None
    if pub:
        out["expediteur_famille"] = pub[0]
    am = d.get("amont")
    if am:
        out["expediteur_hub"] = am.get("hub_tres_actif")
        if am["afflux"]:
            out["expediteur_age_j"] = (d["ts"] - am["afflux"][0][0]) / 86400
        par = collections.Counter()
        for ts, frm, val, sym, h in am["afflux"]:
            par[frm] += 1          # nombre d'envois : les montants mélangent jetons et ETH natif
        tot = sum(par.values()) or 1
        fam = collections.defaultdict(float)
        noms = {}
        for frm, k in par.items():
            e = ETIQ.get(frm)
            p = (e["famille"], e["entite"]) if e else etiquette_publique(ch, frm)
            if p:
                fam[p[0]] += k / tot
                noms[p[0]] = p[1]
        out["familles_amont"] = [(f, noms[f], pf) for f, pf in sorted(fam.items(), key=lambda x: -x[1])]
    return out


def attribuer(g):
    """Répartit le montant stable de la racine sur des terminaux. Un nœud non remonté garde son montant ;
    un nœud remonté le répartit entre ses financeurs au prorata de leurs envois ; un financeur jamais
    récupéré devient un terminal « non_remonte » (sauf s'il porte une étiquette)."""
    enfants = collections.defaultdict(list)
    for n in g["noeuds"]:
        if n["enfant"] is not None:
            enfants[n["enfant"]].append(n)
    racine = g["noeuds"][0]
    terminaux = []

    def descendre(n, montant, chemin):
        if not remonte(n) and n is not racine:
            terminaux.append((n, montant, chemin))
            return
        sur_chemin = {c["adresse"] for c in chemin}
        parents = {p["adresse"]: p for p in enfants.get(n["adresse"], [])
                   if p["profondeur"] == n["profondeur"] + 1 and p["adresse"] not in sur_chemin}
        par_f = collections.defaultdict(float)
        for ts, frm, usd, sym, h in n["afflux"]:
            par_f[frm] += usd or 0.0
        total = sum(par_f.values())
        if total <= 0:
            terminaux.append((n, montant, chemin))
            return
        for frm, usd in par_f.items():
            if usd <= 0:
                continue
            m = montant * usd / total
            if frm in parents:
                descendre(parents[frm], m, chemin + [parents[frm]])
            else:
                pseudo = {"adresse": frm, "contrat": {"nom": ""}, "hub_tres_actif": False, "premier_ts": None,
                          "coupure": None, "n_destinataires_avant": None, "afflux": [], "non_remonte": True,
                          "profondeur": n["profondeur"] + 1}
                terminaux.append((pseudo, m, chemin))

    total_racine = sum(a[2] or 0.0 for a in racine["afflux"])
    descendre(racine, total_racine, [racine])
    return racine, total_racine, terminaux, None


def classer(g):
    racine, total, terminaux, par_cle = attribuer(g)
    natures = [(n, *nature(n)) for n in g["noeuds"][1:]]
    familles_vues = collections.Counter(f for _, f, _, _ in natures)
    for t, m, ch in terminaux:
        if t.get("non_remonte"):
            familles_vues[nature(t)[0]] += 0  # présent comme source non remontée
    montant_par_famille = collections.defaultdict(float)
    for t, m, ch in terminaux:
        montant_par_famille[nature(t)[0]] += m
    # chemin du plus gros financeur : nombre d'EOA intermédiaires non hubs avant étiquette ou hub
    par_f = collections.defaultdict(float)
    for ts, frm, usd, sym, h in racine["afflux"]:
        par_f[frm] += usd or 0.0
    top = max(par_f, key=par_f.get) if par_f else None
    n_eoa_inter, intermediaire_jeune = 0, False
    courant = top
    vus = set()
    while courant and courant not in vus:
        vus.add(courant)
        noeuds_c = [n for n in g["noeuds"] if n["adresse"] == courant]
        if not noeuds_c:
            break
        n = noeuds_c[0]
        f, preuve, entite = nature(n)
        if f != "eoa" and f != "portefeuille":
            break
        n_eoa_inter += 1
        if n["premier_ts"] and n["coupure"] and n["coupure"] - n["premier_ts"] < 7 * 86400:
            intermediaire_jeune = True
        parents = [p for p in g["noeuds"] if p["enfant"] == courant and p["profondeur"] == n["profondeur"] + 1]
        courant = max(parents, key=lambda p: sum(a[2] or 0 for a in n["afflux"] if a[1] == p["adresse"]))["adresse"] if parents else None

    ech = [e for n, f, p, e in natures if f == "echange_instantane"]
    ech_obs = [e for n, f, p, e in natures if f == "echange_instantane" and p == "observe_etiquette_publique"]
    # Origine hors Polygon du plus gros dépôt Relay (data/origine) : expéditeur et ses financeurs amont
    org = origine(g["racine"])
    part_depot = (org["usd"] / total) if (org and total > 0) else 0.0
    if org and org.get("familles_amont"):
        for fam, nom, part_fam in org["familles_amont"]:
            if fam == "echange_instantane":
                ech.append(f"{nom} (origine {org['chaine']})")
                ech_obs.append(nom)
    origine_fraiche = bool(org and org.get("expediteur_age_j") is not None and org["expediteur_age_j"] < 7
                           and not org.get("expediteur_hub") and not org.get("expediteur_famille"))
    part = lambda fam: (montant_par_famille.get(fam, 0.0) / total) if total > 0 else 0.0
    autres_sources = any(f in ("rampe_fiat", "hub_non_nomme", "cex") for _, f, _, _ in natures)
    # part du montant passant par un échange instantané : sur Polygon, plus la part du dépôt Relay venue d'un
    # échange instantané à l'origine
    part_ech_org = part_depot * sum(pf for fam, _, pf in (org or {}).get("familles_amont", []) if fam == "echange_instantane") \
        if org else 0.0
    part_ech_tot = part("echange_instantane") + part_ech_org
    conv_org = bool(org and (org.get("expediteur_hub") or org.get("expediteur_famille") in ("cex", "rampe_fiat")
                             or any(fam in ("cex", "rampe_fiat") for fam, _, _ in org.get("familles_amont", []))))
    pops = set()
    if ech:
        pops.add("ECH")
    if [e for e in ech_obs if "changenow" in e.lower()] or any("ChangeNOW" in e for e in ech):
        pops.add("ECH_CN")
    if ech and part_ech_tot >= 0.8 and not autres_sources and not conv_org:
        pops.add("XMR_COMPAT")
    if n_eoa_inter >= 2 or intermediaire_jeune or origine_fraiche:
        pops.add("COMPLEXE")
    conv_polygon = (part("rampe_fiat") + part("hub_non_nomme") + part("cex")) >= 0.8 and n_eoa_inter <= 1
    conv_relay = part("bridge") >= 0.5 and conv_org
    if not ech and (conv_polygon or conv_relay) and not origine_fraiche:
        pops.add("CLASSIQUE")
    if part("bridge") >= 0.5:
        pops.add("BRIDGE")
    if not pops:
        pops.add("INCONNU")
    financeurs_eoa = sorted({n["adresse"] for n, f, p, e in natures
                             if f == "eoa" and n["profondeur"] in (1, 2) and (n["n_destinataires_avant"] or 0) >= 0})
    return {
        "wallet": g["racine"], "coupure": g["coupure"], "usd_avant": round(total, 2), "n_noeuds": len(g["noeuds"]),
        "populations": "|".join(sorted(pops)), "n_eoa_intermediaires": n_eoa_inter,
        "intermediaire_jeune": intermediaire_jeune, "part_echange": round(part("echange_instantane"), 3),
        "part_rampe_fiat": round(part("rampe_fiat"), 3), "part_hub": round(part("hub_non_nomme"), 3),
        "part_bridge": round(part("bridge"), 3), "part_dex": round(part("dex"), 3), "part_eoa": round(part("eoa"), 3),
        "part_non_remonte": round(part("non_remonte"), 3), "part_portefeuille": round(part("portefeuille"), 3),
        "part_contrat_autre": round(part("contrat_autre"), 3),
        "entites_ech": "|".join(sorted(set(ech))), "financeurs_eoa": "|".join(financeurs_eoa),
        "part_cex": round(part("cex"), 3), "origine_chaine": (org or {}).get("chaine"),
        "origine_part_depot": round(part_depot, 3), "origine_expediteur_famille": (org or {}).get("expediteur_famille"),
        "origine_expediteur_hub": (org or {}).get("expediteur_hub"), "origine_fraiche": origine_fraiche,
        "origine_familles_amont": "|".join(f"{f}:{round(pf, 2)}" for f, _, pf in (org or {}).get("familles_amont", [])),
        "sans_afflux": total <= 0,
    }, g


def grappes(lignes, graphes):
    """Paires de wallets avec un financeur EOA non hub commun, et classe de preuve du lien."""
    par_financeur = collections.defaultdict(list)
    for l in lignes:
        for f in filter(None, l["financeurs_eoa"].split("|")):
            par_financeur[f].append(l["wallet"])
    sortie = []
    for f, ws in par_financeur.items():
        if len(ws) < 2:
            continue
        # envois du financeur vers chaque wallet (s'il est financeur direct) : heure et montant
        envois, dest_max = {}, 0
        for w in ws:
            for n in graphes[w]["noeuds"]:
                if n["adresse"] == f:
                    dest_max = max(dest_max, n["n_destinataires_avant"] or 0)
            r = graphes[w]["noeuds"][0]
            m = [(a[0], a[2] or 0) for a in r["afflux"] if a[1] == f]
            if m:
                envois[w] = (min(t for t, _ in m), sum(u for _, u in m))
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                a, b = ws[i], ws[j]
                if dest_max >= 50:
                    classe = "compatible_ambigu"
                elif a in envois and b in envois:
                    (ta, ma), (tb, mb) = envois[a], envois[b]
                    proche = abs(ta - tb) <= 86400 and min(ma, mb) > 0 and max(ma, mb) / min(ma, mb) <= 2
                    classe = "fortement_compatible" if proche else "observe_directement"
                else:
                    classe = "observe_directement"  # financeur commun à profondeur 2 : transferts observés
                sortie.append({"financeur": f, "wallet_a": a, "wallet_b": b, "classe": classe,
                               "destinataires_financeur": dest_max})
    return sortie


def main():
    lignes, graphes = [], {}
    for fp in sorted(glob.glob(os.path.join(ETUDE, "data", "graphe", "*.json"))):
        g = json.load(open(fp))
        l, g = classer(g)
        lignes.append(l)
        graphes[l["wallet"]] = g
    with open(os.path.join(ETUDE, "derived", "populations.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    paires = grappes(lignes, graphes)
    with open(os.path.join(ETUDE, "derived", "grappes.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["financeur", "wallet_a", "wallet_b", "classe", "destinataires_financeur"])
        w.writeheader()
        w.writerows(paires)
    c = collections.Counter(p for l in lignes for p in l["populations"].split("|"))
    print(f"{len(lignes)} wallets ; populations : {dict(c.most_common())}")
    print(f"sans afflux avant coupure : {sum(l['sans_afflux'] for l in lignes)}")
    print(f"paires de grappe : {len(paires)}, {dict(collections.Counter(p['classe'] for p in paires))}")


if __name__ == "__main__":
    main()
