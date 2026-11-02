"""Contre-vérification du 02/11 : le transfert ETH brace227 -> kraben006, relu sans le code de l'audit. Lecture seule, réseau léger."""
import json, sys, time, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'evidence/contre_verification_20261102'
B = '0xc852b0938f5ad79b640d105ed11c14499454af26'
K = '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65'
TX = '0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98'
NODES = ['https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org', 'https://eth.llamarpc.com']


def get(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def rpc(url, method, params):
    return get(url, dict(jsonrpc='2.0', id=1, method=method, params=params))


def paged(addr, kind, maxp=40):
    out, q = [], ''
    for _ in range(maxp):
        d = get(f'https://eth.blockscout.com/api/v2/addresses/{addr}/{kind}{q}')
        out += d.get('items', [])
        n = d.get('next_page_params')
        if not n:
            return out, True
        q = '?' + '&'.join(f'{k}={v}' for k, v in n.items())
        time.sleep(.4)
    return out, False


res = dict(tx=TX, read_at=time.time(), nodes={})
for u in NODES:
    try:
        t = rpc(u, 'eth_getTransactionByHash', [TX]).get('result')
        rc = rpc(u, 'eth_getTransactionReceipt', [TX]).get('result')
        bl = rpc(u, 'eth_getBlockByNumber', [t['blockNumber'], False]).get('result')
        res['nodes'][u] = dict(frm=t['from'], to=t['to'], value_wei=int(t['value'], 16), input=t['input'], nonce=int(t['nonce'], 16), type=t.get('type'), gas=int(t['gas'], 16), block=int(t['blockNumber'], 16), status=rc['status'], gas_used=int(rc['gasUsed'], 16), price=int(rc['effectiveGasPrice'], 16), logs=len(rc['logs']), ts=int(bl['timestamp'], 16))
    except Exception as e:
        res['nodes'][u] = dict(error=str(e)[:160])
    time.sleep(.5)
for name, a in (('brace227_key', B), ('kraben006_key', K)):
    r = dict(address=a)
    info = get(f'https://eth.blockscout.com/api/v2/addresses/{a}')
    r['is_contract'], r['balance_wei'] = info.get('is_contract'), info.get('coin_balance')
    r['code'] = rpc(NODES[0], 'eth_getCode', [a, 'latest']).get('result')
    for kind in ('transactions', 'internal-transactions', 'token-transfers', 'coin-balance-history'):
        items, complete = paged(a, kind)
        r[kind] = items
        r[kind + '_complete'] = complete
    res[name] = r
    time.sleep(.5)
(OUT / 'transfert_brace_kraben_blockscout.json').write_text(json.dumps(res))
print(json.dumps(res['nodes'], indent=0))
for name in ('brace227_key', 'kraben006_key'):
    r = res[name]
    print(name, 'code', r['code'][:60], {k: len(r[k]) for k in ('transactions', 'internal-transactions', 'token-transfers', 'coin-balance-history')}, {k: r[k + '_complete'] for k in ('transactions', 'internal-transactions', 'token-transfers', 'coin-balance-history')})
