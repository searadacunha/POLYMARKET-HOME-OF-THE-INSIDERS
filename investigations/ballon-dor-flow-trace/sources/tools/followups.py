"""Hand-chosen follow-ups past the walk's stopping points, kept as data so that the reports can cite them: the 1 % intermediary after WenZhuanBuPei, the sweeper behind it, hub measures, and the unnamed wallet's key. Writes state/followups.json and data/followups.csv."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evm
import net
import sol
import walk

ROOT = net.ROOT
INTERMEDIARY = '0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50'
SWEEPER = '0x51cf2d9f67078d76c21258c5aa2cb39a2ca24999'
WEN_RECIPIENT = '0xe820ecb3c6f48a420a5538046cab73d2f40987cd'
OTHER_KEY = '0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d'
OTHER_WALLET = '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5'
HUBS = [('0x0853ea40b121f9135d7e0c07fae35d59aedb4d0b', 137), ('0x6bf18baf7819bd6232879d1cef883caf2dcf7e95', 56), (SWEEPER, 42161), (INTERMEDIARY, 42161), ('0xdd3d72c53ff982ff59853da71158bf1538b3ceee', 1), ('0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', 1), ('0xcc0f311eb2c688f30bc9aadb42781e46899723f7', 1), ('0xa3222357a0eccf60c73606170be6c99adecb59b3', 1)]
FLOW_FIELDS = ['leg', 'chain', 'utc', 'token', 'amount', 'raw', 'decimals', 'src', 'dst', 'tx', 'source']


def row(leg, r):
    return dict(leg=leg, chain=r['chain'], utc=walk.now_utc(r['at']), token=r['token'], amount=int(r['raw']) / 10 ** int(r['decimals']), raw=r['raw'], decimals=r['decimals'], src=r['src'], dst=r['dst'], tx=r['tx'], source=r.get('source'))


def main():
    out, flows = dict(), []
    rows, info = evm.history(INTERMEDIARY, 42161)
    entry = next(r for r in rows if r['src'] == WEN_RECIPIENT and r.get('known') and r['token'] == 'USDC')
    t0 = entry['at']
    flows.append(row('wen_to_intermediary', entry))
    legs = [r for r in rows if r['src'] == INTERMEDIARY and r.get('known') and r['token'] == 'USDC' and t0 <= r['at'] <= t0 + 7200 and int(r['raw']) >= 100_000_000]
    fee = min(legs, key=lambda r: int(r['raw']))
    chunks = [r for r in legs if r is not fee]
    flows.append(row('commission', fee))
    flows += [row('chunk', r) for r in chunks]
    out['commission_pct'] = int(fee['raw']) / int(entry['raw']) * 100
    out['chunks_sum'] = sum(int(r['raw']) for r in chunks) / 1e6
    # how the intermediary behaves elsewhere: a large entry against the largest payment in the next 24 h
    ratios = []
    for r in rows:
        if r['dst'] == INTERMEDIARY and r.get('known') and r['token'] in ('USDC', 'USDT') and int(r['raw']) >= 40_000 * 10 ** 6:
            after = [x for x in rows if x['src'] == INTERMEDIARY and x.get('known') and x['token'] == r['token'] and r['at'] <= x['at'] <= r['at'] + 86400 and int(x['raw']) >= int(r['raw']) * .5]
            if after:
                best = max(after, key=lambda x: int(x['raw']))
                ratios.append(dict(received=int(r['raw']) / 1e6, largest_paid=int(best['raw']) / 1e6, ratio=int(best['raw']) / int(r['raw'])))
    out['intermediary_ratios'] = sorted(ratios, key=lambda x: -x['received'])[:12]
    for r in chunks:
        sweep = next(x for x in evm.history(r['dst'], 42161)[0] if x['src'] == r['dst'] and x.get('known') and x['token'] == 'USDC' and int(x['raw']) > 0)
        flows.append(row('sweep', sweep))
    out['sweep_tx'] = flows[-1]['tx']
    t = net.rpc('eth_getTransactionByHash', [out['sweep_tx']], 42161)
    out['sweep_sender'] = t['from'].lower()
    sw_rows, sw_info = evm.history(SWEEPER, 42161)
    stable = [r for r in sw_rows if r.get('known') and r['ok'] and int(r['raw']) > 0 and r['token'] in ('USDC', 'USDT', 'USDC.e')]
    out['sweeper'] = dict(nonce=evm.probe(SWEEPER, 42161)['nonce'], complete=sw_info['complete'], rows=len(sw_rows), senders=len({r['src'] for r in stable if r['dst'] == SWEEPER}), recipients=len({r['dst'] for r in stable if r['src'] == SWEEPER}))
    out['hubs'] = {f'{a}:{c}': evm.probe(a, c) for a, c in HUBS}
    # latest page of each payout hub, the measure quoted in the reports
    key = dict(apikey=net._key_from_env())
    measures = {}
    for a, c, pages in (('0x0ce9bdf38714143043b1d36de9bd90f7335bf06d', 137, 2), ('0xa3222357a0eccf60c73606170be6c99adecb59b3', 1, 1)):
        page_rows = []
        for page in range(1, pages + 1):
            page_rows += net.get(evm.ETHERSCAN, dict(chainid=c, module='account', action='tokentx', address=a, page=page, offset=1000, sort='desc', startblock=0, endblock=999999999), pause=.35, secret=key).get('result') or []
        times = [int(r['timeStamp']) for r in page_rows]
        measures[a] = dict(rows=len(page_rows), recipients=len({r['to'].lower() for r in page_rows if r['from'].lower() == a}), hours=round((max(times) - min(times)) / 3600, 1))
    out['hub_measures'] = measures
    r_key, _ = evm.history(OTHER_KEY, 1)
    out['other_key'] = dict(balances=walk.balances(OTHER_KEY, 1), musd=next((int(r['raw']) / 10 ** int(r['decimals']) for r in r_key if r['token'] == 'mUSD' and r['dst'] == OTHER_KEY), None), kind=evm.probe(OTHER_KEY, 1))
    for r in r_key:
        if r.get('known') and r['token'] == 'USDC' and int(r['raw']) >= 100_000_000:
            flows.append(row('other_key', r))
    d = net.get(evm.ETHERSCAN, dict(chainid=137, module='contract', action='getcontractcreation', contractaddresses=OTHER_WALLET), pause=.3, secret=dict(apikey=net._key_from_env()))['result'][0]
    out['other_wallet_creation'] = dict(tx=d['txHash'], at=int(d['timestamp']), utc=walk.now_utc(int(d['timestamp'])), factory=d['contractFactory'])
    activity = json.loads((ROOT / 'state/wallet_0xa8e6_activity.json').read_text())
    buys = [r for r in activity if r['type'] == 'TRADE']
    out['other_wallet'] = dict(buy_usd=sum(float(r['usdc_size']) for r in buys), shares=sum(float(r['size']) for r in buys), trades=len(buys), first=walk.now_utc(buys[0]['timestamp']), last=walk.now_utc(buys[-1]['timestamp']), types=Counter(r['type'] for r in activity))
    gx = sol.signatures('BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6')[0]
    out['kucoin_hot_wallet_2'] = dict(signatures_read=len(gx), newest=walk.now_utc(gx[0]['blockTime']), oldest=walk.now_utc(gx[-1]['blockTime']))
    (ROOT / 'state/followups.json').write_text(json.dumps(dict(out, flows=flows), default=str))
    with (ROOT / 'data/followups.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FLOW_FIELDS)
        w.writeheader()
        w.writerows(flows)
    print(json.dumps({k: v for k, v in out.items() if k != 'hubs'}, default=str)[:1700])
    print({k: v['nonce'] for k, v in out['hubs'].items()})
    for x in flows:
        print(x['leg'], x['utc'], x['token'], round(x['amount'], 2), x['src'][:10], x['dst'][:10], x['tx'][:12])


if __name__ == '__main__':
    main()
