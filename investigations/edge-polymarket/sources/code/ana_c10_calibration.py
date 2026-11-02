#!/usr/bin/env python3
"""Criblage C : calibration des prix avant échéance sur l'univers p8 (EXPLORATOIRE, un split à la fois).

Pour chaque marché du split et chaque horizon h, t = endDate - h (date connue d'avance) ; on garde le marché
seulement s'il est encore ouvert à t (createdAt < t < closedTime) et si un trade preneur (>= 100 $) existe dans
[t - fraicheur, t]. Prix OUI = dernier trade avant t (prix du jeton NON converti en 1 - p).
Sorties : derived/c10_<split>.json (tables par tranche de prix, rendements bruts et nets, IC par bootstrap
groupé par événement). Chaque stratégie évaluée est inscrite au registre.

    python3 ana_c10_calibration.py TRAIN
"""
import json
import os
import random
import sys
import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from registre import enregistrer  # noqa: E402

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P8 = os.path.expanduser("~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8")
HORIZONS = {"30j": (30 * 86400, 7 * 86400), "7j": (7 * 86400, 2 * 86400), "2j": (2 * 86400, 86400),
            "12h": (12 * 3600, 6 * 3600)}  # horizon, fraîcheur max du dernier trade
FRAIS = {"geopolitics/war": 0.0, "election/politics": 0.04, "earnings": 0.04, "macro/fed": 0.05, "other": 0.05}
GLISSEMENT = 0.01  # par part : demi-écart + impact, hypothèse prudente
TRANCHES = [0, .02, .05, .10, .20, .35, .50, .65, .80, .90, .95, .98, 1.0001]
STRATEGIES = {  # définies avant tout calcul : côté acheté et tranche de prix OUI
    "S1_vendre_longshot": ("NON", 0.02, 0.15),
    "S2_acheter_favori": ("OUI", 0.85, 0.98),
    "S3_acheter_longshot": ("OUI", 0.02, 0.15),
    "S4_vendre_favori": ("NON", 0.85, 0.98),
}


def ts(s):
    s = s.replace(" ", "T").replace("Z", "+00:00")
    if s.endswith("+00"):
        s += ":00"
    return dt.datetime.fromisoformat(s).timestamp()


def charger(split):
    u = [m for m in json.load(open(os.path.join(P8, "universe.json"))) if m["split"] == split]
    ev = json.load(open(os.path.join(ETUDE, "data", "raw", "p8_events.json")))
    return u, ev


def observations(split):
    u, ev = charger(split)
    obs, compte = [], {"marches": len(u), "issue_ambigue": 0}
    for h in HORIZONS:
        for k in ("ferme_avant_t", "cree_apres_t", "pas_de_trade_frais", "tronque_avant_t", "ok"):
            compte[f"{h}_{k}"] = 0
    for m in u:
        prix_res = json.loads(m["outcomePrices"])
        if prix_res not in (["1", "0"], ["0", "1"]):
            compte["issue_ambigue"] += 1
            continue
        oui_gagne = prix_res[0] == "1"
        d = json.load(open(os.path.join(P8, "trades", m["conditionId"] + ".json")))
        rows = sorted(d["rows"], key=lambda r: r["timestamp"])
        tmin = rows[0]["timestamp"] if rows else None
        fin, ferme, cree = ts(m["endDate"]), ts(m["closedTime"]), ts(m["createdAt"])
        for h, (dh, fraicheur) in HORIZONS.items():
            t = fin - dh
            if ferme <= t:
                compte[f"{h}_ferme_avant_t"] += 1
                continue
            if cree >= t:
                compte[f"{h}_cree_apres_t"] += 1
                continue
            if d.get("maybe_truncated") and (tmin is None or tmin > t - fraicheur):
                compte[f"{h}_tronque_avant_t"] += 1
                continue
            avant = [r for r in rows if t - fraicheur <= r["timestamp"] <= t]
            if not avant:
                compte[f"{h}_pas_de_trade_frais"] += 1
                continue
            r = avant[-1]
            p = r["price"] if r["outcomeIndex"] == 0 else 1 - r["price"]
            compte[f"{h}_ok"] += 1
            obs.append({"h": h, "p": p, "oui": oui_gagne, "cat": m["cat"],
                        "evt": ev[m["conditionId"]]["event_id"], "cid": m["conditionId"]})
    return obs, compte


def rendement(o, cote, frais_net):
    """Rendement par dollar misé, achat au prix observé + glissement, frais preneur de la catégorie."""
    prix = o["p"] if cote == "OUI" else 1 - o["p"]
    gagne = o["oui"] if cote == "OUI" else not o["oui"]
    if not frais_net:
        return (gagne - prix) / prix
    cout = min(prix + GLISSEMENT, 0.999)
    frais = FRAIS[o["cat"]] * cout * (1 - cout)
    return (gagne - cout - frais) / (cout + frais)


def bootstrap_groupe(obs, f, n=2000, graine=10):
    rnd = random.Random(graine)
    par_evt = {}
    for o in obs:
        par_evt.setdefault(o["evt"], []).append(f(o))
    groupes = list(par_evt.values())
    moyennes = []
    for _ in range(n):
        tirage = [x for g in (rnd.choice(groupes) for _ in groupes) for x in g]
        moyennes.append(sum(tirage) / len(tirage))
    moyennes.sort()
    return moyennes[int(0.025 * n)], moyennes[int(0.975 * n)], len(groupes)


def main():
    split = sys.argv[1]
    obs, compte = observations(split)
    sortie = {"split": split, "compte": compte, "calibration": {}, "strategies": {}}
    for h in HORIZONS:
        oh = [o for o in obs if o["h"] == h]
        lignes = []
        for a, b in zip(TRANCHES, TRANCHES[1:]):
            t = [o for o in oh if a <= o["p"] < b]
            if t:
                lignes.append({"tranche": [a, b], "n": len(t), "n_evt": len({o["evt"] for o in t}),
                               "p_moyen": sum(o["p"] for o in t) / len(t), "freq_oui": sum(o["oui"] for o in t) / len(t)})
        brier = sum((o["p"] - o["oui"]) ** 2 for o in oh) / max(len(oh), 1)
        sortie["calibration"][h] = {"n": len(oh), "brier": brier, "tranches": lignes}
        for nom, (cote, a, b) in STRATEGIES.items():
            t = [o for o in oh if a <= o["p"] <= b]
            if len(t) < 10:
                sortie["strategies"][f"{nom}_{h}"] = {"n": len(t)}
                continue
            brut = sum(rendement(o, cote, False) for o in t) / len(t)
            net = sum(rendement(o, cote, True) for o in t) / len(t)
            lo, hi, ng = bootstrap_groupe(t, lambda o: rendement(o, cote, True))
            gagne = sum((o["oui"] if cote == "OUI" else not o["oui"]) for o in t) / len(t)
            sortie["strategies"][f"{nom}_{h}"] = {"n": len(t), "n_evt": ng, "taux_reussite": gagne,
                                                 "rend_brut": brut, "rend_net": net, "ic95_net": [lo, hi]}
    chemin = os.path.join(ETUDE, "derived", f"c10_{split}.json")
    json.dump(sortie, open(chemin, "w"), indent=1)
    for k, v in sortie["strategies"].items():
        if "rend_net" in v:
            enregistrer(ETUDE, test=f"C10_{k}_{split}", declare=False, n=v["n"], n_effectif=v["n_evt"],
                        agent="criblage-principal", params={"split": split, "glissement": GLISSEMENT},
                        stat=v["rend_net"], sortie=f"derived/c10_{split}.json")
    print(json.dumps(compte))
    for h, c in sortie["calibration"].items():
        print(h, "n", c["n"], "brier", round(c["brier"], 4))
        for l in c["tranches"]:
            print(f"   [{l['tranche'][0]:.2f},{l['tranche'][1]:.2f}) n={l['n']:4} evt={l['n_evt']:3} p={l['p_moyen']:.3f} oui={l['freq_oui']:.3f}")
    for k, v in sortie["strategies"].items():
        if "rend_net" in v:
            print(f"{k:28} n={v['n']:4} evt={v['n_evt']:3} réussite={v['taux_reussite']:.3f} brut={v['rend_brut']:+.4f} "
                  f"net={v['rend_net']:+.4f} IC95=[{v['ic95_net'][0]:+.4f},{v['ic95_net'][1]:+.4f}]")


if __name__ == "__main__":
    main()
