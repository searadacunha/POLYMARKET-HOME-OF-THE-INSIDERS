"""Contre-vérification : parmi les comptes remboursés à 5 000 $ ou plus dans le lot Kane, combien retirent dans les 10 minutes ? Contrôle positif sur les deux comptes nommés. Lecture seule."""
import json, time, urllib.parse, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'evidence/contre_verification_20261102'
k = json.load(open(OUT / 'calendrier_kane.json'))
T = 1793066300  # milieu du lot Kane, 01:58:20 UTC
named = {'0x3ed2c452f141c291adecb97ddfc72b1650acff3d', '0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40'}


def wd(user):
    q = dict(user=user, type='WITHDRAWAL', limit=50, sort_by='TIMESTAMP', sort_direction='DESC', exclude_deposits_withdrawals='false')
    time.sleep(.45)
    with urllib.request.urlopen(urllib.request.Request('https://data-api.polymarket.com/v2/activity?' + urllib.parse.urlencode(q), headers={'User-Agent': 'read-only'}), timeout=30) as r:
        return json.load(r).get('data', [])


for w in named:
    rows = wd(w)
    assert any(r['type'] == 'WITHDRAWAL' and 0 < r['timestamp'] - T < 300 for r in rows), ('contrôle positif', w, rows[:2])
print('contrôle positif ok')
big = sorted((e for e in k['events'] if e['amount'] >= 5000), key=lambda e: -e['amount'])
out = []
for e in big:
    try:
        rows = wd(e['user'])
    except Exception as x:
        out.append(dict(user=e['user'], amount=e['amount'], error=str(x)[:80]))
        continue
    after = sorted(r['timestamp'] - T for r in rows if r['type'] == 'WITHDRAWAL' and r['timestamp'] >= T)
    out.append(dict(user=e['user'], amount=e['amount'], n=len(rows), first_after_s=after[0] if after else None, named=e['user'] in named))
(OUT / 'retraits_apres_lot_kane.json').write_text(json.dumps(dict(T=T, rows=out), indent=0))
ok = [x for x in out if 'error' not in x]
un = [x for x in ok if not x['named']]
for lim in (300, 600, 3600, 86400):
    print(f'< {lim} s', sum(1 for x in un if x['first_after_s'] is not None and x['first_after_s'] < lim), '/', len(un))
print('erreurs', len(out) - len(ok), 'nommés', [(x['user'][:8], x['first_after_s']) for x in ok if x['named']])
print('liste < 600 s', [(x['user'][:10], round(x['amount']), x['first_after_s']) for x in un if x['first_after_s'] is not None and x['first_after_s'] < 600])
