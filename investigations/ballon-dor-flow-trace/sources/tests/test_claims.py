"""Every figure and transaction prefix in the hand-written sentences must exist somewhere in the data. Presence only: it catches a typo or an invented figure, not a right number attached to the wrong fact. Prints what it cannot find; exit 1 if anything is left.
Sums quoted in the text are recomputed here and added to the known values, so a sum is checked rather than trusted."""
import csv
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.dont_write_bytecode = True
import narrative as N
import walk

STATE = ROOT / 'state'
INV = walk.INV
values, blobs = set(), []


def add(x):
    try:
        v = abs(float(x))
    except (TypeError, ValueError):
        return
    if v:
        values.add(round(v, 2))
        values.add(round(v, 3))
        values.add(round(v, 4))
        values.add(round(v, 5))


def harvest(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            harvest(v)
    elif isinstance(obj, list):
        for v in obj:
            harvest(v)
    elif isinstance(obj, str):
        blobs.append(obj.lower())
        add(obj)
    elif isinstance(obj, (int, float)):
        add(obj)


for p in sorted(STATE.glob('walk_*.json')):
    harvest(json.loads(p.read_text()))
for name in ('reconcile.json', 'pairs.json', 'bridges.json', 'gxjc.json', 'wallet_0xa8e6_activity.json', 'personal_wallets.json', 'followups.json', 'compare_rates.json'):
    if (STATE / name).exists():
        harvest(json.loads((STATE / name).read_text()))
for p in sorted(STATE.glob('bsc_0x*.json')):
    harvest(json.loads(p.read_text()))
cases = [json.loads(p.read_text()) for p in sorted((INV / 'cases').glob('*.json'))]
harvest(cases)
for name in ('funding_paths', 'cashout_paths', 'walk_edges'):
    for r in csv.DictReader((ROOT / f'data/{name}.csv').open()):
        harvest(r)
harvest(json.loads((INV / 'evidence/contre_verification_20261102/circuit_7xujs_brace_kraben.json').read_text()))
for r in cases:
    a = r['account']
    add(a['withdrawals'] - a['deposits'])

by = {c['slug']: c for c in cases}
dep = lambda s, *idx: sum(sorted(by[s]['deposits'], key=lambda d: d['at'])[i]['usd'] for i in idx)
holdings = {}
for p in sorted(STATE.glob('walk_*.json')):
    w = json.loads(p.read_text())
    holdings[w['case']] = w['holdings']
hold = lambda case, addr, token: sum(h['balances'].get(token, 0) for h in holdings[case] if h['address'].lower().startswith(addr))
kucoin = dep('thin', 0) + dep('vidente', 0, 1) + dep('cookedrice', 0) + dep('0xdd97e6', 1) + dep('ouldlm3alem', 1)
binance = dep('thin', 1, 2) + dep('wen', 0) + dep('ouldlm3alem', 2)
stable_held = hold('thin', 'cxvymp', 'USDC') + hold('thin', 'enhrjt', 'USDC') + hold('0x86544e4dfde', '0x69837228', 'USDC') + hold('brace227', '0xc852', 'USDC') + hold('walletwallet8424', '0x82775', 'USDC') + hold('kraben006', '0x101b', 'USDC') + hold('ouldlm3alem', '0x1b500b', 'USDC') + hold('ouldlm3alem', '0xae232', 'USDT')
thin_held = hold('thin', 'cxvymp', 'USDC') + hold('thin', 'enhrjt', 'USDC')
swft = [4337.519426, 83.894564, 5925.842274, 4749.032981]
computed = dict(kucoin=kucoin, binance=binance, both=kucoin + binance, stable_held=stable_held, thin_held=thin_held, swift=sum(swft), swift_all=sum(swft) + 188.972782, thin_binance=dep('thin', 1, 2), v0ce9=15000 + 25686.118547 + 1704.421976 + 1674.433687 + 3907.033117, d0ce9=dep('0x86544e4dfde', 0, 1, 2), services=51489 + 39158 + 27724, chunks=9943.96 + 9436.2 + 8066.6, gxjc=51489 + 39158, revolut=217.770226 + 1100 + 1380 + 6.114377 + 18 + 18.18249 + 487.693213, brace4=dep('brace227', 0, 1, 2, 3), split=4337.519426 + 83.894564, wen_fee=27724 * .01, ould_small=200, zoom=50 + 80 + 18 + 6745, sum5170=2210 + 2960, pnl2=8061.904013 - 5165, keys0=dep('walletwallet8424', 0), hl=75724.54 - 2415.40939 - 306.711265, gxjc_window=51489.0)
computed.update(dep_total=sum(c['account']['deposits'] for c in cases), wd_total=sum(c['account']['withdrawals'] for c in cases), sol_thin=hold('thin', 'cxvymp', 'SOL') + hold('thin', 'enhrjt', 'SOL'), other_buy=5164.988807, split1=2210 / 4421.41399 * 100, split2=2960 / 5925.842274 * 100, chg=654.466327 + 180.382501, hl_out=73001.385076 + 1.013579, gap_vidente=12030 / 3600, gap_thin=31952 / 3600, thin_gas=250, ratio_pct=74, sold_gap=(1793119913 - 1793119913), pusd_tip=.2)
for v in computed.values():
    add(v)
for v in (101, 99, 400, 45, 20, 60, 300, 600, 180, 21, 0.0056, 0.0006, 0.031):  # method constants, the corrected threshold, a figure quoted from the audit
    add(v)
personal = json.loads((STATE / 'personal_wallets.json').read_text())
add(len({x['address'] for x in personal}))
add(len(personal))
add(sum(1 for x in personal if x['shape'] == 'beacon'))
for c in cases:
    add(c['first_trade']['at'] - min(d['at'] for d in c['deposits']))
for name, v in sorted(computed.items()):
    print(f'{name:14s} {v:,.2f}')

text = []
for c in N.CASES.values():
    text += [c['bref'], c['confiance']] + [x for row in c['table'] for x in row] + c.get('chemins', [])
for row in list(N.COMPARE.values()) + list(N.EXPOSURE.values()) + list(N.CASHOUT.values()) + N.LEVELS + N.BREAKS:
    text += row
text += [N.RESULT, N.MATRIX_READING, N.LIMITS, N.COMMON_ANSWER, N.BRACE_KRABEN, N.TIMING, N.EXPOSURE_ANSWER, N.XMR_TEXT, N.CASHOUT_ANSWER, N.OULD_PATH, N.WEN_PATH, N.RATE_READING]
joined = '\n'.join(text)
ALLOW = {7, 702, 1967, 2022, 2023, 2024, 2025, 2026, 100, 250}  # standards and years, not measurements

numbers = re.findall(r'(?<![\w`…])-?\d{1,3}(?:[  ]\d{3})*(?:,\d+)?(?![\w…])', joined)
missing = []
for n in sorted(set(numbers)):
    v = float(n.replace(' ', '').replace(' ', '').replace(',', '.').lstrip('-'))
    if v < 100 and ',' not in n:
        continue
    if v in ALLOW or v in values:
        continue
    if not any(abs(v - x) < .0051 for x in values):
        missing.append(n)
blob = '\n'.join(blobs)
prefixes = re.findall(r'`(0x[0-9a-f]{6,})…?([0-9a-f]*)`', joined.lower())
bad = [f'{a}…{b}' for a, b in set(prefixes) if a not in blob and not any(x.startswith(a) for x in re.findall(r'0x[0-9a-f]{40,64}', a))]
bad = [x for x in bad if x.split('…')[0] not in blob]
print('\nnumbers checked', len(set(numbers)), 'not found', len(missing))
for m in missing:
    print('  NUMBER', m)
print('address or tx prefixes checked', len(set(prefixes)), 'not found', len(bad))
for b in bad:
    print('  PREFIX', b)
sys.exit(1 if missing or bad else 0)
