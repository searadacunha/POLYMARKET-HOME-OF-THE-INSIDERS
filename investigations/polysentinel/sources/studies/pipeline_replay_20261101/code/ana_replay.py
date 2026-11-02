"""One scenario of the plan: rows, run, sealed-ready output. Usage: ana_replay.py S_A [--grille 60]"""
import argparse
import gc
import gzip
import hashlib
import json
import os
import pickle
import signal
import sys
import time
from collections import Counter
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
import sim_core  # noqa: E402
from sim_core import Sim, SimTime, Store, T_ALERTES, T_FIN, pdb, pbridge, rss_mo, verifie_noyau  # noqa: E402
from charge import charge  # noqa: E402
import univers  # noqa: E402
from univers import scenario_lignes  # noqa: E402

# Frozen copy: production's config.json may change under an amendment, this study's must not.
CONFIG_FICHIER = ETUDE / 'data/config_production.json'
CONFIG = json.loads(CONFIG_FICHIER.read_text())
HORIZONS = dict(S_C=None, S_G=158400, S_A=158400, S_B=None, S_L=158400)
SORTIE_BAC = Path(os.environ.get('PS_BAC', '/private/tmp/claude-501/-Users-benjamindacunha/ddbd5b1b-5e0b-4f3f-a192-c52d7c1360eb/scratchpad/bac'))
LIMITES = ['liquidity_fraction et cohort_size impossibles : liquidité datée absente, dans tous les scénarios.',
           'specialization_shift impossible pour un wallet ayant une ligne sur un événement M1 : pas de tags.',
           'Événements m1 : sans catalogue, supposés ouverts, jamais fermés par échéance ; une priorité sur un match fini reste possible.',
           'Le filtre du recensement relève de fait les seuils de synchronie et de rupture hors famille et témoins.']
arret = False


def demande_arret(*_):
    global arret
    arret = True


def resume_file(sim):
    """Chronological queue positions; ties broken by wallet then event and flagged."""
    queue = sorted(sim.queue, key=lambda e: (e['at'], e['wallet'], e['event_id']))
    heures = Counter(e['at'] for e in queue)
    vus, vus_alertes, positions = set(), set(), []
    depuis_alertes = 0
    vus_sans_m1, sans_m1 = set(), 0
    for i, e in enumerate(queue, 1):
        nouveau = e['wallet'] not in vus
        vus.add(e['wallet'])
        if e['at'] >= T_ALERTES:
            depuis_alertes += 1
            vus_alertes.add(e['wallet'])
        m1 = e['event_id'].startswith('unmapped:')
        if not m1:
            sans_m1 += 1
            vus_sans_m1.add(e['wallet'])
        positions.append(dict(e, m1=m1, position_paire=i, position_wallet=len(vus), nouveau_wallet=nouveau,
                              position_paire_sans_m1=sans_m1 if not m1 else None, position_wallet_sans_m1=len(vus_sans_m1) if not m1 else None,
                              position_paire_depuis_alertes=depuis_alertes if e['at'] >= T_ALERTES else None,
                              position_wallet_depuis_alertes=len(vus_alertes) if e['at'] >= T_ALERTES else None,
                              ex_aequo_heure=heures[e['at']] - 1))
    return positions


def main():
    p = argparse.ArgumentParser()
    p.add_argument('scenario', choices=sorted(HORIZONS))
    p.add_argument('--grille', type=int, default=60)
    a = p.parse_args()
    signal.signal(signal.SIGTERM, demande_arret)
    verifie_noyau()
    univers.regles(neutre=a.scenario != 'S_L')
    root = SORTIE_BAC / a.scenario
    root.mkdir(parents=True, exist_ok=True)
    point = root / 'checkpoint.pickle'
    filtre = json.loads((ETUDE / 'data/global_state.json').read_text())['filtre']
    debut = time.time()
    if point.exists():
        # Own checkpoint, written by this same process tree in the private session folder.
        with point.open('rb') as f:
            sim = pickle.load(f)
        if sim.grid != a.grille:
            raise RuntimeError(f'Reprise à {sim.grid} s demandée à {a.grille} s : retirer le point de reprise ou garder la grille')
        reprise = True
    else:
        u = charge(avec_recensement=a.scenario != 'S_C')
        ecartees = Counter()
        rows = list(scenario_lignes(u, a.scenario, filtre, ecartees=ecartees))
        comptes = u.comptes
        markets, events = u.markets, u.events
        print(json.dumps(dict(scenario=a.scenario, lignes=len(rows), ecartees=ecartees, comptes=comptes, marches=len(markets), evenements=len(events), rss_mo=round(rss_mo())), ensure_ascii=False), flush=True)
        del u
        gc.collect()
        sim = Sim(a.scenario, rows, markets, events, CONFIG, HORIZONS[a.scenario], root, grid=a.grille)
        sim.lignes_entree = len(rows)
        sim.comptes = comptes
        sim.ecartees = dict(ecartees)
        sim.duree_cumulee = 0.0
        del rows
        gc.collect()
        reprise = False
    store = Store(root)
    clock = SimTime()
    pdb.time, pbridge.time = clock, clock

    def progression(s):
        print(json.dumps(dict(s=a.scenario, tick=s.tick, reste_j=round((T_FIN - s.tick) / 86400, 2), lignes=s.i, dossiers=len(s.queue), appels=s.kernel_calls,
                              oracles=s.oracles, rss_mo=round(rss_mo()), duree_s=round(time.time() - debut))), flush=True)

    def sauve_duree():
        sim.duree_cumulee += time.time() - debut

    fini = sim.run(store, clock, checkpoint=point, stop=lambda: arret, progress=progression, avant_sauvegarde=sauve_duree)
    store.close()
    if not fini:
        print(json.dumps(dict(s=a.scenario, arret='demandé', tick=sim.tick)))
        return 5
    positions = resume_file(sim)
    sortie = dict(
        scenario=a.scenario, plan_sha256=hashlib.sha256((ETUDE / 'analysis_plan.md').read_bytes()).hexdigest(), noyau_sha256=sim_core.NOYAU_SHA,
        config_sha256=hashlib.sha256(CONFIG_FICHIER.read_bytes()).hexdigest(), grille_s=a.grille, horizon_s=HORIZONS[a.scenario], filtre=filtre, lignes_entree=sim.lignes_entree,
        comptes=sim.comptes, ecartees=sim.ecartees, limites=LIMITES, regles_de_rotation='production avec littéral' if a.scenario == 'S_L' else 'neutre, littéral retiré',
        file=positions,
        comportements=[dict(wallet=k[0], event_id=k[1], premier=v[0], score=v[1], regles=v[2], score_max=sim.max_score.get(k, 0), m1=k[1].startswith('unmapped:')) for k, v in sorted(sim.first_behavior.items())],
        wallets_vus=sorted(sim.first_ts),
        reobservations=dict(sim.reobservations), nouveaux_par_jour=dict(sim.daily_new),
        oracles=sim.oracles, appels_noyau=sim.kernel_calls, lignes_noyau=sim.kernel_rows, comparaisons=sim.comparisons,
        dossiers_ecrits=sim.dossiers, rss_max_mo_dernier_segment=rss_mo(), duree_s=sim.duree_cumulee + time.time() - debut, reprise=reprise)
    chemin = ETUDE / f'derived/R1_{a.scenario}.json.gz'
    with gzip.GzipFile(chemin, 'wb', mtime=0) as f:
        f.write(json.dumps(sortie, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    point.unlink(missing_ok=True)
    from registre import enregistrer
    enregistrer(str(ETUDE), f'R1_{a.scenario}', False, len(sim.first_ts), 'claude', n_comparaisons=max(1, sim.comparisons), sortie=str(chemin.relative_to(ETUDE)),
                params=dict(grille=a.grille, horizon=HORIZONS[a.scenario], filtre=filtre), note='Rejeu conditionnel ; aucune p-value')
    print(json.dumps(dict(s=a.scenario, fini=True, oracles=sim.oracles, rss_max_mo=round(rss_mo()), duree_s=round(sortie['duree_s']))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
