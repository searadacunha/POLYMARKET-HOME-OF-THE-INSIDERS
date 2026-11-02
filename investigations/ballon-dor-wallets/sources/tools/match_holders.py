"""Resolve press labels by comparing the shares printed in the public screenshot with net shares rebuilt from the market tape.
Known aliases are the positive control. A match is a candidate: it never establishes who holds the wallet."""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
import tape

CAT = Path.home() / 'Projects/PolySentinel/studies/ballon_2026_20261030/data/catalog_refreshed.json'
T_POST = 1792768669  # 23 Oct 15:17:49 UTC, the post carrying the screenshot
PRINTED = {'Thin-Disclaimer-Life': 76083, 'VidenteRibeira': 51346, 'cookedrice': 32002, 'WenZhuanBuPei': 27691, '0x86544e4dfde': 21175, 'brace227': 17107, 'Cypyo': 15061, 'BriardxO': 14309, 'Cypya': 14170, 'pup1': 13946, 'mr.ozi': 12885, 'walletwallet8424': 11777, 'Zoomman17': 11158, 'enginesinmyfactory': 9462, 'kraben006': 9280}
ev = next(i['event'] for i in json.loads(CAT.read_text())['events'] if str(i['event']['id']) == '1105364')
m = ev['markets'][0]
print(m['question'], m['conditionId'], m.get('outcomes'), m.get('clobTokenIds'))
rows = tape.tape(m['conditionId'], 1790000000, 1793600000)
print('rows', len(rows), rows[0].keys() if rows else None, json.dumps({k: rows[0][k] for k in rows[0] if k not in ('icon', 'profileImage', 'profileImageOptimized', 'bio')})[:600])
outcomes = sorted({(r.get('outcome'), r.get('outcomeIndex')) for r in rows}, key=str)
print('outcomes', outcomes)
net_t = defaultdict(list)
names = defaultdict(set)
for r in sorted(rows, key=lambda r: r['timestamp']):
    w = r['proxyWallet'].lower()
    for k in ('name', 'pseudonym'):
        if r.get(k):
            names[w].add(r[k])
    if r.get('outcome') == 'Kylian Mbappé' or r.get('outcomeIndex') == 0:
        net_t[w].append((r['timestamp'], r['size'] if r['side'] == 'BUY' else -r['size']))
snap = {w: sum(s for t, s in v if t < T_POST) for w, v in net_t.items()}
out = dict(market=m['conditionId'], rows=len(rows), snapshot=T_POST, wallets=len(snap), labels={})
for label, shares in PRINTED.items():
    lab = label.lower()
    by_name = [w for w, n in names.items() if any(lab == x.lower() for x in n)]
    near = sorted(snap, key=lambda w: abs(snap[w] - shares))[:3]
    out['labels'][label] = dict(printed=shares, by_name=by_name, nearest=[dict(wallet=w, net=round(snap[w], 2), gap=round(snap[w] - shares, 2), names=sorted(names[w])) for w in near], within_1pct=sum(1 for w in snap if abs(snap[w] - shares) <= .01 * shares))
Path('evidence/holder_match_1105364.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
for k, v in out['labels'].items():
    print(k, v['printed'], 'name:', v['by_name'], 'near:', [(n['wallet'][:12], n['net'], n['names'][:2]) for n in v['nearest'][:2]], 'in1%:', v['within_1pct'])
print('calls', net.Stats.calls, 'cached', net.Stats.cached)
