"""Single-use addresses Blockscout tags ChangeNOW Dep, read as deposit addresses: fingerprint and where they sweep. Then node proof of one transaction per attribution link and of the reverse flows found at the second hop."""
import csv, datetime, gzip, hashlib, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es, net
ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'evidence/onchain'
DEP = '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b'
res = dict(sib=[])
with gzip.open(ROOT / 'state/bs_changenow_list.csv.gz', 'rt') as f:
    sib = [r['address'] for r in csv.DictReader(f) if r['slug'] == 'changenow-dep' and r['chain_id'] == '1']
for a in sib:
    tx = es.rows('txlist', a, sort='asc')
    tk = es.rows('tokentx', a, sort='asc')
    i = [x for x in tx if x['to'] and x['to'].lower() == a and int(x['value']) > 0]
    o = [x for x in tx if x['from'].lower() == a and int(x['value']) > 0]
    row = dict(address=a, tx=len(tx), tokens=len(tk), n_in=len(i), n_out=len(o))
    if len(tx) == 2 and i and o:
        row.update(delay=int(o[0]['timeStamp']) - int(i[0]['timeStamp']), diff=int(i[0]['value']) - int(o[0]['value']), gas_price=o[0]['gasPrice'], gas=o[0]['gas'], to=o[0]['to'].lower(), value=o[0]['value'], t_in=int(i[0]['timeStamp']), sender=i[0]['from'].lower(), hash_out=o[0]['hash'])
    res['sib'].append(row)
    print({k: row.get(k) for k in ('address', 'tx', 'tokens', 'delay', 'diff', 'gas_price', 'gas', 'to', 't_in')}, flush=True)
# node proofs
p9 = json.load(open(ROOT / 'state/p9.json'))
p10 = json.load(open(ROOT / 'state/p10.json'))
want = {}
seen = set()
for l in p9['links']:
    for h in l['hits']:
        me = 'dep' if DEP in (h['f'], h['to']) else 'hot3'
        k = (l['address'], me, 'in' if h['to'] in (DEP, '0xdd3d72c53ff982ff59853da71158bf1538b3ceee') else 'out')
        if k not in seen:
            seen.add(k)
            want[h['h']] = dict(kind='attribution_link', label=l['names'][0], src=h['f'], dst=h['to'], raw=h['v'], sym=h['sym'], dec=h['dec'])
for h in p10['hop2_hits']:
    for x in h['hits']:
        want[x['h']] = dict(kind='second_hop_reverse', label=h['address'], src=x['f'], dst=x['to'], raw=x['v'], sym=x['sym'], dec=None)
out = []
for tx, w in want.items():
    t = net.rpc('eth_getTransactionByHash', [tx], 1)
    rc = net.rpc('eth_getTransactionReceipt', [tx], 1)
    b = net.rpc('eth_getBlockByNumber', [t['blockNumber'], False], 1)
    body = json.dumps(dict(tx=t, receipt=rc, block=dict(number=t['blockNumber'], timestamp=int(b['timestamp'], 16), hash=b['hash'])), sort_keys=True).encode()
    (DIR / f'{tx}.json').write_bytes(body)
    TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    native = t['from'].lower() == w['src'] and (t['to'] or '').lower() == w['dst'] and int(t['value'], 16) == int(w['raw']) and int(t['value'], 16) > 0
    logs = [l for l in rc['logs'] if l['topics'] and l['topics'][0] == TRANSFER and len(l['topics']) == 3 and '0x' + l['topics'][1][-40:] == w['src'] and '0x' + l['topics'][2][-40:] == w['dst'] and l['data'] != '0x' and int(l['data'], 16) == int(w['raw'])]
    ok = int(rc['status'], 16) == 1 and (native or bool(logs))
    out.append(dict(w, tx=tx, block=int(t['blockNumber'], 16), utc=datetime.datetime.fromtimestamp(int(b['timestamp'], 16), datetime.UTC).strftime('%Y-%m-%d %H:%M:%S'), node_ok=ok, contract=(logs[0]['address'].lower() if logs else ''), sha256=hashlib.sha256(body).hexdigest()))
    print(out[-1]['utc'], w['kind'][:6], str(w['label'])[:26], w['src'][:10], w['dst'][:10], w['sym'], w['raw'][:16], 'OK' if ok else 'MISMATCH', flush=True)
res['proofs'] = out
(ROOT / 'state/p14.json').write_text(json.dumps(res))
print('done', len(out), sum(x['node_ok'] for x in out), flush=True)
