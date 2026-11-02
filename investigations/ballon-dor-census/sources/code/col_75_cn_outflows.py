"""Direction 2, step 2: October 2026 value sends of every labeled ChangeNOW address, measured function, then client recipients.
PROTOCOL.md section 4. Streams to one JSONL per step, one address at a time. Checkpoint: the raw archive and derived/cn_functions.json."""
import csv
import gzip
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hist
import net

T0, T1 = 1790812800, 1793491199  # 2026-10-01 00:00:00 UTC to 2026-10-31 23:59:59 UTC
ROWS = net.ROOT / 'derived/cn_sends.jsonl.gz'
FUNCS = net.ROOT / 'derived/cn_functions.json'
RECOGNIZED = {'USDC', 'USDC.e', 'USDT', 'DAI', 'WETH', 'WBTC'}


def block_at(chain, ts, closest):
    d = net.get('https://api.etherscan.io/v2/api', dict(chainid=chain, module='block', action='getblocknobytime', timestamp=ts, closest=closest), secret=dict(apikey=net.etherscan_key()))
    return int(d['result'])


def op_sends(address):
    """Optimism: no key, whole history then filtered. Full page raises in hist._op_all."""
    out = []
    for action in ('txlist', 'tokentx'):
        for r in hist._op_all(action, address):
            if T0 <= int(r['timeStamp']) <= T1:
                out.append((action, r))
    return out


def sends(address, chain, blocks):
    """Value sends of `address` in the window, plus a count of what it received, for the function rule."""
    if chain == 10:
        tagged = op_sends(address)
    else:
        lo, hi = blocks[chain]
        tagged = [('txlist', r) for r in net.es_all(chain, 'txlist', address, lo, hi)] + [('tokentx', r) for r in net.es_all(chain, 'tokentx', address, lo, hi)]
    rows = []
    received_from = set()
    for action, r in tagged:
        if action == 'txlist':
            if r.get('isError') == '1' or int(r['value']) == 0:
                continue
            rec = dict(asset=hist.NATIVE[chain], contract='', decimals=18)
        else:
            known = hist.STABLE.get(chain, {}).get(r['contractAddress'].lower())
            if not known or known[0] not in RECOGNIZED or int(r['value']) == 0:
                continue
            rec = dict(asset=known[0], contract=r['contractAddress'].lower(), decimals=known[1])
        if r['from'].lower() != address:
            received_from.add(r['from'].lower())
            continue
        rows.append(dict(chain=chain, src=address, dst=(r.get('to') or '').lower(), tx=r['hash'], block=int(r['blockNumber']), ts=int(r['timeStamp']), raw=r['value'], amount=int(r['value']) / 10 ** rec['decimals'], **rec))
    return rows, received_from


def function_of(rows, received_from):
    n = len(rows)
    dst = {r['dst'] for r in rows}
    if n >= 100 and len(dst) >= 50:
        return 'PAYOUT_HOT'
    if n >= 20 and len(dst) <= 10:
        return 'CONSOLIDATION'
    if n < 20 and len(received_from) <= 10:
        return 'DEPOT_CLIENT'
    return 'INCONNUE'


def main():
    with open(net.ROOT / 'derived/cn_universe.csv') as f:
        universe = list(csv.DictReader(f))
    blocks = {c: (block_at(c, T0, 'after'), block_at(c, T1, 'before')) for c in (1, 137, 42161)}
    state = json.loads(FUNCS.read_text()) if FUNCS.exists() else {}
    mode = 'at' if state else 'wt'
    n_failed = 0
    with gzip.open(ROWS, mode) as out:
        for i, u in enumerate(sorted(universe, key=lambda x: (int(x['chain']), x['address']))):
            key = f"{u['address']}:{u['chain']}"
            if key in state:
                continue
            chain = int(u['chain'])
            try:
                rows, received = sends(u['address'], chain, blocks)
            except net.FetchError as e:
                state[key] = dict(address=u['address'], chain=chain, function='FAILED', error=str(e)[:160], sources=u['sources'][:200])
                n_failed += 1
                continue
            fn = function_of(rows, received)
            state[key] = dict(address=u['address'], chain=chain, function=fn, sends=len(rows), recipients=len({r['dst'] for r in rows}), received_from=len(received), sources=u['sources'][:200], lineages=u['lineages'])
            for r in rows:
                out.write(json.dumps(dict(r, source_function=fn), separators=(',', ':')) + '\n')
            out.flush()
            if i % 100 == 0:
                FUNCS.write_text(json.dumps(state))
                print(i, len(universe), Counter(v['function'] for v in state.values()), 'failed', n_failed, flush=True)
    FUNCS.write_text(json.dumps(state))
    print('FINAL', Counter(v['function'] for v in state.values()), 'failed', n_failed)
    hot = [v for v in state.values() if v['function'] == 'PAYOUT_HOT']
    for v in sorted(hot, key=lambda x: -x['sends']):
        print(v['chain'], v['address'], v['sends'], v['recipients'], v['sources'][:100])


if __name__ == '__main__':
    main()
