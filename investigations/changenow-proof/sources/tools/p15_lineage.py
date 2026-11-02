"""Node proof of the funder lineage and of the fleet fingerprint counts, then evidence manifests."""
import csv, datetime, gzip, hashlib, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es, net
ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'evidence/onchain'
A, B, X, HW4, HOT3, DEP = '0xa2768df0b1fb437d5d238d5d0e9b7ca584e84628', '0xb2c257557fd1c7a0738d7e9e2c953441f333b8fd', '0x077d360f11d220e4d5d831430c81c26c9be7c4a4', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b'
pick = []
for r in es.rows('txlist', A, sort='asc'):
    if int(r['value']) and ((r['from'].lower() == X and r['to'].lower() == A) or (r['from'].lower() == A and r['to'].lower() in (HW4, B, X))):
        pick.append(r)
for r in es.rows('txlist', B, sort='asc'):
    if int(r['value']) and r['to'] and r['to'].lower() == HOT3:
        pick.append(r)
out, seen = [], set()
for r in sorted(pick, key=lambda x: int(x['timeStamp'])):
    if r['hash'] in seen:
        continue
    seen.add(r['hash'])
    t = net.rpc('eth_getTransactionByHash', [r['hash']], 1)
    rc = net.rpc('eth_getTransactionReceipt', [r['hash']], 1)
    b = net.rpc('eth_getBlockByNumber', [t['blockNumber'], False], 1)
    body = json.dumps(dict(tx=t, receipt=rc, block=dict(number=t['blockNumber'], timestamp=int(b['timestamp'], 16), hash=b['hash'])), sort_keys=True).encode()
    (DIR / f"{r['hash']}.json").write_bytes(body)
    ok = int(rc['status'], 16) == 1 and t['from'].lower() == r['from'].lower() and (t['to'] or '').lower() == r['to'].lower() and int(t['value'], 16) == int(r['value'])
    out.append(dict(tx=r['hash'], src=r['from'].lower(), dst=r['to'].lower(), raw=r['value'], utc=datetime.datetime.fromtimestamp(int(b['timestamp'], 16), datetime.UTC).strftime('%Y-%m-%d %H:%M:%S'), node_ok=ok, sha256=hashlib.sha256(body).hexdigest()))
    print(out[-1]['utc'], out[-1]['src'][:10], out[-1]['dst'][:10], int(r['value']) / 1e18, r['hash'], 'OK' if ok else 'BAD', flush=True)
# fingerprint counts on the 54 single-use witnesses
p = json.load(open(ROOT / 'state/p10.json'))
diffs, delays, gp, gas, n = Counter(), Counter(), Counter(), Counter(), 0
inb = 0
for w in p['witness_relay']:
    if w['tx'] == 2 and w['n_in'] == 1 and w['n_out'] == 1 and w['n_to_dep'] == 1:
        rows = es.rows('txlist', w['address'], sort='asc')
        i = [x for x in rows if x['to'].lower() == w['address']][0]
        o = [x for x in rows if x['from'].lower() == w['address']][0]
        d = int(i['value']) - int(o['value'])
        n += 1
        diffs['exact_6e13' if d == 6 * 10 ** 13 else ('within_6e13_6.01e13' if 6 * 10 ** 13 <= d <= 601 * 10 ** 11 else 'other')] += 1
        delays[int(o['timeStamp']) - int(i['timeStamp'])] += 1
        gp[o['gasPrice']] += 1
        gas[o['gas']] += 1
        inb += 400 <= int(o['timeStamp']) - int(i['timeStamp']) <= 600
res = dict(lineage=out, witness=dict(n=n, diffs=diffs, delays=delays, gas_price=gp, gas=gas, delay_400_600=inb))
(ROOT / 'state/p15.json').write_text(json.dumps(res, default=str))
print(res['witness'])
INV = Path.home() / 'Projects/PolySentinel-investigation'
for s in 'brace227 kraben006 walletwallet8424 ouldlm3alem wen'.split():
    d = json.load(open(INV / f'cases/{s}.json'))
    print(s, d['first_activity'], d['last_activity'], d['account'].get('deposits'), d['account'].get('withdrawals') if 'withdrawals' in d['account'] else '')
