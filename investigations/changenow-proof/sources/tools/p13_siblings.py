"""Out-of-sample test of the sweep fingerprint measured on 0x3f3ee0a9: siblings Blockscout tags changenow-dep, and pools of other services. Fingerprint fixed before this run: 2 transactions, 1 in, 1 out into the pool, gas price 1 gwei, gas limit 22000, in minus out between 6e13 and 6.01e13 wei, delay 400 to 600 s."""
import json, random, sys, gzip, csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch, es
ROOT = Path(__file__).resolve().parent.parent
rng = random.Random(20261103)


def probe(pool, n):
    rows = es.rows('txlist', pool, sort='desc')
    senders = sorted({r['from'].lower() for r in rows if r['to'] and r['to'].lower() == pool and int(r['value']) > 0})
    pick = rng.sample(senders, min(n, len(senders)))
    shape = fp = 0
    for a in pick:
        tx = es.rows('txlist', a, sort='asc')
        i = [x for x in tx if x['to'] and x['to'].lower() == a and int(x['value']) > 0]
        o = [x for x in tx if x['from'].lower() == a]
        if len(tx) == 2 and len(i) == 1 and len(o) == 1 and o[0]['to'] and o[0]['to'].lower() == pool:
            shape += 1
            d = int(i[0]['value']) - int(o[0]['value'])
            dt = int(o[0]['timeStamp']) - int(i[0]['timeStamp'])
            if o[0]['gasPrice'] == '1000000000' and o[0]['gas'] == '22000' and 6 * 10 ** 13 <= d <= 601 * 10 ** 11 and 400 <= dt <= 600:
                fp += 1
    return dict(pool=pool, rows=len(rows), senders=len(senders), sampled=len(pick), same_shape=shape, fingerprint=fp, last=max((int(r['timeStamp']) for r in rows), default=None))


res = dict(siblings=[], controls=[])
lst = []
with gzip.open(ROOT / 'state/bs_changenow_list.csv.gz', 'rt') as f:
    for r in csv.DictReader(f):
        if r['slug'] == 'changenow-dep' and r['chain_id'] == '1':
            lst.append(r['address'])
for a in lst:
    res['siblings'].append(probe(a, 5))
    print('sibling', a[:12], {k: res['siblings'][-1][k] for k in ('rows', 'senders', 'sampled', 'same_shape', 'fingerprint')}, flush=True)
res['target'] = probe('0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', 30)
print('target', res['target'], flush=True)
for a, n in (('0x4e5b2e1dc63f6b91cb6cd759936495434c7e972f', 'FixedFloat: Hot Wallet 2'), ('0x7bacd3e83522f484bc5128ea93bf7290f1f1b9e5', 'SimpleSwap 7'), ('0xc1d13492285eb664951e201bf7c80c7c6318a1b5', 'SwftSwap'), ('0x4976a4a02f38326660d17bf34b431dc6e2eb2327', 'Binance 20'), ('0xcad621da75a66c7a8f4ff86d30a2bf981bfc8fdd', 'KuCoin 10')):
    res['controls'].append(dict(probe(a, 20), name=n))
    print('control', n, {k: res['controls'][-1][k] for k in ('rows', 'senders', 'sampled', 'same_shape', 'fingerprint')}, flush=True)
# funders, tags, calldata
fund = ['0xb2c257557fd1c7a0738d7e9e2c953441f333b8fd', '0x262386755624eefd0c2d46ccf4a8ad35d480f1ee']
s, b = arch.fetch('https://metadata.services.blockscout.com/api/v1/metadata?chainId=1&addresses=' + ','.join(fund), 'bs_funders_tags.json')
res['funder_tags'] = json.loads(b)
res['funder_first'] = {a: [(r['from'], r['to'], r['value'], r['timeStamp'], r['hash']) for r in es.rows('txlist', a, sort='asc')[:3]] for a in fund}
print(res['funder_tags'], flush=True)
# comparators on the same raw reading as the keys
snap = [json.loads(l) for l in open(ROOT / 'evidence/comparators_snapshot.jsonl')]
use = [r for r in snap if r.get('state') == 'READ' and r.get('key') and r.get('key_history_complete')]
cp, new = {}, {}
for r in use:
    k = r['key'].lower()
    c = set()
    for chain in (1, 137, 42161):
        for action in ('txlist', 'txlistinternal', 'tokentx'):
            for x in es.rows(action, k, chain):
                for side in (x['from'], x['to']):
                    if side and side.lower() != k:
                        c.add((side.lower(), chain))
    cp[r['wallet']] = (k, r['group'], c)
    for a, chain in c:
        new.setdefault(chain, set()).add(a)
    print('comparator', r['wallet'][:10], r['group'][:6], len(c), flush=True)
tags = {}
for chain, addrs in sorted(new.items()):
    addrs = sorted(addrs)
    for i in range(0, len(addrs), 200):
        s, b = arch.fetch(f'https://metadata.services.blockscout.com/api/v1/metadata?chainId={chain}&addresses=' + ','.join(addrs[i:i + 200]), f'bs_comp_raw_{chain}_{i // 200:04d}.json', pause=.5)
        if s == 200:
            for a, v in json.loads(b).get('addresses', {}).items():
                tags[(a.lower(), chain)] = [t['name'] for t in v.get('tags', [])]
hit = {w: sorted(x for x in c if 'changenow' in ' '.join(tags.get(x, [])).lower()) for w, (k, g, c) in cp.items()}
res['comparators_raw'] = dict(usable=len(use), read_keys=len(cp), with_any_row=sum(bool(v[2]) for v in cp.values()), median_cp=sorted(len(v[2]) for v in cp.values())[len(cp) // 2], lookups={c: len(a) for c, a in new.items()}, hits={w: v for w, v in hit.items() if v}, n_hit=sum(bool(v) for v in hit.values()))
print(res['comparators_raw'], flush=True)
(ROOT / 'state/p13.json').write_text(json.dumps(res, default=str))
print('done', flush=True)
