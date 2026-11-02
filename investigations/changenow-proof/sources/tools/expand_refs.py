"""Reports keep short forms for legibility: truncated hashes become full inline, truncated addresses get a full table at the end of each report. An unresolved or ambiguous reference stops the run."""
import csv, gzip, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
known = set()
for f in (ROOT / 'data').glob('*.csv'):
    known |= set(re.findall(r'0x[0-9a-f]{40,64}', f.read_text().lower()))
for f in ('state/study_addresses.csv', 'state/universe_raw.csv', 'state/figures.json', 'state/hop2.json', 'state/p9.json', 'state/p10.json', 'state/p14.json', 'state/p15.json'):
    known |= set(re.findall(r'0x[0-9a-f]{40,64}', (ROOT / f).read_text().lower()))
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as g:
    for line in g:
        known |= set(re.findall(r'0x[0-9a-f]{40,64}', line.lower()))
known |= {p.stem for p in (ROOT / 'evidence/onchain').glob('*.json')}
ADDR = {a for a in known if len(a) == 42}
HASH = {a for a in known if len(a) == 66}
SHORT = re.compile(r'0x[0-9a-fA-F]{6,20}…[0-9a-fA-F]{0,8}')
START, END = '<!-- adresses -->', '<!-- fin adresses -->'
NAMES = {'0xdd3d72c53ff982ff59853da71158bf1538b3ceee': 'ChangeNOW: Hot Wallet 3', '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b': 'ChangeNOW Dep: 0x3f3...07B', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1': 'ChangeNOW: Hot Wallet 4, ChangeNOW 16', '0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23': 'Aucune, relais', '0xa03400e098f4421b34a3a44a1b4e571419517687': 'HTX: Hot Wallet, HTX 52', '0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055': 'Binance: Hot Wallet 34', '0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a': 'ChangeNOW 22', '0x4778480c6c46521c41f7e4f2318f884b157cb1c9': 'ChangeNow (0x4778)', '0x077d360f11d220e4d5d831430c81c26c9be7c4a4': 'changenow (dawsbot), ChangeNOW: hot wallet'}
bad = []
for r in 'CHANGENOW_PROOF_FINAL ATTRIBUTION_EVIDENCE PAYIN_TRANSACTIONS PAYOUT_MATCHES XMR_VISIBILITY FALSE_POSITIVES'.split():
    path = ROOT / f'reports/{r}.md'
    t = path.read_text()
    if START in t:
        t = t[:t.index(START)].rstrip() + '\n'
    seen = {}

    def fix(m):
        s = m.group(0)
        head, _, tail = s.lower().partition('…')
        cand_h = [h for h in HASH if h.startswith(head) and h.endswith(tail)]
        cand_a = [a for a in ADDR if a.startswith(head) and a.endswith(tail)]
        if len(cand_h) == 1 and not cand_a:
            return cand_h[0]
        if len(cand_a) == 1 and not cand_h:
            seen[cand_a[0]] = s
            return s
        bad.append((r, s, len(cand_a), len(cand_h)))
        return s
    t = SHORT.sub(fix, t)
    if seen:
        t += f'\n{START}\n## Adresses citées en forme courte\n\n| Adresse complète | Étiquette publique lue |\n|---|---|\n' + ''.join(f"| `{a}` | {NAMES.get(a, 'Voir `data/changenow_candidates.csv` ou aucune')} |\n" for a in sorted(seen)) + f'{END}\n'
    path.write_text(t)
    print(r, 'short addresses', len(seen))
if bad:
    print('UNRESOLVED', bad)
    sys.exit(1)
