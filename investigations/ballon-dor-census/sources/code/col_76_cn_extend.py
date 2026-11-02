"""Amendment 2. Level A: every labeled non-client address on chains 1, 137, 42161. Level B: payout-like addresses one or two hops from level A, weaker attribution. Sends are appended with their level; nothing already read is read twice."""
import csv
import gzip
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import col_75_cn_outflows as C
import labels
import net

ROOT = net.ROOT
CHAINS = (1, 137, 42161)
HUB = '0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423'
OUT = ROOT / 'derived/cn_sends_ext.jsonl.gz'
FUNCS = ROOT / 'derived/cn_functions_ext.json'
SEVICE = ('exchange', 'instant_exchange', 'bridge', 'mixer', 'dex_or_router', 'polymarket')


def main():
    universe = list(csv.DictReader(open(ROOT / 'derived/cn_universe.csv')))
    labeled = sorted({u['address'] for u in universe if 'sample of client deposit' not in u['sources']})
    sources = {u['address']: u['sources'][:160] for u in universe}
    blocks = {c: (C.block_at(c, C.T0, 'after'), C.block_at(c, C.T1, 'before')) for c in CHAINS}
    state = {}
    with gzip.open(OUT, 'wt') as out:
        def read(address, chain, level, parent=None):
            key = f'{address}:{chain}'
            if key in state:
                return state[key]
            try:
                rows, received = C.sends(address, chain, blocks)
            except net.FetchError as e:
                state[key] = dict(address=address, chain=chain, level=level, function='FAILED', error=str(e)[:160], parent=parent)
                return state[key]
            fn = C.function_of(rows, received)
            state[key] = dict(address=address, chain=chain, level=level, function=fn, sends=len(rows), recipients=len({r['dst'] for r in rows}), received_from=len(received), usd_like=round(sum(r['amount'] for r in rows if r['asset'] in ('USDC', 'USDC.e', 'USDT', 'DAI'))), sources=sources.get(address, '')[:160], parent=parent)
            for r in rows:
                out.write(json.dumps(dict(r, source_function=fn, level=level), separators=(',', ':')) + '\n')
            out.flush()
            return state[key]

        for i, a in enumerate(labeled):
            for c in CHAINS:
                read(a, c, 'A')
            if i % 20 == 0:
                FUNCS.write_text(json.dumps(state))
                print('A', i, len(labeled), Counter(v['function'] for v in state.values()), flush=True)
        print('level A', Counter(v['function'] for v in state.values()), flush=True)
        # level B, two hops at most
        frontier = []
        with gzip.open(OUT, 'rt') as f:
            pass
        out.flush()
        rows_seen = []
        for hop in (1, 2):
            prev = [v for v in state.values() if v['function'] in ('CONSOLIDATION', 'PAYOUT_HOT') and v['level'] in ('A', f'B{hop - 1}')]
            dest = Counter()
            parents = {}
            for v in prev:
                r, _ = C.sends(v['address'], v['chain'], blocks)
                for s in r:
                    dest[(s['dst'], v['chain'])] += 1
                    parents[(s['dst'], v['chain'])] = v['address']
            # only destinations served repeatedly: a client paid once is not a hub
            cand = [k for k, n in dest.items() if n >= 3 and k[0] not in labeled and f'{k[0]}:{k[1]}' not in state]
            print('hop', hop, 'from', len(prev), 'destinations', len(dest), 'candidates', len(cand), flush=True)
            for a, c in cand:
                try:
                    lab = labels.lookup(a, c)
                except net.FetchError:
                    lab = None
                if lab and lab['category'] in SEVICE and 'changenow' not in lab['name'].lower():
                    state[f'{a}:{c}'] = dict(address=a, chain=c, level=f'B{hop}', function='AUTRE_SERVICE', label=lab['name'], parent=parents[(a, c)])
                    continue
                read(a, c, f'B{hop}', parents[(a, c)])
            FUNCS.write_text(json.dumps(state))
        for c in CHAINS:
            read(HUB, c, 'B_hub', 'cn_pm_sakana/case_02_cn_infra.md')
    FUNCS.write_text(json.dumps(state))
    print('FINAL', Counter((v['level'], v['function']) for v in state.values()))
    for v in sorted([x for x in state.values() if x['function'] in ('PAYOUT_HOT', 'CONSOLIDATION')], key=lambda x: -x.get('sends', 0))[:30]:
        print(v['level'], v['chain'], v['address'], v['function'][:8], 'sends', v.get('sends'), 'rcpt', v.get('recipients'), 'stable$', v.get('usd_like'), 'parent', str(v.get('parent'))[:12], v.get('sources', '')[:40])


if __name__ == '__main__':
    main()
