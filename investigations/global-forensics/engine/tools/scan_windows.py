"""Read the Base and BSC history that files still need, in windows, from SQD Portal. Usage: scan_windows.py <results> <list.json> [...] [--days=7] [--max-seconds=N] [--plan].

No free explorer serves these chains. Each window comes from the walk: before the hop for funding, after it for exits. A key read at depth 0 has no hop, so it takes the account's first and last activity. Scans resume from their own state. A re-run of the trace finds them through windows.Index, and a node read this way is written as read in windows only.
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import bridges, env
from gf.net import Net
from gf.sqd import Scan

env.redirect_temp()
DAY = 86400
BLOCKS_PER_SECOND = {8453: 150, 56: 1250}  # measured on 03/11, for the plan only


def wanted(paths, days):
    """(address, chain) to time ranges, from each file's WINDOW_SCAN_NEEDED stops."""
    out = defaultdict(list)
    for path in paths:
        result = json.loads(path.read_text())
        account = result.get('account') or {}
        for s in result['stops']:
            if s['reason'] != 'WINDOW_SCAN_NEEDED' or s['chain'] not in BLOCKS_PER_SECOND:
                continue
            if s.get('depth') == 0 or not s.get('limit'):
                low, high = (account.get('first_activity') or 0) - days * DAY, (account.get('last_activity') or 0) + days * DAY
            elif s['direction'] == 'funding':
                low, high = s['limit'] - days * DAY, s['limit']
            else:
                low, high = s['limit'], s['limit'] + days * DAY
            out[(s['address'], s['chain'])].append((low, min(high, int(time.time()))))
    return out


def merged(ranges):
    """Overlapping ranges of one chain become one scan with all their addresses, since a scan costs by blocks and not by addresses."""
    items, out = sorted(ranges), []
    for low, high, address in items:
        if out and low <= out[-1][1]:
            out[-1][1] = max(out[-1][1], high)
            out[-1][2].add(address)
        else:
            out.append([low, high, {address}])
    return out


def main(results, *rest):
    days = next((int(a.split('=', 1)[1]) for a in rest if a.startswith('--days=')), 7)
    limit = next((int(a.split('=', 1)[1]) for a in rest if a.startswith('--max-seconds=')), None)
    root = env.data_root() / 'wallets'
    paths = [root / e['slug'] / 'trace.json' for name in rest if not name.startswith('--') for e in json.loads((Path(results) / name).read_text())]
    needs = wanted([p for p in paths if p.exists()], days)
    by_chain = defaultdict(list)
    for (address, chain), ranges in needs.items():
        by_chain[chain] += [(low, high, address) for low, high in ranges]
    net = Net(budget=2000)
    started, finished, total = time.time(), 0, 0
    for chain, ranges in sorted(by_chain.items()):
        for low, high, addresses in merged(ranges):
            total += 1
            seconds = {8453: 2.0, 56: .75}[chain]
            estimate = (high - low) / seconds / BLOCKS_PER_SECOND[chain]
            print(f"chain {chain} {time.strftime('%Y-%m-%d', time.gmtime(low))} to {time.strftime('%Y-%m-%d', time.gmtime(high))} addresses {len(addresses)} estimate {estimate / 60:.0f} min", flush=True)
            if '--plan' in rest:
                continue
            first, _ = bridges.block_near(net, chain, low)
            last, _ = bridges.block_near(net, chain, high)
            left = None if limit is None else limit - (time.time() - started)
            if left is not None and left <= 0:
                print('time box spent', flush=True)
                return
            done = Scan(chain, sorted(addresses), first, last).run(max_seconds=left, log=lambda m: print(m, flush=True))
            finished += bool(done)
            print('scan', 'done' if done else 'stopped, resumes from its state', flush=True)
    print(f'{finished} of {total} scans finished', flush=True)


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
