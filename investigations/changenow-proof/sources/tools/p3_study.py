"""Study universe: every address the prior work ties to the 11 accounts, with its relation. Read only from flow-trace and investigation outputs."""
import csv, json
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
FT = Path.home() / 'Projects/PolySentinel-flow-trace'
INV = Path.home() / 'Projects/PolySentinel-investigation'
SLUGS = 'thin vidente cookedrice wen 0x86544e4dfde brace227 walletwallet8424 zoomman17 kraben006 ouldlm3alem 0xdd97e6'.split()
rel = defaultdict(set)  # address -> {(case, relation)}
for s in SLUGS:
    d = json.load(open(INV / f'cases/{s}.json'))
    rel[d['wallet']['address'].lower()].add((s, 'wallet'))
    for k in d.get('owner_nonces') or {}:
        rel[k.lower()].add((s, 'owner_key'))
    for x in d.get('recipients') or []:
        rel[x['address'].lower() if x['address'].startswith('0x') else x['address']].add((s, 'withdrawal_recipient'))
for file, relation in (('funding_paths.csv', 'funding_path'), ('cashout_paths.csv', 'cashout_path')):
    for r in csv.DictReader(open(FT / 'data' / file)):
        for col in ('source', 'target'):
            a = (r[col] or '').strip()
            if a and not r.get('service') and not (r.get(col + '_class') or '').upper().startswith('SERVICE'):
                rel[a.lower() if a.startswith('0x') else a].add((r['case'], relation))
for r in csv.DictReader(open(FT / 'data/walk_edges.csv')):
    for col in ('src', 'dst'):
        a = (r[col] or '').strip()
        if a:
            rel[a.lower() if a.startswith('0x') else a].add((r['case'], 'walk_' + r['direction']))
rows = [dict(address=a, cases=';'.join(sorted({c for c, _ in v})), relations=';'.join(sorted({f'{c}:{t}' for c, t in v}))) for a, v in sorted(rel.items())]
with (ROOT / 'state/study_addresses.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['address', 'cases', 'relations'])
    w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(t for v in rel.values() for _, t in v))
print({s: sorted(a for a, v in rel.items() if (s, 'owner_key') in v) for s in SLUGS})
