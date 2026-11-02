"""Load every collected source into one Univers. Shared by the collection checks and the replay.

Census-only events stay without catalogue on purpose: the local catalogue only knows markets still
alive after T_FIN, so using it would give metadata according to the future.
"""
import gc
import gzip
import json
import sys
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ETUDE / 'code'))
sys.path.insert(0, str(ETUDE / 'code/vendor'))
import univers  # noqa: E402
from univers import Univers, CENSUS, FAMILY, CONTROL, lignes_flux  # noqa: E402

BALLON = ETUDE.parent / 'ballon_2026_20261030/data'
T_ROT, T_FIN = univers.T_ROT, univers.T_FIN


def charge(avec_recensement=True, avec_lignes=True):
    u = Univers()
    # Metadata first, so rows map to their market and event on arrival.
    refreshed = json.loads((BALLON / 'catalog_refreshed.json').read_text())
    for item in refreshed['events']:
        u.ajoute_gamma(item['event'], 'family')
    del refreshed
    with gzip.open(ETUDE / 'data/control_events.jsonl.gz', 'rt') as f:
        for line in f:
            u.ajoute_gamma(json.loads(line), 'control')
    gc.collect()
    if not avec_lignes:
        return u
    familles = 0
    with gzip.open(BALLON / 'trades_minimal.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if T_ROT <= r['timestamp'] < T_FIN:
                r.setdefault('market_slug', '')
                r.setdefault('outcome', '')
                u.ajoute_ligne(r, FAMILY)
                familles += 1
    extra = 0
    for r in lignes_flux(ETUDE / 'data/family_extra.jsonl.gz'):
        u.ajoute_ligne(r, FAMILY)
        extra += 1
    temoins = 0
    for r in lignes_flux(ETUDE / 'data/controls.jsonl.gz'):
        u.ajoute_ligne(r, CONTROL)
        temoins += 1
    recensement = 0
    if avec_recensement:
        for r in lignes_flux(ETUDE / 'data/global_window.jsonl.gz'):
            if r['timestamp'] < T_FIN:
                u.ajoute_ligne(r, CENSUS)
                recensement += 1
    u.comptes = dict(famille_antérieure=familles, famille_ajoutée=extra, témoins=temoins, recensement=recensement, uniques=len(u.rows),
                     rejets=dict(univers.REJETS))
    gc.collect()
    return u
