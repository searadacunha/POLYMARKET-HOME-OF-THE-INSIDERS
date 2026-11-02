"""Amendment 001, S_A only, asked separately by Benjamin. Partial and conditional. Reads no other scenario and changes no ranking."""
import gzip
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
from ana_suite import NOYEE_72H, T_ALERTES, fenetres, verdict  # noqa: E402
from charge import charge  # noqa: E402
from registre import enregistrer  # noqa: E402

sceau = json.loads((ETUDE / 'derived/interim_seal_S_A_20261101.json').read_text())
brut = (ETUDE / sceau['fichier']).read_bytes()
if hashlib.sha256(brut).hexdigest() != sceau['sha256']:
    raise RuntimeError('S_A differs from its seal')
r = json.loads(gzip.decompress(brut))
source = json.loads((ETUDE.parent / 'detection_20261030/data/labels_after.json').read_text())
sample = json.loads((ETUDE / 'data/sample.json').read_text())
temoins = {u['event_id']: u for u in sample['unites'] if u['statut'] == 'inclus'}
famille = {str(x) for x in charge(avec_lignes=False).family_events}
classe = lambda e: 'famille' if e in famille else 'temoins' if e in temoins else 'recensement_seul'
r['wallets_vus_set'] = set(r['wallets_vus'])
r['wallets_comportement'] = {c['wallet'] for c in r['comportements'] if c['score_max'] >= 1}
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
lignes = []
for label in source['rows']:
    resolu = bool(label.get('wallet')) and label.get('mapping_status') == 'exact_current_profile_alias'
    wallet = label['wallet'].lower() if resolu else None
    entrees = sorted((e for e in r['file'] if e['wallet'] == wallet), key=lambda e: e['at']) if wallet else []
    comportements = sorted((c for c in r['comportements'] if c['wallet'] == wallet), key=lambda c: c['premier']) if wallet else []
    details = []
    for e in entrees:
        avant = [x for x in r['file'] if x['at'] < e['at']]
        details.append(dict(event_id=e['event_id'], title=e.get('title'), utc=UTC(e['at']), classe=classe(e['event_id']), score=e['score'], max_score=e['max_score'], rules=e['rules'], rank_tick=e['rank_tick'], pairs_tick=e['pairs_tick'], tied_tick=e['tied_tick'], position_wallet=e['position_wallet'], position_paire=e['position_paire'], position_wallet_depuis_alertes=e['position_wallet_depuis_alertes'], position_wallet_sans_m1=e['position_wallet_sans_m1'], wallets_avant=len({x['wallet'] for x in avant}), dossiers_avant=len(avant), trigger=e.get('trigger'), fenetres=fenetres(r['file'], e['at'])))
    lignes.append(dict(label=label['public_label'], groupe=label['source_group'], wallet=wallet, resolu=resolu, mapping=label.get('mapping_status'), vu=bool(wallet and wallet in r['wallets_vus_set']), verdict=verdict(wallet, entrees, r) if resolu else 'NON_RESOLU', priorites=details, comportements=[dict(c, utc=UTC(c['premier'])) for c in comportements[:6]]))
sortie = dict(statut='PARTIEL ET CONDITIONNEL : S_A seul, amendement 001. Aucune validation indépendante. Les comptes publics ne sont pas une vérité terrain.', sceau=sceau['sha256'], wallets_vus=len(r['wallets_vus']), paires_comportement=len(r['comportements']), file_paires=len(r['file']), file_wallets=len({e['wallet'] for e in r['file']}), comptes=r['comptes'], lignes=lignes, precision=None, rappel=None, faux_positifs=None)
chemin = ETUDE / 'derived/interim_R3_S_A_20261101.json.gz'
with gzip.GzipFile(chemin, 'wb', mtime=0) as f:
    f.write(json.dumps(sortie, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
enregistrer(str(ETUDE), 'interim_R3_S_A', False, len(source['rows']), 'claude', n_comparaisons=len(source['rows']), sortie=str(chemin.relative_to(ETUDE)), note='Comparaison intermédiaire S_A seul, amendement 001 ; exploratoire, partielle, conditionnelle.')
print(json.dumps({k: v for k, v in sortie.items() if k not in ('lignes', 'comptes')}, ensure_ascii=False))
for l in lignes:
    print(json.dumps(dict(label=l['label'], groupe=l['groupe'], wallet=(l['wallet'] or '')[:12], resolu=l['resolu'], vu=l['vu'], verdict=l['verdict'], n_priorites=len(l['priorites']), priorites=[{k: p[k] for k in ('utc', 'event_id', 'classe', 'score', 'rules', 'rank_tick', 'pairs_tick', 'tied_tick', 'position_wallet', 'wallets_avant', 'dossiers_avant', 'position_wallet_depuis_alertes', 'position_wallet_sans_m1')} for p in l['priorites'][:2]], comportements=[(c['utc'], c['event_id'], c['score_max'], c['regles']) for c in l['comportements'][:3]]), ensure_ascii=False))
