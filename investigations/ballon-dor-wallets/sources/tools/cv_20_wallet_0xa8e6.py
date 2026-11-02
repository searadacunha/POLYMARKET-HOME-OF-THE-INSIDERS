"""Vérification d'un fait signalé par flow-trace : le wallet non nommé 0xa8e64a3c, financé par la clé de brace227. Quelques lectures publiques, puis recoupement local. Ne cherche pas d'autres wallets : flow-trace s'en charge."""
import glob, gzip, json, os, re, subprocess, time, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
W, K = '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5', '0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d'
B = '0xc852b0938f5ad79b640d105ed11c14499454af26'
POLY, ETH = 'https://polygon-bor-rpc.publicnode.com', 'https://ethereum-rpc.publicnode.com'
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
U = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))


def rpc(node, method, params):
    time.sleep(.4)
    req = urllib.request.Request(node, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=40))
    if 'error' in d:
        raise RuntimeError(str(d['error'])[:200])
    return d['result']


def get(url):
    time.sleep(.6)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'read-only'}), timeout=40))


res = {}
res['owner'] = '0x' + rpc(POLY, 'eth_call', [dict(to=W, data='0x8da5cb5b'), 'latest'])[-40:]
assert res['owner'].lower() == K, res['owner']
res['code_wallet_octets'] = (len(rpc(POLY, 'eth_getCode', [W, 'latest'])) - 2) // 2
res['cle_nonce'] = {n: int(rpc(u, 'eth_getTransactionCount', [K, 'latest']), 16) for n, u in (('ethereum', ETH), ('polygon', POLY))}
res['cle_usdc_eth'] = int(rpc(ETH, 'eth_call', [dict(to=USDC, data='0x70a08231' + '0' * 24 + K[2:]), 'latest']), 16) / 1e6
rows, cursor = [], None
for _ in range(10):
    q = dict(user=W, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
    if cursor:
        q['cursor'] = cursor
    b = get('https://data-api.polymarket.com/v2/activity?' + urllib.parse.urlencode(q))
    rows += b.get('data', [])
    cursor = (b.get('pagination') or {}).get('next_cursor')
    if not cursor:
        break
res['activite_complete'] = cursor is None
for r in rows:
    for k in ('name', 'pseudonym', 'bio', 'profile_image', 'profile_image_optimized'):
        r.pop(k, None)
res['lignes'] = len(rows)
res['types'] = {}
for r in rows:
    res['types'][r['type']] = res['types'].get(r['type'], 0) + 1
sum_ = lambda f: round(sum(float(r.get('usdc_size') or 0) for r in rows if f(r)), 6)
res['depots'] = [(U(r['timestamp']), r['usdc_size'], r['transaction_hash']) for r in rows if r['type'] == 'DEPOSIT']
res['retraits'] = [(U(r['timestamp']), r['usdc_size'], r['transaction_hash']) for r in rows if r['type'] == 'WITHDRAWAL']
res['redeem'] = [(U(r['timestamp']), r['usdc_size'], r.get('title'), r['transaction_hash']) for r in rows if r['type'] == 'REDEEM']
buys = [r for r in rows if r['type'] == 'TRADE' and r.get('side') == 'BUY']
res['achats'] = dict(n=len(buys), usd=sum_(lambda r: r['type'] == 'TRADE' and r.get('side') == 'BUY'), parts=round(sum(float(r['size']) for r in buys), 4), premier=U(buys[0]['timestamp']) if buys else None, dernier=U(buys[-1]['timestamp']) if buys else None, marches=sorted({(r.get('title'), r.get('outcome')) for r in buys}))
res['ventes'] = sum_(lambda r: r['type'] == 'TRADE' and r.get('side') == 'SELL')
res['net_retraits_moins_depots'] = round(sum(float(x[1]) for x in res['retraits']) - sum(float(x[1]) for x in res['depots']), 6)
d = get(f'https://eth.blockscout.com/api/v2/addresses/{K}/token-transfers')
res['cle_tokens_blockscout'] = [(t['timestamp'][:19], t['from']['hash'], t['to']['hash'], (t.get('token') or {}).get('symbol'), int((t.get('total') or {}).get('value') or 0) / 10 ** int((t.get('token') or {}).get('decimals') or 0), t['transaction_hash']) for t in d.get('items', [])]
res['cle_tokens_page_complete'] = not d.get('next_page_params')
tx = get(f'https://eth.blockscout.com/api/v2/addresses/{K}/transactions')
res['cle_tx_blockscout'] = [(t['timestamp'][:19], t['from']['hash'], (t.get('to') or {}).get('hash'), int(t['value']) / 1e18, t.get('method'), t['hash']) for t in tx.get('items', [])]
(OUT / 'wallet_0xa8e6.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))

# Recoupement local
sv = json.load(open(OUT / 'transfert_brace_kraben_blockscout.json'))['brace227_key']
flux = sorted(sv['token-transfers'], key=lambda t: t['timestamp'])
print('owner', res['owner'], 'code', res['code_wallet_octets'], 'nonce', res['cle_nonce'], 'USDC eth', res['cle_usdc_eth'])
print('activité', res['lignes'], res['activite_complete'], res['types'])
print('dépôts', res['depots']); print('retraits', res['retraits']); print('redeem', res['redeem']); print('achats', res['achats'], 'ventes', res['ventes'], 'net', res['net_retraits_moins_depots'])
print('\nflux USDC de la clé de brace227, 9 et 10 oct. (hors leurres, hors 0)')
for t in flux:
    v = int((t.get('total') or {}).get('value') or 0) / 10 ** int((t.get('token') or {}).get('decimals') or 0)
    sym = (t.get('token') or {}).get('symbol')
    if sym == 'USDC' and v >= 1 and '2026-10-09' <= t['timestamp'] < '2026-10-11':
        print(' ', t['timestamp'][:19], t['from']['hash'][:12], '->', t['to']['hash'][:12], round(v, 4), t['transaction_hash'][:14])
print('\nclé 0x48ec, jetons'); [print(' ', x[0], x[1][:12], '->', x[2][:12], x[3], round(x[4], 4), x[5][:14]) for x in sorted(res['cle_tokens_blockscout'])[:30]]
print('clé 0x48ec, tx', res['cle_tokens_page_complete']); [print(' ', x[0], x[1][:12], '->', (x[2] or '')[:12], round(x[3], 6), x[4], x[5][:14]) for x in sorted(res['cle_tx_blockscout'])[:30]]
print('\npar où ce wallet apparaît déjà chez moi')
for f in ('collective/derived', 'controls', 'graphs', 'cases', 'evidence/contre_verification_20261102'):
    p = subprocess.run(['grep', '-rl', '-i', W[2:], str(ROOT / f)], capture_output=True, text=True).stdout.split()
    q = subprocess.run(['grep', '-rl', '-i', K[2:], str(ROOT / f)], capture_output=True, text=True).stdout.split()
    print(' ', f, 'wallet', [os.path.basename(x) for x in p], 'clé', [os.path.basename(x) for x in q])
e6 = json.load(open(ROOT / 'collective/derived/B_E6.json'))
print('groupes E6', [g for g, v in e6['groups'].items() if W in v])
cal = json.load(open(OUT / 'calendrier_kane.json'))
print('lot Kane', [(U(e['ts']), e['amount'], e['tx'][:12]) for e in cal['events'] if e['user'] == W])
st = [json.loads(l) for l in open(OUT / 'fenetre_lot_kane.jsonl')]
print('comparateur du lot', [x['user'] == W for x in st].count(True), 'vendeur', W in {json.loads(l)['user'] for l in open(OUT / 'fenetre_vendeurs_kane.jsonl')})
# Achats proches de brace227 sur le même marché
act = [json.loads(l) for l in gzip.open(ROOT / 'evidence/activity/brace227.jsonl.gz', 'rt')]
bb = sorted((r['timestamp'], r['usdc_size'], r.get('title', '')[:30], r.get('outcome')) for r in act if r['type'] == 'TRADE' and r.get('side') == 'BUY' and 'Harry Kane win' in (r.get('title') or ''))
print('achats Kane brace227 du 9 au 11 oct.', [(U(t)[5:], round(u)) for t, u, _, _ in bb if t < 1791849600][:14])
print('achats Kane 0xa8e6', [(U(r['timestamp'])[5:], round(float(r['usdc_size']))) for r in buys][:18])
