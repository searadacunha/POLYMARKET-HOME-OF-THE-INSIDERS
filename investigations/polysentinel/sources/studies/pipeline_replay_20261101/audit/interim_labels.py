"""Amendment 001: compares the sealed S_A and the sealed beginning of S_C with the public accounts.

Partial and conditional. Refuses to read a label unless both seals match their files. Changes no ranking.
"""
import gzip
import hashlib
import json
import pickle
import re
import sys
import time
from collections import Counter
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
from ana_suite import NOYEE_72H, T_ALERTES, fenetres, verdict  # noqa: E402
from charge import charge  # noqa: E402
from registre import enregistrer  # noqa: E402
from sim_core import BUY, OBS, TS, TX, EK, W  # noqa: E402

UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t)) if t else None
sceaux = {n: json.loads((ETUDE / f).read_text()) for n, f in (('S_A', 'derived/interim_seal_S_A_20261101.json'), ('S_C', 'derived/interim_seal_S_C_prefix_20261101.json'))}
sorties = {}
for nom, sceau in sceaux.items():
    brut = (ETUDE / sceau['fichier']).read_bytes()
    if hashlib.sha256(brut).hexdigest() != sceau['sha256']:
        raise RuntimeError('Differs from its seal: ' + nom)
    sorties[nom] = json.loads(gzip.decompress(brut))
copie = Path(sceaux['S_C']['copie_persistante'])
if hashlib.sha256((copie / 'checkpoint.pickle').read_bytes()).hexdigest() != sceaux['S_C']['checkpoint_sha256']:
    raise RuntimeError('Sealed checkpoint copy differs')
# Past this line the public accounts are read.
source = json.loads((ETUDE.parent / 'detection_20261030/data/labels_after.json').read_text())
sim = pickle.loads((copie / 'checkpoint.pickle').read_bytes())
sample = json.loads((ETUDE / 'data/sample.json').read_text())
temoins = {u['event_id']: u for u in sample['unites'] if u['statut'] == 'inclus'}
famille = {str(x) for x in charge(avec_lignes=False).family_events}
classe = lambda e: 'famille' if e in famille else 'temoins' if e in temoins else 'recensement_seul'
fin = {'S_A': None, 'S_C': sorties['S_C']['dernier_tick_calcule']}


def histoire(wallet):
    """What the replay held for this wallet at the stop. Every row must have been visible by then."""
    rows = sim.by_wallet.get(wallet, [])
    return dict(lignes=len(rows), achats=sum(bool(r[BUY]) for r in rows), premiere=UTC(min((r[TS] for r in rows), default=None)), derniere_vue=UTC(max((r[OBS] for r in rows), default=None)), futur=sum(r[OBS] > sorties['S_C']['dernier_tick_calcule'] for r in rows), evenements=dict(Counter(r[EK] for r in rows).most_common(6)))


resultat = dict(statut='PARTIEL ET CONDITIONNEL, amendement 001. Aucune validation indépendante. Les comptes publics ne sont pas une vérité terrain.', sceaux={k: v['sha256'] for k, v in sceaux.items()}, s_c_arret=UTC(sorties['S_C']['dernier_tick_calcule']), part_s_c=sorties['S_C']['part_de_la_periode'], scenarios={}, resumes={}, precision=None, rappel=None, faux_positifs=None)
for nom, r in sorties.items():
    r['wallets_vus_set'] = set(r['wallets_vus'])
    r['wallets_comportement'] = {c['wallet'] for c in r['comportements'] if c['score_max'] >= 1}
    lignes = []
    for label in source['rows']:
        resolu = bool(label.get('wallet')) and label.get('mapping_status') == 'exact_current_profile_alias'
        wallet = label['wallet'].lower() if resolu else None
        entrees = sorted((e for e in r['file'] if e['wallet'] == wallet), key=lambda e: e['at']) if wallet else []
        comportements = sorted((c for c in r['comportements'] if c['wallet'] == wallet), key=lambda c: c['premier']) if wallet else []
        details = []
        for e in entrees:
            avant = [x for x in r['file'] if x['at'] < e['at']]
            d = {k: e.get(k) for k in ('event_id', 'title', 'at', 'score', 'max_score', 'rules', 'rank_tick', 'pairs_tick', 'tied_tick', 'position_paire', 'position_wallet', 'position_paire_depuis_alertes', 'position_wallet_depuis_alertes', 'position_paire_sans_m1', 'position_wallet_sans_m1', 'ex_aequo_heure', 'm1', 'trigger', 'nouveau_wallet', 'marches', 'announcement')}
            d['utc'] = UTC(e['at'])
            d['classe'] = classe(e['event_id'])
            d['wallets_avant'] = len({x['wallet'] for x in avant})
            d['dossiers_avant'] = len(avant)
            d['avant_par_classe'] = dict(Counter(classe(x['event_id']) for x in avant))
            d['fenetres_avant'] = fenetres(r['file'], e['at'])
            d['noyee'] = d['fenetres_avant']['72h']['dossiers'] > NOYEE_72H
            details.append(d)
        ligne = dict(label=label['public_label'], groupe=label['source_group'], wallet=wallet, resolu=resolu, mapping=label.get('mapping_status'), verdict=verdict(wallet, entrees, r) if resolu else 'NON_RESOLU', priorites=details, comportements=comportements[:6], vu=bool(wallet and wallet in r['wallets_vus_set']))
        if wallet and nom == 'S_C':
            ligne['historique_au_point_d_arret'] = histoire(wallet)
        lignes.append(ligne)
    resultat['scenarios'][nom] = lignes
    resultat['resumes'][nom] = dict(wallets_analyses=len(r['wallets_vus']), paires_comportement=len(r['comportements']), file_paires=len(r['file']), file_wallets=len({e['wallet'] for e in r['file']}), file_par_classe=dict(Counter(classe(e['event_id']) for e in r['file'])), wallets_par_classe={c: len({e['wallet'] for e in r['file'] if classe(e['event_id']) == c}) for c in ('famille', 'temoins', 'recensement_seul')},
                                    temoins_par_evenement=[(temoins[k]['strate'], temoins[k]['slug'], v) for k, v in Counter(e['event_id'] for e in r['file'] if e['event_id'] in temoins).most_common()], familles_par_evenement=Counter(e['event_id'] for e in r['file'] if e['event_id'] in famille).most_common(), comptes=r.get('comptes'), oracles=r['oracles'])
chemin = ETUDE / 'derived/interim_R3_20261101.json.gz'
if chemin.exists():
    raise RuntimeError('Already written')
with gzip.GzipFile(chemin, 'wb', mtime=0) as f:
    f.write(json.dumps(resultat, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode())
enregistrer(str(ETUDE), 'interim_R3', False, len(source['rows']), 'claude', n_comparaisons=len(source['rows']) * 2, sortie=str(chemin.relative_to(ETUDE)), note='Comparaison intermédiaire, amendement 001 ; exploratoire, partielle, conditionnelle.')
print('ecrit', hashlib.sha256(chemin.read_bytes()).hexdigest()[:16])
