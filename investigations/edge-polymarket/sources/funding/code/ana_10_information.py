#!/usr/bin/env python3
"""Valeur informationnelle des achats des wallets de l'échantillon, par population de financement (analysis_plan.md).

mesurer() : une ligne par achat preneur (>= 100 $, 0,02 <= p0 <= 0,98) d'un wallet de l'échantillon.
  Chemin de prix du jeton acheté = trades des AUTRES wallets seulement (jeton opposé converti en 1 - p).
  delta_h = p(t0+h) - p0 ; deltap_h = p(t0+h) - p_post (p_post = 1er prix d'un autre wallet après t0+60 s) ;
  max_fav = max sur ]t0, t0+24 h] de p - p0 ; t_X = délai du 1er franchissement de +X points ;
  gain = jeton gagnant ; rendement brut et net (frais preneur actuels par catégorie, 1 point de glissement).
comparer() : écart population - contrôle, stratifié par tranche de prix, IC 95 % par bootstrap groupé par wallet.

Exécution sur données réelles : seulement après le gel (le registre refuse sinon pour les tests déclarés).
    python3 ana_10_information.py mesurer
    python3 ana_10_information.py comparer
"""
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P8 = os.path.expanduser("~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8")
HORIZONS = {"1m": 60, "5m": 300, "30m": 1800, "1h": 3600, "6h": 21600, "24h": 86400}
SEUILS = (0.01, 0.02, 0.05, 0.10)
FRAIS = {"geopolitics/war": 0.0, "election/politics": 0.04, "earnings": 0.04, "macro/fed": 0.05, "other": 0.05}
GLISSEMENT = 0.01
TRANCHES = [0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.9801]


def mesurer_marche(rows, echantillon, cat, gagnant):
    """rows : trades d'un marché (dicts data-api). echantillon : set de wallets. gagnant : index gagnant ou None."""
    rows = sorted(rows, key=lambda r: r["timestamp"])
    if not rows:
        return []
    ts = np.array([r["timestamp"] for r in rows], dtype=np.int64)
    p0_tok0 = np.array([r["price"] if r["outcomeIndex"] == 0 else 1 - r["price"] for r in rows])
    ids = {}
    wid = np.array([ids.setdefault(r["proxyWallet"].lower(), len(ids)) for r in rows])
    sortie = []
    for i, r in enumerate(rows):
        w = r["proxyWallet"].lower()
        if w not in echantillon or r["side"] != "BUY":
            continue
        p0 = r["price"]
        if not (0.02 <= p0 <= 0.98) or r["size"] * p0 < 100:
            continue
        k, t0 = r["outcomeIndex"], r["timestamp"]
        j0 = np.searchsorted(ts, t0, "right")
        j24 = np.searchsorted(ts, t0 + 86400, "right")
        m = wid[j0:j24] != ids[w]
        t_aut = ts[j0:j24][m]
        p_aut = p0_tok0[j0:j24][m] if k == 0 else 1 - p0_tok0[j0:j24][m]
        ligne = {"wallet": w, "t0": t0, "k": k, "p0": p0, "usd": r["size"] * p0, "cat": cat,
                 "n_autres_24h": int(len(t_aut))}
        for h, s in HORIZONS.items():
            j = np.searchsorted(t_aut, t0 + s, "right")
            ligne[f"delta_{h}"] = float(p_aut[j - 1] - p0) if j > 0 else 0.0
        jp = np.searchsorted(t_aut, t0 + 60, "left")
        p_post = float(p_aut[jp]) if jp < len(t_aut) else None
        ligne["p_post"] = p_post
        for h, s in HORIZONS.items():
            j = np.searchsorted(t_aut, t0 + s, "right")
            ligne[f"deltap_{h}"] = (float(p_aut[j - 1]) - p_post) if (p_post is not None and j > jp) else (
                0.0 if p_post is not None else None)
        ligne["max_fav"] = float(p_aut.max() - p0) if len(p_aut) else 0.0
        for x in SEUILS:
            hit = np.nonzero(p_aut - p0 >= x - 1e-9)[0]
            ligne[f"t_{int(x * 100)}"] = int(t_aut[hit[0]] - t0) if len(hit) else None
        if gagnant is not None:
            g = 1.0 if k == gagnant else 0.0
            cout = min(p0 + GLISSEMENT, 0.999)
            frais = FRAIS.get(cat, 0.05) * cout * (1 - cout)
            ligne.update(gain=g, rend_brut=(g - p0) / p0, rend_net=(g - cout - frais) / (cout + frais))
        sortie.append(ligne)
    return sortie


def tranche(p):
    for a, b in zip(TRANCHES, TRANCHES[1:]):
        if a <= p < b:
            return a
    return None


def comparer(lignes, est_pop, metrique, n_boot=5000, graine=7):
    """Écart stratifié (population - contrôle) par tranche de prix. Deux IC 95 % bootstrap : groupés par wallet et
    groupés par marché (les achats d'un même marché partagent le même chemin de prix). Un signal exige les deux."""
    vals = [(l["wallet"], l["cid"], tranche(l["p0"]), l[metrique], est_pop(l["wallet"])) for l in lignes
            if l.get(metrique) not in (None, "") and tranche(l["p0"]) is not None]
    vals = [(w, c, s, float(x), e) for w, c, s, x, e in vals]
    pop = [v for v in vals if v[4]]
    ctl = [v for v in vals if not v[4]]
    if len(pop) < 5 or len(ctl) < 5:
        return {"n_pop": len(pop), "n_ctl": len(ctl), "ecart": None}

    def ecart(vp, vc):
        sp, sc = {}, {}
        for _, _, s, x, _ in vp:
            sp.setdefault(s, []).append(x)
        for _, _, s, x, _ in vc:
            sc.setdefault(s, []).append(x)
        tot = sum(len(v) for s, v in sp.items() if s in sc)
        if tot == 0:
            return None
        return sum(len(v) / tot * (np.mean(v) - np.mean(sc[s])) for s, v in sp.items() if s in sc)

    def boot(cle):
        grp = {}
        for v in vals:
            grp.setdefault(v[cle], []).append(v)
        groupes = list(grp.values())
        rng = np.random.default_rng(graine)
        out = []
        for _ in range(n_boot):
            tir = [x for i in rng.integers(0, len(groupes), len(groupes)) for x in groupes[i]]
            e = ecart([v for v in tir if v[4]], [v for v in tir if not v[4]])
            if e is not None:
                out.append(e)
        out.sort()
        arr = np.array(out)
        return [float(out[int(0.025 * len(out))]), float(out[int(0.975 * len(out)) - 1])], \
            float(min(1.0, 2 * min(np.mean(arr <= 0), np.mean(arr >= 0))))

    ic_w, p_w = boot(0)
    ic_m, p_m = boot(1)
    return {"n_pop": len(pop), "n_ctl": len(ctl), "w_pop": len({v[0] for v in pop}), "w_ctl": len({v[0] for v in ctl}),
            "m_pop": len({v[1] for v in pop}), "ecart": float(ecart(pop, ctl)), "ic95_wallet": ic_w, "p_wallet": p_w,
            "ic95_marche": ic_m, "p_marche": p_m, "moy_pop": float(np.mean([v[3] for v in pop])),
            "moy_ctl": float(np.mean([v[3] for v in ctl])),
            "signal": bool((ic_w[0] > 0 and ic_m[0] > 0) or (ic_w[1] < 0 and ic_m[1] < 0))}


def main_mesurer():
    univ = json.load(open(os.path.join(P8, "universe.json")))
    ech = {e["wallet"] for e in json.load(open(os.path.join(ETUDE, "data", "echantillon.json")))["wallets"]}
    lignes = []
    for m in univ:
        prix = json.loads(m["outcomePrices"])
        gagnant = 0 if prix == ["1", "0"] else (1 if prix == ["0", "1"] else None)
        d = json.load(open(os.path.join(P8, "trades", m["conditionId"] + ".json")))
        for l in mesurer_marche(d["rows"], ech, m["cat"], gagnant):
            l.update(cid=m["conditionId"], split=m["split"])
            lignes.append(l)
    champs = sorted({k for l in lignes for k in l})
    with open(os.path.join(ETUDE, "derived", "info_trades.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(lignes)
    print(f"{len(lignes)} achats mesurés, {len({l['wallet'] for l in lignes})} wallets")


if __name__ == "__main__":
    if sys.argv[1:] == ["mesurer"]:
        main_mesurer()
    else:
        print(__doc__)
