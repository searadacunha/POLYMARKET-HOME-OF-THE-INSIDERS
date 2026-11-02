"""Offline. Adds to state/recipients.csv the category of each recipient, from Blockscout tags, contract code and deposit-like behaviour. Order of the rules is the order of the code: a service label beats a code reading, a ChangeNOW tag beats both. Writes state/recipients_final.csv, data/unique_recipients.csv."""
import csv, json, re, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
tags = {}
for line in open(ROOT / 'state/recipient_tags.jsonl'):
    d = json.loads(line)
    tags[(str(d['chain']), d['address'])] = d['tags']
code = {}
p = ROOT / 'state/recipient_code.csv'
if p.exists():
    for c, a, k in csv.reader(open(p)):
        code[(c, a)] = k
SERVICE = re.compile(r'exchange|hot wallet|deposit|dep:|\bdep\b|bridge|dex\b|router|pool|token contract|stablecoin|swap|cex|relay|solver|market maker|custod|payment|treasury|vault|staking|aggregator|wrapped|multisig|gas station', re.I)


def category(chain, a, classes):
    t = tags.get((chain, a)) or []
    names = [x['name'] for x in t]
    if any('changenow' in n.lower() or 'change now' in n.lower() for n in names):
        return 'CHANGENOW_ETIQUETE', names
    if any(SERVICE.search(n) for n in names):
        return 'SERVICE_ETIQUETE', names
    if classes == 'depot_service_probable':
        return 'DEPOT_SERVICE_PROBABLE', names
    return code.get((chain, a), 'CODE_NON_LU'), names


cnt = Counter()
FIELDS = None
with (ROOT / 'state/recipients_final.csv').open('w', newline='') as fo, (ROOT / 'data/unique_recipients.csv').open('w', newline='') as fp:
    wa = wb = None
    for r in csv.DictReader(open(ROOT / 'state/recipients.csv')):
        cat, names = category(r['chain'], r['recipient'], r['classes'])
        r['category'] = cat
        r['tags'] = '|'.join(names)[:200]
        r['code'] = code.get((r['chain'], r['recipient']), '')
        cnt[(r['tier'], r['chain'], cat)] += 1
        if wa is None:
            wa = csv.DictWriter(fo, fieldnames=list(r))
            wa.writeheader()
            wb = csv.DictWriter(fp, fieldnames=list(r))
            wb.writeheader()
        wa.writerow(r)
        wb.writerow(r)
for k, v in sorted(cnt.items()):
    print(k, v)
(ROOT / 'state/category_counts.json').write_text(json.dumps({'|'.join(k): v for k, v in cnt.items()}, indent=0))
