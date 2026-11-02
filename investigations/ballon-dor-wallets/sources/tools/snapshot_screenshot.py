"""When was the press screenshot taken, and does the rebuilt holder list reproduce it row by row? Offline on the cached tape, then owners read on-chain."""
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path.home() / 'Projects/PolySentinel'))
import net
import tape
from signal_engine.fund_flow import wallets
from signal_engine.fund_flow.client import Client

CID = '0xa3cf5e6b27c672d56f3c883139ae87a2dcef9d16a373decab50621cb793b3af4'
PRINTED = [('Thin-Disclaimer-Life', 76083), ('VidenteRibeira', 51346), ('cookedrice', 32002), ('WenZhuanBuPei', 27691), ('0x86544e4dfde', 21175), ('brace227', 17107), ('Cypyo', 15061), ('BriardxO', 14309), ('Cypya', 14170), ('pup1', 13946), ('mr.ozi', 12885), ('walletwallet8424', 11777), ('Zoomman17', 11158), ('enginesinmyfactory', 9462), ('kraben006', 9280)]
rows = sorted(tape.tape(CID, 1790000000, 1793600000), key=lambda r: r['timestamp'])
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
names = defaultdict(set)
for r in rows:
    for k in ('name', 'pseudonym'):
        if r.get(k):
            names[r['proxyWallet'].lower()].add(r[k])
# Rebuild the Mbappé position at every trade; keep the instants where the top 15 agree with the screenshot best.
pos = defaultdict(float)
best = []
stamps = sorted({r['timestamp'] for r in rows})
i = 0
for t in stamps:
    while i < len(rows) and rows[i]['timestamp'] <= t:
        r = rows[i]
        if r['outcomeIndex'] == 0:
            pos[r['proxyWallet'].lower()] += r['size'] if r['side'] == 'BUY' else -r['size']
        i += 1
    if t < 1792500000:
        continue
    top = sorted(pos.items(), key=lambda kv: -kv[1])[:15]
    score = sum(1 for (w, s), (_, p) in zip(top, PRINTED) if abs(s - p) <= .5)
    best.append((score, t))
top_score = max(s for s, _ in best)
window = [t for s, t in best if s == top_score]
print('max rows matched', top_score, 'of 15, from', UTC(window[0]), 'to', UTC(window[-1]), 'n instants', len(window))
pos = defaultdict(float)
for r in rows:
    if r['timestamp'] > window[-1]:
        break
    if r['outcomeIndex'] == 0:
        pos[r['proxyWallet'].lower()] += r['size'] if r['side'] == 'BUY' else -r['size']
top = sorted(pos.items(), key=lambda kv: -kv[1])[:17]
table = []
for k, (w, s) in enumerate(top):
    p = PRINTED[k] if k < 15 else (None, None)
    table.append(dict(rank=k + 1, printed_label=p[0], printed_shares=p[1], wallet=w, net_shares=round(s, 2), gap=None if p[1] is None else round(s - p[1], 2), names_now=sorted(names[w])))
    print(k + 1, p, w, round(s, 2), sorted(names[w]))
# Accidental match: how many other wallets sit within half a share of a printed value, given the local density of positions.
acc = {}
for label, p in PRINTED:
    band = [s for s in pos.values() if abs(s - p) <= .1 * p]
    acc[label] = dict(wallets_within_10pct=len(band), expected_accidental_within_half_share=round(len(band) * 1.0 / (.2 * p), 5))
client = Client(80, 5, ledger=Path('state/classify_ledger.jsonl'))
owners = {}
for row in table[:17]:
    if row['printed_label'] in ('0x86544e4dfde', 'Zoomman17', 'kraben006', 'cookedrice'):
        owners[row['wallet']] = wallets.classify_wallet(client, row['wallet'])
        print(row['printed_label'], owners[row['wallet']]['type'], owners[row['wallet']].get('owners'), owners[row['wallet']].get('signer'), owners[row['wallet']]['signer_status'])
client.close()
Path('evidence/screenshot_reconstruction.json').write_text(json.dumps(dict(market=CID, rows=len(rows), window=[window[0], window[-1]], window_utc=[UTC(window[0]), UTC(window[-1])], matched_rows=top_score, table=table, accidental=acc, owners=owners), indent=1, ensure_ascii=False, default=str))
print(json.dumps(acc))
