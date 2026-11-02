"""Étiquettes publiques Blockscout portées par les contreparties des clés de brace227 et kraben006. Elles sont dans les objets from/to des transactions : la page /addresses/ les rendait vides, d'où le « aucune étiquette » faux du premier brouillon. Source unique, à recouper. Trois compteurs relus."""
import json, time, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'evidence/contre_verification_20261102'
res = dict(source='eth.blockscout.com, objets from/to, lu le 02/11', adresses={}, flux={})


def visit(x, key):
    if isinstance(x, dict):
        if isinstance(x.get('hash'), str) and len(x['hash']) == 42:
            tags = sorted({t.get('name') for t in ((x.get('metadata') or {}).get('tags') or []) if t.get('name')})
            if tags or x.get('name'):
                res['adresses'].setdefault(x['hash'].lower(), dict(nom=x.get('name'), etiquettes=tags))
        for v in x.values():
            visit(v, key)
    elif isinstance(x, list):
        for v in x:
            visit(v, key)


d = json.load(open(OUT / 'transfert_brace_kraben_blockscout.json'))
v = json.load(open(OUT / 'voisinage_transfert.json'))
visit(d, 'keys')
visit(v, 'next')
SERVICES = ('changenow', 'near intents', 'thorchain', 'swft', 'bridgers', 'kucoin', 'binance', 'deblock', 'fixedfloat')
for name in ('brace227_key', 'kraben006_key'):
    rows = []
    for kind in ('transactions', 'token-transfers', 'internal-transactions'):
        for t in d[name][kind]:
            for side in ('from', 'to'):
                o = t.get(side) or {}
                info = res['adresses'].get((o.get('hash') or '').lower())
                if not info or not any(w in ' '.join(info['etiquettes'] + [info['nom'] or '']).lower() for w in SERVICES):
                    continue
                dec = int((t.get('token') or {}).get('decimals') or 18)
                val = int((t.get('total') or {}).get('value') or t.get('value') or 0)
                rows.append(dict(t=t['timestamp'][:19], type=kind, sens=side, adresse=o['hash'], etiquette=(info['nom'] or '') + ' ' + ' / '.join(info['etiquettes'][:3]), montant=val / 10 ** dec, jeton=(t.get('token') or {}).get('symbol', 'ETH'), tx=t.get('hash') or t.get('transaction_hash')))
    res['flux'][name] = sorted(rows, key=lambda r: r['t'])
res['compteurs'] = {}
for a in ('0x3f3Ee0a9cAC2d01DB44001eca3E8382fbe40207B', '0xdd3d72C53Ff982ff59853da71158bf1538b3Ceee', '0x7e67dF45E0a0Bab092cbB2FF045f8AA8DFaB6E23'):
    time.sleep(.6)
    res['compteurs'][a] = json.load(urllib.request.urlopen(urllib.request.Request(f'https://eth.blockscout.com/api/v2/addresses/{a}/counters', headers={'User-Agent': 'read-only'}), timeout=30))
(OUT / 'etiquettes_blockscout.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
for name, rows in res['flux'].items():
    print(name)
    for r in rows:
        print(' ', r['t'], r['type'][:5], r['sens'], r['adresse'][:12], r['etiquette'][:44], round(r['montant'], 5), r['jeton'], r['tx'])
print({k[:10]: (v.get('transactions_count'), v.get('token_transfers_count')) for k, v in res['compteurs'].items()})
