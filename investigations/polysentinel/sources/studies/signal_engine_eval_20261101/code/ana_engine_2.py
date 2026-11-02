"""The frozen copy of the engine over the pilot's reference rows, in a private store. Usage: ana_engine.py clean|injected|thinned"""
import gc
import gzip
import hashlib
import json
import os
import random
import resource
import signal
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
RACINE = ETUDE.parent.parent
REJEU = ETUDE.parent / 'pipeline_replay_20261101'
BALLON = ETUDE.parent / 'ballon_2026_20261030/data'
sys.path.insert(0, str(ETUDE / 'code/vendor_engine_2'))
sys.path.insert(0, str(REJEU / 'code'))
sys.path.insert(0, str(ETUDE / 'code'))

from signal_engine.prospective_detection import apply_review_budget, load_config, run_cycle  # noqa: E402
from signal_engine.store import SignalStore  # noqa: E402
from charge import charge  # noqa: E402
from univers import scenario_lignes, instant  # noqa: E402
from sim_core import T_DEBUT, T_ALERTES, T_FIN  # noqa: E402

GRILLE = 300
BAC = Path(os.environ.get('PS_BAC', '/private/tmp/claude-501/-Users-benjamindacunha/ddbd5b1b-5e0b-4f3f-a192-c52d7c1360eb/scratchpad/bac')) / 'engine'
MONTANTS = (2500, 5000, 10000, 25000, 50000, 100000)
TITRE_INJECTE = 'Will the company announce the synthetic merger before the deadline?'
arret = False


def demande_arret(*_):
    global arret
    arret = True


def motifs():
    """Synthetic events: their keys start with inj and can never match a real row."""
    plan, lignes = [], []
    envol = T_FIN - T_ALERTES - 3 * 86400
    n = 0
    for nb_wallets, repetitions in ((3, 6), (1, 3)):
        for _ in range(repetitions):
            for montant in MONTANTS:
                debut = T_ALERTES + 86400 + int(envol * (n + .5) / 54)
                plan.append(dict(id=n, event_key=f'inj:{n}', wallets=nb_wallets, montant=montant, debut=debut))
                for k in range(nb_wallets):
                    ts = debut + 400 * k
                    lignes.append(dict(key=f'inj{n}:{k}', wallet=f'0xinj{n}w{k}', ts=ts, observed_at=ts + 60, event_key=f'inj:{n}', market_id=f'cond:inj{n}', condition_id=f'inj{n}', token_id=f'tokinj{n}', is_buy=True, size=montant / .2, price=.2, tx=f'0xinj{n}t{k}'))
                n += 1
    return plan, lignes


def catalogue(store, u):
    """Rules, tags and dates from the raw Gamma objects of the sampled events; the census keeps its row titles."""
    vus = set()
    sources = [item['event'] for item in json.loads((BALLON / 'catalog_refreshed.json').read_text())['events']]
    with gzip.open(REJEU / 'data/control_events.jsonl.gz', 'rt') as f:
        sources += [json.loads(line) for line in f]
    for event in sources:
        tags = [t['slug'] for t in event.get('tags', []) if isinstance(t, dict) and t.get('slug')]
        for m in event.get('markets', []):
            if not m.get('conditionId'):
                continue
            closed = instant(m.get('closedTime'))
            condition = m['conditionId'].lower()
            vus.add(condition)
            store.add_market(condition, title=m.get('question'), event_key=str(event['id']), market_id=str(m['id']), end_at=instant(m.get('endDate')), closed_at=closed if closed and closed <= T_FIN else None,
                             rules=m.get('description'), tags=tags, sports=bool(m.get('sportsMarketType') or m.get('gameId')), neg_risk=bool(m.get('negRisk')), group_title=m.get('groupItemTitle'), cataloged=True)
    return vus


def main():
    passe = sys.argv[1]
    if passe not in ('clean', 'injected', 'thinned'):
        raise SystemExit('clean, injected ou thinned')
    signal.signal(signal.SIGTERM, demande_arret)
    BAC.mkdir(parents=True, exist_ok=True)
    chemin = BAC / f'{passe}.sqlite3'
    for suffixe in ('', '-wal', '-shm'):
        Path(str(chemin) + suffixe).unlink(missing_ok=True)
    config = load_config()
    store = SignalStore(chemin)
    filtre = json.loads((REJEU / 'data/global_state.json').read_text())['filtre']
    u = charge()
    source = sorted(scenario_lignes(u, 'S_A', filtre), key=lambda r: (r[1], r[14]))
    vus = catalogue(store, u)
    for r in source:
        if r[10] not in vus:
            vus.add(r[10])
            store.add_market(r[10], title=u.titres.get(r[10]), event_key=r[15], market_id=r[8])
    if passe == 'thinned':
        tirage = random.Random(20261101)
        source = [r for r in source if tirage.random() >= .1]
    plan, injectees = ([], [])
    if passe == 'injected':
        plan, injectees = motifs()
        for m in plan:
            store.add_market(f"inj{m['id']}", title=TITRE_INJECTE, event_key=m['event_key'], market_id=f"cond:inj{m['id']}", end_at=T_FIN + 30 * 86400, cataloged=True)
    famille = set(u.family_events)
    temoins = set(u.control_events)
    entree = dict(lignes=len(source), comptes=u.comptes, plan_sha256=hashlib.sha256((ETUDE / 'analysis_plan.md').read_bytes()).hexdigest(), configuration=config['version'])
    del u
    gc.collect()
    arrivees = sorted(injectees, key=lambda r: r['observed_at'])
    i = j = 0
    categories, risques, par_jour, trouvailles, totaux = Counter(), Counter(), defaultdict(Counter), Counter(), Counter()
    revues_jour = Counter()
    emissions = []
    injections = {m['event_key']: dict(m, categorie_max=None, premier=None, revue=False, trouvailles=[]) for m in plan}
    ordre = {'EXPLORATORY': 1, 'ANOMALOUS': 2, 'CORROBORATED_BEHAVIOR': 3}
    debut = time.time()
    for tick in range(T_DEBUT, T_FIN, GRILLE):
        lot = []
        while i < len(source) and source[i][1] <= tick:
            r = source[i]
            lot.append(dict(key=r[14], wallet=r[2], ts=r[0], observed_at=r[1], event_key=r[15], market_id=r[8], condition_id=r[10], token_id=r[3], is_buy=r[4], size=r[5], price=r[6], tx=r[7], outcome=r[13]))
            i += 1
        while j < len(arrivees) and arrivees[j]['observed_at'] <= tick:
            lot.append(arrivees[j])
            j += 1
        if lot:
            touchees = store.add_trades(lot)
            sorties, resume = run_cycle(store, touchees, tick, config, emit=tick >= T_ALERTES)
            totaux.update(resume)
            jour = str(tick // 86400)
            reelles = [s for s in sorties if not s['continuous_market'] and not s['event_key'].startswith('inj:')]
            apply_review_budget(reelles, revues_jour[jour], config)
            for s in sorties:
                vues = Counter(f for p in s['pairs'] for f in list(p['wallet_findings']) + list(p['position_findings']))
                if s['event_key'].startswith('inj:'):
                    res = injections[s['event_key']]
                    if ordre[s['category']] > ordre.get(res['categorie_max'], 0):
                        res['categorie_max'] = s['category']
                    res['premier'] = res['premier'] or s['at']
                    res['revue'] = res['revue'] or s['wants_review']
                    res['trouvailles'] = sorted(set(res['trouvailles']) | set(vues))
                    continue
                categories[s['category']] += 1
                risques[s['risk']['level']] += 1
                nature = 'continu' if s['continuous_market'] else 'discret'
                par_jour[jour][f"{nature}|{s['category']}"] += s['new_case']
                if s['wants_review'] and not s['already_review']:
                    revues_jour[jour] += 1
                trouvailles.update(vues)
                emissions.append(dict(event_key=s['event_key'], titre=s.get('title'), at=s['at'], version=s['version'], nouveau=s['new_case'], categorie=s['category'], revue=s['wants_review'], retenu_par_plafond=s.get('budget_held', False), nature=nature, risque=s['risk']['level'], structure=s['risk']['decision_structure'], confiance=s['risk']['confidence'],
                                      m1=s['event_key'].startswith('unmapped:'), famille=s['event_key'] in famille, temoin=s['event_key'] in temoins, marche_ouvert=s['market_open'], wallets=[dict(wallet=p['wallet'], trouvailles=sorted(list(p['wallet_findings']) + list(p['position_findings'])), mise=p['measures']['max_market_spend'], prix=p['position']['entry_vwap'], tx=p['position']['largest_tx']) for p in s['pairs']], convergence=len(s['collective']['convergence']), montants=len(s['collective']['identical_amounts']), repetes=len(s['collective']['repeated_across_events']), rang=s['rank']))
        if arret:
            print(json.dumps(dict(passe=passe, arret=True, tick=tick)))
            return 5
        if (tick - T_DEBUT) % (GRILLE * 288) == 0:
            print(json.dumps(dict(passe=passe, tick=tick, lignes=i, emis=len(emissions), rss_mo=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576), duree_s=round(time.time() - debut))), flush=True)
    jours = (T_FIN - T_ALERTES) / 86400
    nouveaux = [e for e in emissions if e['nouveau']]
    discrets = [e for e in nouveaux if e['nature'] == 'discret']
    sortie = dict(passe=passe, entree=entree, grille_s=GRILLE, resume=dict(totaux), categories=dict(categories), risques=dict(risques), nouveaux_dossiers=len(nouveaux), nouveaux_discrets_par_jour=len(discrets) / jours, par_jour={k: dict(v) for k, v in par_jour.items()}, revues_par_jour=dict(revues_jour), trouvailles=dict(trouvailles),
                  reobservations=store.cx.execute("SELECT SUM(reobservations) FROM cases WHERE event_key NOT LIKE 'inj:%'").fetchone()[0] or 0, emissions=emissions, injections=list(injections.values()), rss_max_mo=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576, duree_s=time.time() - debut)
    destination = ETUDE / f'derived/{passe}_2.json.gz'
    with gzip.GzipFile(destination, 'wb', mtime=0) as f:
        f.write(json.dumps(sortie, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
    store.close()
    from registre import enregistrer
    enregistrer(str(ETUDE), f'engine_{passe}_2', False, totaux['pairs'], 'claude', n_comparaisons=max(1, totaux['pairs']), sortie=str(destination.relative_to(ETUDE)), params=dict(grille=GRILLE), note='Exploratoire, moteur conçu en connaissant les cas')
    print(json.dumps({k: sortie[k] for k in ('passe', 'categories', 'risques', 'nouveaux_dossiers', 'nouveaux_discrets_par_jour', 'reobservations', 'rss_max_mo', 'duree_s')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
