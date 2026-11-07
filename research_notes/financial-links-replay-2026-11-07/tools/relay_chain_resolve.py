"""Chain-only resolution of Relay same-chain Polygon orders: the 32-byte tail of the deposit tx input is the request id,
and the solver's payout tx carries the same tail. Searches USDC.e/USDC Transfer logs from known Relay solvers in the
next 60 blocks with an amount within 3% below the deposit, then confirms by the input tail. Raw responses archived.
Usage: relay_chain_resolve.py OUTDIR hashes.txt"""
import json, sys, pathlib, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import rpc
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
TOKENS = ['0x2791bca1f2de4661ed88a30c99a7a9449aa84174', '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359']
SOLVERS = ['0xf70da97812cb96acdf810712aa562db8dfa3dbef', '0x56c262027e0de4aea31d2489529cb25d23e58a8b', '0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb', '0xabb2acd3be814a80e502575d6c1dc5f789e9cd10', '0xca7ded7e4f4ba8ab3b10009236ae6d1b95094589']
def pad(a): return '0x' + '0' * 24 + a[2:]
def keep(name, obj):
    b = json.dumps(obj, sort_keys=True).encode(); (OUT / name).write_bytes(b); (OUT / (name + '.sha256')).write_text(hashlib.sha256(b).hexdigest())
res = []
for h in open(sys.argv[2]).read().split():
    p = OUT / f'resolved_{h}.json'
    if p.exists(): res.append(json.loads(p.read_bytes())); continue
    tx = rpc.call('polygon', 'eth_getTransactionByHash', [h]); rc = rpc.call('polygon', 'eth_getTransactionReceipt', [h])
    rid = '0x' + tx['input'][-64:]; B = int(tx['blockNumber'], 16)
    dep = [l for l in rc['logs'] if l['topics'][0] == T and len(l['topics']) == 3 and l['topics'][2][26:] in [s[2:] for s in SOLVERS]]
    amt = int(dep[0]['data'], 16) if dep else 0
    found = None
    for tok in TOKENS:
        logs = rpc.call('polygon', 'eth_getLogs', [{'address': tok, 'fromBlock': hex(B), 'toBlock': hex(B + 60), 'topics': [T, [pad(s) for s in SOLVERS]]}])
        cands = [l for l in logs if 0.97 * amt <= int(l['data'], 16) <= amt]
        for l in cands:
            c = rpc.call('polygon', 'eth_getTransactionByHash', [l['transactionHash']])
            if c['input'][-64:] == rid[2:]:
                found = {'payout_tx': l['transactionHash'], 'payout_block': int(l['blockNumber'], 16), 'payout_logIndex': int(l['logIndex'], 16), 'payout_token': tok,
                         'recipient': '0x' + l['topics'][2][26:], 'payout_atomic': int(l['data'], 16), 'solver': '0x' + l['topics'][1][26:]}
                keep(f'payout_tx_{l["transactionHash"]}.json', c); break
        if found: break
    r = {'deposit_tx': h, 'depositor': tx['from'], 'deposit_block': B, 'deposit_atomic': amt, 'request_id_from_input_tail': rid, **(found or {'recipient': None})}
    keep(f'deposit_tx_{h}.json', {'tx': tx, 'receipt': rc}); p.write_text(json.dumps(r)); res.append(r)
    print(h[:12], 'found' if found else 'NOT FOUND', r.get('recipient'), flush=True)
json.dump(res, open(OUT / 'resolved_all.json', 'w'), indent=1)
print(sum(1 for r in res if r.get('recipient')), 'of', len(res), 'resolved')
