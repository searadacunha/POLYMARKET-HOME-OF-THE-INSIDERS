#!/usr/bin/env python3
"""Contrôles positifs : le pipeline mesurer() + comparer() sur des marchés synthétiques, AVANT le gel.

Marchés synthétiques : prix en marche aléatoire, trades de nombreux wallets. Population « informée » : après chacun
de ses achats, le prix dérive de +effet points sur l'heure suivante (puis reste). Contrôle : aucune dérive.
Cas : nul (effet 0), moyen (1 point), fort (3 points) ; tailles proches des populations réelles ; plusieurs graines.
Verdict attendu : le nul reste muet (IC contient 0 dans ~95 % des graines), le fort est détecté.
Écrit controles/controles_positifs.md.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ana_10_information import mesurer_marche, comparer  # noqa: E402
from registre import enregistrer  # noqa: E402

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


POOL_POP = [f"0xpop{i}" for i in range(40)]
POOL_CTL = [f"0xctl{i}" for i in range(600)]


def marche_synthetique(rng, n_wallets_pop, n_wallets_ctl, effet, n_trades=400):
    t, p = 1_700_000_000, 0.5
    rows, derive = [], []  # derive : (début, fin, ampleur) des dérives induites
    pop = [POOL_POP[i] for i in rng.choice(len(POOL_POP), n_wallets_pop, replace=False)]
    ctl = [POOL_CTL[i] for i in rng.choice(len(POOL_CTL), n_wallets_ctl, replace=False)]
    tous = pop + ctl
    for _ in range(n_trades):
        t += int(rng.exponential(300))
        bruit = rng.normal(0, 0.004)
        d = sum(a * min(1.0, (t - s) / 3600) - a * min(1.0, (t - 3600 - s) / 3600 if t > s + 3600 else 0)
                for s, e, a in derive if t > s)
        prix = float(np.clip(p + bruit + d, 0.03, 0.97))
        w = tous[rng.integers(0, len(tous))]
        if w in pop and effet:
            derive.append((t, t + 3600, effet))
        rows.append({"proxyWallet": w, "outcomeIndex": 0, "price": prix, "timestamp": t, "side": "BUY", "size": 400.0})
        p = prix - d if not derive else p + bruit
    return rows, set(pop), set(ctl)


def un_cas(effet, graine, n_marches=60):
    rng = np.random.default_rng(graine)
    lignes, pop_tot = [], set()
    for _ in range(n_marches):
        rows, pop, ctl = marche_synthetique(rng, 3, 40, effet)
        for l in mesurer_marche(rows, pop | ctl, "other", int(rng.integers(0, 2))):
            l["cid"] = f"m{len(pop_tot)}_{graine}_{_}"
            lignes.append(l)
        pop_tot |= pop
    return comparer(lignes, lambda w: w.startswith("0xpop"), "deltap_1h", n_boot=500, graine=graine)


def main():
    lignes_rapport = ["# Contrôles positifs (tables synthétiques)", "",
                      "Critère principal deltap_1h, population contre contrôle, IC 95 % bootstrap groupé par wallet.", "",
                      "| cas | effet (points) | graine | n achats pop | écart estimé | IC 95 % | détecté |", "|---|---|---|---|---|---|---|"]
    bilan = {}
    for nom, effet in (("nul", 0.0), ("faible", 0.003), ("moyen", 0.01), ("fort", 0.03)):
        for graine in range(1, 11):
            r = un_cas(effet, graine)
            det = r["signal"]
            bilan.setdefault(nom, []).append(det)
            lignes_rapport.append(f"| {nom} | {effet} | {graine} | {r['n_pop']} | {r['ecart']:+.4f} | "
                                  f"w [{r['ic95_wallet'][0]:+.4f}, {r['ic95_wallet'][1]:+.4f}] m [{r['ic95_marche'][0]:+.4f}, {r['ic95_marche'][1]:+.4f}] | {'oui' if det else 'non'} |")
    lignes_rapport += ["", "Bilan : " + ", ".join(f"{k} détecté {sum(v)}/{len(v)}" for k, v in bilan.items()), "",
                       "Attendu : nul muet (au plus 1/10 par hasard), fort détecté 10/10. Le cas faible donne l'ordre de grandeur de l'écart minimal détectable à cette taille."]
    os.makedirs(os.path.join(ETUDE, "controles"), exist_ok=True)
    chemin = os.path.join(ETUDE, "controles", "controles_positifs.md")
    open(chemin, "w").write("\n".join(lignes_rapport) + "\n")
    for k, v in bilan.items():
        enregistrer(ETUDE, test=f"CTL_{k}_deltap_1h", declare=False, n=len(v), agent="controles-positifs",
                    params={"cas": k}, stat=sum(v) / len(v), donnees="synthetiques", sortie="controles/controles_positifs.md")
    print("\n".join(lignes_rapport))


if __name__ == "__main__":
    main()
