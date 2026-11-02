"""Contre-vérification : voisins immédiats du transfert brace227 -> kraben006 (origine de l'ETH reçu, destination de l'ETH reparti, délégation 7702). Lecture seule."""
import json, time, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'evidence/contre_verification_20261102'
d = json.load(open(OUT / 'transfert_brace_kraben_blockscout.json'))
full = {t['hash'][:12]: t['hash'] for n in ('brace227_key', 'kraben006_key') for t in d[n]['transactions']}


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'read-only'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)
    except Exception as e:
        return {'_error': str(e)[:160]}


res = {'hashes': {k: full[k] for k in ('0xb17e1c4627', '0xb32fb0edca', '0x1a39308b89', '0xd07bea20a2', '0xb81d1330bf')}}
res['addresses'] = {}
for a in ('0x7e67dF45', '0xadA5bb90', '0x2CfF890f', '0xb43C1981', '0x6B33c41c', '0xcaD621da', '0xd2e28229f6f2c235e57de2ebc727025a1d0530fb'):
    full_a = a
    if len(a) < 42:
        for n in ('brace227_key', 'kraben006_key'):
            for t in d[n]['transactions']:
                for side in ('from', 'to'):
                    h = (t.get(side) or {}).get('hash') or ''
                    if h.lower().startswith(a.lower()):
                        full_a = h
    info = get(f'https://eth.blockscout.com/api/v2/addresses/{full_a}')
    c = get(f'https://eth.blockscout.com/api/v2/addresses/{full_a}/counters')
    res['addresses'][full_a] = dict(contract=info.get('is_contract'), name=info.get('name'), tags=[x.get('display_name') for x in (info.get('public_tags') or [])], metadata=[x.get('name') for x in ((info.get('metadata') or {}).get('tags') or [])], implementations=info.get('implementations'), balance=int(info.get('coin_balance') or 0) / 1e18, txs=c.get('transactions_count'), transfers=c.get('token_transfers_count'))
    time.sleep(.5)
target = [a for a in res['addresses'] if a.lower().startswith('0x7e67df45')][0]
for kind in ('transactions', 'token-transfers', 'internal-transactions'):
    res['next_hop_' + kind] = get(f'https://eth.blockscout.com/api/v2/addresses/{target}/{kind}').get('items', [])[:50]
    time.sleep(.5)
for k in ('0xb17e1c4627', '0xb32fb0edca', '0x1a39308b89'):
    res['relay_' + k] = get(f'https://api.relay.link/requests/v2?hash={full[k]}')
    time.sleep(18)
(OUT / 'voisinage_transfert.json').write_text(json.dumps(res))
print(json.dumps(res['hashes']))
print(json.dumps(res['addresses'], indent=0))
for k in ('0xb17e1c4627', '0xb32fb0edca', '0x1a39308b89'):
    print(k, json.dumps(res['relay_' + k])[:1800])
for kind in ('transactions', 'token-transfers'):
    print(kind, len(res['next_hop_' + kind]))
    for t in res['next_hop_' + kind][:30]:
        print(t.get('timestamp', '')[:19], (t.get('hash') or t.get('transaction_hash') or '')[:12], (t.get('from') or {}).get('hash', '')[:12], '->', ((t.get('to') or {}).get('hash') or '')[:12], (t.get('to') or {}).get('name'), round(int(t.get('value') or 0) / 1e18, 6), t.get('method'), (t.get('token') or {}).get('symbol'), (t.get('total') or {}).get('value'))
