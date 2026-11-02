"""Contre-vérification : les 14 transactions communes à deux dossiers, décodées. Qui est de quel côté, combien d'autres comptes dans la même transaction. Lecture seule."""
import glob, gzip, json, os, time, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
NODE = 'https://polygon-bor-rpc.publicnode.com'
ORDERFILLED = '0xd543adfd'
REDEEM = '0x2682012a'


def rpc(method, params):
    time.sleep(.25)
    req = urllib.request.Request(NODE, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if 'error' in d:
        raise RuntimeError(str(d['error'])[:200])
    return d['result']


U = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
cases = {Path(f).stem: json.load(open(f)) for f in glob.glob(str(ROOT / 'cases/*.json'))}
owner = {c['address'].lower(): s for s, c in cases.items()}
by_tx = defaultdict(list)
for s, rows in act.items():
    for r in rows:
        by_tx[r['transaction_hash']].append((s, r))
out = []
for tx, v in by_tx.items():
    who = sorted({s for s, _ in v})
    if len(who) < 2:
        continue
    rc = rpc('eth_getTransactionReceipt', [tx])
    t = rpc('eth_getTransactionByHash', [tx])
    entry = dict(tx=tx, who=who, frm=t['from'], to=t['to'], block=int(rc['blockNumber'], 16), logs=len(rc['logs']), rows=[dict(case=s, type=r['type'], side=r.get('side'), title=r.get('title'), outcome=r.get('outcome'), price=r.get('price'), size=r.get('size'), usd=r.get('usdc_size'), ts=r['timestamp'], utc=U(r['timestamp'])) for s, r in v])
    fills, redeemers = [], Counter()
    for l in rc['logs']:
        if l['topics'][0].startswith(ORDERFILLED):
            maker = '0x' + l['topics'][2][-40:]
            taker = '0x' + l['topics'][3][-40:]
            words = [l['data'][2 + 64 * i: 2 + 64 * (i + 1)] for i in range((len(l['data']) - 2) // 64)]
            fills.append(dict(maker=maker, taker=taker, maker_case=owner.get(maker), taker_case=owner.get(taker), side=int(words[0], 16) if words else None, words=[int(w, 16) if len(w) == 64 else w for w in words[:6]]))
        if l['topics'][0].startswith(REDEEM):
            redeemers['0x' + l['topics'][1][-40:]] += 1
    entry['fills'] = fills
    entry['distinct_redeemers'] = len(redeemers)
    entry['named_redeemers'] = sorted(owner[a] for a in redeemers if a in owner)
    out.append(entry)
(OUT / 'transactions_communes.json').write_text(json.dumps(out, indent=0))
for e in sorted(out, key=lambda e: e['rows'][0]['ts']):
    print('\n', e['tx'], e['who'], 'from', e['frm'][:12], 'to', e['to'][:12], 'logs', e['logs'], 'redeemers', e['distinct_redeemers'], e['named_redeemers'])
    for r in e['rows']:
        print('   ', r['utc'], r['case'], r['type'], r['side'], (r['title'] or '')[:40], r['outcome'], r['price'], r['size'], r['usd'])
    for f in e['fills']:
        print('    fill maker', f['maker'][:10], f['maker_case'], 'taker', f['taker'][:10], f['taker_case'], f['words'][:5])
