"""Local only. Who received real value from the 11 keys and the other personal-sized study addresses, and was never read. Spoofed tokens and dust stay out: only native value and the listed value tokens count."""
import csv, gzip, json
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
VALUE = {1: {'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0xdac17f958d2ee523a2206206994597c13d831ec7', '0x6b175474e89094c44da98b954eedeac495271d0f', '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'},
         137: {'0x2791bca1f2de4661ed88a30c99a7a9449aa84174', '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359', '0xc2132d05d31c914a87c6611c10748aeb04b58e8f', '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb', '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270', '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619'},
         42161: {'0xaf88d065e77c8cc2239327c5edb3a432268e5831', '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8', '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9', '0x82af49447d8a07e3bd95bd0d56f35241523fbab1'},
         10: {'0x0b2c639c533813f4aa9d7837caf62653d097ff85', '0x7f5c764cbc14f9669b88837ca1490cca17c31607', '0x94b008aa00579c1307b0ef2c499ad98a8ce58e58', '0x4200000000000000000000000000000000000006'}}
study = {r['address']: r for r in csv.DictReader(open(ROOT / 'state/study_addresses.csv'))}
cov = list(csv.DictReader(open(ROOT / 'state/history_coverage.csv')))
capped = {r['address'] for r in cov if int(r['full_pages_1000'])}
read = {(r['address'], int(r['chain_id'])) for r in cov}
keys = {a for a, r in study.items() if 'owner_key' in r['relations']}
keys.add('0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d')
personal = {a for a in study if a.startswith('0x') and a not in capped}
tagged = {}
with gzip.open(ROOT / 'state/batch_tags.jsonl.gz', 'rt') as f:
    for l in f:
        x = json.loads(l)
        tagged[(x['address'], x['chain'])] = [t['name'] for t in x['tags']]
out = defaultdict(lambda: dict(n=0, cases=set(), usd=0.0, first=None, senders=set(), kinds=set()))
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as f:
    for l in f:
        r = json.loads(l)
        if r['src'] not in personal and r['src'] not in keys:
            continue
        if not r['dst'] or r['err'] == '1' or r['raw'] in (None, 'None') or int(r['raw']) == 0:
            continue
        if r['kind'] == 'erc20' and r['contract'] not in VALUE.get(r['chain'], ()):
            continue
        k = (r['dst'], r['chain'])
        if k in read or k in tagged:
            continue
        o = out[k]
        o['n'] += 1
        o['senders'].add(r['src'])
        o['kinds'].add(r['kind'])
        o['cases'] |= set((study.get(r['src']) or {'cases': ''})['cases'].split(';'))
rows = sorted(({'address': a, 'chain': c, 'n': o['n'], 'senders': sorted(o['senders']), 'kinds': sorted(o['kinds']), 'cases': sorted(x for x in o['cases'] if x), 'from_key': bool(o['senders'] & keys)} for (a, c), o in out.items()), key=lambda r: (not r['from_key'], r['chain'], r['address']))
(ROOT / 'state/hop2_targets.json').write_text(json.dumps(rows, indent=0))
print(len(rows), Counter(r['chain'] for r in rows), 'from a key', sum(r['from_key'] for r in rows))
for r in rows[:50]:
    print(r['address'], r['chain'], r['n'], r['kinds'], r['cases'], 'KEY' if r['from_key'] else '')
