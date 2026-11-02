"""Base and BSC have no free history. For each Relay deposit that started there: the origin transaction, and a backward scan of Transfer logs into the payer. Bounded, written, and any node failure is written as such."""
import glob
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net

ROOT = net.ROOT
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
STEP = {56: 900, 8453: 900}
MAX_STEPS = 60


def scan(chain, token, payer, block):
    topic = '0x' + '0' * 24 + payer[2:]
    hits = []
    b = block
    for _ in range(MAX_STEPS):
        lo = max(0, b - STEP[chain])
        try:
            logs = net.rpc('eth_getLogs', [dict(fromBlock=hex(lo), toBlock=hex(b), address=token, topics=[TRANSFER, None, topic])], chain=chain)
        except net.FetchError as e:
            return hits, f'node failure at block {lo}: {str(e)[:100]}'
        for l in logs:
            hits.append(dict(tx=l['transactionHash'], block=int(l['blockNumber'], 16), src='0x' + l['topics'][1][-40:], raw=int(l['data'], 16)))
        if hits:
            return hits, 'found'
        b = lo - 1
    return hits, f'nothing in {MAX_STEPS * STEP[chain]} blocks'


def main():
    out = []
    seen = set()
    flows = json.load(open(ROOT / 'derived/flows_table.json'))
    records = []
    for r in flows:
        for q in r['relay']:
            for c, h in zip(q['in_chain'], q['in_tx']):
                if c in (56, 8453):
                    records.append((r['wallet'], r['labels'], c, h, q['user']))
    for f in glob.glob(str(ROOT / 'derived/walk/*.json')):
        w = json.load(open(f))
        for p in w['relay_records'].values():
            for t in p['in_txs']:
                if t['chain'] in (56, 8453):
                    records.append((w['wallet'], w['labels'], t['chain'], t['hash'], p['user']))
    for wallet, lab, chain, tx, user in records:
        if (chain, tx) in seen or not tx:
            continue
        seen.add((chain, tx))
        try:
            t = net.rpc('eth_getTransactionByHash', [tx], chain=chain)
            rc = net.rpc('eth_getTransactionReceipt', [tx], chain=chain)
        except net.FetchError as e:
            out.append(dict(wallet=wallet, labels=lab, chain=chain, tx=tx, error=str(e)[:120]))
            continue
        # tx.from may be a bundler: the payer is the sender of the token leg, Relay's user when it is an EVM address
        payer = (user or t['from']).lower() if str(user or '').startswith('0x') else t['from'].lower()
        block = int(t['blockNumber'], 16)
        leg = [l for l in rc['logs'] if l['topics'][0] == TRANSFER and len(l['topics']) == 3 and l['topics'][1][-40:] == payer[2:]]
        token = leg[0]['address'].lower() if leg else None
        hits, state = scan(chain, token, payer, block - 1) if token else ([], 'no token leg')
        for h in hits:
            lb = labels.lookup(h['src'], chain)
            h['label'] = lb['name'] if lb else None
            h['label_sources'] = [s['source'] for s in lb['sources']] if lb else []
        out.append(dict(wallet=wallet, labels=lab, chain=chain, tx=tx, payer=payer, relay_user=user, block=block, token=token, scan=state, inflows=hits[:5]))
        print(wallet[:10], lab[:1], chain, tx[:12], 'payer', payer[:12], 'token', str(token)[:12], state, [(h['src'][:14], h['raw'], h['label'], h['tx'][:12]) for h in hits[:3]], flush=True)
    (ROOT / 'derived/bsc_base_origins.json').write_text(json.dumps(out, indent=1))
    print('records', len(out))


if __name__ == '__main__':
    main()
