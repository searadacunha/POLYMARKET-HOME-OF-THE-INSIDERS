"""After R1: control statistics, wallet enrichment, seal, then and only then the public comparison.

Usage: ana_suite.py stats | enrichir | sceller | labels
"""
import gc
import gzip
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
from registre import enregistrer  # noqa: E402

T_ALERTES, T_FIN, T_ROT, T_DEBUT = 1791849600, 1792768669, 1790176669, 1791691200
SCENARIOS = ('S_A', 'S_C', 'S_G', 'S_B', 'S_L')
A5_PLAFOND = 100
DATA = 'https://data-api.polymarket.com'
NOYEE_72H = 50


def lit(nom):
    with gzip.open(ETUDE / f'derived/{nom}.json.gz', 'rt') as f:
        return json.load(f)


def ecrit(nom, valeur):
    chemin = ETUDE / f'derived/{nom}.json.gz'
    with gzip.GzipFile(chemin, 'wb', mtime=0) as f:
        f.write(json.dumps(valeur, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    return chemin


def ht(y, inclus, sample, second_degre):
    """Horvitz-Thompson over sampled events, with or without the within-event market weight."""
    total = 0.0
    for strate, n in sample['inclus_par_strate'].items():
        if n:
            for u in inclus:
                if u['strate'] == strate:
                    total += sample['effectifs_strates'][strate] / n * y[u['event_id']] * (1 / u['pi_marche_sachant_evenement'] if second_degre and u['pi_marche_sachant_evenement'] else 1)
    return total


def bootstrap(y, inclus, sample, second_degre, graine=20261101, tirages=2000):
    rng = random.Random(graine)
    valeurs = []
    for _ in range(tirages):
        total = 0.0
        for strate, n in sample['inclus_par_strate'].items():
            unites = [u for u in inclus if u['strate'] == strate]
            for u in (rng.choice(unites) for _ in unites):
                total += sample['effectifs_strates'][strate] / n * y[u['event_id']] * (1 / u['pi_marche_sachant_evenement'] if second_degre and u['pi_marche_sachant_evenement'] else 1)
        valeurs.append(total)
    valeurs.sort()
    return [valeurs[int(.025 * tirages)], valeurs[int(.975 * tirages) - 1]]


def stats():
    """Descriptive only: events are the clusters, strata are small, and the bootstrap is fragile."""
    sample = json.loads((ETUDE / 'data/sample.json').read_text())
    inclus = [u for u in sample['unites'] if u['statut'] == 'inclus']
    par_id = {u['event_id']: u for u in inclus}
    # Multi-market weights only hold on retained markets: the census also carries other markets' big rows.
    retenus = {}
    with gzip.open(ETUDE / 'data/control_events.jsonl.gz', 'rt') as f:
        for line in f:
            e = json.loads(line)
            u = par_id.get(str(e['id']))
            if u:
                retenus[u['event_id']] = {str(m['id']) for m in e.get('markets', []) if m.get('conditionId') in u['retenus']}
    resultat = dict(base=sample['base_evenements'], effectifs=sample['effectifs_strates'], inclus=sample['inclus_par_strate'], limite_strates='Le motif prix/sport a été testé sur le titre de la ligne la plus récente, pas celui de l’événement : la lecture par strate est fragile.', scenarios={})
    priorites = {}
    for s in SCENARIOS:
        r = lit('R1_' + s)
        y_p, y_c = Counter(), Counter()
        for e in r['file']:
            if e['at'] >= T_ALERTES and e['event_id'] in par_id and set(e['marches']) & retenus.get(e['event_id'], set()):
                y_p[e['event_id']] += 1
        for c in r['comportements']:
            if c['premier'] >= T_ALERTES and c['event_id'] in par_id and c['score_max'] >= 1:
                y_c[c['event_id']] += 1
        priorites[s] = y_p
        file_depuis = [e for e in r['file'] if e['at'] >= T_ALERTES]
        sans_m1 = [e for e in file_depuis if not e['m1']]
        par_evenement = Counter(e['event_id'] for e in file_depuis)
        jours = (T_FIN - T_ALERTES) / 86400
        catalogues = [e for e in file_depuis if e.get('announcement') is not None]
        resultat['scenarios'][s] = dict(
            dossiers_depuis_alertes=len(file_depuis), wallets_depuis_alertes=len({e['wallet'] for e in file_depuis}),
            dossiers_sans_m1=len(sans_m1), wallets_sans_m1=len({e['wallet'] for e in sans_m1}),
            dossiers_par_jour=len(file_depuis) / jours, dossiers_par_jour_sans_m1=len(sans_m1) / jours,
            evenements_distincts=len(par_evenement), top_evenements=par_evenement.most_common(10),
            part_annonce_sur_catalogues=sum(bool(e['announcement']) for e in catalogues) / len(catalogues) if catalogues else None,
            reobservations=sum(r['reobservations'].values()),
            temoins=dict(priorites=dict(y_p), comportements=dict(y_c), ht_priorites=ht(y_p, inclus, sample, False), ht_priorites_second_degre=ht(y_p, inclus, sample, True),
                         ic95_priorites=bootstrap(y_p, inclus, sample, False), ht_comportements=ht(y_c, inclus, sample, False), ic95_comportements=bootstrap(y_c, inclus, sample, False)),
            oracles=r['oracles'], lignes=r['lignes_entree'], ecartees=r['ecartees'], duree_s=r['duree_s'])
    surplus = Counter({e: priorites['S_A'][e] - priorites['S_G'][e] for e in par_id})
    resultat['surplus_petites_lignes'] = dict(par_evenement=dict(surplus), ht=ht(surplus, inclus, sample, False), ht_second_degre=ht(surplus, inclus, sample, True), ic95=bootstrap(surplus, inclus, sample, False),
                                              note='Dossiers que la visibilité des petites lignes ajouterait à S_G hors famille ; S_G ne voit ces lignes nulle part.')
    chemin = ecrit('R1_stats', resultat)
    enregistrer(str(ETUDE), 'R1_stats', False, len(inclus), 'claude', n_comparaisons=len(SCENARIOS) * 2, sortie=str(chemin.relative_to(ETUDE)), note='HT descriptif sur les témoins, aucune inférence')
    print(json.dumps({k: {x: v[x] for x in ('dossiers_depuis_alertes', 'wallets_depuis_alertes', 'dossiers_sans_m1', 'dossiers_par_jour', 'evenements_distincts', 'reobservations')} for k, v in resultat['scenarios'].items()}, ensure_ascii=False))


def enrichir():
    """A5, then a point-in-time kernel call on each wallet with the taker history the API returns.

    Order: reference queue first, then the sample-only one; wallet-level second chance noted in the plan.
    """
    from ledger import appel, compteur
    from sim_core import signals
    from charge import charge
    from univers import normalise_api, collect
    entrees = {s: {(e['wallet'], e['event_id']): e for e in lit('R1_' + s)['file']} for s in ('S_A', 'S_C')}
    ordre, vu = [], set()
    for s in ('S_A', 'S_C'):
        for e in sorted((e for e in entrees[s].values() if e['at'] >= T_ALERTES), key=lambda x: (x['at'], x['wallet'], x['event_id'])):
            if e['wallet'] not in vu:
                vu.add(e['wallet'])
                ordre.append(e['wallet'])
    u = charge(avec_lignes=False)
    config = json.loads((ETUDE / 'data/config_production.json').read_text())
    sortie = []
    interrogations = vides = 0
    with gzip.open(ETUDE / 'data/wallet_histories.jsonl.gz', 'wt', compresslevel=6) as f:
        for wallet in ordre:
            if interrogations >= A5_PLAFOND:
                break
            # No start bound: a page under the limit is then the wallet's whole taker history.
            body, recu = appel(DATA + '/trades', dict(user=wallet, end=T_FIN - 1, limit=10000, takerOnly='true'), phase='A5')
            interrogations += 1
            rows = body if isinstance(body, list) else body.get('data')
            if not isinstance(rows, list):
                raise RuntimeError('Schéma user')
            hors = [r for r in rows if int(r['timestamp']) >= T_FIN]
            if hors:
                raise RuntimeError(f'/trades user hors bornes: {len(hors)} lignes')
            tronque = len(rows) >= 10000
            vides += not rows
            normal, compte, courant, rejets = [], {}, None, 0
            for raw in sorted(rows, key=lambda r: -int(r['timestamp'])):
                mapped = {'proxy_wallet': raw.get('proxyWallet'), 'condition_id': raw.get('conditionId'), 'token_id': raw.get('asset'), 'side': raw.get('side'),
                          'size': raw.get('size'), 'price': raw.get('price'), 'timestamp': raw.get('timestamp'), 'transaction_hash': raw.get('transactionHash'),
                          'event_slug': raw.get('eventSlug'), 'slug': raw.get('slug'), 'outcome': raw.get('outcome')}
                try:
                    row = normalise_api(mapped, 1)
                except collect.SourceError:
                    rejets += 1
                    continue
                ts = row['timestamp']
                if ts != courant:
                    compte, courant = {}, ts
                compte[row['signature']] = compte.get(row['signature'], 0) + 1
                row['id'] = f"{row['signature']}:{compte[row['signature']]}"
                condition = row['condition_id'].lower()
                mid, eid = u.by_condition.get(condition, ('', ''))
                row.update(market_id=mid or 'cond:' + condition, event_id=eid)
                normal.append(row)
                f.write(json.dumps({k: row[k] for k in ('id', 'wallet', 'timestamp', 'side', 'size', 'price', 'token_id', 'condition_id', 'transaction_hash', 'event_slug')}, separators=(',', ':')) + '\n')
            premier = min((r['timestamp'] for r in normal), default=None)
            hashes = {r['transaction_hash'] for r in normal}
            for s, table in entrees.items():
                for (w, event_key), entry in table.items():
                    if w != wallet:
                        continue
                    t = entry['at']
                    connues = sorted((dict(r, observed_at=r['timestamp'] + 60) for r in normal if r['timestamp'] + 60 <= t), key=lambda r: (r['timestamp'], r['id']))
                    for r in connues:
                        if not r['event_id']:
                            u.synthetique('unmapped:' + (r.get('event_slug') or r['condition_id']), None)
                    markets = [v for m in {r['market_id'] for r in connues} for v in u.markets.get(m, ()) if v['observed_at'] <= t]
                    events = [v for e in ({r['event_id'] or 'unmapped:' + (r.get('event_slug') or r['condition_id']) for r in connues}) for v in u.events.get(e, ()) if v['observed_at'] <= t]
                    cases = signals.evaluate(connues, markets, events, now=t, config=config, wallet_history={wallet: dict(first_timestamp=premier or t, observations=0)})
                    case = next((c for c in cases if c['event_id'] == event_key), None)
                    regles = sorted({x['rule'] for x in case['signals']}) if case else []
                    familles = {x['family'] for x in case['signals'] if x['weight']} if case else set()
                    if 'synchronized_entries' in entry['rules']:
                        familles.add('synchrony')
                    estimable = bool(rows) and entry['trigger'] in hashes and not tronque
                    sortie.append(dict(wallet=wallet, event_id=event_key, scenario=s, at=t, score_avant=entry['score'], regles_avant=entry['rules'],
                                       score_historique_api=len(familles), regles_apres=regles, priorite_maintenue=(len(familles) >= 2) if estimable else None,
                                       estimable=estimable, declencheur_retrouve=entry['trigger'] in hashes, lignes_utilisateur=len(rows), lignes_connues_a_t=len(connues),
                                       marches_utilisateur_a_t=len({r['condition_id'] for r in connues}), premier_trade_api=premier,
                                       age_reel_h_a_t=(t - premier) / 3600 if premier else None, concentration_apres=next((x['value'] for x in (case['signals'] if case else ()) if x['rule'] == 'event_concentration'), None),
                                       tronque=tronque, rejets=rejets, synchronie_reportee_du_scenario='synchronized_entries' in entry['rules']))
            del body, rows, normal
            gc.collect()
            time.sleep(.2)
    resume = dict(wallets_a_enrichir=len(ordre), wallets_interroges=interrogations, reponses_vides=vides, requetes_totales=compteur(), paires_evaluees=len(sortie),
                  estimables=sum(x['estimable'] for x in sortie), maintenues=sum(x['priorite_maintenue'] is True for x in sortie), perdues=sum(x['priorite_maintenue'] is False for x in sortie), tronques=sum(x['tronque'] for x in sortie))
    chemin = ecrit('R2_enrichment', dict(resume=resume, paires=sortie, limite='Taker seulement ; synchronie reportée du scénario, non recalculée ; une réponse vide ou sans la transaction déclencheuse est non estimable'))
    enregistrer(str(ETUDE), 'R2_enrichment', False, interrogations, 'claude', n_comparaisons=max(1, len(sortie)), sortie=str(chemin.relative_to(ETUDE)), note='Fragilité aux trades hors univers')
    print(json.dumps(resume, ensure_ascii=False))


def sceller():
    chemin = ETUDE / 'derived/pre_label_seal.json'
    if chemin.exists():
        raise RuntimeError('Sceau déjà écrit : il ne se réécrit pas')
    fichiers = {}
    for nom in [f'derived/R1_{s}.json.gz' for s in SCENARIOS] + ['derived/R1_stats.json.gz', 'derived/R2_enrichment.json.gz', 'data/wallet_histories.jsonl.gz']:
        cible = ETUDE / nom
        fichiers[nom] = dict(sha256=hashlib.sha256(cible.read_bytes()).hexdigest(), octets=cible.stat().st_size)
    sceau = dict(scelle_a=time.time(), scelle_a_utc=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), fichiers=fichiers,
                 note='Sorties écrites avant toute lecture de labels_after.json par le code ; l’auteur connaît le wallet de l’affaire')
    chemin.write_text(json.dumps(sceau, indent=1, sort_keys=True))
    print(json.dumps(sceau)[:600])


def verdict(wallet, entrees, scenario):
    if wallet not in scenario['wallets_vus_set']:
        return 'NON_EVALUE'
    if entrees:
        return f"DETECTE_RANG_{entrees[0]['rank_tick']}"
    if wallet in scenario['wallets_comportement']:
        return 'COMPORTEMENT_SANS_PRIORITE'
    return 'NON_DETECTE'


def fenetres(file_complete, t):
    avant = [e for e in file_complete if e['at'] < t]
    return {f'{h}h': dict(dossiers=sum(e['at'] >= t - h * 3600 for e in avant), sans_m1=sum(e['at'] >= t - h * 3600 and not e['m1'] for e in avant),
                          wallets=len({e['wallet'] for e in avant if e['at'] >= t - h * 3600})) for h in (24, 72)}


def labels():
    sceau = json.loads((ETUDE / 'derived/pre_label_seal.json').read_text())
    for nom, fiche in sceau['fichiers'].items():
        if hashlib.sha256((ETUDE / nom).read_bytes()).hexdigest() != fiche['sha256']:
            raise RuntimeError('Sortie modifiée après scellement: ' + nom)
    source = json.loads((ETUDE.parent / 'detection_20261030/data/labels_after.json').read_text())
    resultat = dict(sceau=sceau['scelle_a_utc'], scenarios={}, n_effectif_externe=1, precision=None, rappel=None, faux_positifs=None,
                    regle_noyee=f'plus de {NOYEE_72H} dossiers nouveaux dans les 72 h précédant la première priorité',
                    note='Alias actuels, continuité non prouvée ; aucune vérité terrain')
    enrich = lit('R2_enrichment')
    for s in SCENARIOS:
        r = lit('R1_' + s)
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
                d = {k: e.get(k) for k in ('event_id', 'at', 'score', 'max_score', 'rules', 'rank_tick', 'pairs_tick', 'tied_tick', 'position_paire', 'position_wallet', 'position_paire_sans_m1', 'position_wallet_sans_m1', 'position_paire_depuis_alertes', 'position_wallet_depuis_alertes', 'announcement', 'ex_aequo_heure')}
                d['fenetres_avant'] = fenetres(r['file'], e['at'])
                d['noyee'] = d['fenetres_avant']['72h']['dossiers'] > NOYEE_72H
                details.append(d)
            lignes.append(dict(label=label['public_label'], groupe=label['source_group'], wallet=wallet, resolu=resolu, verdict=verdict(wallet, entrees, r) if resolu else 'NON_RESOLU',
                               priorites=details, comportements=comportements[:8], enrichissement=[x for x in enrich['paires'] if x['wallet'] == wallet and x['scenario'] == s]))
        resultat['scenarios'][s] = lignes
    chemin = ecrit('R3_labels', resultat)
    enregistrer(str(ETUDE), 'R3_labels', False, len(source['rows']), 'claude', n_comparaisons=len(source['rows']) * len(SCENARIOS), sortie=str(chemin.relative_to(ETUDE)), note='Comparaison publique après scellement, exploratoire')
    print('R3 écrit')


if __name__ == '__main__':
    dict(stats=stats, enrichir=enrichir, sceller=sceller, labels=labels)[sys.argv[1]]()
