"""Contre-vérification : calendrier du marché Kane. Résolution sur la chaîne, redemptions par lots, ventes à 0,999. Lecture seule."""
import glob, gzip, json, os, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
NODE = 'https://polygon-bor-rpc.publicnode.com'
R = json.load(open(OUT / 'redemptions.json'))['kane_tx']


def rpc(method, params):
    time.sleep(.3)
    req = urllib.request.Request(NODE, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if 'error' in d:
        raise RuntimeError(str(d['error'])[:300])
    return d['result']


U = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
cases = {Path(f).stem: json.load(open(f)) for f in glob.glob(str(ROOT / 'cases/*.json'))}
owner = {c['address'].lower(): s for s, c in cases.items()}
act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
row = next(r for r in act['0x86544e4dfde'] if r['type'] == 'REDEEM' and 'Harry Kane win' in (r.get('title') or ''))
cid = row['condition_id']
print('condition', cid, 'tx', row['transaction_hash'], 'ts', U(row['timestamp']))
router_log = next(l for l in R['logs'] if l['t0'].startswith('0x74a51ebefec3'))
ROUTER, T_RED = router_log['addr'], router_log['t0']
print('router', ROUTER, 'topic', T_RED, 'topics', router_log['topics'])
b0 = R['block']
res = dict(condition=cid, router=ROUTER, topic=T_RED, block_ref=b0, events=[], resolution=[])
step = 3000
for start in range(b0 - 12000, b0 + 12000, step):
    logs = rpc('eth_getLogs', [dict(address=ROUTER, fromBlock=hex(start), toBlock=hex(start + step - 1), topics=[T_RED, None, cid])])
    for l in logs:
        res['events'].append(dict(block=int(l['blockNumber'], 16), tx=l['transactionHash'], user='0x' + l['topics'][1][-40:], amount=int(l['data'][2:66], 16) / 1e6))
    res_logs = rpc('eth_getLogs', [dict(address='0x4d97dcd97ec945f40cf65f87097ace5ea0476045', fromBlock=hex(start), toBlock=hex(start + step - 1), topics=['0xb44d84d3289691f71497564b85d4233648d9dbae8cbdbb4329f301c3a0185894', cid])])
    res['resolution'] += [dict(block=int(l['blockNumber'], 16), tx=l['transactionHash']) for l in res_logs]
blocks = sorted({e['block'] for e in res['events']} | {x['block'] for x in res['resolution']})
ts = {b: int(rpc('eth_getBlockByNumber', [hex(b), False])['timestamp'], 16) for b in blocks[:400]}
for e in res['events']:
    e['ts'] = ts.get(e['block'])
for e in res['resolution']:
    e['ts'] = ts.get(e['block'])
    e['utc'] = U(e['ts'])
print('resolution', res['resolution'])
print('redemption events', len(res['events']), 'distinct users', len({e['user'] for e in res['events']}), 'blocks', len(blocks), 'txs', len({e['tx'] for e in res['events']}))
per = Counter()
for e in res['events']:
    if e['ts']:
        per[e['ts'] // 60] += 1
for k in sorted(per):
    print(' ', U(k * 60)[5:16], per[k])
print('named', [(owner[e['user']], U(e['ts']), e['amount'], e['tx'][:12]) for e in res['events'] if e['user'] in owner])
(OUT / 'calendrier_kane.json').write_text(json.dumps(res))
