"""One line per deposit and withdrawal of the accounts: what Relay recorded, what the receipt shows. Answers "did all use Relay" on the data."""
import glob
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

ROOT = net.ROOT
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
USDCE = '0x2791bca1f2de4661ed88a30c99a7a9449aa84174'
CH = {1: 'eth', 137: 'polygon', 42161: 'arb', 10: 'op', 8453: 'base', 56: 'bsc', 792703809: 'sol', 8253038: 'btc', 7897: 'arena'}


def main():
    relay = json.load(open(ROOT / 'derived/relay.json'))
    led = json.load(open(ROOT / 'derived/ledger.json'))
    only = sys.argv[1:]
    out = []
    for f in sorted(glob.glob(str(ROOT / 'derived/chain/*.json'))):
        c = json.load(open(f))
        w = c['wallet']
        if w not in led:
            continue
        for tx, fl in sorted(c['flows'].items(), key=lambda x: x[1]['ts']):
            rec = (relay.get(tx) or {}).get('requests') or []
            logs = [(l['address'].lower(), '0x' + l['topics'][1][-40:], '0x' + l['topics'][2][-40:], int(l['data'], 16)) for l in fl['receipt']['logs'] if l['topics'][0] == T and len(l['topics']) == 3 and l['data'] != '0x']
            usdce = [x for x in logs if x[0] == USDCE]
            row = dict(wallet=w, labels=led[w]['labels'], type=fl['type'], usd=round(fl['usdc'], 2), ts=fl['ts'], tx=tx, first=usdce[0][1] if usdce else None, last=usdce[-1][2] if usdce else None, relay=[])
            for q in rec:
                d = q.get('data') or {}
                m = d.get('metadata') or {}
                row['relay'].append(dict(id=q.get('id'), status=q.get('status'), user=q.get('user'), recipient=q.get('recipient'), in_chain=[t.get('chainId') for t in d.get('inTxs') or []], in_tx=[t.get('hash') for t in d.get('inTxs') or []], out_chain=[t.get('chainId') for t in d.get('outTxs') or []], out_tx=[t.get('hash') for t in d.get('outTxs') or []], cin=((m.get('currencyIn') or {}).get('currency') or {}).get('symbol'), cin_amt=(m.get('currencyIn') or {}).get('amountFormatted'), cout=((m.get('currencyOut') or {}).get('currency') or {}).get('symbol'), cout_amt=(m.get('currencyOut') or {}).get('amountFormatted')))
            out.append(row)
    (ROOT / 'derived/flows_table.json').write_text(json.dumps(out, indent=0))
    for r in out:
        if only and r['wallet'][:6] not in only:
            continue
        rr = r['relay'][0] if r['relay'] else None
        print(r['wallet'][:8], time.strftime('%m-%d %H:%M', time.gmtime(r['ts'])), r['type'][:3], str(r['usd']).rjust(9), ('RELAY ' + str(CH.get((rr['in_chain'] or [None])[0], rr['in_chain'])) + '>' + str(CH.get((rr['out_chain'] or [None])[0], rr['out_chain'])) + ' ' + str(rr['cin']) + ' ' + str(rr['cin_amt'])[:9] + ' user ' + str(rr['user'])[:14] + ' rcpt ' + str(rr['recipient'])[:14]) if rr else ('no relay record; first ' + str(r['first'])[:12] + ' last ' + str(r['last'])[:12]))


if __name__ == '__main__':
    main()
