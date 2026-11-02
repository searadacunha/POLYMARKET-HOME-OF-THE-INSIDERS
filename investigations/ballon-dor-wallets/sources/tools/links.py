"""Links between the named wallets, across every case file. Exploratory, written after part A was sealed. A shared service never links anyone."""
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import identities as I

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261101
ONE_HOUR, SIX_HOURS, DAY = 3600, 6 * 3600, 86400
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))


def infrastructure(address, relation):
    """Service label, high nonce, or the pUSD mechanics: an address of this kind says nothing about ownership."""
    if relation.get('source_label') and relation['source'] == address or relation.get('target_label') and relation['target'] == address:
        return True
    basis = relation.get('basis') or ''
    return 'nonce ' in basis and int(basis.split('nonce ')[1].split(',')[0]) > 10_000


def candidates(exits, entries, low=.90, high=1.001, window=SIX_HOURS):
    """An exit of one wallet followed by a similar entry into another. Amount and time make a candidate, never a link."""
    found = []
    for wallet, at, usd in exits:
        for other, then, amount in entries:
            if other != wallet and 0 <= then - at <= window and usd > 0 and low <= amount / usd <= high:
                found.append((wallet, other, at, then, usd, amount))
    return found


def placebo(exits, entries, draws=2000, shifts=(3, 5, 7, 11)):
    """The same rule with exits moved by days: what still matches is accident by construction."""
    rng = random.Random(SEED)
    hits = 0
    for _ in range(draws):
        moved = [(w, t + rng.choice(shifts) * rng.choice((-1, 1)) * DAY, u) for w, t, u in exits]
        hits += len(candidates(moved, entries))
    return hits / draws


def main():
    cases = {}
    for slug in I.IDS:
        path = ROOT / f'cases/{slug}.json'
        if path.exists():
            cases[slug] = json.loads(path.read_text())
    touched = defaultdict(lambda: defaultdict(list))
    for slug, c in cases.items():
        wallet = c['address']
        for r in c.get('chain_relations', []):
            for address in (r['source'], r['target']):
                if address != wallet:
                    touched[address][slug].append(r)
    pooled = json.loads((ROOT / 'tools/pooled.json').read_text())['addresses']
    shared, services, measured = [], [], []
    for address, by_case in touched.items():
        if len(by_case) < 2:
            continue
        sample = next(iter(by_case.values()))[0]
        row = dict(address=address, cases=sorted(by_case), relations={k: [x['id'] for x in v] for k, v in by_case.items()}, chains=sorted({x['chain'] for v in by_case.values() for x in v}), label=(sample.get('source_label') if sample['source'] == address else sample.get('target_label')))
        if address in pooled:
            measured.append(dict(row, measured=pooled[address]))
        else:
            (services if infrastructure(address, sample) else shared).append(row)
    direct = []
    addresses = {c['address']: s for s, c in cases.items()}
    for slug, c in cases.items():
        for r in c.get('chain_relations', []):
            if r['source'] in addresses and r['target'] in addresses and r['source'] != r['target']:
                direct.append(r)
    exits = [(s, w['at'], float(w['usd'])) for s, c in cases.items() for w in c['withdrawals']]
    entries = [(s, d['at'], float(d['usd'])) for s, c in cases.items() for d in c['deposits']]
    real = candidates(exits, entries)
    out = dict(cases=sorted(cases), direct_transfers=direct, shared_non_infrastructure=shared, shared_pooled_measured=[dict(address=x['address'], cases=x['cases'], chains=x['chains'], measured=x['measured']) for x in measured], shared_services=[dict(address=x['address'], cases=x['cases'], label=x['label']) for x in services],
               candidates_amount_time=[dict(zip(('exit_wallet', 'entry_wallet', 'exit_at', 'entry_at', 'exit_usd', 'entry_usd'), x), exit_utc=UTC(x[2]), entry_utc=UTC(x[3]), category='STATISTICAL_CANDIDATE') for x in real], candidates_per_placebo_draw=placebo(exits, entries), exits=len(exits), entries=len(entries), ownership='OWNERSHIP_NOT_ESTABLISHED')
    (ROOT / 'graphs/links.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k not in ('shared_services',)}, ensure_ascii=False)[:3500])
    print('services', [(x['label'] or {}).get('name', x['address'][:12]) + ':' + str(len(x['cases'])) for x in out['shared_services']])


# Self-check of the rules that decide a candidate.
assert candidates([('a', 0, 100.0)], [('b', 3600, 99.0)]) and not candidates([('a', 0, 100.0)], [('a', 3600, 99.0)])
assert not candidates([('a', 0, 100.0)], [('b', 7 * 3600, 99.0)]) and not candidates([('a', 0, 100.0)], [('b', 3600, 80.0)])
assert infrastructure('x', dict(source='x', target='y', source_label=dict(name='s'), target_label=None, basis=''))
assert infrastructure('x', dict(source='x', target='y', source_label=None, target_label=None, basis='Sender nonce 58893846, kind EOA.'))
assert not infrastructure('x', dict(source='x', target='y', source_label=None, target_label=None, basis='Sender nonce 3, kind EOA.'))

if __name__ == '__main__':
    main()
