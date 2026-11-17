"""Profile a Solana wallet from public RPC: all signatures (paged), then USDC deltas and counterparties of every tx.
Archives raw responses (sha256). Usage: sol_wallet_profile.py OUTDIR ADDRESS [max_tx]"""
import json, sys, time, hashlib, pathlib, urllib.request, collections, datetime
OUT = pathlib.Path(sys.argv[1]); A = sys.argv[2]; MAXTX = int(sys.argv[3]) if len(sys.argv) > 3 else 200
D = OUT / A; D.mkdir(parents=True, exist_ok=True)
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
def rpc(method, params, name):
    p = D / name
    if p.exists(): return json.loads(p.read_bytes())['result']
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
    for i in range(8):
        try:
            raw = urllib.request.urlopen(urllib.request.Request('https://api.mainnet-beta.solana.com', data=body, headers={'content-type': 'application/json'}), timeout=60).read()
            r = json.loads(raw)
            if 'result' in r:
                p.write_bytes(raw); (D / (name + '.sha256')).write_text(hashlib.sha256(raw).hexdigest()); time.sleep(0.7); return r['result']
        except Exception as e:
            r = {'error': str(e)}
        time.sleep(4 * (i + 1))
    raise RuntimeError(f'{method}: {r}')
sigs, before, page = [], None, 0
while True:
    opt = {'limit': 1000}
    if before: opt['before'] = before
    res = rpc('getSignaturesForAddress', [A, opt], f'sigs_{page:03d}.json'); sigs += res; page += 1
    if len(res) < 1000: break
    before = res[-1]['signature']
print(A, 'signatures', len(sigs), 'complete' if len(sigs) < MAXTX * 10 else '')
rows = []
for s in sorted(sigs, key=lambda s: s['blockTime'] or 0)[:MAXTX]:
    r = rpc('getTransaction', [s['signature'], {'encoding': 'jsonParsed', 'maxSupportedTransactionVersion': 0}], f"tx_{s['signature']}.json")
    if not r: continue
    m = r['meta']
    own = lambda bal: {b['accountIndex']: int(b['uiTokenAmount']['amount']) for b in bal if b['mint'] == USDC}
    pre, post = own(m['preTokenBalances']), own(m['postTokenBalances'])
    owners = {b['accountIndex']: b['owner'] for b in m['preTokenBalances'] + m['postTokenBalances'] if b['mint'] == USDC}
    deltas = collections.Counter()
    for k in set(pre) | set(post): deltas[owners[k]] += post.get(k, 0) - pre.get(k, 0)
    signers = [k['pubkey'] for k in r['transaction']['message']['accountKeys'] if k.get('signer')]
    rows.append({'sig': s['signature'], 'utc': datetime.datetime.fromtimestamp(r['blockTime'], datetime.timezone.utc).isoformat(), 'err': m['err'],
                 'self_usdc_delta': deltas.get(A, 0) / 1e6, 'others': {o: v / 1e6 for o, v in deltas.items() if o != A and v}, 'signers': signers})
json.dump({'address': A, 'n_signatures': len(sigs), 'rows': rows}, open(D / 'profile.json', 'w'), indent=1)
for x in rows: print(x['utc'][:19], f"{x['self_usdc_delta']:>12.6f}", {k[:8]: round(v, 2) for k, v in x['others'].items()}, 'signers', [k[:8] for k in x['signers']])
