"""Base rate. Share of comparator keys whose counterparties carry a ChangeNOW tag, same lookup as for the 11 keys, first hop only. Snapshot of the comparators file, it is still growing at flow-trace. Exploratory: comparators were chosen after the dossiers were read."""
import ast, csv, gzip, hashlib, json, math, shutil, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch
ROOT = Path(__file__).resolve().parent.parent
SRC = Path.home() / 'Projects/PolySentinel-flow-trace/state/comparators.jsonl'
SNAP = ROOT / 'evidence/comparators_snapshot.jsonl'
if not SNAP.exists():  # evidence: a replay must not overwrite it
    shutil.copyfile(SRC, SNAP)
rows = [json.loads(l) for l in open(SNAP)]
print('snapshot', len(rows), hashlib.sha256(SNAP.read_bytes()).hexdigest(), Counter((r.get('group'), r.get('state')) for r in rows))
use, excl = [], Counter()
for r in rows:
    if r.get('state') != 'READ' or not r.get('key'):
        excl['not read or no key'] += 1
    elif not r.get('key_history_complete'):
        excl['key history truncated'] += 1
    elif 'counterparties' not in r:
        excl['no counterparties field'] += 1
    else:
        use.append(r)
print('usable', len(use), excl)
by_chain = defaultdict(set)
for r in use:
    for x in r['counterparties']:
        a, c = x.split(':')
        by_chain[int(c)].add(a.lower())
tags = {}
for c, addrs in sorted(by_chain.items()):
    addrs = sorted(addrs)
    for i in range(0, len(addrs), 200):
        s, b = arch.fetch(f'https://metadata.services.blockscout.com/api/v1/metadata?chainId={c}&addresses=' + ','.join(addrs[i:i + 200]), f'bs_comp_{c}_{i // 200:04d}.json', pause=.5)
        if s == 200:
            for a, v in json.loads(b).get('addresses', {}).items():
                tags[(a.lower(), c)] = [t['name'] for t in v.get('tags', [])]
        else:
            print('failed', c, i, s, flush=True)
    print('chain', c, len(addrs), flush=True)
hits = []
for r in use:
    h = [(x, tags[(x.split(':')[0].lower(), int(x.split(':')[1]))]) for x in r['counterparties'] if 'changenow' in ' '.join(tags.get((x.split(':')[0].lower(), int(x.split(':')[1])), [])).lower()]
    if h:
        hits.append(dict(group=r['group'], wallet=r['wallet'], key=r['key'], hits=h))
# same measure on the 11 keys: first-hop counterparties on chains 1, 137, 42161, read from the same cache
study = {r['address']: r for r in csv.DictReader(open(ROOT / 'state/study_addresses.csv'))}
keys = {a: r['relations'] for a, r in study.items() if 'owner_key' in r['relations']}
cp = defaultdict(set)
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as f:
    for l in f:
        x = json.loads(l)
        if x['chain'] in (1, 137, 42161):
            if x['src'] in keys and x['dst']:
                cp[x['src']].add((x['dst'], x['chain']))
            if x['dst'] in keys and x['src']:
                cp[x['dst']].add((x['src'], x['chain']))
tagged = {}
with gzip.open(ROOT / 'state/batch_tags.jsonl.gz', 'rt') as f:
    for l in f:
        x = json.loads(l)
        tagged[(x['address'], x['chain'])] = [t['name'] for t in x['tags']]
named = {k: sorted(a for a in v if 'changenow' in ' '.join(tagged.get(a, [])).lower()) for k, v in cp.items()}
named_hits = {k: v for k, v in named.items() if v}
n1, k1, n0, k0 = len(keys), len(named_hits), len(use), len(hits)


def fisher_two_sided(a, b, c, d):
    def p(x):
        return math.comb(a + b, x) * math.comb(c + d, a + c - x) / math.comb(a + b + c + d, a + c)
    obs = p(a)
    return sum(p(x) for x in range(max(0, a + c - (c + d)), min(a + b, a + c) + 1) if p(x) <= obs * (1 + 1e-9))


out = dict(snapshot_sha256=hashlib.sha256(SNAP.read_bytes()).hexdigest(), comparators_total=len(rows), usable=n0, excluded=excl, comparator_hits=hits, comparators_with_hit=k0, named_keys=n1, named_keys_read=len(cp), named_with_hit=k1, named_hits={k: v for k, v in named_hits.items()}, by_group={g: [sum(1 for r in use if r['group'] == g), sum(1 for r in hits if r['group'] == g)] for g in {r['group'] for r in use}}, fisher_two_sided=fisher_two_sided(k1, n1 - k1, k0, n0 - k0))
(ROOT / 'state/p11.json').write_text(json.dumps(out, indent=1, default=str))
print({k: v for k, v in out.items() if k not in ('comparator_hits',)})
print(hits[:12])
