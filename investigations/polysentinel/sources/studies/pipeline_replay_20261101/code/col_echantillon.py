"""A2 to A4: complete the truncated family streams, draw the controls, fetch their trades.

Usage: col_echantillon.py famille|tirage|temoins|catalogue. Each step is rerunnable on what it wrote.
Errors raise and every empty or truncated stream is counted; a zero is never assumed.
"""
import gzip
import hashlib
import json
import random
import re
import sqlite3
import sys
import time
import zlib
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
sys.path.insert(0, str(ETUDE / 'code/vendor'))
from ledger import appel, compteur  # noqa: E402
from polysentinel.priority import _PRICE, _SPORT  # noqa: E402

T_ROT, T_ALERTES, T_FIN = 1790176669, 1791849600, 1792768669
DATA = 'https://data-api.polymarket.com'
GAMMA = 'https://gamma-api.polymarket.com'
BALLON = ETUDE.parent / 'ballon_2026_20261030/data'
TAILLE_PAGE = 10000
EVENEMENTS_TRONQUES = ('811117', '811116', '48361')
STRATES = [('D+', 8), ('D-', 8), ('C+', 5), ('C-', 4)]
MARCHES_MAX, PAR_EVENEMENT = 50, 4
CHAMPS = {'proxyWallet': 'proxy_wallet', 'conditionId': 'condition_id', 'asset': 'token_id', 'side': 'side', 'size': 'size', 'price': 'price',
          'timestamp': 'timestamp', 'transactionHash': 'transaction_hash', 'eventSlug': 'event_slug', 'slug': 'slug', 'outcome': 'outcome',
          'outcomeIndex': 'outcome_index', 'title': 'title'}


def minimal_ancien(row):
    return {new: row[old] for old, new in CHAMPS.items() if old in row}


def marche_borne(params, debut, fin, plafond, phase, ecrire):
    """Walk a bounded /trades shape, newest to oldest. Returns the coverage actually obtained."""
    pages, lignes, borne = 0, 0, fin
    deja = {}
    while True:
        if pages >= plafond:
            return dict(pages=pages, lignes=lignes, complet=False, atteint=borne, motif='plafond de requêtes')
        body, recu = appel(DATA + '/trades', dict(params, start=debut, end=borne, limit=TAILLE_PAGE, takerOnly='true'), phase=phase)
        rows = body if isinstance(body, list) else body.get('data')
        if not isinstance(rows, list):
            raise RuntimeError('Schéma /trades inattendu: ' + str(type(body)))
        ts = [int(r['timestamp']) for r in rows]
        hors = [t for t in ts if not debut <= t <= borne]
        if hors:
            raise RuntimeError(f'/trades a rendu {len(hors)} lignes hors bornes: {params}')
        pages += 1
        nouvelles = 0
        for r in rows:
            cle = hashlib.sha256(json.dumps([r.get('proxyWallet'), r.get('transactionHash'), r.get('asset'), r.get('side'), r.get('size'), r.get('price'), r.get('timestamp')]).encode()).hexdigest()
            deja_vu = deja.get(cle, 0)
            if int(r['timestamp']) == borne and deja_vu > 0:
                deja[cle] = deja_vu - 1  # the shared timestamp was already written by the previous page
                continue
            ecrire(minimal_ancien(r))
            nouvelles += 1
        lignes += nouvelles
        if len(rows) < TAILLE_PAGE:
            return dict(pages=pages, lignes=lignes, complet=True, atteint=debut, motif='page incomplète: fenêtre épuisée')
        oldest = min(ts)
        if oldest == borne:
            raise RuntimeError(f'Page pleine sur une seule seconde {borne}: couverture inconnue')
        deja = {}
        for r in rows:
            if int(r['timestamp']) == oldest:
                cle = hashlib.sha256(json.dumps([r.get('proxyWallet'), r.get('transactionHash'), r.get('asset'), r.get('side'), r.get('size'), r.get('price'), r.get('timestamp')]).encode()).hexdigest()
                deja[cle] = deja.get(cle, 0) + 1
        borne = oldest
        time.sleep(.25)


def famille():
    """Round-robin would cost more calls than it saves: the three streams are walked in plan order."""
    sortie = ETUDE / 'data/family_extra.jsonl.gz'
    resume = {}
    restant = 15
    with gzip.open(sortie, 'wt', compresslevel=6) as f:
        for event in EVENEMENTS_TRONQUES:
            def ecrire(row, _f=f, _e=event):
                _f.write(json.dumps(dict(row, source_event=_e), separators=(',', ':')) + '\n')
            couverture = marche_borne(dict(eventId=event), T_ROT, T_FIN - 1, restant, 'A2', ecrire) if restant else dict(pages=0, lignes=0, complet=False, atteint=None, motif='budget A2 épuisé')
            resume[event] = couverture
            restant -= couverture['pages']
    (ETUDE / 'data/family_extra_summary.json').write_text(json.dumps(dict(resume=resume, requetes=compteur()), indent=1))
    print(json.dumps(resume))


def slugs_famille():
    slugs, ids = set(), set()
    for name in ('catalog_refreshed.json', 'catalog_search.json'):
        data = json.loads((BALLON / name).read_text())
        for item in data.get('events', data if isinstance(data, list) else []):
            event = item.get('event', item) if isinstance(item, dict) else {}
            if event.get('slug'):
                slugs.add(event['slug'])
            if event.get('id'):
                ids.add(str(event['id']))
    return slugs, ids


def tirage():
    """The draw itself: no score exists yet, and the seed is the census file's hash."""
    census = ETUDE / 'data/global_window.jsonl.gz'
    graine = hashlib.sha256(census.read_bytes()).hexdigest()
    exclus, ids = slugs_famille()
    compte, titres = {}, {}
    with gzip.open(census, 'rt') as f:
        for line in f:
            r = json.loads(line)
            if int(r['timestamp']) >= T_ALERTES and r.get('event_slug'):
                compte[r['event_slug']] = compte.get(r['event_slug'], 0) + 1
                titres.setdefault(r['event_slug'], r.get('title') or '')
    strates = {s: [] for s, _ in STRATES}
    for slug in sorted(compte):
        if slug in exclus:
            continue
        continu = bool(_PRICE.search(titres[slug]) or _SPORT.search(titres[slug]))
        strates[('C' if continu else 'D') + ('+' if compte[slug] >= 20 else '-')].append(slug)
    rng = random.Random(int(graine, 16))
    candidats = {}
    for strate, n in STRATES:
        tires = list(strates[strate])
        rng.shuffle(tires)
        candidats[strate] = tires[:n]
    ordre = []
    for i in range(max(n for _, n in STRATES)):
        for strate, _ in STRATES:
            if i < len(candidats[strate]):
                ordre.append((strate, candidats[strate][i]))
    retenus, total, arret = [], 0, None
    catalogue = gzip.open(ETUDE / 'data/control_events.jsonl.gz', 'wt')
    for strate, slug in ordre:
        if total >= MARCHES_MAX:
            arret = 'plafond de marchés atteint'
            break
        body, recu = appel(GAMMA + '/events/slug/' + slug, {}, phase='A3')
        if not isinstance(body, dict) or not body.get('id'):
            raise RuntimeError('Événement Gamma invalide: ' + slug)
        marches = [m for m in body.get('markets', []) if m.get('conditionId')]
        if not marches:
            retenus.append(dict(strate=strate, slug=slug, event_id=str(body['id']), M=0, retenus=[], statut='aucun marché exploitable'))
            continue
        tire = sorted(m['conditionId'] for m in marches)
        random.Random(int(hashlib.sha256((graine + slug).encode()).hexdigest(), 16)).shuffle(tire)
        tire = sorted(tire[:PAR_EVENEMENT])
        if total + len(tire) > MARCHES_MAX:
            arret = f'{slug} dépasserait {MARCHES_MAX} marchés'
            retenus.append(dict(strate=strate, slug=slug, event_id=str(body['id']), M=len(marches), retenus=[], statut=arret))
            break
        total += len(tire)
        retenus.append(dict(strate=strate, slug=slug, event_id=str(body['id']), M=len(marches), retenus=tire, statut='inclus'))
        catalogue.write(json.dumps(body, separators=(',', ':')) + '\n')
    catalogue.close()
    effectifs = {s: len(v) for s, v in strates.items()}
    inclus = {s: sum(1 for r in retenus if r['strate'] == s and r['statut'] == 'inclus') for s, _ in STRATES}
    for r in retenus:
        r['pi_evenement'] = inclus[r['strate']] / effectifs[r['strate']] if effectifs[r['strate']] else None
        r['pi_marche_sachant_evenement'] = len(r['retenus']) / r['M'] if r['M'] else None
    out = dict(graine=graine, base_evenements=sum(effectifs.values()), exclus_famille=len([s for s in compte if s in exclus]),
               effectifs_strates=effectifs, candidats=candidats, inclus_par_strate=inclus, marches=total, arret=arret, unites=retenus, requetes=compteur())
    (ETUDE / 'data/sample.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k not in ('unites', 'candidats', 'graine')}))


def temoins():
    sample = json.loads((ETUDE / 'data/sample.json').read_text())
    sortie = ETUDE / 'data/controls.jsonl.gz'
    couverture = {}
    restant = 40
    with gzip.open(sortie, 'wt', compresslevel=6) as f:
        for unite in sample['unites']:
            if unite['statut'] != 'inclus':
                continue
            def ecrire(row, _f=f, _s=unite['slug']):
                _f.write(json.dumps(dict(row, source_event=_s), separators=(',', ':')) + '\n')
            if restant <= 0:
                couverture[unite['slug']] = dict(pages=0, lignes=0, complet=False, atteint=None, motif='budget A4 épuisé')
                continue
            res = marche_borne(dict(market=','.join(unite['retenus'])), T_ROT, T_FIN - 1, min(3, restant), 'A4', ecrire)
            couverture[unite['slug']] = res
            restant -= res['pages']
    (ETUDE / 'data/controls_summary.json').write_text(json.dumps(dict(couverture=couverture, requetes=compteur()), indent=1))
    print(json.dumps(dict(evenements=len(couverture), complets=sum(v['complet'] for v in couverture.values()), lignes=sum(v['lignes'] for v in couverture.values()), requetes=compteur())))


def catalogue():
    """Stream the production catalogue once, read-only, keeping only conditions the census saw."""
    conditions = set()
    with gzip.open(ETUDE / 'data/global_window.jsonl.gz', 'rt') as f:
        for line in f:
            conditions.add(json.loads(line)['condition_id'].lower())
    db = ETUDE.parent.parent / 'data/polysentinel.sqlite3'
    cx = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=10)
    garder = ('createdAt', 'closedTime', 'startDate', 'endDate', 'resolutionSource', 'sportsMarketType', 'gameId', 'umaResolutionStatus', 'negRisk', 'groupItemTitle')
    markets, events_wanted = {}, set()
    vus = 0
    for body, in cx.execute("SELECT c.body FROM object_refs r JOIN contents c ON c.id=r.content_id WHERE r.kind='market'"):
        vus += 1
        m = json.loads(zlib.decompress(body))
        if str(m.get('condition_id', '')).lower() in conditions:
            raw = m.get('raw') or {}
            markets[m['id']] = dict(id=m['id'], event_id=str(m['event_id']), condition_id=m['condition_id'], question=m.get('question'),
                                    end_date=m.get('end_date'), tokens=m.get('tokens', []), mapping_quality=m.get('mapping_quality'),
                                    raw={k: raw[k] for k in garder if raw.get(k) is not None}, snapshot_observed_at=m.get('observed_at'))
            events_wanted.add(str(m['event_id']))
    events = {}
    for key, body in cx.execute("SELECT r.key,c.body FROM object_refs r JOIN contents c ON c.id=r.content_id WHERE r.kind='event'"):
        if key in events_wanted:
            e = json.loads(zlib.decompress(body))
            raw = e.get('raw') or {}
            events[key] = dict(id=key, title=e.get('title'), slug=e.get('slug'), tags=e.get('tags', []), end_date=e.get('end_date'),
                               raw={k: raw[k] for k in garder if raw.get(k) is not None}, snapshot_observed_at=e.get('observed_at'))
    cx.close()
    with gzip.open(ETUDE / 'data/catalog_local.json.gz', 'wt', compresslevel=6) as f:
        json.dump(dict(markets=markets, events=events), f, separators=(',', ':'))
    out = dict(conditions_recensement=len(conditions), marches_lus=vus, marches_retenus=len(markets), evenements_retenus=len(events),
               conditions_sans_metadonnee=len(conditions - {m['condition_id'].lower() for m in markets.values()}))
    (ETUDE / 'data/catalog_local_summary.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


if __name__ == '__main__':
    dict(famille=famille, tirage=tirage, temoins=temoins, catalogue=catalogue)[sys.argv[1]]()
