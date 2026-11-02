"""Collection checks written before any score: recall of the census against two other sources."""
import gc
import gzip
import json
import sqlite3
import sys
import time
import zlib
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
from charge import charge  # noqa: E402
from univers import CENSUS, FAMILY, CONTROL, lignes_flux  # noqa: E402

FILTRE = json.loads((ETUDE / 'data/global_state.json').read_text())['filtre']
T_ROT, T_DEBUT, T_FIN = 1790176669, 1791691200, 1792768669
# Production has run since 27 Oct; these are whole UTC days inside both sources.
PROD_DEBUT, PROD_FIN = 1793145600, 1793404800  # 28 Oct 00:00 to 31 Oct 00:00


def main():
    u = charge()
    sortie = dict(comptes=u.comptes, filtre=FILTRE)

    # 1. Sampled rows at or above the filter should also be in the census (only from T_DEBUT).
    for nom, bit in (('famille', FAMILY), ('temoins', CONTROL)):
        total = trouves = 0
        for ident, r in u.rows.items():
            if u.sources[ident] & bit and r[0] >= T_DEBUT and r[4] * r[5] >= FILTRE:
                total += 1
                trouves += bool(u.sources[ident] & CENSUS)
        sortie['rappel_recensement_' + nom] = dict(attendues=total, trouvees=trouves, part=trouves / total if total else None)

    # 2. Time shape of the census.
    par_jour = {}
    for ident, r in u.rows.items():
        if u.sources[ident] & CENSUS:
            jour = time.strftime('%Y-%m-%d', time.gmtime(r[0]))
            par_jour[jour] = par_jour.get(jour, 0) + 1
    sortie['recensement_par_jour'] = par_jour
    sortie['evenements_m1'] = len({r[10] for r in u.rows.values() if not r[8]})
    sortie['lignes_m1'] = sum(1 for r in u.rows.values() if not r[8])
    # /v2/trades by event against the bounded /trades: same rows, compared on identifiers.
    anciennes = set()
    with gzip.open(ETUDE.parent / 'ballon_2026_20261030/data/trades_minimal.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r.get('event_id') in ('811116', '811117') and T_ROT <= r['timestamp'] < T_FIN:
                anciennes.add(r['id'])
    bornees = {r['id'] for r in lignes_flux(ETUDE / 'data/family_extra.jsonl.gz')}
    sortie['trades_borne_vs_v2'] = dict(lignes_v2=len(anciennes), retrouvees=len(anciennes & bornees))
    sortie['doublons_signature'] = sum(1 for i in u.rows if not i.endswith(':1'))
    del u
    gc.collect()

    # 3. Census against production, on whole days both cover: real coverage of each by the other.
    post = set()
    for r in lignes_flux(ETUDE / 'data/global_post.jsonl.gz'):
        if PROD_DEBUT <= r['timestamp'] < PROD_FIN:
            post.add(r['id'])
    db = ETUDE.parent.parent / 'data/polysentinel.sqlite3'
    cx = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=10)
    prod = set()
    lus = 0
    for key, body in cx.execute("""SELECT t.key,c.body FROM trade_index t JOIN object_refs r ON r.kind='trade' AND r.key=t.key
                                   JOIN contents c ON c.id=r.content_id WHERE t.trade_time>=? AND t.trade_time<?""", (PROD_DEBUT, PROD_FIN)):
        lus += 1
        p = json.loads(zlib.decompress(body))
        if p['size'] * p['price'] >= FILTRE:
            prod.add(key)
    cx.close()
    sortie['recensement_vs_production'] = dict(fenetre=[PROD_DEBUT, PROD_FIN], lignes_production_lues=lus, production_ge_filtre=len(prod), recensement=len(post),
                                               communes=len(prod & post), production_seule=len(prod - post), recensement_seul=len(post - prod))
    (ETUDE / 'data/collecte_controles.json').write_text(json.dumps(sortie, indent=1, ensure_ascii=False))
    print(json.dumps(sortie, ensure_ascii=False)[:2500])


if __name__ == '__main__':
    main()
