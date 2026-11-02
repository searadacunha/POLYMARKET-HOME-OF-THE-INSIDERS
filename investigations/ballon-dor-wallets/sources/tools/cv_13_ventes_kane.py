"""Contre-vérification, data-api seulement, aucune chaîne : fenêtre d'activité des comptes du lot Kane, âge, ventes de Kane à 0,99 ou plus, marché Kane du 24 oct.
Reprend là où il s'est arrêté : une ligne JSONL par wallet, déjà lu = sauté. Remplace la version interrompue du 02/11 10:10, qui n'a rien écrit."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
API = 'https://data-api.polymarket.com'
CID = '0x12dc2b61723b2a54fc1947a307389b5f32038e7a29a0e936ad1fe410b969d06a'
T = 1793066300  # lot Kane, 27 oct. 01:58:20 UTC
DAY = 86400
BASE = dict(sort_by='TIMESTAMP', exclude_deposits_withdrawals='false')


def get(path, q, pause=.5):
    url = f'{API}{path}?' + urllib.parse.urlencode(q)
    for attempt in range(5):
        time.sleep(pause * (1 + 3 * attempt))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'read-only'}), timeout=40) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last = e
    raise RuntimeError(f'{url}: {last}')


def window(user, start, end):
    """Toutes les lignes de la fenêtre. complete=False si le plafond de pages coupe la lecture : jamais compté comme un zéro."""
    rows, cursor = [], None
    for _ in range(30):
        q = dict(user=user, limit=500, sort_direction='ASC', start=start, end=end, **BASE)
        if cursor:
            q['cursor'] = cursor
        b = get('/v2/activity', q)
        rows += [dict(t=r['timestamp'], k=r['type'], s=r.get('side'), u=r.get('usdc_size'), c=r.get('condition_id')) for r in b.get('data', [])]
        cursor = (b.get('pagination') or {}).get('next_cursor')
        if not cursor:
            return rows, True
    return rows, False


def resume(path):
    return {json.loads(l)['user'] for l in path.read_text().splitlines()} if path.exists() else set()


def append(path, row):
    with path.open('a') as f:
        f.write(json.dumps(row) + '\n')


# 1. Tout le lot à 5 000 $ ou plus : fenêtre de deux jours et premier événement du compte
batch = sorted((e for e in json.load(open(OUT / 'calendrier_kane.json'))['events'] if e['amount'] >= 5000), key=lambda e: -e['amount'])
path = OUT / 'fenetre_lot_kane.jsonl'
done = resume(path)
for e in batch:
    if e['user'] in done:
        continue
    try:
        rows, complete = window(e['user'], T - DAY, T + DAY)
        first = get('/v2/activity', dict(user=e['user'], limit=1, sort_direction='ASC', **BASE)).get('data', [])
        append(path, dict(user=e['user'], amount=e['amount'], redeem_ts=e['ts'], complete=complete, first_event=first[0]['timestamp'] if first else None, rows=rows))
    except RuntimeError as x:
        append(path, dict(user=e['user'], amount=e['amount'], redeem_ts=e['ts'], error=str(x)[:160]))
print('lot Kane lu', len(resume(path)), 'sur', len(batch), flush=True)

# 2. Marché Kane : ventes autour de l'annonce, et fenêtre du 24 oct.
market = OUT / 'trades_kane.json'
if not market.exists():
    out = {}
    for name, a, b in (('annonce', 1793052000, 1793066261), ('24_oct', 1792850400, 1792861200)):
        rows = get('/trades', dict(market=CID, start=a, end=b, limit=10000, takerOnly='true'))
        assert len(rows) < 10000, 'page pleine'
        out[name] = [dict(t=r['timestamp'], w=r['proxyWallet'].lower(), s=r['side'], o=r.get('outcome'), p=r['price'], z=r['size']) for r in rows]
    market.write_text(json.dumps(out))
tr = json.load(open(market))
print('lignes taker', {k: len(v) for k, v in tr.items()}, flush=True)

# 3. Vendeurs à 0,99 ou plus, 5 000 $ ou plus, dans les 30 min après la première vente à ce prix
hi = sorted((r for r in tr['annonce'] if str(r['o']).lower() == 'yes' and r['s'] == 'SELL' and r['p'] >= .99), key=lambda r: r['t'])
t0 = hi[0]['t']
sellers = {}
for r in hi:
    s = sellers.setdefault(r['w'], dict(usd=0., t=r['t']))
    s['usd'] += r['z'] * r['p']
pick = sorted((w for w, v in sellers.items() if v['usd'] >= 5000 and v['t'] - t0 <= 1800), key=lambda w: sellers[w]['t'])
print('première vente 0,99', t0, 'vendeurs', len(sellers), 'retenus', len(pick), flush=True)
path = OUT / 'fenetre_vendeurs_kane.jsonl'
done = resume(path)
for w in pick:
    if w in done:
        continue
    v = sellers[w]
    try:
        rows, complete = window(w, v['t'] - DAY, v['t'] + DAY)
        append(path, dict(user=w, usd=round(v['usd'], 2), sale_ts=v['t'], complete=complete, rows=rows))
    except RuntimeError as x:
        append(path, dict(user=w, usd=round(v['usd'], 2), sale_ts=v['t'], error=str(x)[:160]))
print('fini, vendeurs lus', len(resume(path)), flush=True)
