"""Contre-vérification : Gxjc, 59 POL, sortie des POL, ETH de 0xdd97e6, nonces hors Ethereum, délégations 7702, retraits après le lot Kane. Lecture seule, réseau léger."""
import glob, json, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
POLY, ETH = 'https://polygon-bor-rpc.publicnode.com', 'https://ethereum-rpc.publicnode.com'
CHAINS = dict(bsc='https://bsc-rpc.publicnode.com', optimism='https://optimism-rpc.publicnode.com', arbitrum='https://arbitrum-one-rpc.publicnode.com', base='https://base-rpc.publicnode.com', polygon=POLY, ethereum=ETH)
SOL = 'https://api.mainnet-beta.solana.com'


def post(url, method, params, pause=.25):
    time.sleep(pause)
    req = urllib.request.Request(url, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        return d.get('result') if 'error' not in d else dict(_error=str(d['error'])[:200])
    except Exception as e:
        return dict(_error=str(e)[:160])


def get(url, pause=.35):
    time.sleep(pause)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'read-only'}), timeout=40) as r:
            return json.load(r)
    except Exception as e:
        return dict(_error=str(e)[:160])


cases = {Path(f).stem: json.load(open(f)) for f in sorted(glob.glob(str(ROOT / 'cases/*.json')))}
keys = {s: next(r['source'] for r in c['chain_relations'] if r['tx'] is None and r['basis'].startswith('owner()')) for s, c in cases.items()}
res = dict(keys=keys)
# 1. Nonces et code par chaîne
res['nonces'] = {}
for s, k in keys.items():
    res['nonces'][s] = {}
    for name, url in CHAINS.items():
        n = post(url, 'eth_getTransactionCount', [k, 'latest'])
        code = post(url, 'eth_getCode', [k, 'latest'])
        res['nonces'][s][name] = dict(nonce=int(n, 16) if isinstance(n, str) else n, code=code[:48] if isinstance(code, str) else code)
print('nonces')
for s in keys:
    print(' ', s, keys[s][:12], {c: v['nonce'] for c, v in res['nonces'][s].items()}, {c: v['code'] for c, v in res['nonces'][s].items() if isinstance(v['code'], str) and len(v['code']) > 2})
# 2. 59 POL
tx = '0x4b89cf4f04f9ce694b9dc26bc870fd873a5e00aa71ce1d3e99fd556a75005ac8'
rc, t = post(POLY, 'eth_getTransactionReceipt', [tx]), post(POLY, 'eth_getTransactionByHash', [tx])
LOGT = '0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4'
moves = []
for l in rc['logs']:
    if l['address'].lower() == '0x0000000000000000000000000000000000001010' and l['topics'][0] == LOGT:
        moves.append(dict(frm='0x' + l['topics'][2][-40:], to='0x' + l['topics'][3][-40:], pol=int(l['data'][2:66], 16) / 1e18))
    elif l['topics'][0].startswith('0xddf252ad') and len(l['topics']) == 3:
        moves.append(dict(token=l['address'], frm='0x' + l['topics'][1][-40:], to='0x' + l['topics'][2][-40:], raw=int(l['data'][2:66] or '0', 16)))
res['pol59'] = dict(tx=tx, frm=t['from'], to=t['to'], value=int(t['value'], 16), block=int(rc['blockNumber'], 16), moves=moves)
print('59 POL', t['from'], t['to'])
for m in moves:
    print('  ', m)
# 3. Retrait 77 050,77 $ et sortie des POL
wd = '0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1'
rc = post(POLY, 'eth_getTransactionReceipt', [wd])
res['ould_wd'] = [dict(log=int(l['logIndex'], 16), frm='0x' + l['topics'][2][-40:], to='0x' + l['topics'][3][-40:], pol=int(l['data'][2:66], 16) / 1e18) for l in rc['logs'] if l['address'].lower() == '0x0000000000000000000000000000000000001010' and l['topics'][0] == LOGT and int(l['data'][2:66], 16) > 10 ** 20]
bw = int(rc['blockNumber'], 16)
res['ould_wd_ts'] = int(post(POLY, 'eth_getBlockByNumber', [hex(bw), False])['timestamp'], 16)
ex = '0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3'
t2, rc2 = post(POLY, 'eth_getTransactionByHash', [ex]), post(POLY, 'eth_getTransactionReceipt', [ex])
res['ould_swap'] = dict(tx=ex, frm=t2['from'], to=t2['to'], pol=int(t2['value'], 16) / 1e18, block=int(t2['blockNumber'], 16), ts=int(post(POLY, 'eth_getBlockByNumber', [t2['blockNumber'], False])['timestamp'], 16), status=rc2['status'], transfers_to_key=[dict(token=l['address'], raw=int(l['data'][2:66] or '0', 16)) for l in rc2['logs'] if l['topics'][0].startswith('0xddf252ad') and len(l['topics']) == 3 and l['topics'][2][-40:] == t2['from'][-40:]])
print('Ould retrait', res['ould_wd'], res['ould_wd_ts'], 'swap', res['ould_swap'])
kk = keys['ouldlm3alem']
res['ould_key_now'] = dict(pol=int(post(POLY, 'eth_getBalance', [kk, 'latest']), 16) / 1e18)
# USDT du swap : où est-il ?
USDT = '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'
bal = post(POLY, 'eth_call', [dict(to=USDT, data='0x70a08231' + '0' * 24 + kk[2:]), 'latest'])
res['ould_key_now']['usdt'] = int(bal, 16) / 1e6 if isinstance(bal, str) else bal
print('clé Ould maintenant', res['ould_key_now'])
# 4. 26,97 ETH
a = '0xca8B1f1a56A0Fe8947D325BAAFA286F5bD4D6165'
res['dd97_eth'] = dict(address=a, eth=int(post(ETH, 'eth_getBalance', [a, 'latest']), 16) / 1e18, nonce=int(post(ETH, 'eth_getTransactionCount', [a, 'latest']), 16), read_at=time.time())
print('0xca8b', res['dd97_eth'])
# 5. Gxjc : les deux sorties
GX = 'GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW'
res['gxjc'] = {}
for name, addr in (('vidente', 'DMmDPF9sFcNbq8dVKfxqZsKV4xKZBtsUZ4hXSwy1wt5T'), ('cookedrice', 'F7ew8r8X5YL3DPLtzg9Az3cPDKcVxXGjUpqgpskNh5Eh')):
    sigs = post(SOL, 'getSignaturesForAddress', [addr, dict(limit=30)], pause=3) or []
    rows = []
    for s in sigs[:12]:
        x = post(SOL, 'getTransaction', [s['signature'], dict(encoding='jsonParsed', maxSupportedTransactionVersion=0)], pause=3)
        if not x or '_error' in x:
            rows.append(dict(sig=s['signature'], error=str(x)[:80]))
            continue
        ks = x['transaction']['message']['accountKeys']
        pre = {(b['owner'], b['mint']): float(b['uiTokenAmount']['uiAmount'] or 0) for b in x['meta'].get('preTokenBalances', [])}
        post_ = {(b['owner'], b['mint']): float(b['uiTokenAmount']['uiAmount'] or 0) for b in x['meta'].get('postTokenBalances', [])}
        rows.append(dict(sig=s['signature'], t=s['blockTime'], signers=[k['pubkey'] for k in ks if k['signer']], fee_payer=ks[0]['pubkey'], diffs=[[k[0], k[1][:6], round(post_.get(k, 0) - pre.get(k, 0), 4)] for k in set(pre) | set(post_) if abs(post_.get(k, 0) - pre.get(k, 0)) > 1e-6]))
    res['gxjc'][name] = dict(address=addr, n_sigs=len(sigs), rows=rows)
    print(name, addr[:10], 'signatures', len(sigs))
    for r in sorted(rows, key=lambda r: r.get('t', 0)):
        print('  ', r.get('t'), r['sig'][:12], 'payeur', str(r.get('fee_payer'))[:10], 'signataires', [x[:10] for x in r.get('signers', [])], r.get('diffs'))
(OUT / 'faux_signaux.json').write_text(json.dumps(res, indent=0, default=str))
