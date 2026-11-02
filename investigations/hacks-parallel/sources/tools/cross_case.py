"""Cross-check of every address and transaction seen in this study against the other PolySentinel investigations. Read only. Levels follow the mission: 1 same address, 2 same transaction, 3 shared service, 4 statistical only, 5 no link shown."""
import csv
import glob
import gzip
import json
import os
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import labels

HOME = Path.home() / 'Projects'
ROOT = Path(__file__).resolve().parent.parent
ADDR = re.compile(r'0x[0-9a-fA-F]{40}')
HASH = re.compile(r'0x[0-9a-fA-F]{64}')
FILES = {
    'ballon_or_cases': [str(HOME / 'PolySentinel-investigation/cases/*.json')],
    'ballon_or_flow_trace': [str(HOME / 'PolySentinel-flow-trace/data/funding_paths.csv'), str(HOME / 'PolySentinel-flow-trace/data/cashout_paths.csv'), str(HOME / 'PolySentinel-flow-trace/data/walk_edges.csv'), str(HOME / 'PolySentinel-flow-trace/data/followups.csv')],
    'changenow_proof': [str(HOME / 'PolySentinel-ChangeNOW-proof/data/*.csv'), str(HOME / 'PolySentinel-ChangeNOW-proof/state/study_addresses.csv')],
    'ballon_dor_2026': [str(HOME / 'PolySentinel-ballon-dor-2026/TRADES.csv'), str(HOME / 'PolySentinel-ballon-dor-2026/derived/positions.csv'), str(HOME / 'PolySentinel-ballon-dor-2026/derived/relay.json'), str(HOME / 'PolySentinel-ballon-dor-2026/derived/ledger.json'), str(HOME / 'PolySentinel-ballon-dor-2026/derived/chain/*.json')],
    'cn_to_polymarket_2026': [str(Path.home() / 'Documents/Crypto/cn_pm_sakana/state/pm_traders.csv')],
}
SHARED_OK = re.compile(r'relay|cow protocol|gpv2|uniswap|polymarket|usdc|usdt|tether|circle|1inch|permit2', re.I)


def scan(patterns):
    addrs, hashes, found = set(), set(), []
    for pattern in patterns:
        for p in glob.glob(pattern):
            found.append(p)
            text = Path(p).read_text(errors='ignore') if not p.endswith('.gz') else gzip.open(p, 'rt').read()
            hashes |= {h.lower() for h in HASH.findall(text)}
            addrs |= {a.lower() for a in ADDR.findall(HASH.sub(' ', text))}
    return addrs, hashes, found


def ours():
    """Our addresses and hashes, with the incident each belongs to."""
    out = {}
    tx = {}
    for name, inc in (('may_polygon_full', 'A_0522'), ('june_eth', 'C_0625')):
        p = ROOT / f'state/runs/{name}.json'
        if p.exists():
            r = json.loads(p.read_text())
            for a, n in r['nodes'].items():
                out.setdefault(a, set()).add(inc)
            for e in r['edges']:
                tx.setdefault(e['tx'], set()).add(inc)
    p = ROOT / 'state/runs/june_core.json'
    if p.exists():
        for k, es_ in json.loads(p.read_text()).items():
            out.setdefault(k.split(':')[1], set()).add('C_0625')
            for e in es_:
                tx.setdefault(e['tx'], set()).add('C_0625')
                if int(e['raw']) >= 10 ** 5 and e['kind'] != 'erc20' or e['token'] in ('0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb',):
                    out.setdefault(e['src'], set()).add('C_0625')
                    out.setdefault(e['dst'], set()).add('C_0625')
    p = ROOT / 'state/runs/oct_core.json'
    if p.exists():
        for k, es_ in json.loads(p.read_text()).items():
            for e in es_:
                tx.setdefault(e['tx'], set()).add('D_1029')
                if e['kind'] != 'erc20' and int(e['raw']) >= 10 ** 18:
                    out.setdefault(e['src'], set()).add('D_1029')
                    out.setdefault(e['dst'], set()).add('D_1029')
    out.pop('0x' + '0' * 40, None)
    return out, tx


def main():
    addrs, txs = ours()
    rows = []
    summary = {}
    for case, patterns in FILES.items():
        a, h, found = scan(patterns)
        shared_a = sorted(set(addrs) & a)
        shared_t = sorted(set(txs) & h)
        summary[case] = dict(files=len(found), their_addresses=len(a), their_hashes=len(h), shared_addresses=len(shared_a), shared_hashes=len(shared_t))
        for s in shared_a:
            rows.append(dict(case=case, kind='address', value=s, incidents=';'.join(sorted(addrs[s]))))
        for s in shared_t:
            rows.append(dict(case=case, kind='tx', value=s, incidents=';'.join(sorted(txs[s]))))
    # incident against incident: what the attack trails share
    inc = {}
    for a, s in addrs.items():
        for i in s:
            inc.setdefault(i, set()).add(a)
    pairs = {}
    names = sorted(inc)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            pairs[f'{x}|{y}'] = sorted(inc[x] & inc[y])
    (ROOT / 'state/runs/cross_case.json').write_text(json.dumps(dict(summary=summary, rows=rows, pairs=pairs), indent=1))
    print(json.dumps(summary, indent=1))
    print(len(rows), 'shared rows')
    print({k: len(v) for k, v in pairs.items()})


if __name__ == '__main__':
    main()
