"""Direction 2, step 1: every address a public source attributes to ChangeNOW, then its measured function in October 2026.
A label is what a source wrote. The function comes from behaviour. Only PAYOUT_HOT addresses become sources of client payouts (PROTOCOL.md, section 4)."""
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net

CHAINS = (1, 137, 42161, 10)
BASE = 'https://metadata.services.blockscout.com/api/v1'
T0, T1 = 1790812800, 1793491199  # 2026-10-01 00:00:00 UTC to 2026-10-31 23:59:59 UTC
OUT = net.ROOT / 'derived/cn_universe.csv'


def by_slug(slug, chain, tag_type, cap=40):
    out, token = [], None
    for _ in range(cap):
        p = dict(slug=slug, tagType=tag_type, chainId=chain, pageSize=50)
        if token:
            p['page_token'] = token
        d = net.get(BASE + '/addresses', p, accept=(400, 404))
        if isinstance(d, net.Miss):
            return out, 'miss'
        out += d.get('addresses') or []
        token = (d.get('next_page_params') or {}).get('page_token')
        if not token:
            return sorted(set(out)), 'complete'
    return sorted(set(out)), 'capped'


QUERIES = ('changenow hot', 'changenow:', 'changenow 1', 'changenow 2', 'changenow 3', 'changenow 4', 'changenow 5', 'changenow 6', 'changenow 7', 'changenow 8', 'changenow 9', 'changenow (', 'changenow binance', 'change now', 'changenow deployer', 'changenow treasury', 'changenow cold', 'changenow fee')


def tag_names(chain):
    """Name tags other than per-client deposit addresses. Blockscout holds over 20 000 of those on chain 1 alone: they cannot be payout sources, a random sample of them is measured apart."""
    tags = {}
    for q in QUERIES:
        token = None
        for _ in range(6):
            p = dict(chainId=chain, tag_types='name', name=q, pageSize=50)
            if token:
                p['page_token'] = token
            d = net.get(BASE + '/tags:search', p, accept=(400, 404))
            if isinstance(d, net.Miss):
                break
            for i in d.get('items') or []:
                t = i.get('tag') or i
                n = t.get('name', '')
                if 'changenow' in n.lower().replace(' ', '') and 'dep:' not in n.lower() and 'deposit' not in n.lower():
                    tags[t['slug']] = t
            token = (d.get('next_page_params') or {}).get('page_token')
            if not token:
                break
    return list(tags.values()), True


def main():
    rows = {}

    def add(a, chain, source, text):
        key = (a.lower(), chain)
        rows.setdefault(key, dict(address=a.lower(), chain=chain, sources=[]))['sources'].append(f'{source}:{text}')

    for chain in CHAINS:
        tags, complete = tag_names(chain)
        print('chain', chain, 'tags', len(tags), 'complete', complete, flush=True)
        for t in tags:
            got, state = by_slug(t['slug'], chain, 'name')
            for a in got:
                add(a, chain, 'blockscout', t.get('name'))
        for a in by_slug('changenow', chain, 'generic')[0]:
            add(a, chain, 'blockscout', 'generic:changenow')
        print('  after tags, addresses on chain', sum(1 for k in rows if k[1] == chain), flush=True)
    for a, hits in labels._load_lists().items():
        for h in hits:
            if 'changenow' in h['text'].lower() or 'change now' in h['text'].lower():
                for chain in CHAINS:
                    if {'brianleect/etherscan.json': 1, 'brianleect/polygonscan.json': 137, 'brianleect/arbiscan.json': 42161, 'brianleect/optimism.json': 10}.get(h['source'], chain) == chain and (h['source'].startswith('brianleect') or chain == 1):
                        add(a, chain, h['source'], h['text'])
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['address', 'chain', 'n_sources', 'lineages', 'sources'])
        w.writeheader()
        for r in rows.values():
            srcs = sorted(set(r['sources']))
            lines = sorted({s.split(':')[0].split('/')[0] for s in srcs})
            w.writerow(dict(address=r['address'], chain=r['chain'], n_sources=len(srcs), lineages='|'.join(lines), sources=' ; '.join(srcs)[:600]))
    from collections import Counter
    print(Counter(k[1] for k in rows))
    names = Counter()
    for r in rows.values():
        for s in set(r['sources']):
            names[s.split(':', 1)[1][:40] if 'Dep:' not in s else 'ChangeNOW Dep:*'] += 1
    print(names.most_common(40))


if __name__ == '__main__':
    main()
