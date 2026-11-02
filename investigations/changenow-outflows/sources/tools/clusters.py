"""Offline. Groups of recipients first paid inside 1, 5, 15 and 60 minute windows, per tier and period, against a null: first-payout times shuffled inside their own hour of week. A busy service pays many addresses at once by construction: only an excess over this null is reported, and even that is not coordination. Writes state/clusters.json."""
import csv, json, random, resource, sys, time
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
win = json.loads((ROOT / 'state/window.json').read_text())
T1 = win['t_end']
BO = (1790208000, 1792713599)
WINDOWS = (60, 300, 900, 3600)
PERMS = 200
PERIODS = {'24h': (T1 - 86400, T1), '7j': (T1 - 7 * 86400, T1), '30j': (T1 - 30 * 86400, T1), '90j': (win['t_start'], T1), 'ballon': BO}
status = {}
p = ROOT / 'state/firstfund.jsonl'
pop = defaultdict(list)
for r in csv.DictReader(open(ROOT / 'state/recipients_final.csv')):
    if 'externe' in r['classes'] and r['category'] in ('EOA', 'EOA_7702'):
        pop[(r['tier'], r['chain'], r['first_source'])].append(int(r['first_ts']))


def tumbling_max(ts, w):
    """Largest count in a fixed grid of windows, and how many windows hold 2 or more, 5 or more, 10 or more."""
    c = Counter(t // w for t in ts)
    v = list(c.values())
    return dict(max=max(v) if v else 0, ge2=sum(x >= 2 for x in v), ge5=sum(x >= 5 for x in v), ge10=sum(x >= 10 for x in v), windows=len(v))


def shuffled(ts, rng):
    """Same count per hour of week: each time keeps its week-hour and takes a random second in it, and a random week in the period."""
    out = []
    lo, hi = min(ts), max(ts)
    weeks = max(1, (hi - lo) // (7 * 86400) + 1)
    for t in ts:
        hw = (t % (7 * 86400)) // 3600
        for _ in range(8):
            base = lo - lo % (7 * 86400) + rng.randrange(weeks + 1) * 7 * 86400
            x = base + hw * 3600 + rng.randrange(3600)
            if lo <= x <= hi:
                break
        else:
            x = t
        out.append(x)
    return out


res = {}
rng = random.Random(20261102)
for key, ts in pop.items():
    name = '|'.join(key)
    res[name] = {}
    for pname, (a, b) in PERIODS.items():
        sub = [t for t in ts if a <= t <= b]
        if len(sub) < 2:
            res[name][pname] = dict(n=len(sub))
            continue
        row = dict(n=len(sub))
        for w in WINDOWS:
            obs = tumbling_max(sub, w)
            nulls = [tumbling_max(shuffled(sub, rng), w)['max'] for _ in range(PERMS if len(sub) < 40000 else 40)]
            nulls.sort()
            row[str(w)] = dict(obs, null_median=nulls[len(nulls) // 2], null_p975=nulls[int(.975 * (len(nulls) - 1))], perms=len(nulls), p_max=round((1 + sum(x >= obs['max'] for x in nulls)) / (1 + len(nulls)), 4))
        res[name][pname] = row
    print(name, {k: v.get('n') for k, v in res[name].items()}, 'rss', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 2**20, flush=True)
(ROOT / 'state/clusters.json').write_text(json.dumps(res, indent=0))
