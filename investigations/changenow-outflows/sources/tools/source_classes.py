"""Offline. Per source: rows, amounts and recipients by class. Writes state/source_classes.csv."""
import csv, gzip, json
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = Counter(); usd = defaultdict(float); rcpt = defaultdict(set)
with gzip.open(ROOT / 'data/outgoing_transactions.csv.gz', 'rt', newline='') as f:
    for r in csv.DictReader(f):
        k = (r['chain'], r['source'], r['source_tier'], r['period'], r['kind'], r['class'])
        rows[k] += 1
        if r['usd']:
            usd[k] += float(r['usd'])
        rcpt[k].add(r['recipient'])
with (ROOT / 'state/source_classes.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow('chain,source,tier,period,kind,class,rows,recipients,usd'.split(','))
    for k in sorted(rows):
        w.writerow(list(k) + [rows[k], len(rcpt[k]), round(usd[k], 2)])
