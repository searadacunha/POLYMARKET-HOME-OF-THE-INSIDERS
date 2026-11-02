"""Blockscout metadata in batches, for every counterparty of the personal-sized study addresses, on each chain they were read. Also the full lists behind the protocol tags changenow and changenow-dep. Every answer archived with SHA-256."""
import csv, gzip, json, sys, urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch
ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://metadata.services.blockscout.com/api/v1'
study = {r['address']: r for r in csv.DictReader(open(ROOT / 'state/study_addresses.csv'))}
capped = {r['address'] for r in csv.DictReader(open(ROOT / 'state/history_coverage.csv')) if int(r['full_pages_1000'])}
personal = {a for a in study if a.startswith('0x') and a not in capped}
cp = defaultdict(set)
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as f:
    for line in f:
        r = json.loads(line)
        if r['src'] in personal and r['dst']:
            cp[r['chain']].add(r['dst'])
        if r['dst'] in personal and r['src']:
            cp[r['chain']].add(r['src'])
print('personal', len(personal), {k: len(v) for k, v in cp.items()}, flush=True)
tags = {}
for chain, addrs in sorted(cp.items()):
    addrs = sorted(addrs | set(study) & {a for a in study if a.startswith('0x')})
    for i in range(0, len(addrs), 200):
        part = addrs[i:i + 200]
        s, b = arch.fetch(f'{BASE}/metadata?chainId={chain}&addresses=' + ','.join(part), f'bs_batch_{chain}_{i // 200:04d}.json', pause=.5)
        if s != 200:
            print('batch failed', chain, i, s, b[:120], flush=True)
            continue
        for a, v in json.loads(b).get('addresses', {}).items():
            tags[(a.lower(), chain)] = v.get('tags') or []
    print('chain', chain, 'looked up', len(addrs), 'tagged so far', len(tags), flush=True)
with gzip.open(ROOT / 'state/batch_tags.jsonl.gz', 'wt') as f:
    for (a, c), t in tags.items():
        f.write(json.dumps(dict(address=a, chain=c, tags=t)) + '\n')
hits = {k: v for k, v in tags.items() if 'changenow' in json.dumps(v).lower()}
print('changenow tagged counterparties', len(hits))
for (a, c), t in sorted(hits.items()):
    print(' ', a, c, [x['name'] for x in t])
# Full lists behind the protocol tags, chain 1 first
listing = {}
for chain in (1, 137, 42161, 8453, 10, 56):
    for slug in ('changenow-dep', 'changenow'):
        tok, n = '', 0
        for page in range(1, 41):
            s, b = arch.fetch(f'{BASE}/addresses?slug={slug}&tagType=protocol&chainId={chain}&pageSize=1000' + (f'&pageToken={urllib.parse.quote(tok)}' if tok else ''), f'bs_list_{chain}_{slug}_{page:03d}.json', pause=.5)
            if s != 200:
                print('list failed', chain, slug, page, s, b[:120], flush=True)
                break
            d = json.loads(b)
            for a in d.get('addresses') or []:
                listing.setdefault(a.lower(), set()).add((chain, slug))
                n += 1
            tok = (d.get('next_page_params') or {}).get('page_token') or d.get('next_page_token') or ''
            if not tok:
                break
        print('list', chain, slug, 'n', n, 'pages', page, 'more' if tok else 'end', flush=True)
with gzip.open(ROOT / 'state/bs_changenow_list.csv.gz', 'wt') as f:
    w = csv.writer(f)
    w.writerow(['address', 'chain_id', 'slug'])
    for a, v in sorted(listing.items()):
        for c, s in sorted(v):
            w.writerow([a, c, s])
print('listed addresses', len(listing), Counter(s for v in listing.values() for _, s in v))
print('study addresses inside the lists', sorted(a for a in listing if a in study))
