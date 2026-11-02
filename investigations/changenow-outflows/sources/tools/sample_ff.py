"""Stratified random sample of external recipients, seed 20261102, and their first funding status. Strata: tier, chain, source of first payout, inside or outside the Ballon d'Or window. Resumes. Writes state/firstfund.jsonl."""
import csv, json, random, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import firstfund, net
ROOT = net.ROOT
BO = (1790208000, 1792713599)  # 2026-09-24 00:00:00 to 2026-10-23 23:59:59 UTC, PLAN.md
N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
frame = defaultdict(list)
for r in csv.DictReader(open(ROOT / 'state/recipients_final.csv')):
    if r['category'] in ('EOA', 'EOA_7702') and 'externe' in r['classes']:
        t = int(r['first_ts'])
        frame[(r['tier'], r['chain'], r['first_source'], 'ballon' if BO[0] <= t <= BO[1] else 'hors')].append(r)
rng = random.Random(20261102)
sample = []
sizes = {}
for k in sorted(frame):
    rows = sorted(frame[k], key=lambda r: r['recipient'])
    pick = rng.sample(rows, min(N, len(rows)))
    sizes['|'.join(k)] = dict(population=len(rows), sampled=len(pick))
    sample += [(k, r) for r in pick]
(ROOT / 'state/firstfund_frame.json').write_text(json.dumps(sizes, indent=0))
print(sizes, flush=True)
out = ROOT / 'state/firstfund.jsonl'
done = {(d['chain'], d['address'], d['tier']) for d in map(json.loads, out.open())} if out.exists() else set()
rng2 = random.Random(1)
rng2.shuffle(sample)  # read strata evenly: a stop leaves a balanced sample
with out.open('a') as f:
    for i, (k, r) in enumerate(sample):
        key = (int(r['chain']), r['recipient'], r['tier'])
        if key in done:
            continue
        d = firstfund.classify(int(r['chain']), r['recipient'], int(r['first_ts']), r['first_tx'])
        d.update(tier=r['tier'], stratum='|'.join(k))
        f.write(json.dumps(d) + '\n')
        f.flush()
        if i % 50 == 0:
            print(i, len(sample), d['status'], flush=True)
print('done')
