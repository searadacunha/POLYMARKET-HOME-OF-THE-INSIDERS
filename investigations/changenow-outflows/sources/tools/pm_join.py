"""Offline join: which recipients own or are a Polymarket wallet (official factory logs), and which trading accounts appear in the Ballon d'Or tape. The tape is read from PolySentinel-ballon-dor-2026/derived/census_trades.jsonl.gz, never written. Writes state/pm_matches.csv, state/ballon_accounts.csv."""
import csv, gzip, json, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TAPE = Path.home() / 'Projects/PolySentinel-ballon-dor-2026/derived/census_trades.jsonl.gz'
own, is_wallet = defaultdict(list), {}
for name in ('deposit', 'safe'):
    p = ROOT / f'state/pm_wallets_{name}.csv.gz'
    if p.exists():
        with gzip.open(p, 'rt', newline='') as f:
            for w, o, b, t, tx in csv.reader(f):
                own[o].append((w, name, int(t), tx))
                is_wallet[w] = (o, name, int(t), tx)
print('wallets', len(is_wallet), 'owners', len(own), flush=True)
ballon = {}
with gzip.open(TAPE, 'rt') as f:
    for line in f:
        r = json.loads(line)
        w = r['w'].lower()
        v = ballon.setdefault(w, dict(n=0, usd=0.0, first=r['ts'], last=r['ts'], eids=set(), name=r.get('name') or ''))
        v['n'] += 1
        v['usd'] += float(r['size']) * float(r['price'])
        v['first'], v['last'] = min(v['first'], r['ts']), max(v['last'], r['ts'])
        v['eids'].add(str(r['eid']))
print('ballon tape accounts', len(ballon), flush=True)
with (ROOT / 'state/ballon_accounts.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['account', 'trades', 'usd', 'first', 'last', 'eids', 'name'])
    for a, v in ballon.items():
        w.writerow([a, v['n'], round(v['usd'], 2), v['first'], v['last'], '|'.join(sorted(v['eids'])), v['name']])
n = 0
with (ROOT / 'state/pm_matches.csv').open('w', newline='') as fo:
    w = csv.writer(fo)
    w.writerow('chain,recipient,tier,first_ts,first_source,first_tx,usd,classes,match_kind,account,wallet_kind,wallet_created,wallet_tx,in_ballon_tape,ballon_trades,ballon_usd,ballon_first'.split(','))
    for r in csv.DictReader(open(ROOT / 'state/recipients.csv')):
        a = r['recipient']
        hits = []
        if a in is_wallet:
            o, kind, t, tx = is_wallet[a]
            hits.append(('destinataire_est_le_wallet', a, kind, t, tx))
        for wl, kind, t, tx in own.get(a, ()):
            hits.append(('destinataire_proprietaire', wl, kind, t, tx))
        if a in ballon and not any(h[1] == a for h in hits):
            hits.append(('destinataire_compte_direct', a, 'eoa', '', ''))
        for kind, acct, wk, t, tx in hits:
            b = ballon.get(acct)
            w.writerow([r['chain'], a, r['tier'], r['first_ts'], r['first_source'], r['first_tx'], r['usd'], r['classes'], kind, acct, wk, t, tx, bool(b), b['n'] if b else '', round(b['usd'], 2) if b else '', b['first'] if b else ''])
            n += 1
print('match rows', n)
