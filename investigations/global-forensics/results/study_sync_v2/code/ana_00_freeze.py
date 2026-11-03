"""Analytic table of the holdout, built once from the tapes, without outcomes. Usage: ana_00_freeze.py <universe.json> <seen.json> <part 0 last due date, ISO> [--count]. Writes derived/table.npz, derived/facts.json, derived/market_index.json, derived/freeze_counts.json. Prints counts only. Tapes hold prices, so a final price shows an outcome: nothing here reads or prints one. Stops on any unreadable tape."""
import gzip
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_v2 as lib  # noqa: E402

ETUDE = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATE_WORDS = re.compile(r'(?:^|-)(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|by|before|end|of|on|in|\d+)(?=-|$)')


def seconds(text):
    if not text:
        return None
    text = text.replace(' ', 'T').replace('Z', '+00:00')
    text = re.sub(r'\+00$', '+00:00', text)
    value = datetime.fromisoformat(text)
    return int((value if value.tzinfo else value.replace(tzinfo=timezone.utc)).timestamp())


def stem(slug):
    previous = None
    while previous != slug:
        previous, slug = slug, DATE_WORDS.sub('', slug)
    return slug.strip('-')


def facts_of(markets):
    """One world fact spans many events and a deadline ladder. Connected components over the event, the negRisk group and the slug stripped of dates. No outcome enters."""
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for m in markets:
        marks = [('e', s) for s in m.get('event_slugs') or []] + ([('n', m['negRiskMarketID'])] if m.get('negRiskMarketID') else []) + [('s', stem(m.get('slug') or m['conditionId']))]
        node = ('m', m['conditionId'].lower())
        for mark in marks:
            parent[find(mark)] = find(node)
    roots = {}
    return {m['conditionId'].lower(): roots.setdefault(find(('m', m['conditionId'].lower())), len(roots)) for m in markets}


def main(universe, seen, part_zero_end, mode='build'):
    count_only = mode == '--count'
    data = json.loads(Path(universe).read_text())
    excluded = json.loads(Path(seen).read_text())
    conditions, events = set(excluded['conditions']), set(excluded['event_ids'])
    words = re.compile('|'.join(excluded['slug_patterns']))
    counts = Counter(markets_universe=len(data['markets']))
    markets = []
    for m in data['markets']:
        if m['conditionId'].lower() in conditions or words.search(m['slug']) or set(m.get('event_ids') or []) & events:
            counts['excluded_seen'] += 1
        else:
            markets.append(m)
    fact = facts_of(markets)
    counts['facts'] = len(set(fact.values()))
    (ETUDE / 'derived' / 'facts.json').write_text(json.dumps(fact, indent=0, sort_keys=True))
    cut = seconds(part_zero_end)
    rows = []
    wallets, tokens, conditions_seen = {}, {}, {}
    for m in markets:
        condition = m['conditionId'].lower()
        path = ETUDE / 'data' / 'tapes' / f"{m['conditionId']}.jsonl.gz"
        if not path.exists():
            counts['tape_missing'] += 1
            continue
        tape, coverage = [], None
        with gzip.open(path, 'rt') as f:
            for line in f:
                r = json.loads(line)
                if '_coverage' in r:
                    coverage = r['_coverage']
                    continue
                tape.append(dict(wallet=r['proxy_wallet'].lower(), side=r['side'], token=str(r['token_id']), size=float(r['size']), price=float(r['price']), ts=int(r['timestamp'])))
        if coverage is None:
            raise RuntimeError(f'{condition}: tape without its coverage line')
        if coverage['stop'] != 'exhausted':
            counts['tape_empty' if coverage['stop'] == 'empty' else 'tape_partial_excluded'] += 1
            continue
        counts['tapes_read'] += 1
        counts['rows_read'] += len(tape)
        close = seconds(m.get('closedTime')) or seconds(m.get('endDate'))
        end = seconds(m.get('endDate')) or close
        part = 0 if end <= cut else 1  # by scheduled end, never by when it closed
        for e in lib.entrants_of_market(tape, end, close):
            rows.append((tokens.setdefault(e['token'], len(tokens)), fact[condition], wallets.setdefault(e['wallet'], len(wallets)), e['ts'], e['price'], e['usd'], e['prior_volume'], e['mom'], e['tte_s'], e['guard_ok'], e['strict_ok'], part, conditions_seen.setdefault(condition, len(conditions_seen)), e['token']))
    a = {name: np.array([r[i] for r in rows]) for i, name in enumerate(('token', 'fact', 'wallet', 'ts', 'price', 'usd', 'prior_volume', 'mom', 'tte_s', 'guard_ok', 'strict_ok', 'part'))}
    a['token_id'] = np.array([r[13] for r in rows])
    a['market'] = np.array([r[12] for r in rows])
    (ETUDE / 'derived' / 'market_index.json').write_text(json.dumps(conditions_seen, indent=0))
    a = lib.sort_table(a)
    counts.update(entrants=len(rows), tokens=len(tokens), wallets=len(wallets), part0=int((a['part'] == 0).sum()), part1=int((a['part'] == 1).sum()))
    for window in lib.WINDOWS:
        role, _ = lib.roles(a, window)
        # the stopping count leaves out the guard, which leans on later prices and so on the outcome
        ok = (a['prior_volume'] >= lib.MIN_PRIOR_VOLUME) & (a['ts'] >= lib.HOLDOUT_FROM)
        counts[f'triggers_{window}'] = int(((role == 1) & ok).sum())
        counts[f'facts_triggers_{window}'] = int(len(np.unique(a['fact'][(role == 1) & ok])))
    if count_only:  # for the stopping rule: counts with no guard, and no table to look at
        (ETUDE / 'derived' / f'stop_count_{int(time.time())}.json').write_text(json.dumps(counts, indent=1, sort_keys=True))
        print(json.dumps(counts, sort_keys=True))
        return
    counts['eligible'] = int(lib.eligible(a).sum())
    np.savez_compressed(ETUDE / 'derived' / 'table.npz', **a)
    (ETUDE / 'derived' / 'freeze_counts.json').write_text(json.dumps(counts, indent=1, sort_keys=True))
    print(json.dumps(counts, sort_keys=True))


if __name__ == '__main__':
    main(*sys.argv[1:])
