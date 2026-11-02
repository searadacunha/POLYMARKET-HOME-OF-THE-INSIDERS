#!/usr/bin/env python3
"""Phase 11 : relecture des données brutes du collecteur (donnees/brut_p11/).
Reconstruit le carnet d'un jeton à l'instant t en n'utilisant QUE les messages reçus avant t (heure locale de réception) :
dernier `book` reçu, puis les `price_change` reçus ensuite, dans l'ordre. Fournit aussi les trades (last_trade_price) et RTDS.
Contrôle de cohérence : comparaison avec les instantanés REST /books (`--check`).
Usage : python3 p11_replay.py --check [--heures 3]"""
import os, sys, json, glob, heapq, bisect, argparse, collections, datetime as dt
import zstandard as zstd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW  # noqa: E402


def _files(kind, t0_ns, t1_ns):
    """Fichiers horaires couvrant [t0, t1] (une heure de marge de chaque côté)."""
    out = []
    h = dt.datetime.fromtimestamp(t0_ns / 1e9, dt.UTC).replace(minute=0, second=0, microsecond=0) - dt.timedelta(hours=1)
    end = dt.datetime.fromtimestamp(t1_ns / 1e9, dt.UTC) + dt.timedelta(hours=1)
    while h <= end:
        out += sorted(glob.glob(os.path.join(RAW, kind, h.strftime('%Y-%m-%d'), h.strftime('%H') + '*.jsonl.zst')))
        h += dt.timedelta(hours=1)
    return out


def _read(fp):
    """Lit un fichier zstd (trames successives, éventuellement tronqué en fin)."""
    with open(fp, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        try:
            with dctx.stream_reader(f, read_across_frames=True) as r:
                buf = b''
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    buf += chunk
                    *lines, buf = buf.split(b'\n')
                    for l in lines:
                        if l:
                            yield json.loads(l)
        except zstd.ZstdError:
            return


def iter_raw(kind, t0_ns, t1_ns):
    """Messages bruts [t_local_ns, connexion, message] dans [t0, t1], fusionnés par heure locale."""
    its = [(x for x in _read(fp) if t0_ns <= x[0] <= t1_ns) for fp in _files(kind, t0_ns, t1_ns)]
    return heapq.merge(*its, key=lambda x: x[0])


def events(msg):
    try:
        x = json.loads(msg) if isinstance(msg, str) else msg
    except Exception:
        return []
    return x if isinstance(x, list) else [x]


class Book:
    def __init__(self):
        self.bids, self.asks = {}, {}
        self.t_local = self.t_exch = None
        self.hash = None
        self.ok = False                         # vrai dès qu'un instantané complet a été reçu

    def snapshot(self, e, t):
        self.bids = {float(x['price']): float(x['size']) for x in e.get('bids', [])}
        self.asks = {float(x['price']): float(x['size']) for x in e.get('asks', [])}
        self.t_local, self.t_exch, self.hash, self.ok = t, int(e.get('timestamp') or 0), e.get('hash'), True

    def change(self, c, t, ts):
        side = self.bids if c['side'] == 'BUY' else self.asks
        p, s = float(c['price']), float(c['size'])
        if s <= 0:
            side.pop(p, None)
        else:
            side[p] = s
        self.t_local, self.t_exch, self.hash = t, ts, c.get('hash')

    def best(self):
        bb = max(self.bids) if self.bids else None
        ba = min(self.asks) if self.asks else None
        return bb, ba

    def view(self):
        bb, ba = self.best()
        mid = (bb + ba) / 2 if bb is not None and ba is not None else None
        return dict(best_bid=bb, best_ask=ba, mid=mid, spread=(ba - bb) if mid is not None else None,
                    bid_depth=sum(p * s for p, s in self.bids.items()), ask_depth=sum(p * s for p, s in self.asks.items()))

    def asks_sorted(self):
        return sorted(self.asks.items())

    def bids_sorted(self):
        return sorted(self.bids.items(), reverse=True)

    def copy(self):
        b = Book()
        b.bids, b.asks = dict(self.bids), dict(self.asks)
        b.t_local, b.t_exch, b.hash, b.ok = self.t_local, self.t_exch, self.hash, self.ok
        return b


class Timeline:
    """Carnets successifs d'un ensemble de jetons sur [t0, t1] ; book_at(asset, t) = carnet connu à t (messages reçus avant t)."""
    def __init__(self, assets, t0_ns, t1_ns, warm_s=1800):
        self.assets = set(assets)
        self.states = {a: [] for a in assets}        # liste de (t_local, Book figé)
        self.trades = []                              # last_trade_price
        cur = {a: Book() for a in assets}
        src = heapq.merge(iter_raw('ws_market', t0_ns - warm_s * 10 ** 9, t1_ns), iter_raw('rest_books', t0_ns - warm_s * 10 ** 9, t1_ns), key=lambda x: x[0])
        self.n_rest = 0
        for t, conn, msg in src:
            if isinstance(msg, dict):          # instantané REST (rafale après alerte ou toutes les 10 min) : carnet complet, connu à la réception
                for bk in msg.get('books') or []:
                    a = bk.get('asset_id')
                    if a in self.assets:
                        cur[a].snapshot(bk, t)
                        cur[a].source = 'rest'
                        self.states[a].append((t, cur[a].copy()))
                        self.n_rest += 1
                continue
            for e in events(msg):
                et = e.get('event_type')
                if et == 'book' and e.get('asset_id') in self.assets:
                    cur[e['asset_id']].snapshot(e, t)
                    self.states[e['asset_id']].append((t, cur[e['asset_id']].copy()))
                elif et == 'price_change':
                    ts = int(e.get('timestamp') or 0)
                    touched = set()
                    for c in e.get('price_changes', []):
                        a = c.get('asset_id')
                        if a in self.assets and cur[a].ok:
                            cur[a].change(c, t, ts)
                            touched.add(a)
                    for a in touched:
                        self.states[a].append((t, cur[a].copy()))
                elif et == 'last_trade_price' and e.get('asset_id') in self.assets:
                    self.trades.append(dict(t_local=t, t_exch=int(e.get('timestamp') or 0), asset=e['asset_id'], price=float(e['price']),
                                            size=float(e['size']), side=e.get('side'), fee_rate_bps=e.get('fee_rate_bps'), tx=e.get('transaction_hash')))
        self.keys = {a: [s[0] for s in v] for a, v in self.states.items()}

    def book_at(self, asset, t_ns):
        k = bisect.bisect_right(self.keys[asset], t_ns) - 1
        return self.states[asset][k][1] if k >= 0 else None

    def path(self, asset, t0_ns, t1_ns):
        a, b = bisect.bisect_left(self.keys[asset], t0_ns), bisect.bisect_right(self.keys[asset], t1_ns)
        return self.states[asset][a:b]


def rtds_rows(t0_ns, t1_ns, cids=None):
    out = []
    for t, conn, msg in iter_raw('rtds', t0_ns, t1_ns):
        if not isinstance(msg, str) or not msg.startswith('{'):
            continue
        p = (json.loads(msg).get('payload') or {})
        if p.get('transactionHash') and (cids is None or p.get('conditionId') in cids):
            out.append(dict(t_local=t, **p))
    return out


def check(heures=3):
    """Compare les instantanés REST (rest_10min) au carnet reconstruit à leur heure d'envoi."""
    import time
    t1 = time.time_ns()
    t0 = t1 - heures * 3600 * 10 ** 9
    snaps = []
    for t, tag, obj in iter_raw('rest_books', t0, t1):
        if tag == 'rest_10min' and isinstance(obj, dict) and obj.get('books'):
            for b in obj['books']:
                snaps.append((obj['t_envoi_ns'], b))
    rnd = __import__('random').Random(11)
    snaps = rnd.sample(snaps, min(300, len(snaps)))
    res = collections.Counter()
    by = collections.defaultdict(list)
    for t, b in snaps:
        by[b['asset_id']].append((t, b))
    for a, lst in list(by.items())[:150]:
        tl = Timeline([a], min(t for t, _ in lst) - 60 * 10 ** 9, max(t for t, _ in lst) + 10 ** 9, warm_s=3600)
        for t, b in lst:
            bk = tl.book_at(a, t)
            if bk is None:
                res['carnet_absent'] += 1; continue
            rb = max((float(x['price']) for x in b['bids']), default=None)
            ra = min((float(x['price']) for x in b['asks']), default=None)
            vb, va = bk.best()
            res['n'] += 1
            res['best_bid_egal'] += int(rb == vb)
            res['best_ask_egal'] += int(ra == va)
            lv = {float(x['price']): float(x['size']) for x in b['asks']}
            res['niveaux_ask_egaux'] += int(lv == bk.asks)
    return dict(res)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--heures', type=int, default=3)
    a = ap.parse_args()
    if a.check:
        print(check(a.heures))
