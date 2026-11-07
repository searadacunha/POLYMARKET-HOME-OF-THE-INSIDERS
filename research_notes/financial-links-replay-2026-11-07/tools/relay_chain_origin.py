"""Reverse of relay_chain_resolve.py: from a Relay solver payout on Polygon (calldata tail = request id), find the same-chain
deposit carrying that tail in the 60 previous blocks (USDC or USDC.e Transfer to a known solver, amount 0-3 % above the payout).
No match = the order came from another chain (left for the Relay API). Usage: relay_chain_origin.py OUTDIR payout_hashes.txt"""
import json, sys, pathlib, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import rpc
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
TOKENS = ['0x3c499c542cef5e3811e1192ce70d8cc03d5c3359', '0x2791bca1f2de4661ed88a30c99a7a9449aa84174']
SOLVERS = ['0xf70da97812cb96acdf810712aa562db8dfa3dbef', '0x56c262027e0de4aea31d2489529cb25d23e58a8b', '0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb',
           '0xabb2acd3be814a80e502575d6c1dc5f789e9cd10', '0xca7ded7e4f4ba8ab3b10009236ae6d1b95094589']
pad = lambda a: '0x' + '0' * 24 + a[2:]
res = []
for h in open(sys.argv[2]).read().split():
    p = OUT / f'origin_{h}.json'
    if p.exists(): res.append(json.loads(p.read_bytes())); continue
    tx = rpc.call('polygon', 'eth_getTransactionByHash', [h]); rc = rpc.call('polygon', 'eth_getTransactionReceipt', [h])
    rid = tx['input'][-64:]; B = int(tx['blockNumber'], 16)
    pay = [l for l in rc['logs'] if l['topics'][0] == T and len(l['topics']) == 3 and l['topics'][1][26:] in [s[2:] for s in SOLVERS]]
    amt = int(pay[0]['data'], 16) if pay else 0
    found = None
    for tok in TOKENS:
        logs = rpc.call('polygon', 'eth_getLogs', [{'address': tok, 'fromBlock': hex(B - 60), 'toBlock': hex(B), 'topics': [T, None, [pad(s) for s in SOLVERS]]}])
        for l in [l for l in logs if amt <= int(l['data'], 16) <= 1.03 * amt]:
            c = rpc.call('polygon', 'eth_getTransactionByHash', [l['transactionHash']])
            if c['input'][-64:] == rid:
                found = {'origin_tx': l['transactionHash'], 'origin_block': int(l['blockNumber'], 16), 'origin_user': '0x' + l['topics'][1][26:], 'origin_atomic': int(l['data'], 16), 'origin_token': tok}
                b = json.dumps(c, sort_keys=True).encode(); (OUT / f'origin_tx_{l["transactionHash"]}.json').write_bytes(b); break
        if found: break
    r = {'payout_tx': h, 'request_id': '0x' + rid, 'payout_block': B, 'payout_atomic': amt, **(found or {'origin_user': None, 'origin': 'OTHER_CHAIN_OR_UNMATCHED'})}
    p.write_text(json.dumps(r)); res.append(r); print(h[:12], r['origin_user'], flush=True)
json.dump(res, open(OUT / 'origins_all.json', 'w'), indent=1)
print(sum(1 for r in res if r['origin_user']), 'of', len(res), 'same-chain origins found')
