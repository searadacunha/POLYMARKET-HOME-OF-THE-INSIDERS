"""Every full hash and address cited in reports must exist in the evidence, the key sums must recompute, and the deliverables must exist. Exits non-zero on any failure."""
import csv, gzip, json, re, sys, xml.dom.minidom
from decimal import Decimal
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
REPORTS = 'CHANGENOW_PROOF_FINAL ATTRIBUTION_EVIDENCE PAYIN_TRANSACTIONS PAYOUT_MATCHES XMR_VISIBILITY FALSE_POSITIVES'.split()
fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)


known = set()
for f in (ROOT / 'data').glob('*.csv'):
    known |= set(re.findall(r'0x[0-9a-f]{40,64}', f.read_text().lower()))
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as g:
    for line in g:
        known |= set(re.findall(r'0x[0-9a-f]{40,64}', line.lower()))
for name in ('evidence/labels/changenow_rows.json', 'state/study_addresses.csv', 'state/universe_raw.csv', 'state/p9.json', 'state/p10.json', 'state/p13.json', 'state/p14.json', 'state/p15.json', 'evidence/repos/thirdparty/amit-dev01__Chain-Sleuth-Backend__registry.py.txt'):
    known |= set(re.findall(r'0x[0-9a-f]{40,64}', (ROOT / name).read_text(errors='replace').lower()))
known |= {p.stem for p in (ROOT / 'evidence/onchain').glob('*.json')}
SHA = re.compile(r'(?<![0-9a-fx])[0-9a-f]{64}(?![0-9a-f])')
for r in REPORTS:
    path = ROOT / f'reports/{r}.md'
    check(path.exists(), f'missing {r}')
    t = path.read_text()
    check('—' not in t, f'{r}: em dash')
    for x in set(re.findall(r'0x[0-9a-fA-F]{64}(?![0-9a-fA-F])|0x[0-9a-fA-F]{40}(?![0-9a-fA-F])', t)):
        check(x.lower() in known, f'{r}: {x} not in evidence')
for name in 'data/changenow_candidates.csv data/verified_transfers.csv data/unresolved_paths.csv data/attribution_links.csv graphs/changenow_network.graphml evidence/api/MANIFEST.csv evidence/SHA256SUMS'.split():
    check((ROOT / name).exists() and (ROOT / name).stat().st_size > 0, f'missing {name}')
rows = list(csv.DictReader(open(ROOT / 'data/verified_transfers.csv')))
check(all(r['node_ok'] == 'True' for r in rows), 'a transfer failed its node proof')
for r in rows:
    check((ROOT / r['node_proof_file']).exists(), 'missing proof ' + r['tx'])
    check(Decimal(r['amount']) == Decimal(int(r['raw'])) / (Decimal(10) ** int(r['decimals'])), 'inexact amount ' + r['tx'])
HOT3, HW4, KEY, FUND = '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65', '0x3eaef6d5e91ecf7b7623eb19978e145ebd417013'
s = lambda a, b: sum(Decimal(r['amount']) for r in rows if r['src'] == a and r['dst'] == b)
check(s(HOT3, KEY) == Decimal('834.848793'), 'kraben sum')
check(s(HOT3, FUND) == Decimal('510.494311'), 'funder USDT sum')
check(s(HW4, FUND) == Decimal('0.01000021'), 'funder ETH sum')
# key USDC balance reconciles with the balance flow-trace read on chain
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
seen, bal = set(), 0
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as g:
    for line in g:
        r = json.loads(line)
        if r['contract'] == USDC and KEY in (r['src'], r['dst']) and r['chain'] == 1:
            k = (r['tx'], r['src'], r['dst'], r['raw'])
            if k not in seen:
                seen.add(k)
                bal += int(r['raw']) * (1 if r['dst'] == KEY else -1)
check(bal == 15154826661, f'key USDC balance {bal}')
# fee arithmetic of the 4 October send, from the node
proof = json.load(open(ROOT / 'evidence/onchain/0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71.json'))
spent = int(proof['tx']['value'], 16) + int(proof['receipt']['gasUsed'], 16) * int(proof['receipt']['effectiveGasPrice'], 16)
check(4056876899262451 - spent == 1559054917606451, 'send arithmetic')
check(spent - 2007933228056898 == 489888753599102, 'minimum from brace')
check(round((spent - 2007933228056898) / int(proof['tx']['value'], 16) * 100, 1) == 19.8, 'share low')
check(round(2048943671205553 / int(proof['tx']['value'], 16) * 100, 1) == 82.8, 'share high')
p16 = json.load(open(ROOT / 'state/p16.json'))
check((p16['usable'], p16['with_rows'], p16['comparators_with_hit']) == (54, 14, 0), 'base rate counts')
check((round(p16['fisher_11'], 2), round(p16['fisher_rows'], 2)) == (0.17, 0.3), 'base rate p')
# levels: a level of 1 or more needs a labelled side; every field the mission lists is filled
LABELLED = {HOT3, HW4, '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', '0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a'}
for r in rows:
    check(int(r['proof_level']) == 0 or {r['src'], r['dst']} & LABELLED, 'level without a label ' + r['tx'])
    for col in ('service_label', 'label_source', 'attribution_proof', 'relation_to_account', 'alternatives', 'visibility_limit', 'src', 'dst', 'tx', 'utc', 'raw', 'chain_id'):
        check(r[col] != '', f'empty {col} on {r["tx"]}')
level2 = [r for r in rows if r['proof_level'] == '2']
check(len(level2) == 18, f'level 2 rows {len(level2)}')
for r in csv.DictReader(open(ROOT / 'data/changenow_candidates.csv')):
    check(r['evidence_file'] and r['evidence_sha256'], 'candidate without evidence ' + r['address'])
for r in csv.DictReader(open(ROOT / 'data/unresolved_paths.csv')):
    check(r['proof_level'] != '' and r['source'] and r['amount'] != 'non calcule', 'unresolved incomplete ' + r['path_id'])
fig = json.load(open(ROOT / 'state/figures.json'))
check(fig['sib']['fingerprint'] == 12 and fig['sib']['two_tx'] == 13 and fig['fixedfloat_dep_fingerprint'] == 0, 'fingerprint counts')
check(round(fig['controls']['upper95_one_sided_12'], 2) == 0.22 and fig['controls']['with_ff_dep'] == 12, 'control bound')
check(fig['calldata']['non_standard'] == [] and fig['calldata']['proofs'] == 49, 'calldata')
check(fig['a2768']['senders'] == 22 and fig['a2768']['recipients'] == 173, 'a2768')
check(fig['htx_deposit']['stable_out'] == 44, 'htx')
# short references: hashes must be expanded, addresses must be in the report's table
for r in REPORTS:
    t = (ROOT / f'reports/{r}.md').read_text()
    for s_ in set(re.findall(r'0x[0-9a-fA-F]{6,20}…[0-9a-fA-F]{0,8}', t)):
        head, _, tail = s_.lower().partition('…')
        check(any(a.lower().startswith(head) and a.lower().endswith(tail) for a in re.findall(r'`(0x[0-9a-fA-F]{40})`', t)), f'{r}: {s_} has no full form')
g = xml.dom.minidom.parse(str(ROOT / 'graphs/changenow_network.graphml'))
ids = {n.getAttribute('id') for n in g.getElementsByTagName('node')}
check(all(e.getAttribute('source') in ids and e.getAttribute('target') in ids for e in g.getElementsByTagName('edge')), 'dangling edge')
check(KEY in ids and HOT3 in ids, 'graph nodes')
print('FAIL' if fails else 'OK', len(fails))
for f in fails:
    print(' ', f)
sys.exit(1 if fails else 0)
