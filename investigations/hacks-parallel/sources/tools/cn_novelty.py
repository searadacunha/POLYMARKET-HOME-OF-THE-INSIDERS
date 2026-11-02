"""First-funded test on a random sample of recipients, target window against a control week, seed fixed. FIRST_FUNDED: full history readable and no recognized value received before the first payout of the window. An empty list only counts after the retries of es.rows."""
import collections
import json
import math
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import cn_common as cc
import cn_windows as w
import es
import tokens

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = 40
SEED = 20261102
HOURS = 24
PLAN = [('A_0522', 'f2020'), ('A_0522', '6976'), ('A_0522', 'HW3'), ('C_0625', 'f2020'), ('C_0625', 'HW3'), ('D_1029', 'f2020'), ('D_1029', 'DEP3F3')]


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p, d = k / n, 1 + z * z / n
    m = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(m - h, 4), round(m + h, 4)


def status(a, chain, first_ts):
    """FIRST_FUNDED, ALREADY_ACTIVE, or UNKNOWN. Reads the 10 oldest rows of each list."""
    tx = es.rows('txlist', a, chain=chain, offset=10)
    if any(int(r['timeStamp']) < first_ts and r['to'].lower() == a and int(r['value']) > 0 and r['isError'] == '0' for r in tx):
        return 'ALREADY_ACTIVE'
    if any(int(r['timeStamp']) < first_ts and r['from'].lower() == a for r in tx):
        return 'ALREADY_ACTIVE'
    internal = es.rows('txlistinternal', a, chain=chain, offset=10)
    if any(int(r['timeStamp']) < first_ts and r['to'].lower() == a and int(r['value']) > 0 for r in internal):
        return 'ALREADY_ACTIVE'
    token = es.rows('tokentx', a, chain=chain, offset=40)
    edges = [e for e in c.token_edges(token, chain) if e['dst'] == a and e['ts'] < first_ts and tokens.recognized(chain, e)]
    if edges:
        return 'ALREADY_ACTIVE'
    if len(token) == 40 and int(token[-1]['timeStamp']) < first_ts:
        return 'UNKNOWN'  # history older than what was read may hold a recognized token
    return 'FIRST_FUNDED'


def main():
    excluded = set(json.loads((ROOT / 'state/runs/cn_excluded.json').read_text()))
    rng = random.Random(SEED)
    results = []
    per_address = {}
    for incident, source in PLAN:
        chain = w.SOURCES[source][1]
        controls = w.INCIDENTS[incident]['controls']
        for name in ('target48', f'ctrl{controls[1]:+d}d'):
            rows, _ = cc.payouts(incident, source, name)
            start = cc.window_start(incident, name)
            first = {}
            for e in sorted(rows or [], key=lambda x: x['ts']):
                if start <= e['ts'] < start + HOURS * 3600 and e['dst'] not in excluded and tokens.worth_following(chain, e):
                    first.setdefault(e['dst'], e['ts'])
            pool = sorted(first)
            sample = rng.sample(pool, min(SAMPLE, len(pool)))
            tally = collections.Counter()
            for a in sample:
                code = None
                try:
                    st = status(a, chain, first[a])
                except RuntimeError as err:
                    st, code = 'UNKNOWN', str(err)[:100]
                tally[st] += 1
                per_address[f'{incident}|{source}|{name}|{a}'] = dict(status=st, first_ts=first[a], error=code)
            known = tally['FIRST_FUNDED'] + tally['ALREADY_ACTIVE']
            results.append(dict(incident=incident, source=source, window=name, recipients=len(pool), sampled=len(sample), first_funded=tally['FIRST_FUNDED'], already_active=tally['ALREADY_ACTIVE'], unknown=tally['UNKNOWN'], wilson95=wilson(tally['FIRST_FUNDED'], known)))
            print(results[-1], flush=True)
            (ROOT / 'state/runs/novelty.json').write_text(json.dumps(dict(results=results, per_address=per_address)))


if __name__ == '__main__':
    main()
