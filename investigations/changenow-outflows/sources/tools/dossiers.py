"""Offline: every address of the 11 dossiers worth comparing: wallets, owners, personal-sized neighbours, the unnamed wallet and its owner. Services and contracts are left out on purpose: sharing one links nobody. Writes state/dossier_addresses.csv."""
import csv, glob, json
from pathlib import Path
FT = Path.home() / 'Projects/PolySentinel-flow-trace'
INV = Path.home() / 'Projects/PolySentinel-investigation'
rows = {}


def add(a, case, role):
    if isinstance(a, str) and a.startswith('0x') and len(a) == 42 and int(a, 16) != 0:
        rows.setdefault(a.lower(), {}).setdefault(case, set()).add(role)


for p in glob.glob(str(INV / 'cases/*.json')):
    d = json.load(open(p))
    add(d['address'], d['slug'], 'wallet')
    for r in d.get('recipients') or []:
        add(r['address'], d['slug'], 'destinataire')
for p in FT.glob('state/walk_*.json'):
    w = json.load(open(p))
    for a in w['own']:
        add(a, w['case'], 'propre')
    for e in w['edges']:
        for a, k in ((e['src'], 'funding'), (e['dst'], 'cashout')):
            if e.get('other_cls') == 'PERSONAL_SIZED' and e['direction'] == k:
                add(a, w['case'], 'voisin_personnel')
for f in ('funding_paths', 'cashout_paths'):
    for r in csv.DictReader(open(FT / f'data/{f}.csv')):
        for a, c in ((r['source'], r['source_class']), (r['target'], r['target_class'])):
            if c == 'PERSONAL_SIZED':
                add(a, r['case'], 'chemin_personnel')
for w in json.load(open(FT / 'state/personal_wallets.json')):
    for c in w['cases']:
        add(w['address'], c, 'voisin_personnel')
add('0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d', 'brace227', 'proprietaire_wallet_non_nomme')
add('0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5', 'brace227', 'wallet_non_nomme')
with open(Path(__file__).parent.parent / 'state/dossier_addresses.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['address', 'cases', 'roles'])
    for a, v in sorted(rows.items()):
        w.writerow([a, ';'.join(sorted(v)), ';'.join(sorted({x for s in v.values() for x in s}))])
print(len(rows), 'addresses;', {c: sum(c in v for v in rows.values()) for c in sorted({c for v in rows.values() for c in v})})
