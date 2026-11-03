"""Exploratory: catalogue markets against tokens of the same volume decile, by the largest group of entrants inside each window in the 8 days before the public event. Selected on suspicion and on outcome: it can say "ordinary or not", nothing more."""
import gzip
import json
import os
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ana_20_primary as primary
import lib_bursts as lib
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOKBACK = 8 * 86400


def largest(times, window):
    times, best, left = sorted(times), 0, 0
    for right, t in enumerate(times):
        while times[left] <= t - window:
            left += 1
        best = max(best, right - left + 1)
    return best


def main():
    catalog = json.loads((Path(ETUDE) / 'catalog_markets.json').read_text())
    event_at = {m['condition'].lower(): int(datetime.fromisoformat(m['event_utc'].replace('Z', '+00:00')).timestamp()) for m in catalog}
    names = {m['condition'].lower(): m['id'] for m in catalog}
    _, entrants = primary.read()
    meta = {}
    with gzip.open(Path(ETUDE) / 'derived/tokens.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            meta[(r['condition'].lower(), r['token'])] = r
    tokens = defaultdict(list)
    for r in entrants:
        key = (r['condition'].lower(), r['token'])
        cut = event_at.get(key[0], r['closed'])
        if cut - LOOKBACK <= r['ts'] < cut:
            tokens[key].append(r['ts'])
    volumes = sorted(m['volume'] for m in meta.values())
    decile = {k: min(9, 10 * bisect_right(volumes, m['volume']) // max(1, len(volumes))) for k, m in meta.items()}
    measure = {w: {k: largest(t, w) for k, t in tokens.items()} for w in lib.WINDOWS}
    peers_of = defaultdict(list)
    for k, m in meta.items():
        if k[0] not in names and not m['partial']:
            peers_of[decile[k]].append(k)
    rows, pvals = [], []
    for key, m in meta.items():
        if key[0] not in names:
            continue
        for w in lib.WINDOWS:
            peers = [measure[w].get(k, 0) for k in peers_of[decile[key]]]
            mine = measure[w].get(key, 0)
            share = sum(v >= mine for v in peers) / max(1, len(peers))
            rows.append(dict(market=names[key[0]], token=key[1], token_won=m['win'], partial_file=bool(m['partial']), volume_decile=decile[key], window=w, largest_group=mine, peers=len(peers), share_of_peers_at_or_above=round(share, 5)))
            pvals.append((f'{names[key[0]]}|{key[1][:8]}|{w}', max(share, 1 / max(1, len(peers)))))
    passed = lib.benjamini_hochberg(pvals) if pvals else set()
    for r in rows:
        r['bh_flag'] = f"{r['market']}|{r['token'][:8]}|{r['window']}" in passed
    tables = Path(ETUDE) / 'tables'
    tables.mkdir(exist_ok=True)
    (tables / 'catalog.json').write_text(json.dumps(dict(rows=rows, reading='Selected on suspicion and on outcome: this is no test of insider trading.', in_universe=sorted({r['market'] for r in rows}), not_in_universe=sorted(set(names.values()) - {r['market'] for r in rows})), indent=1))
    enregistrer(ETUDE, test='catalog_ranks', declare=True, n=len(rows), agent='etude-sync', n_comparaisons=max(1, len(rows)), sortie='tables/catalog.json', note='exploratory, selected on suspicion and outcome')


if __name__ == '__main__':
    main()
