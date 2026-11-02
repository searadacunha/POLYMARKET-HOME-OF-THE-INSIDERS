"""Label-free output of S_C's beginning, read from a sealed copy of a clean checkpoint. Amendment 001.

The run is causal: nothing after the stop can change what precedes it. Reads the checkpoint, writes nothing
into the replay's sandbox, and refuses a state where a row or a queue entry lies after the stop.
Usage: interim_S_C_prefix.py COPY_DIR [--essai]
"""
import gzip
import hashlib
import json
import pickle
import sys
import time
from collections import Counter
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
import sim_core  # noqa: E402
from ana_replay import resume_file  # noqa: E402
from registre import enregistrer  # noqa: E402
from sim_core import ID, OBS, TS, T_ALERTES, T_DEBUT, T_FIN, T_ROT  # noqa: E402

CIBLE = 1791917460  # 13 October 18:51:00 UTC
copie = Path(sys.argv[1])
essai = '--essai' in sys.argv
brut = (copie / 'checkpoint.pickle').read_bytes()
manifeste = json.loads((copie / 'MANIFEST.json').read_text())
if hashlib.sha256(brut).hexdigest() != manifeste['sha256']['checkpoint.pickle']:
    raise RuntimeError('Checkpoint differs from its manifest')
sim = pickle.loads(brut)
if (sim.name, sim.grid, sim.horizon) != ('S_C', 60, None):
    raise RuntimeError(f'Unexpected run: {sim.name} {sim.grid} {sim.horizon}')
if not essai and sim.tick <= CIBLE:
    raise RuntimeError(f'Checkpoint at {sim.tick}, before the target')
# Causality, checked on the state itself: nothing visible yet may come from after the stop.
dernier = sim.tick - sim.grid
vues = sum(len(v) for v in sim.by_wallet.values())
if any(r[OBS] > dernier or r[TS] > r[OBS] for rows in sim.by_wallet.values() for r in rows):
    raise RuntimeError('A row in the state lies after the stop, or was seen before it happened')
if sim.i < len(sim.pending) and sim.pending[sim.i][OBS] <= dernier:
    raise RuntimeError('A due row was not ingested')
if vues != sim.i:
    raise RuntimeError(f'{vues} rows held, {sim.i} ingested')
if any(e['at'] > dernier for e in sim.queue):
    raise RuntimeError('A queue entry lies after the stop')
if any(sim.pending[j][OBS] > sim.pending[j + 1][OBS] for j in range(max(0, sim.i - 2000), min(len(sim.pending) - 1, sim.i + 2000))):
    raise RuntimeError('Rows out of order around the stop')
positions = resume_file(sim)
sortie = dict(
    statut='PARTIEL ET CONDITIONNEL : début de S_C seul, arrêt propre. Amendement 001. Ni R1 complet, ni verdict final.', scenario='S_C', arret_tick=sim.tick, dernier_tick_calcule=dernier, arret_utc=time.strftime('%d/%m %H:%M:%S', time.gmtime(dernier)), part_de_la_periode=(dernier - T_DEBUT) / (T_FIN - T_DEBUT),
    grille_s=sim.grid, horizon_s=sim.horizon, lignes_entree=sim.lignes_entree, lignes_ingerees=sim.i, comptes=sim.comptes, ecartees=sim.ecartees, oracles=sim.oracles, appels_noyau=sim.kernel_calls, comparaisons=sim.comparisons, dossiers_ecrits=sim.dossiers, duree_s=sim.duree_cumulee,
    premiere_ligne_ts=min(r[TS] for rows in sim.by_wallet.values() for r in rows), derniere_ligne_vue_obs=max(r[OBS] for rows in sim.by_wallet.values() for r in rows), plancher_T_ROT=T_ROT,
    file=positions, comportements=[dict(wallet=k[0], event_id=k[1], premier=v[0], score=v[1], regles=v[2], score_max=sim.max_score.get(k, 0), m1=k[1].startswith('unmapped:')) for k, v in sorted(sim.first_behavior.items())], wallets_vus=sorted(sim.first_ts), reobservations=dict(sim.reobservations), nouveaux_par_jour=dict(sim.daily_new),
    checkpoint_sha256=manifeste['sha256']['checkpoint.pickle'], base_sha256=manifeste['sha256']['polysentinel.sqlite3'], base_lignes_apres_le_point=manifeste['base']['lignes_apres_le_point'], noyau_sha256=sim_core.NOYAU_SHA)
resume = {k: v for k, v in sortie.items() if k not in ('file', 'comportements', 'wallets_vus', 'comptes', 'reobservations', 'nouveaux_par_jour', 'statut')}
resume.update(wallets=len(sortie['wallets_vus']), paires_comportement=len(sortie['comportements']), file_paires=len(positions), file_wallets=len({e['wallet'] for e in positions}))
print(json.dumps(resume, ensure_ascii=False, indent=0))
if not essai:
    chemin = ETUDE / 'derived/interim_S_C_prefix_20261101.json.gz'
    if chemin.exists():
        raise RuntimeError('Already written')
    with gzip.GzipFile(chemin, 'wb', mtime=0) as f:
        f.write(json.dumps(sortie, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    empreinte = hashlib.sha256(chemin.read_bytes()).hexdigest()
    sceau = dict(portee='PARTIEL : début de S_C, amendement 001. Ne remplace pas derived/pre_label_seal.json.', scelle_a=time.time(), scelle_a_utc=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), fichier=str(chemin.relative_to(ETUDE)), sha256=empreinte, octets=chemin.stat().st_size,
                 checkpoint_sha256=sortie['checkpoint_sha256'], base_sha256=sortie['base_sha256'], arret_tick=sim.tick, labels_lus=False, copie_persistante=str(copie), s_a=json.loads((ETUDE / 'derived/interim_seal_S_A_20261101.json').read_text())['sha256'], note='Sceau écrit avant toute lecture des comptes publics. Horloge locale : pas un horodatage indépendant.')
    (ETUDE / 'derived/interim_seal_S_C_prefix_20261101.json').write_text(json.dumps(sceau, indent=1, sort_keys=True, ensure_ascii=False) + '\n')
    enregistrer(str(ETUDE), 'interim_S_C_prefix', False, len(sortie['wallets_vus']), 'claude', n_comparaisons=max(1, sim.comparisons), sortie=str(chemin.relative_to(ETUDE)), params=dict(arret_tick=sim.tick, grille=sim.grid), note='Début de S_C, arrêt propre, amendement 001 ; aucune p-value, aucun label lu.')
    print('sceau', sceau['scelle_a_utc'], empreinte[:16])
