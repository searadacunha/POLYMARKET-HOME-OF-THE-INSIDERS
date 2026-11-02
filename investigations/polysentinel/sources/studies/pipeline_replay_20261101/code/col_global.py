"""A1: resumable walk of the bare global feed, newest to oldest, at the plan's nominal filter.

One page in memory at a time; rows go straight to gzip. Identity fields never reach the disk.
"""
import gzip
import json
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ledger import appel, compteur, ETUDE, BudgetEpuise

T_FIN, T_DEBUT = 1792768669, 1791691200
PAGES_MAX = 170
CHAMPS = ('proxy_wallet', 'condition_id', 'token_id', 'side', 'size', 'price', 'timestamp',
          'transaction_hash', 'event_slug', 'slug', 'outcome', 'outcome_index', 'title')
ETAT = ETUDE / 'data/global_state.json'
FENETRE = ETUDE / 'data/global_window.jsonl.gz'
POST = ETUDE / 'data/global_post.jsonl.gz'
stop = False


def arreter(*_):
    global stop
    stop = True


def minimal(row):
    return {k: row[k] for k in CHAMPS if k in row}


def main():
    signal.signal(signal.SIGTERM, arreter)
    etat = json.loads(ETAT.read_text()) if ETAT.exists() else dict(
        filtre=2500, curseur=None, pages=0, lignes=0, ligne_min=None, ligne_max=None, fini=False,
        vides=0, desordres=0, rythme_decide=False, relances=0)
    while not stop and not etat['fini']:
        if etat['pages'] >= PAGES_MAX:
            etat['arret'] = 'plafond de pages'
            break
        params = dict(limit=1000, taker_only='true', filter_type='CASH', filter_amount=etat['filtre'])
        if etat['curseur']:
            params['cursor'] = etat['curseur']
        body, recu = appel('https://data-api.polymarket.com/v2/trades', params, phase='A1')
        page = body.get('pagination')
        rows = body.get('data')
        if not isinstance(rows, list) or not isinstance(page, dict) or not isinstance(page.get('has_more'), bool):
            raise RuntimeError('Schéma /v2/trades invalide, numéro %s' % recu['n'])
        curseur = page.get('next_cursor')
        if bool(curseur) != page['has_more']:
            raise RuntimeError('Pagination incohérente')
        if curseur and curseur == etat['curseur']:
            raise RuntimeError('Curseur immobile')
        if not rows and curseur:
            raise RuntimeError('Page vide avec suite: couverture inconnue')
        if not rows:
            etat['vides'] += 1
        ts = [int(r['timestamp']) for r in rows]
        etat['desordres'] += sum(a < b for a, b in zip(ts, ts[1:]))
        # Append before moving the durable cursor: a crash duplicates a page, it never loses one.
        with gzip.open(FENETRE, 'at', compresslevel=6) as dedans, gzip.open(POST, 'at', compresslevel=6) as apres:
            for r in rows:
                cible = apres if int(r['timestamp']) >= T_FIN else dedans
                cible.write(json.dumps(dict(minimal(r), page=etat['pages']), separators=(',', ':')) + '\n')
        etat['pages'] += 1
        etat['lignes'] += len(rows)
        if ts:
            etat['ligne_min'] = min(ts) if etat['ligne_min'] is None else min(etat['ligne_min'], min(ts))
            etat['ligne_max'] = max(ts) if etat['ligne_max'] is None else max(etat['ligne_max'], max(ts))
        etat['curseur'] = curseur
        etat['fini'] = not curseur or (etat['ligne_min'] is not None and etat['ligne_min'] < T_DEBUT)
        if etat['pages'] == 20 and not etat['rythme_decide']:
            etat['rythme_decide'] = True
            secondes_par_page = (etat['ligne_max'] - etat['ligne_min']) / 20
            projetees = (etat['ligne_max'] - T_DEBUT) / secondes_par_page
            etat['projection_pages'] = projetees
            print(json.dumps(dict(projection_pages=round(projetees, 1), secondes_par_page=round(secondes_par_page))), flush=True)
            if projetees > PAGES_MAX:
                # Plan's fallback rule: restart once at 5,000.
                FENETRE.unlink(missing_ok=True)
                POST.unlink(missing_ok=True)
                etat.update(filtre=5000, curseur=None, pages=0, lignes=0, ligne_min=None, ligne_max=None, relances=etat['relances'] + 1)
        tmp = ETAT.with_suffix('.tmp')
        tmp.write_text(json.dumps(etat, indent=1))
        tmp.replace(ETAT)
        time.sleep(.25)
    etat['requetes_totales'] = compteur()
    tmp = ETAT.with_suffix('.tmp')
    tmp.write_text(json.dumps(etat, indent=1))
    tmp.replace(ETAT)
    print(json.dumps({k: v for k, v in etat.items() if k != 'curseur'}))


if __name__ == '__main__':
    try:
        main()
    except BudgetEpuise as exc:
        print('Budget épuisé:', exc, file=sys.stderr)
        sys.exit(4)
