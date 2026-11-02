"""Offline: one row per (address, chain, label, source) with the lineage of the source, so that lists copying one tag never count as two. Writes data/attribution_sources.csv."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
P = Path.home() / 'Projects/PolySentinel-ChangeNOW-proof'
READ = '2026-11-02'
rows = {}


def add(a, chain, label, source, lineage, date):
    a = a.lower() if a.startswith('0x') else a
    rows[(a, str(chain), label, source)] = dict(address=a, chain=chain, label=label, source=source, lineage=lineage, source_date=date, read_at=READ)


for r in csv.DictReader(open(P / 'state/universe_raw.csv')):
    k, s = r['source_kind'], r['source']
    if k == 'blockscout':  # the tag search misses some tags (Hot Wallet 3 and 4 among them): keep what the proof session read address by address
        add(r['address'], r['chain_id'], r['name'], s[:60], 'oli_hildobby' if 'OLI' in s or 'hildobby' in s else 'blockscout_name', READ)
        continue
    lineage = {'dawsbot': 'etherscan_tag', 'brianleect': 'etherscan_tag', 'etherscan_page': 'etherscan_tag', 'arkham_copy': 'arkham_copie', 'amlbot_copy': 'amlbot_copie'}.get(k)
    if k == 'github_list':
        lineage = 'osint_faible' if 'Marzel7' in s else 'etherscan_tag'
    if k == 'services_json':
        lineage = 'osint_faible' if 'candidate' in r['name'] else 'etherscan_tag'
    date = {'brianleect': '2023 (dump)', 'etherscan_page': READ}.get(k, 'non datée')
    add(r['address'], r['chain_id'], r['name'], s, lineage, date)
for line in open(ROOT / 'state/bs_tags.jsonl'):
    v = json.loads(line)
    n = v['name'] or ''
    if 'change' in n.lower() and 'now' in n.lower():
        meta = v.get('meta') or ''
        lineage = 'oli_hildobby' if 'OLI' in meta or 'hildobby' in meta else 'blockscout_name'
        for a in v['addresses']:
            add(a, v['chain'], n, f"blockscout_metadata:{v['slug']}:{v['type']}", lineage, READ)
out = sorted(rows.values(), key=lambda r: (r['address'], str(r['chain']), r['label']))
with (ROOT / 'data/attribution_sources.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
print(len(out), 'rows', len({r['address'] for r in out}), 'addresses')
