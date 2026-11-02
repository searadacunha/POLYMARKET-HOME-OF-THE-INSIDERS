"""Complète cv_20 : complétude de la page de transactions de 0x48ec, identifiant Relay des deux dépôts du wallet 0xa8e64a3c, rafale E2 où il figure. Quatre lectures publiques au plus. Lecture seule."""
import glob, gzip, json, os, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
W = '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5'
K = '0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d'


def get(url):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'read-only'}), timeout=40))
    except Exception as e:
        return dict(_error=str(e)[:120])


res = {}
d = get(f'https://eth.blockscout.com/api/v2/addresses/{K}/transactions')
envois = [t for t in d.get('items', []) if t['from']['hash'].lower() == K]
res['page_tx'] = dict(lignes=len(d.get('items', [])), page_suivante=bool(d.get('next_page_params')), envois=len(envois), nonces=sorted(t['nonce'] for t in envois), types=sorted({t.get('type') for t in envois}, key=str), plus_ancienne=min(t['timestamp'] for t in d.get('items', []))[:19] if d.get('items') else None)
res['relay'] = {}
for name, h in (('depot_2200', '0x2e7684ba9eaf'), ('depot_2965', '0x0f7314786495')):
    full = next(x[5] for x in json.load(open(OUT / 'wallet_0xa8e6.json'))['cle_tokens_blockscout'] if x[5].startswith(h))
    time.sleep(25)
    r = get(f'https://api.relay.link/requests/v2?hash={full}')
    q = (r.get('requests') or [{}])[0] if isinstance(r, dict) else {}
    res['relay'][name] = dict(tx=full, erreur=r.get('_error'), id=q.get('id'), status=q.get('status'), user=q.get('user'), recipient=q.get('recipient'), in_txs=[t.get('hash') for t in (q.get('data') or {}).get('inTxs', [])], out_txs=[t.get('hash') for t in (q.get('data') or {}).get('outTxs', [])])
e2 = json.load(open(ROOT / 'collective/derived/A_E2.json'))
hits = []
def walk(x, path=''):
    if isinstance(x, dict):
        for k, v in x.items():
            walk(v, f'{path}.{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x):
            if isinstance(v, dict) and W in json.dumps(v):
                hits.append((f'{path}[{i}]', v))
            else:
                walk(v, f'{path}[{i}]')
walk(e2)
res['rafales_E2'] = [(p, {k: v[k] for k in v if k != 'members'}, v.get('members')) for p, v in hits]
cases = {json.load(open(f))['address'].lower(): Path(f).stem for f in glob.glob(str(ROOT / 'cases/*.json'))}
for p, v in hits:
    print(p, json.dumps({k: v[k] for k in v if k not in ('members',)})[:300], [cases.get(m, m[:10]) for m in v.get('members', [])])
act = [json.loads(l) for l in gzip.open(ROOT / 'evidence/activity/brace227.jsonl.gz', 'rt')]
buy = [r for r in act if r['type'] == 'TRADE' and r.get('side') == 'BUY']
res['brace_9_10_oct'] = dict(total=round(sum(r['usdc_size'] for r in buy if 1791504000 <= r['timestamp'] < 1791676800), 2), kane=round(sum(r['usdc_size'] for r in buy if 1791504000 <= r['timestamp'] < 1791676800 and 'Harry Kane win' in r['title']), 2), kane_24_26=round(sum(r['usdc_size'] for r in buy if r['timestamp'] >= 1792800000 and 'Harry Kane win' in r['title']), 2), kane_9=round(sum(r['usdc_size'] for r in buy if 1791504000 <= r['timestamp'] < 1791590400 and 'Harry Kane win' in r['title']), 2))
b = json.load(open(OUT / 'etiquettes_blockscout.json'))
res['blofin'] = [(t['timestamp'][:19], t['from']['hash'][:12], int(t['total']['value']) / 1e6, t['transaction_hash']) for t in json.load(open(OUT / 'transfert_brace_kraben_blockscout.json'))['brace227_key']['token-transfers'] if t['from']['hash'].lower().startswith('0x7ff8bbf9')]
(OUT / 'wallet_0xa8e6_preuves.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps({k: res[k] for k in ('page_tx', 'relay', 'brace_9_10_oct', 'blofin')}, indent=0, ensure_ascii=False))
