"""Contre-vérification : le payeur Solana de l'ETH reçu par la clé de brace227. Relay par utilisateur, historique Solana, recoupement avec les adresses des dossiers. Lecture seule."""
import glob, json, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
S = '7XUJsJBNp7WykVXG4y76ntsSn3H7tFdLVcmehAgJfrZc'
RPC = 'https://api.mainnet-beta.solana.com'


def get(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)
    except Exception as e:
        return {'_error': str(e)[:160]}


def rpc(method, params):
    time.sleep(2.5)
    return get(RPC, dict(jsonrpc='2.0', id=1, method=method, params=params)).get('result')


res = {}
for name, u in (('solana_payer', S), ('brace_key', '0xc852b0938f5ad79b640d105ed11c14499454af26'), ('kraben_key', '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65')):
    time.sleep(18)
    res['relay_user_' + name] = get(f'https://api.relay.link/requests/v2?user={u}&limit=50')
sigs = rpc('getSignaturesForAddress', [S, dict(limit=200)]) or []
res['signatures'] = sigs
res['balance'] = rpc('getBalance', [S])
res['tokens'] = rpc('getTokenAccountsByOwner', [S, dict(programId='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'), dict(encoding='jsonParsed')])
txs = {}
picks = sigs[:6] + sigs[-6:] if len(sigs) > 12 else sigs
for s in picks:
    txs[s['signature']] = rpc('getTransaction', [s['signature'], dict(encoding='jsonParsed', maxSupportedTransactionVersion=0)])
res['txs'] = txs
(OUT / 'payeur_solana_7xujs.json').write_text(json.dumps(res))

known = {}
for f in glob.glob(str(ROOT / 'cases/*.json')):
    blob = open(f).read()
    known[Path(f).stem] = blob
seen = set()
for s, t in txs.items():
    if not t:
        continue
    for k in t['transaction']['message']['accountKeys']:
        seen.add(k['pubkey'])
print('signatures', len(sigs), 'first', sigs[-1]['blockTime'] if sigs else None, 'last', sigs[0]['blockTime'] if sigs else None, 'balance', res['balance'])
print('accounts touched in sampled txs', len(seen))
for a in sorted(seen):
    hits = [c for c, b in known.items() if a in b]
    if hits:
        print('  IN DOSSIERS', a, hits)
for name in ('solana_payer', 'brace_key', 'kraben_key'):
    r = res['relay_user_' + name].get('requests') if isinstance(res['relay_user_' + name], dict) else None
    print('relay', name, None if r is None else len(r), str(res['relay_user_' + name])[:120] if r is None else '')
    for q in (r or [])[:50]:
        m = (q.get('data') or {}).get('metadata') or {}
        print('   ', q.get('createdAt', '')[:19], q.get('status'), 'to', q.get('recipient'), (m.get('currencyIn') or {}).get('amountFormatted'), ((m.get('currencyIn') or {}).get('currency') or {}).get('symbol'), ((m.get('currencyIn') or {}).get('currency') or {}).get('chainId'), '->', (m.get('currencyOut') or {}).get('amountFormatted'), ((m.get('currencyOut') or {}).get('currency') or {}).get('symbol'), ((m.get('currencyOut') or {}).get('currency') or {}).get('chainId'))
