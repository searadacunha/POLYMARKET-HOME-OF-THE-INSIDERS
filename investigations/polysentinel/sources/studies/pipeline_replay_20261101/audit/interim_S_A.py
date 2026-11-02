"""Partial, descriptive reading of the sealed S_A output. No label is read and no address is searched.

Written after the freeze and exploratory. It changes nothing in S_A: it checks the sealed hash, then only counts.
"""
import gzip
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
from ana_suite import T_ALERTES, T_DEBUT, T_FIN, bootstrap, ht  # noqa: E402
from charge import charge  # noqa: E402
from registre import enregistrer  # noqa: E402

SCEAU = json.loads((ETUDE / 'derived/interim_seal_S_A_20261101.json').read_text())
BRUT = (ETUDE / SCEAU['fichier']).read_bytes()
if hashlib.sha256(BRUT).hexdigest() != SCEAU['sha256']:
    raise RuntimeError('S_A differs from its seal')
R = json.loads(gzip.decompress(BRUT))
# Instant supplied by Benjamin's question and the 30 October study, with the plan's 60 s delay. A count before it, never a look at it.
INSTANT = 1791917460  # 13 October 2026 18:51:00 UTC
assert time.strftime('%d/%m %H:%M:%S', time.gmtime(INSTANT)) == '13/10 18:51:00'

sample = json.loads((ETUDE / 'data/sample.json').read_text())
inclus = [u for u in sample['unites'] if u['statut'] == 'inclus']
par_id = {u['event_id']: u for u in inclus}
retenus = {}
with gzip.open(ETUDE / 'data/control_events.jsonl.gz', 'rt') as f:
    for line in f:
        e = json.loads(line)
        u = par_id.get(str(e['id']))
        if u:
            retenus[u['event_id']] = {str(m['id']) for m in e.get('markets', []) if m.get('conditionId') in u['retenus']}
famille = {str(x) for x in charge(avec_lignes=False).family_events}


def classe(event_id):
    return 'famille_ballon' if event_id in famille else 'temoins' if event_id in par_id else 'recensement_seul'


depuis = [e for e in R['file'] if e['at'] >= T_ALERTES]
jours = (T_FIN - T_ALERTES) / 86400
par_classe = {}
for nom in ('famille_ballon', 'temoins', 'recensement_seul'):
    lignes = [e for e in depuis if classe(e['event_id']) == nom]
    comportements = [c for c in R['comportements'] if c['premier'] >= T_ALERTES and c['score_max'] >= 1 and classe(c['event_id']) == nom]
    par_classe[nom] = dict(dossiers=len(lignes), wallets=len({e['wallet'] for e in lignes}), evenements=len({e['event_id'] for e in lignes}), dossiers_sans_m1=sum(not e['m1'] for e in lignes), comportements=len(comportements), scores=dict(sorted(Counter(e['score'] for e in lignes).items())))
y_p, y_c = Counter(), Counter()
for e in depuis:
    if e['event_id'] in par_id and set(e['marches']) & retenus.get(e['event_id'], set()):
        y_p[e['event_id']] += 1
for c in R['comportements']:
    if c['premier'] >= T_ALERTES and c['event_id'] in par_id and c['score_max'] >= 1:
        y_c[c['event_id']] += 1
strates = {}
for u in inclus:
    d = strates.setdefault(u['strate'], dict(evenements=0, avec_priorite=0, priorites=0, comportements=0))
    d['evenements'] += 1
    d['avec_priorite'] += bool(y_p[u['event_id']])
    d['priorites'] += y_p[u['event_id']]
    d['comportements'] += y_c[u['event_id']]
avant = [e for e in R['file'] if e['at'] < INSTANT]
avant_alertes = [e for e in avant if e['at'] >= T_ALERTES]
fenetre = lambda h: [e for e in avant if e['at'] >= INSTANT - h * 3600]
sortie = dict(
    statut='PARTIEL : S_A seul, descriptif, sans lecture des comptes publics. Ce n\'est ni le résultat R3 ni le verdict.', sceau=SCEAU['scelle_a_utc'], r1_sha256=SCEAU['sha256'], lignes_entree=R['lignes_entree'], comptes=R['comptes'], ecartees=R['ecartees'], oracles=R['oracles'], appels_noyau=R['appels_noyau'], duree_s=R['duree_s'], limites=R['limites'],
    wallets_vus=len(R['wallets_vus']), paires_avec_comportement=len(R['comportements']), file_totale_paires=len(R['file']), file_totale_wallets=len({e['wallet'] for e in R['file']}),
    depuis_T_alertes=dict(dossiers=len(depuis), wallets=len({e['wallet'] for e in depuis}), dossiers_par_jour=len(depuis) / jours, sans_m1=sum(not e['m1'] for e in depuis), wallets_sans_m1=len({e['wallet'] for e in depuis if not e['m1']}), jours=jours),
    par_classe=par_classe, top_evenements=Counter(e['event_id'] for e in depuis).most_common(12), titres={e['event_id']: e.get('title') for e in depuis},
    temoins=dict(evenements_inclus=len(inclus), base=sample['base_evenements'], effectifs=sample['effectifs_strates'], par_strate=strates, ht_priorites=ht(y_p, inclus, sample, False), ic95_priorites=bootstrap(y_p, inclus, sample, False), ht_comportements=ht(y_c, inclus, sample, False), ic95_comportements=bootstrap(y_c, inclus, sample, False), note='Descriptif ; 13 événements seulement, strates petites, bootstrap fragile.'),
    denominateur_avant_18h51=dict(note='Comptes avant le 13/10 18:51:00 UTC. Ils ne disent pas si un wallet donné est dans la file.', depuis_T_debut=dict(paires=len(avant), wallets=len({e['wallet'] for e in avant})), depuis_T_alertes=dict(paires=len(avant_alertes), wallets=len({e['wallet'] for e in avant_alertes}), sans_m1_paires=sum(not e['m1'] for e in avant_alertes)), fenetre_24h=dict(paires=len(fenetre(24)), wallets=len({e['wallet'] for e in fenetre(24)})), fenetre_72h=dict(paires=len(fenetre(72)), wallets=len({e['wallet'] for e in fenetre(72)}))),
    nouveaux_par_jour=R['nouveaux_par_jour'], reobservations=sum(R['reobservations'].values()),
    file=[dict(position_paire=e['position_paire_depuis_alertes'], position_wallet=e['position_wallet_depuis_alertes'], at=e['at'], utc=time.strftime('%d/%m %H:%M:%S', time.gmtime(e['at'])), wallet=e['wallet'], classe=classe(e['event_id']), event_id=e['event_id'], title=e.get('title'), score=e['score'], max_score=e['max_score'], rules=e['rules'], rank_tick=e['rank_tick'], pairs_tick=e['pairs_tick'], tied_tick=e['tied_tick'], m1=e['m1'], trigger=e.get('trigger')) for e in sorted(depuis, key=lambda e: e['position_paire_depuis_alertes'])])
chemin = ETUDE / 'derived/interim_S_A_20261101.json.gz'
with gzip.GzipFile(chemin, 'wb', mtime=0) as f:
    f.write(json.dumps(sortie, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
enregistrer(str(ETUDE), 'interim_S_A', False, len(R['wallets_vus']), 'claude', n_comparaisons=1, sortie=str(chemin.relative_to(ETUDE)), note='Lecture partielle et descriptive de S_A scellé, demandée par Benjamin ; hors plan, exploratoire, aucun label lu.')
print(json.dumps({k: v for k, v in sortie.items() if k not in ('file', 'titres', 'comptes', 'limites')}, ensure_ascii=False, indent=0))
