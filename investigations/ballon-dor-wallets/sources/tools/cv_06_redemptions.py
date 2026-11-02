"""Contre-vérification : redemptions partagées entre dossiers et calendrier du marché Kane, lus sur Polygon. Lecture seule."""
import glob, gzip, json, os, time, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
NODE = 'https://polygon-bor-rpc.publicnode.com'


def rpc(method, params, node=NODE):
    time.sleep(.25)
    req = urllib.request.Request(node, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if 'error' in d:
        raise RuntimeError(str(d['error'])[:200])
    return d['result']


act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
wallet = {Path(f).stem: json.load(open(f))['address'].lower() for f in glob.glob(str(ROOT / 'cases/*.json'))}
by_tx = defaultdict(set)
rows_tx = {}
for s, rows in act.items():
    for r in rows:
        by_tx[r['transaction_hash']].add(s)
        rows_tx[(s, r['transaction_hash'])] = r
shared = {tx: sorted(v) for tx, v in by_tx.items() if len(v) > 1}
print('transactions communes à deux dossiers, tous types confondus', len(shared))
res = dict(shared={})
for tx, who in shared.items():
    types = {s: (rows_tx[(s, tx)]['type'], rows_tx[(s, tx)].get('title', '')[:50], rows_tx[(s, tx)].get('outcome'), rows_tx[(s, tx)].get('side'), rows_tx[(s, tx)].get('usdc_size')) for s in who}
    rc = rpc('eth_getTransactionReceipt', [tx])
    t = rpc('eth_getTransactionByHash', [tx])
    topics = Counter(l['topics'][0] for l in rc['logs'])
    res['shared'][tx] = dict(who=who, types=types, tx_from=t['from'], tx_to=t['to'], logs=len(rc['logs']), topics=topics.most_common(8), block=int(rc['blockNumber'], 16))
    print(tx[:14], who, [v[0] for v in types.values()], 'from', t['from'][:12], 'to', t['to'][:12], 'logs', len(rc['logs']))
# Lire le lot Kane : redemption à 01:58:15, deux dossiers
kane = {s: [r for r in rows if r['type'] == 'REDEEM' and 'Harry Kane win' in (r.get('title') or '')] for s, rows in act.items()}
kane = {s: v for s, v in kane.items() if v}
print('Kane REDEEM', {s: [(r['timestamp'], r['transaction_hash'][:12], r['usdc_size']) for r in v] for s, v in kane.items()})
tx0 = kane['0x86544e4dfde'][0]['transaction_hash']
rc = rpc('eth_getTransactionReceipt', [tx0])
t0 = rpc('eth_getTransactionByHash', [tx0])
block = int(rc['blockNumber'], 16)
res['kane_tx'] = dict(tx=tx0, frm=t0['from'], to=t0['to'], block=block, logs=[dict(addr=l['address'], t0=l['topics'][0], topics=l['topics'][1:], data=l['data'][:200]) for l in rc['logs']][:30])
for l in res['kane_tx']['logs']:
    print(' ', l['addr'][:12], l['t0'][:14], [x[:14] for x in l['topics']], l['data'][:80])
(OUT / 'redemptions.json').write_text(json.dumps(res, default=str))
